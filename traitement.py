import pandas as pd
import tomllib

FORMAT_DATE = "%Y-%m-%d"
CHEMIN_CONFIG = "config.toml"


def load_config():
    with open(CHEMIN_CONFIG, "rb") as f:
        config = tomllib.load(f)

    return config

def colonne_itks(colonne, s_prod, df_itks, df_itks_vivaces):
    return (s_prod.map(df_itks[colonne])
            .combine_first(s_prod.map(df_itks_vivaces[colonne])))

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

def conversion_unite_rendement(s_unite, m):
    return s_unite.map(m["otf"])

def conversion_unite_vente(s_unite, m):
    return s_unite.map(m["vente"])

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

def deduire_nom_produit(s_species, s_unite, m):
    return s_species + " " + s_unite.map(m["dans_nom_produit"])
