import csv
from sqlalchemy import create_engine, text

# --- Configuration ---
USER = 'postgres'
PASSWORD = ''
HOST = '127.0.0.1'
PORT = 5434
DB_NAME = 'sport'

# URL de connexion PostgreSQL
DB_URL = f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}"

# Dictionnaire : "Nom de la table" -> "Chemin du fichier"
CSV_FILES = {
    "data_es_activite_updated": "./csv/data-es-activite-updated.csv",
    "data_es_equipement_updated": "./csv/data-es-equipement-updated.csv",
    "data_es_installation_updated": "./csv/data-es-installation-updated.csv",
}

def main():
    # Création du moteur de base de données
    engine = None

    print("Début de l'importation...")
    try:
        engine = create_engine(DB_URL)

        # engine.begin() gère automatiquement la transaction (commit ou rollback)
        with engine.begin() as conn:
            for table_name, file_path in CSV_FILES.items():
                print(f"Traitement de '{file_path}' vers la table '{table_name}'...")

                try:
                    with open(file_path, mode='r', encoding='utf-8') as f:
                        # DictReader utilise la 1ère ligne comme clés pour chaque ligne suivante
                        reader = csv.DictReader(f, delimiter=';')
                        
                        # On récupère les noms des colonnes
                        headers = reader.fieldnames
                        if not headers:
                            print(f"  -> Fichier vide, ignoré.")
                            continue

                        # 1. Réinitialisation de la table
                        # On définit toutes les colonnes en TEXT pour éviter les erreurs de type
                        columns_def = ", ".join([f'"{col}" TEXT' for col in headers])
                        conn.execute(text(f'DROP TABLE IF EXISTS "{table_name}"'))
                        conn.execute(text(f'CREATE TABLE "{table_name}" ({columns_def})'))

                        # 2. Préparation de la requête d'insertion
                        # Exemple: INSERT INTO "table" VALUES (:col1, :col2, ...)
                        placeholders = ", ".join([f":{col}" for col in headers])
                        insert_query = text(f'INSERT INTO "{table_name}" VALUES ({placeholders})')

                        # 3. Exécution de l'insertion
                        # SQLAlchemy sait insérer une liste de dictionnaires directement
                        data = list(reader)
                        if data:
                            conn.execute(insert_query, data)
                            print(f"  -> {len(data)} lignes insérées.")

                except FileNotFoundError:
                    print(f"  -> ERREUR : Le fichier '{file_path}' est introuvable.")

        print("Importation terminée.")
    finally:
        if engine is not None:
            engine.dispose()
        print(f"Déconnexion de {HOST}:{PORT}.")

if __name__ == '__main__':
    main()
