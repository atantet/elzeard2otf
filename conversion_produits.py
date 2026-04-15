from pathlib import Path
import pandas as pd
import traitement as tr


LABEL_ANNEE = 'Année de production'
LABEL_PRODUCTION = 'Production'

def main():
    # Configuration
    config = tr.load_config()

    # Chargement des fichiers Elzeard
    df_productions = pd.read_excel(
        Path(config["chemins_elzeard"]['productions']))
    itks_sheets = pd.read_excel(
        Path(config["chemins_elzeard"]['itks']),
        sheet_name=None, index_col=1)
    df_itks = itks_sheets['ITKs annuels']
    df_itks_vivaces = itks_sheets['ITKs vivaces']

    # Chargement des fichiers de correspondance
    s_correspondance_especes = pd.read_csv(
        Path(config["chemins_correspondances"]["especes"]),
        index_col=0).squeeze()
    df_correspondance_unite_rendement = pd.read_csv(
        Path(config["chemins_correspondances"]["unite_rendement"]),
        index_col=0)

    # Garder que l'année la plus récente
    df_productions = (
        df_productions.sort_values(LABEL_ANNEE, ascending=False)
        .drop_duplicates(subset=LABEL_PRODUCTION)
        .set_index(LABEL_PRODUCTION)
        .drop(columns=LABEL_ANNEE))

    # Indice des productions
    idx = df_productions.index
    s_prod = df_productions.reset_index()["Production"]
    s_prod.index = idx

    # Création du tableur de sortie
    columns = pd.read_csv(
        config["url_exemples"]["produits"]).columns
    df_dst = pd.DataFrame(columns=columns)

    # Espèces
    colonne = "Culture"
    s_culture = tr.colonne_itks(
        colonne, s_prod, df_itks, df_itks_vivaces)
    df_productions[colonne] = s_culture
    species_translated = s_culture.map(s_correspondance_especes) 
    df_dst["species"] = species_translated.combine_first(s_culture)

    # Unité
    s_unite = tr.colonne_itks(
        "Unité de rendement", s_prod, df_itks, df_itks_vivaces)
    df_dst["unit"] = tr.conversion_unite_vente(
        s_unite, df_correspondance_unite_rendement)

    # Nom du produit
    df_dst["name"] = tr.deduire_nom_produit(
        df_dst["species"], s_unite, df_correspondance_unite_rendement)

    # Type de produit
    df_dst["type"] = "plant"

    # Prix pour les particuliers
    df_dst["price_private"] = df_productions["Prix unitaire moyen"]
    
    # Prix pour les professionnels
    df_dst["price_pro"] = df_productions["Prix unitaire moyen"]

    # Taux de TVA
    df_dst["vat_rate"] = config["produits"]["taux_de_tva_par_defaut"]

    # Origine du produit
    df_dst["origin"] = config["produits"]["origine_par_defaut"]

    # Signe de qualité
    df_dst["quality"] = config["produits"]["qualite_par_defaut"]

    # Mode de distribution
    df_dst["distribution"] = config["produits"]["distribution_par_defaut"]
    
    # Écriture
    chemin = Path(config["chemins_otf"]["produits"])
    chemin.parent.mkdir(parents=True, exist_ok=True)
    df_dst.reset_index(drop=True).to_csv(chemin, index=False)


if __name__ == "__main__":
    main()
