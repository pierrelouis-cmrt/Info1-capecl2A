from sqlalchemy import create_engine, text

# --- Configuration ---
USER = 'postgres'
PASSWORD = ''
HOST = '127.0.0.1'
PORT = 5434
DB_TO_CREATE = 'sport'  # Nom de la base à créer

def main():
    # On se connecte à la base 'postgres' par défaut avec AUTOCOMMIT
    # AUTOCOMMIT est obligatoire pour exécuter CREATE DATABASE
    url = f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/postgres"
    engine = None

    print(f"Création de la base '{DB_TO_CREATE}' sur {HOST}:{PORT}...")

    try:
        engine = create_engine(url, isolation_level="AUTOCOMMIT")
        with engine.connect() as conn:
            conn.execute(text(f'CREATE DATABASE "{DB_TO_CREATE}"'))
        print("Succès : La base de données a été créée.")
        
    except Exception as e:
        print(f"Erreur : {e}")
    finally:
        if engine is not None:
            engine.dispose()
        print(f"Déconnexion de {HOST}:{PORT}.")

if __name__ == "__main__":
    main()
