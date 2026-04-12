from pathlib import Path
import pandas as pd
import tomllib


CHEMIN_CONFIG = "config.toml"
URL_EXEMPLE_PLAN_DE_CULTURE = "https://www.ouvretaferme.org/asset/production/series/series.csv"
FORMAT_DATE = "%Y-%m-%d"

def load_config(chemin_config):
    with open(chemin_config, "rb") as f:
        config = tomllib.load(f)

    return config

def sem_elzeard_to_date(s):
    datestr = s.apply(lambda d: d + '.1' if pd.notna(d) else d)
    return pd.to_datetime(datestr, format="%Y.S.%W.%w")


def strftime(d):
    return d.dt.strftime(FORMAT_DATE)


def sem_elzeard_to_strftime(s):
    return strftime(sem_elzeard_to_date(s))


def conversion_date_semis(df_series, df_dst):
    date_plant = sem_elzeard_to_date(df_series["Semaine implantation"])
    td = pd.to_timedelta(df_series["Pépinière (jours)"].fillna(0), unit="D")
    date_semis = (date_plant - td).where(
        df_dst["planting_type"].values != "young-plant-bought")
    return strftime(date_semis).values


def conversion_date_implantation(df_series, df_dst):
    date_plant = sem_elzeard_to_date(df_series["Semaine implantation"])
    return strftime(date_plant.where(
        df_dst["planting_type"].values != "sowing")).values

    return strftime(date_plant).values

def colonne_itks(colonne, s_production, df_itks, df_itks_vivaces):
    return (s_production.map(df_itks[colonne])
            .combine_first(s_production.map(df_itks_vivaces[colonne])))


def conversion_unite_rendement(s_unite, m):
    return s_unite.map(m["otf"])


def conversion_rendement(s_unite, s_rendement, m):
    return s_rendement * s_unite.map(m["multiplicateur"])


def colonnes_espacements(use, s_use, s_surface, s_lineaire, s_densite,
                         s_interrang, s_surrang, s_nrangs, df_dst):
    df_dst[f"{use}_density"] = s_densite.where(s_use == use, None).values
    df_dst[f"{use}_spacing_plants"] = s_surrang.where(s_use == use, None).values
    if use == "block":
        df_dst[f"{use}_area"] = s_surface.where(
            s_use == use, None).values
        df_dst[f"{use}_spacing_rows"] = s_interrang.where(
            s_use == use, None).values
    elif use == "bed":
        df_dst[f"{use}_length"] = s_lineaire.where(s_use == use, None).values
        df_dst[f"{use}_rows"] = s_nrangs.where(s_use == use, None).values


