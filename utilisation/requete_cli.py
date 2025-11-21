from sqlalchemy import create_engine, text

# --- Configuration ---
USER = 'postgres'
PASSWORD = ''
HOST = '127.0.0.1'
PORT = 5434
DB_NAME = 'sport'

# --- Dictionnaire des requêtes prédéfinies ---
PREDEFINED_QUERIES = {
    1: """
    SELECT "numero", "nom", "commune", "dep_nom"
    FROM "data_es_installation_updated"
    LIMIT 5
    """,
    2: """
    SELECT "type", COUNT(*) AS total_equipements
    FROM "data_es_equipement_updated"
    GROUP BY "type"
    ORDER BY total_equipements DESC
    LIMIT 5
    """,
    3: """
    SELECT i."reg_nom", COUNT(*) AS nb_equipements
    FROM "data_es_equipement_updated" e
    JOIN "data_es_installation_updated" i ON i."numero" = e."installation_numero"
    GROUP BY i."reg_nom"
    ORDER BY nb_equipements DESC
    LIMIT 5
    """,
    4: """
    SELECT i."commune", COUNT(DISTINCT a."aps_discipline") AS nb_disciplines
    FROM "data_es_installation_updated" i
    JOIN "data_es_equipement_updated" e ON i."numero" = e."installation_numero"
    JOIN "data_es_activite_updated" a ON e."numero" = a."equip_numero"
    GROUP BY i."commune"
    HAVING COUNT(DISTINCT a."aps_discipline") > 0
    ORDER BY nb_disciplines DESC, i."commune"
    LIMIT 5
    """
}

def main():
    # Connexion
    url = f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}"
    engine = create_engine(url)

    # --- Menu Console ---
    print(f"--- Menu Requetes SQL ({DB_NAME}) ---")
    print("0 : Ecrire une requete manuelle")
    for num, q in PREDEFINED_QUERIES.items():
        # On affiche juste la première ligne de la requête pour info
        preview = q.strip().split('\n')[0]
        print(f"{num} : {preview}...")
    
    try:
        choix = int(input("\nVotre choix (numero) : "))
    except ValueError:
        print("Erreur : Veuillez entrer un nombre.")
        return

    # --- Selection de la requete ---
    sql_query = ""
    
    if choix == 0:
        sql_query = input("Entrez votre requete SQL : ")
    elif choix in PREDEFINED_QUERIES:
        sql_query = PREDEFINED_QUERIES[choix]
        print(f"\nRequete selectionnee :\n{sql_query}")
    else:
        print("Choix invalide.")
        return

    # --- Execution ---
    try:
        with engine.connect() as conn:
            print("-" * 80)
            result = conn.execute(text(sql_query))

            # Si la requête ne retourne rien (ex: UPDATE/DELETE), on s'arrête là
            if not result.returns_rows:
                print("Requete executee avec succes (pas de lignes retournées).")
                return

            # Affichage des colonnes
            headers = list(result.keys())
            print(f"COLONNES : {headers}")
            print("-" * 80)

            # Affichage des données
            rows = result.fetchall()
            for row in rows:
                print(row)

            print("-" * 80)
            print(f"Total : {len(rows)} ligne(s).")

    except Exception as e:
        print(f"Erreur SQL : {e}")

if __name__ == "__main__":
    main()
