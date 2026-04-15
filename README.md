# elzeard2otf

## Utilisation

Conversion du format Elzeard au format Ouvretaferme :
- d'un plan de culture
- d'une liste de produits

## Attention

- Commencer par lire la documentation OTF : 
  - [Comment importer un plan de culture ?](https://www.ouvretaferme.org/doc/import:series)
  - [Importer des produits](https://www.ouvretaferme.org/doc/import:products)
- Ces scripts n'ont été testés que sur un cas particulier. Pour d'autres cas, il faudra probablement les faire évoluer. Cependant, il est possible qu'il suffise de modifier le fichier de configuration et les tableaux CSV des corrrespondances entre Elzeard et OTF (voir ci-dessous).
- Actuellement, OTF ne permet pas de définir les largeurs de planches et de passe-pieds à l'importation.

## Mode d'emploi

1) Préparer un environnement pour le programme :

- Avoir une distribution Python fonctionnelle (par ex : [Miniconda](https://www.anaconda.com/docs/getting-started/miniconda/install/overview))
- Clôner ce dépôt Git depuis un terminal : `git clone https://github.com/atantet/elzeard2otf.git` (alternativement, [télécharger l'archive du code](https://github.com/atantet/elzeard2otf/archive/refs/heads/main.zip) et la dé-zipper)
- Installer les paquets Python où utiliser la recette `environment.yml` pour le faire automatiquement depuis un terminal : 
```
conda env create -f environment.yml
conda activate elzeard2otf
```

2) Exporter les données Elzeard depuis la plateforme Elzeard :

  - **Les ITKs** : [*Planifier > Mes itinéraires de culture*](https://app.elzeard.co/itk/table) ;
  - **Les productions** : [*Paramétrer > Ma planification > Productions*](https://app.elzeard.co/plan/planningscenario/main/productions).
  - **Les séries** : [*Planifier > Ma planification > Séries*](https://app.elzeard.co/plan/planningscenario/main/surface) ;
  - **Les variétés** : [*Paramétrer > Mes intrants et consommables > Semences et plants*](https://app.elzeard.co/cultivars/enabled).

Sont nécéssaires,
- à la conversion du plan de culture : les ITKs, les séries et les variétés ;
- à la conversion des produits : les ITKs et les productions.

3) Dé-zipper les exports si besoin.

4) Modifier les chemins vers les fichiers Elzeard exportés dans `elzeard2otf/config.toml` (ou `elzeard2otf-main/config.toml`).

5) Pour la conversion du plan de culture, s'assurer que les listes des espèces (*Paramètres > Fonctionnalités > Production > Les espèces*) et du matériel (*Paramètres > Fonctionnalités > Production > Le matériel*) dans OTF sont suffisamment complètes pour correspondre aux données Elzeard (voir [Comment importer un plan de culture ?](https://www.ouvretaferme.org/doc/import:series)).

6) Modifier si besoin les tableurs CSV du dossier `correspondances/` qui permettent de faire le lien entre un nom Elzeard et un nom OTF :

 - `correspondance_especes.csv` : pour associer le nom d'une *Culture* (export ITK d'Elzeard) au nom d'une espèce OTF.
 - `correspondance_plateaux.csv` : pour faire correspondre le nombre de *Plants/plateau* (export variété d'Elzeard) au nom du matériel correspondant dans OTF. 
 - `correspondance_unite_rendement.csv` : appellations des unités et facteurs de conversion (peut-être à compléter).
 - `correspondance_type_implantation.csv` : appellations plantation/semis (ne devrait pas nécessiter de modification ; à noter que la catégorie *young-plant-bought* n'existe pas dans Elzeard, mais qu'elle est déduite à partir des dates de semis et de plantations).
 - `correspondance_mode.csv` : appellations plein champ/abri (ne devrait pas nécessiter de modification ; à noter qu'un mode mixte n'est pas possible sur Elzeard).

7) Exécuter le programme depuis le dossier `elzeard2otf/` (ou `elzeard2otf-main`) dans un terminal,

- pour la conversion du plan de culture :

```python conversion_plan_de_culture.py```

- pour la conversion des produits :

```python conversion_produits.py```

8) Importer le fichier `elzeard2otf/otf/plan_de_culture.csv` (ou `elzeard2otf-main/otf/plan_de_culture.csv`) depuis la page *Paramètres > Importer des données > Importer un plan de culture* d'OTF.