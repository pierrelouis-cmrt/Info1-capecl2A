import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from sqlalchemy import create_engine, text, inspect

# --- Configuration ---
USER = 'postgres'
PASSWORD = ''
HOST = '127.0.0.1'
PORT = 5434
DB_NAME = 'sport'

# --- Requêtes Prédéfinies ---
PREDEFINED_QUERIES = {
    "1. Aperçu installations (5 lignes)": """
    SELECT "numero", "nom", "commune", "dep_nom"
    FROM "data_es_installation_updated"
    LIMIT 5
    """,
    "2. Top 5 types d'équipements": """
    SELECT "type", COUNT(*) AS total_equipements
    FROM "data_es_equipement_updated"
    GROUP BY "type"
    ORDER BY total_equipements DESC
    LIMIT 5
    """,
    "3. Équipements par région": """
    SELECT i."reg_nom", COUNT(*) AS nb_equipements
    FROM "data_es_equipement_updated" e
    JOIN "data_es_installation_updated" i ON i."numero" = e."installation_numero"
    GROUP BY i."reg_nom"
    ORDER BY nb_equipements DESC
    LIMIT 5
    """,
    "4. Communes aux activités variées": """
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

class SportDBApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Explorateur SQL - Base: {DB_NAME}")
        self.root.geometry("900x600")
        self.configure_tree_style()

        # Connexion
        self.url = f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}"
        self.engine = create_engine(self.url)
        
        # Layout principal
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Zone du haut : Onglets de commande
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.X, pady=(0, 10))

        # --- Onglet 1 : Prédéfinies ---
        self.tab_predef = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_predef, text="Prédéfinies")
        self.setup_tab_predef()

        # --- Onglet 2 : Builder (Menus déroulant) ---
        self.tab_builder = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_builder, text="Générateur")
        self.setup_tab_builder()

        # --- Onglet 3 : Libre (SQL) ---
        self.tab_free = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_free, text="Custom")
        self.setup_tab_free()

        # Zone du bas : Résultats (Treeview)
        self.tree_frame = ttk.LabelFrame(self.main_frame, text="Résultats", padding="5")
        self.tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbars pour le tableau
        self.tree_scroll_y = ttk.Scrollbar(self.tree_frame)
        self.tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_scroll_x = ttk.Scrollbar(self.tree_frame, orient=tk.HORIZONTAL)
        self.tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.tree = ttk.Treeview(self.tree_frame, yscrollcommand=self.tree_scroll_y.set, xscrollcommand=self.tree_scroll_x.set)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.tag_configure("even", background="#ffffff", foreground="#111111")
        self.tree.tag_configure("odd", background="#f6f6f6", foreground="#111111")
        
        self.tree_scroll_y.config(command=self.tree.yview)
        self.tree_scroll_x.config(command=self.tree.xview)

        # Initialisation des données du builder
        self.load_db_metadata()

    def setup_tab_predef(self):
        frame = ttk.Frame(self.tab_predef, padding="10")
        frame.pack(fill=tk.X)
        
        lbl = ttk.Label(frame, text="Choisissez une requête :")
        lbl.pack(side=tk.LEFT, padx=5)

        self.combo_predef = ttk.Combobox(frame, values=list(PREDEFINED_QUERIES.keys()), width=50, state="readonly")
        self.combo_predef.current(0)
        self.combo_predef.pack(side=tk.LEFT, padx=5)
        self.combo_predef.bind("<<ComboboxSelected>>", self.update_predef_preview)

        btn = ttk.Button(frame, text="Exécuter", command=self.run_predefined)
        btn.pack(side=tk.LEFT, padx=5)

        preview_frame = ttk.Frame(self.tab_predef, padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(preview_frame, text="Aperçu SQL de la requête sélectionnée :").pack(anchor="w")
        self.txt_predef_preview = scrolledtext.ScrolledText(preview_frame, height=6, wrap=tk.NONE)
        self.txt_predef_preview.pack(fill=tk.BOTH, expand=True)
        self.txt_predef_preview.configure(state="disabled")
        self.update_predef_preview()

    def setup_tab_builder(self):
        frame = ttk.Frame(self.tab_builder, padding="10")
        frame.pack(fill=tk.X)

        # Choix Table
        ttk.Label(frame, text="Table :").pack(side=tk.LEFT)
        self.combo_tables = ttk.Combobox(frame, state="readonly", width=25)
        self.combo_tables.pack(side=tk.LEFT, padx=5)
        self.combo_tables.bind("<<ComboboxSelected>>", self.on_table_select)

        # Choix Colonne
        ttk.Label(frame, text="Colonne :").pack(side=tk.LEFT)
        self.combo_columns = ttk.Combobox(frame, state="readonly", width=20)
        self.combo_columns.pack(side=tk.LEFT, padx=5)

        # Limite
        ttk.Label(frame, text="Limite :").pack(side=tk.LEFT)
        self.entry_limit = ttk.Entry(frame, width=5)
        self.entry_limit.insert(0, "100")
        self.entry_limit.pack(side=tk.LEFT, padx=5)

        btn = ttk.Button(frame, text="Générer & Exécuter", command=self.run_builder)
        btn.pack(side=tk.LEFT, padx=10)

    def setup_tab_free(self):
        frame = ttk.Frame(self.tab_free, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        self.txt_sql = scrolledtext.ScrolledText(frame, height=5)
        self.txt_sql.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        btn = ttk.Button(frame, text="Exécuter SQL", command=self.run_free_sql)
        btn.pack(side=tk.RIGHT)

    # --- Logique ---

    def load_db_metadata(self):
        """Charge la liste des tables pour le Builder."""
        try:
            insp = inspect(self.engine)
            tables = insp.get_table_names()
            self.combo_tables['values'] = tables
            if tables:
                self.combo_tables.current(0)
                self.on_table_select(None)
        except Exception as e:
            messagebox.showerror("Erreur Connexion", f"Impossible de lire la structure de la base.\n{e}")

    def configure_tree_style(self):
        """Définit un style lisible pour le tableau de résultats."""
        style = ttk.Style()
        style.configure(
            "Treeview",
            rowheight=24,
            font=("Arial", 10),
            background="#ffffff",
            fieldbackground="#ffffff",
            foreground="#111111"
        )
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"), foreground="#111111")
        style.map("Treeview", background=[("selected", "#e5e5ff")])

    def update_predef_preview(self, event=None):
        """Affiche l'aperçu SQL de la requête prédéfinie sélectionnée."""
        key = self.combo_predef.get()
        sql = PREDEFINED_QUERIES.get(key, "").strip()
        self.txt_predef_preview.configure(state="normal")
        self.txt_predef_preview.delete("1.0", tk.END)
        self.txt_predef_preview.insert(tk.END, sql)
        self.txt_predef_preview.configure(state="disabled")

    def on_table_select(self, event):
        """Met à jour la liste des colonnes quand on change de table."""
        table_name = self.combo_tables.get()
        if not table_name: return
        
        try:
            insp = inspect(self.engine)
            cols = [c['name'] for c in insp.get_columns(table_name)]
            # Ajout de l'option "Toutes (*)"
            cols.insert(0, "*") 
            self.combo_columns['values'] = cols
            self.combo_columns.current(0)
        except Exception as e:
            print(f"Erreur lecture colonnes : {e}")

    def run_predefined(self):
        key = self.combo_predef.get()
        sql_query = PREDEFINED_QUERIES[key]
        self.execute_query(sql_query)

    def run_builder(self):
        table = self.combo_tables.get()
        col = self.combo_columns.get()
        limit = self.entry_limit.get()

        if col != "*":
            col = f'"{col}"'
        
        sql_query = f'SELECT {col} FROM "{table}" LIMIT {limit}'
        self.execute_query(sql_query)

    def run_free_sql(self):
        sql_query = self.txt_sql.get("1.0", tk.END).strip()
        if sql_query:
            self.execute_query(sql_query)

    def _compute_column_width(self, header, rows, idx):
        """Calcule une largeur de colonne lisible à partir d'un échantillon."""
        sample = rows[:50]  # on échantillonne pour rester léger
        max_len = len(str(header))
        for row in sample:
            cell = "" if row[idx] is None else str(row[idx])
            if len(cell) > max_len:
                max_len = len(cell)
        # Conversion approximative caractères -> pixels
        return min(max(90, max_len * 7), 260)

    def execute_query(self, sql_query):
        """Exécute la requête et met à jour le tableau."""
        # Nettoyer le tableau
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = []

        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(sql_query))
                
                if not result.returns_rows:
                    messagebox.showinfo("Succès", "Requête exécutée (pas de retour de données).")
                    return

                # Configuration des colonnes
                headers = list(result.keys())
                self.tree["columns"] = headers
                self.tree["show"] = "headings" # Cache la colonne d'index vide

                rows = result.fetchall()
                if not rows:
                    messagebox.showinfo("Résultat", "Aucune ligne retournée.")
                    return

                for idx, col in enumerate(headers):
                    width = self._compute_column_width(col, rows, idx)
                    self.tree.heading(col, text=col)
                    self.tree.column(col, width=width, anchor="w", stretch=True)

                # Insertion des données (en alternant la couleur pour la lisibilité)
                for i, row in enumerate(rows):
                    tag = "odd" if i % 2 else "even"
                    self.tree.insert("", tk.END, values=list(row), tags=(tag,))
                
        except Exception as e:
            messagebox.showerror("Erreur SQL", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = SportDBApp(root)
    root.mainloop()
