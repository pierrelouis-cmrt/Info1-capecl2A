# Base sport (PostgreSQL + Python)

Projet d'info n°1 de 2A pour charger des jeux de données d'équipements/activités sportives dans PostgreSQL, puis les explorer via trois interfaces (console, Tkinter ou web).

> Elsa Mauron, Camille Simond, Pierre-Louis Camaret

## Prérequis

- Python 3 + `pip install sqlalchemy psycopg2-binary flask`
- PostgreSQL accessible (par défaut : `postgres` sans mot de passe sur `127.0.0.1:5434`)
- Les CSV sont déjà dans `csv/`. Si vos identifiants changent, mettez à jour `USER`, `PASSWORD`, `HOST`, `PORT` dans chaque script.

## 1. Ordre conseillé d'éxécution (dossier `creation/`)

1. **Optionnel : reset** – `python creation/suppression.py` supprime la base `sport` si elle existe.
2. **Création** – `python creation/creation.py` crée la base vide `sport`.
3. **Chargement CSV** – `python creation/remplissage.py` crée les tables `data_es_*_updated` et y injecte les CSV du dossier `csv/`.

## Explorer la base (dossier `utilisation/`)

- `requete_cli.py` : menu console simple pour lancer les requêtes prédéfinies ou saisir du SQL libre.
- `requete_tk.py` : interface tkinter avec trois onglets (prédéfinies, générateur de requête par table/colonne/limite, SQL libre) et résultats en tableaux.
- `requete_web.py` : lance un serveur web Flask (http://127.0.0.1:5001) ; propose des requêtes prédéfinies, un générateur (builder), et du SQL libre. C'est essentiellement une version web de l'interface tkinter : css généré rapidement par IA, js équivalent au Python mais avec affichage en tableaux directement dans la page et un builder plus complet que dans Tkinter.

## Notes utiles

- Le nom de la base créée : `sport`.
- Les noms de tables créées : `data_es_activite_updated`, `data_es_equipement_updated`, `data_es_installation_updated`.

## Exemples de résultats de requête

- **Installations (5 premières lignes)**

  ```sql
  SELECT "numero", "nom", "commune", "dep_nom"
  FROM "data_es_installation_updated"
  LIMIT 5;
  ```

  Exemple de sortie :

  | numero     | nom                              | commune                 | dep_nom |
  |------------|----------------------------------|-------------------------|---------|
  | I973130006 | La Mangrove                      | Montsinéry-Tonnegrande  | Guyane  |
  | I275070005 | Local de l'ASA Cyclo             | Saint-André-de-l'Eure   | Eure    |
  | I275070009 | Terrain de pétanque              | Saint-André-de-l'Eure   | Eure    |
  | I275140001 | La Boucle des Bois               | Saint-Aubin-du-Thenney  | Eure    |
  | I275160004 | Stade de Saint-Aubin-le-Vertueux | Treis-Sants-en-Ouche    | Eure    |

- **Top types d'équipements**

  ```sql
  SELECT "type", COUNT(*) AS total_equipements
  FROM "data_es_equipement_updated"
  GROUP BY "type"
  ORDER BY total_equipements DESC
  LIMIT 5;
  ```

  Exemple de sortie :

  | type                    | total_equipements |
  |-------------------------|-------------------|
  | Court de tennis         | 38758             |
  | Terrain de football     | 36636             |
  | Boucle de randonnée     | 29688             |
  | Multisports/City-stades | 25222             |
  | Terrain de pétanque     | 21186             |

- **Équipements par région**

  ```sql
  SELECT "data_es_installation_updated"."reg_nom", COUNT(*) AS nb_equipements
  FROM "data_es_installation_updated"
  JOIN "data_es_equipement_updated"
    ON "data_es_installation_updated"."numero" = "data_es_equipement_updated"."installation_numero"
  GROUP BY "data_es_installation_updated"."reg_nom"
  ORDER BY nb_equipements DESC
  LIMIT 5;
  ```

  Exemple de sortie :

  | reg_nom              | nb_equipements |
  |----------------------|----------------|
  | Auvergne-Rhône-Alpes | 42967          |
  | Occitanie            | 39497          |
  | Nouvelle-Aquitaine   | 36227          |
  | Grand Est            | 31960          |
  | Île-de-France        | 30035          |

- **Nombre de disciplines par commune**

  ```sql
  SELECT "data_es_installation_updated"."commune",
         COUNT(DISTINCT "data_es_activite_updated"."aps_discipline") AS nb_disciplines
  FROM "data_es_installation_updated"
  JOIN "data_es_equipement_updated"
    ON "data_es_installation_updated"."numero" = "data_es_equipement_updated"."installation_numero"
  JOIN "data_es_activite_updated"
    ON "data_es_equipement_updated"."numero" = "data_es_activite_updated"."equip_numero"
  GROUP BY "data_es_installation_updated"."commune"
  HAVING COUNT(DISTINCT "data_es_activite_updated"."aps_discipline") > 0
  ORDER BY nb_disciplines DESC, "data_es_installation_updated"."commune"
  LIMIT 5;
  ```

  Exemple de sortie :

  | commune         | nb_disciplines |
  |-----------------|----------------|
  | Toulouse        | 62             |
  | Le Mans         | 59             |
  | Nîmes           | 58             |
  | Aix-en-Provence | 56             |
  | Nantes          | 54             |
