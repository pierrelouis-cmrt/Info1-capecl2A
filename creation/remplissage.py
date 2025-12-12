import csv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from psycopg2.errors import UniqueViolation, ForeignKeyViolation  # AJOUT

# --- Configuration de la base de données ---
USER = 'postgres'
PASSWORD = ''
HOST = '127.0.0.1'
PORT = 5434
DB_NAME = 'sport' # Nom de la base à remplir

DB_URL = f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}"

TAILLE_LOT = 1000  # Commit tous les 1000 lignes (évite les erreurs de mémoire de pyscopg2 en librérant les verrous)

# --- Configuration des Tables ---
TABLES = [
    {
        "nom_table": "data_es_installation_updated",
        "chemin_csv": "./csv/data-es-installation-updated.csv",
        "cle_primaire": ["numero"],
        "cle_etrangere": [],
        "colonnes_extra": []
    },
    {
        "nom_table": "data_es_equipement_updated",
        "chemin_csv": "./csv/data-es-equipement-updated.csv",
        "cle_primaire": ["numero"],
        "cle_etrangere": [
            ("installation_numero", "data_es_installation_updated", "numero")
        ],
        "colonnes_extra": []
    },
    {
        "nom_table": "data_es_activite_updated",
        "chemin_csv": "./csv/data-es-activite-updated.csv",
        "cle_primaire": ["activite_pk"],
        "cle_etrangere": [
            ("equip_numero", "data_es_equipement_updated", "numero")
        ],
        "colonnes_extra": ["activite_pk BIGSERIAL"]
    },
]

def main():
    engine = None
    print("DEMARRAGE DU PROGRAMME D'IMPORTATION")
    print("-" * 50)

    try:
        engine = create_engine(DB_URL)

        with engine.connect() as conn:

            for config in TABLES:
                table_nom = config["nom_table"]
                fichier_csv = config["chemin_csv"]
                
                print(f"\nTraitement de la table : {table_nom}")
                
                try:
                    with open(fichier_csv, mode="r", encoding="utf-8-sig") as f:
                        reader = csv.DictReader(f, delimiter=";")
                        
                        headers = reader.fieldnames
                        if not headers:
                            print("  -> Fichier vide, passage à la suite.")
                            continue

                        # ÉTAPE 1 : CREATE TABLE
                        definitions_colonnes = []

                        for col_extra in config["colonnes_extra"]:
                            definitions_colonnes.append(col_extra)

                        for col in headers:
                            definitions_colonnes.append(f'"{col}" TEXT')

                        if config["cle_primaire"]:
                            liste_pk = []
                            for pk_col in config["cle_primaire"]:
                                liste_pk.append(f'"{pk_col}"')
                            pk_str = ", ".join(liste_pk)
                            definitions_colonnes.append(f"PRIMARY KEY ({pk_str})")

                        for col_fk, table_ref, col_ref in config["cle_etrangere"]:
                            constraint = f'FOREIGN KEY ("{col_fk}") REFERENCES "{table_ref}"("{col_ref}")'
                            definitions_colonnes.append(constraint)

                        corps_table = ", ".join(definitions_colonnes)
                        requete_creation = f'CREATE TABLE "{table_nom}" ({corps_table})'

                        print("  -> Réinitialisation de la structure SQL...")
                        conn.execute(text(f'DROP TABLE IF EXISTS "{table_nom}" CASCADE'))
                        conn.execute(text(requete_creation))
                        conn.commit()

                        # ÉTAPE 2 : Préparation de l'insertion
                        liste_cols_propre = []
                        liste_params_propre = []
                        
                        for h in headers:
                            liste_cols_propre.append(f'"{h}"')
                            liste_params_propre.append(f':{h}')

                        cols_str = ", ".join(liste_cols_propre)
                        params_str = ", ".join(liste_params_propre)
                        
                        sql_insert = text(f'INSERT INTO "{table_nom}" ({cols_str}) VALUES ({params_str})')

                        # ÉTAPE 3 : Insertion ligne par ligne
                        print("  -> Insertion des données en cours...")
                        
                        succes = 0
                        doublons = 0
                        erreurs_fk = 0
                        autres_erreurs = 0
                        compteur_lot = 0

                        for ligne in reader:
                            
                            ligne_propre = {}
                            for cle, valeur in ligne.items():
                                if valeur == "" or valeur is None:
                                    ligne_propre[cle] = None
                                else:
                                    ligne_propre[cle] = valeur.strip()

                            try:
                                with conn.begin_nested():
                                    conn.execute(sql_insert, ligne_propre)
                                succes = succes + 1
                            
                            except IntegrityError as e:
                                # MODIF: Classes d'exception au lieu des codes
                                if isinstance(e.orig, UniqueViolation):
                                    doublons = doublons + 1
                                
                                elif isinstance(e.orig, ForeignKeyViolation):
                                    erreurs_fk = erreurs_fk + 1
                                
                                else:
                                    autres_erreurs = autres_erreurs + 1
                                    print(f"  -> Erreur SQL sur la ligne : {ligne_propre}")
                                    print(f"     Message : {e}")

                            except Exception as e:
                                print(f"  -> Erreur Python : {e}")

                            compteur_lot = compteur_lot + 1
                            if compteur_lot % TAILLE_LOT == 0:
                                conn.commit()

                        conn.commit()

                        print(f"  -> FINI. Bilan :")
                        print(f"     ✅ Insérés avec succès  : {succes}")
                        print(f"     ⚠️ Doublons ignorés     : {doublons}")
                        print(f"     ⛔️ Parents manquants (FK): {erreurs_fk}")
                        
                except FileNotFoundError:
                    print(f"  -> ERREUR FATALE : Le fichier '{fichier_csv}' est introuvable.")

    except Exception as global_e:
        print(f"Erreur générale de connexion ou de script : {global_e}")

    finally:
        if engine:
            engine.dispose()
        print("-" * 50)
        print("Fin du programme.")

if __name__ == '__main__':
    main()