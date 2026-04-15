from pathlib import Path
import pandas as pd
import traitement as tr


def main():
    # Configuration
    config = tr.load_config()

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

    # Création du tableur de sortie
    columns = pd.read_csv(
        config["url_exemples"]["plan_de_culture"]).columns[:-2]
    df_dst = pd.DataFrame(columns=columns)

    # Indice des productions
    idx = df_series.index
    s_prod = df_series.reset_index()["Production"]
    s_prod.index = idx

    # Nom de la série et saison
    df_dst['series_name'] = df_series['Nom de la série']
    df_dst['season'] = df_series.index.get_level_values(
        "Année de production")

    # Mode
    df_dst['mode'] = tr.colonne_itks(
        "Mode de culture", s_prod, df_itks, df_itks_vivaces).map(
            s_correspondance_mode)

    # Espèces
    colonne = "Culture"
    s_culture = tr.colonne_itks(
        colonne, s_prod, df_itks, df_itks_vivaces)
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
    df_dst["seeds_per_hole"] = s_prod.map(
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
    df_dst["young_plants_tray"] = (
        df_series["Plants/plateau"]
        .fillna(-1).astype(int).map(s_correspondance_plateaux))

    # Dates
    df_dst["sowing_date"] = tr.conversion_date_semis(df_series, df_dst)
    df_dst["planting_date"] = tr.conversion_date_implantation(
        df_series, df_dst)
    df_dst["first_harvest_date"] = tr.sem_elzeard_to_strftime(
        df_series["Début récolte"])
    df_dst["last_harvest_date"] = tr.sem_elzeard_to_strftime(
        df_series["Fin récolte"])

    # Écartements et densité
    s_densite = tr.colonne_itks("Densité (plants/m²)",
                                s_prod, df_itks, df_itks_vivaces)
    s_interrang = tr.colonne_itks("Ecartement inter-rang (cm)",
                                  s_prod, df_itks, df_itks_vivaces)
    s_surrang = tr.colonne_itks("Ecartement dans le rang (cm)",
                                s_prod, df_itks, df_itks_vivaces)
    s_nrangs = tr.colonne_itks("Nombre de rangs",
                               s_prod, df_itks, df_itks_vivaces)
    s_densite = s_densite.where(
        s_interrang.isnull() & s_surrang.isnull(), None)
    s_use = tr.colonne_itks("use", s_prod, df_itks, df_itks_vivaces)
    df_dst["use"] = s_use

    for use in ("block", "bed"):
        tr.colonnes_espacements(
            use, s_use, df_series["Surface (m²)"], df_series["Linéaire (m)"],
            s_densite, s_interrang, s_surrang, s_nrangs, df_dst)

    # Unité
    s_unite = tr.colonne_itks(
        "Unité de rendement", s_prod, df_itks, df_itks_vivaces)
    df_dst["harvest_unit"] = tr.conversion_unite_rendement(
        s_unite, df_correspondance_unite_rendement)

    # Rendement
    s_rendement = tr.colonne_itks(
        "Rendement prévisionnel", s_prod, df_itks, df_itks_vivaces)
    df_dst["yield_expected_area"] = tr.conversion_rendement(
        s_unite, s_rendement, df_correspondance_unite_rendement)

    # Écriture
    chemin = Path(config["chemins_otf"]["plan_de_culture"])
    chemin.parent.mkdir(parents=True, exist_ok=True)
    df_dst.reset_index(drop=True).to_csv(chemin, index=False)


if __name__ == "__main__":
    main()
