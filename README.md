# Base sport (PostgreSQL + Python)

Projet d'info de deuxième année pour charger des jeux de données d'équipements/activités sportives dans PostgreSQL, puis les explorer via trois interfaces (console, Tkinter ou web).

## Prérequis express

- Python 3 + `pip install sqlalchemy psycopg2-binary flask`
- PostgreSQL accessible (par défaut : `postgres` sans mot de passe sur `127.0.0.1:5434`)
- Les CSV sont déjà dans `csv/`. Si vos identifiants changent, mettez à jour `USER`, `PASSWORD`, `HOST`, `PORT` dans chaque script.

## 1. Pipeline de base (ordre conseillé)

1. **Optionnel : reset** – `python creation/suppression.py` supprime la base `sport` si elle existe.
2. **Création** – `python creation/creation.py` crée la base vide `sport`.
3. **Chargement CSV** – `python creation/remplissage.py` crée les tables `data_es_*_updated` et y injecte les CSV du dossier `csv/`.

## Explorer la base (dossier `utilisation/`)

- `requete_cli.py` : menu console simple pour lancer les requêtes prédéfinies ou saisir du SQL libre.
- `requete_tk.py` : interface tkinter avec trois onglets (prédéfinies, générateur de requête par table/colonne/limite, SQL libre) et résultats en tableaux.
- `requete_web.py` : lance un serveur web Flask (http://127.0.0.1:5001) ; propose des requêtes prédéfinies, un générateur, et du SQL libre. C'est essentiellement une version améliorée de l'interface tkinter.

## Notes utiles

- Le nom de la base créée : `sport`.
- Les noms de tables créées : `data_es_activite_updated`, `data_es_equipement_updated`, `data_es_installation_updated`.
- Le dossier `Scripts "tuto" moodle/` peut être considéré comme une archive.
