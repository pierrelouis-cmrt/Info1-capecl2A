from sqlalchemy import create_engine, text

# --- Configuration ---
USER = 'postgres'
PASSWORD = ''
HOST = '127.0.0.1'
PORT = 5434
DB_TO_DROP = 'sport'  # <--- Nom de la base à supprimer (hardcodé)

def main():
    # Connexion à 'postgres' avec AUTOCOMMIT (obligatoire pour DROP DATABASE)
    url = f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/postgres"
    engine = None

    print(f"Suppression de la base '{DB_TO_DROP}'...")

    try:
        engine = create_engine(url, isolation_level="AUTOCOMMIT")
        with engine.connect() as conn:
            conn.execute(text(f'DROP DATABASE IF EXISTS "{DB_TO_DROP}"'))

        print("Terminé.")
    finally:
        if engine is not None:
            engine.dispose()
        print(f"Déconnexion de {HOST}:{PORT}.")

if __name__ == "__main__":
    main()