def main():
    # Configuration
    config = load_config(CHEMIN_CONFIG)

    # Chargement des fichiers Elzeard
    df_series = pd.read_excel(
        Path(config["chemins_elzeard"]['series']), index_col=[1, 0])
    itks_sheets = pd.read_excel(
        Path(config["chemins_elzeard"]['itks']),
        sheet_name=None, index_col=1)
    df_itks = itks_sheets['ITKs annuels']
    df_itks_vivaces = itks_sheets['ITKs vivaces']
    df_varietes = pd.read_excel(
        Path(config["chemins_elzeard"]['export-variétés']))

    # Chargement des fichiers de correspondance
    s_correspondance_especes = pd.read_csv(
        Path(config["chemins_correspondances"]["especes"]),
        index_col=0).squeeze()
    s_correspondance_mode = pd.read_csv(
        Path(config["chemins_correspondances"]["mode"]),
        index_col=0).squeeze()
    df_correspondance_unite_rendement = pd.read_csv(
        Path(config["chemins_correspondances"]["unite_rendement"]),
        index_col=0)
    s_correspondance_plateaux = pd.read_csv(
        Path(config["chemins_correspondances"]["plateaux"]),
        index_col=0).squeeze()
    s_correspondance_type_implantation = pd.read_csv(
        Path(config["chemins_correspondances"]["type_implantation"]),
        index_col=0).squeeze()

    columns = pd.read_csv(URL_EXEMPLE_PLAN_DE_CULTURE).columns[:-2]
    df_dst = pd.DataFrame(columns=columns)

    idx = df_series.index
    s_production = df_series.reset_index()["Production"]
    s_production.index = idx

    # Nom de la série et saison
    df_dst['series_name'] = df_series['Nom de la série']
    df_dst['season'] = df_series.index.get_level_values(
        "Année de production")

    # Mode
    s_mode = colonne_itks(
        "Mode de culture", s_production, df_itks, df_itks_vivaces)
    df_dst['mode'] = s_mode

    # Espèces
    colonne = "Culture"
    s_culture = colonne_itks(
        colonne, s_production, df_itks, df_itks_vivaces)
    df_series[colonne] = s_culture
    species_translated = s_culture.map(s_correspondance_especes) 
    df_dst["species"] = species_translated.combine_first(s_culture)

    # Type de plantation
    df_dst["planting_type"] = df_series["Type d'implantation"].map(
        s_correspondance_type_implantation).where(
        ~((df_series["Type d'implantation"] == "Plantation") &
          df_series["Pépinière (jours)"].isnull()),
        "young-plant-bought")

    # Graines
    df_dst["seeds_per_hole"] = s_production.map(
        df_itks["Graines/plant ou poquet"])

    # Variété
    df_series["Variété"] = df_series["Variété"].where(
        ~df_series["Variété"].isnull(), "Indéter.").str.split(" - ").str[0]
    df_dst["variety_name"] = df_series["Variété"].where(
        df_series["Variété"] != "Indéter.", None)
    df_dst["variety_part"] = 100

    # Plants par plateau
    df_series = df_series.merge(
        df_varietes[["Culture", "Variété", "Plants/plateau"]]
        .drop_duplicates(["Culture", "Variété"]),
        on=["Culture", "Variété"], how="left").set_index(idx)
    df_dst["young_plants_tray"] = (df_series["Plants/plateau"]
                                   .fillna(-1).astype(int)
                                   .map(s_correspondance_plateaux))

    # Dates
    df_dst["sowing_date"] = conversion_date_semis(df_series, df_dst)
    df_dst["planting_date"] = conversion_date_implantation(df_series, df_dst)
    df_dst["first_harvest_date"] = sem_elzeard_to_strftime(
        df_series["Début récolte"])
    df_dst["last_harvest_date"] = sem_elzeard_to_strftime(
        df_series["Fin récolte"])

    # Écartements et densité
    s_densite = colonne_itks("Densité (plants/m²)",
                             s_production, df_itks, df_itks_vivaces)
    s_interrang = colonne_itks("Ecartement inter-rang (cm)",
                               s_production, df_itks, df_itks_vivaces)
    s_surrang = colonne_itks("Ecartement dans le rang (cm)",
                             s_production, df_itks, df_itks_vivaces)
    s_nrangs = colonne_itks("Nombre de rangs",
                            s_production, df_itks, df_itks_vivaces)
    s_densite = s_densite.where(s_interrang.isnull() & s_surrang.isnull(), None)
    s_use = colonne_itks("use", s_production, df_itks, df_itks_vivaces)
    df_dst["use"] = s_use

    for use in ("block", "bed"):
        colonnes_espacements(
            use, s_use, df_series["Surface (m²)"], df_series["Linéaire (m)"],
            s_densite, s_interrang, s_surrang, s_nrangs, df_dst)

    # Unité
    s_unite = colonne_itks(
        "Unité de rendement", s_production, df_itks, df_itks_vivaces)
    df_dst["harvest_unit"] = conversion_unite_rendement(
        s_unite, df_correspondance_unite_rendement)

    # Rendement
    s_rendement = colonne_itks(
        "Rendement prévisionnel", s_production, df_itks, df_itks_vivaces)
    df_dst["yield_expected_area"] = conversion_rendement(
        s_unite, s_rendement, df_correspondance_unite_rendement)

    # Écriture
    chemin = Path(config["chemins_otf"]["plan_de_culture"])
    chemin.parent.mkdir(parents=True, exist_ok=True)
    df_dst.reset_index(drop=True).to_csv(chemin, index=False)


if __name__ == "__main__":
    main()
