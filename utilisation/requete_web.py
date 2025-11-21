import os
from flask import Flask, render_template_string, request, jsonify
from sqlalchemy import create_engine, text, inspect

# --- Configuration ---
USER = 'postgres'
PASSWORD = ''
HOST = '127.0.0.1'
PORT = 5434
DB_NAME = 'sport'

# Configuration de l'application Flask
app = Flask(__name__)

# Connexion Base de Données
db_url = f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}"
engine = create_engine(db_url)

# --- Requêtes Prédéfinies ---
PREDEFINED_QUERIES = {
    "1": {
        "label": "Aperçu installations (5 lignes)",
        "sql": """
        SELECT "numero", "nom", "commune", "dep_nom"
        FROM "data_es_installation_updated"
        LIMIT 5
        """
    },
    "2": {
        "label": "Top 5 types d'équipements",
        "sql": """
        SELECT "type", COUNT(*) AS total_equipements
        FROM "data_es_equipement_updated"
        GROUP BY "type"
        ORDER BY total_equipements DESC
        LIMIT 5
        """
    },
    "3": {
        "label": "Équipements par région",
        "sql": """
        SELECT i."reg_nom", COUNT(*) AS nb_equipements
        FROM "data_es_equipement_updated" e
        JOIN "data_es_installation_updated" i ON i."numero" = e."installation_numero"
        GROUP BY i."reg_nom"
        ORDER BY nb_equipements DESC
        LIMIT 5
        """
    },
    "4": {
        "label": "Communes aux activités variées",
        "sql": """
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
}

# --- TEMPLATE HTML/CSS/JS ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Explorateur SQL Minimaliste</title>
    <style>
        :root {
            --bg: #ffffff;
            --surface: #f9f9f9; /* Gris très léger pour la sidebar */
            --border: #e0e0e0;
            --text: #111;
            --text-light: #666;
            --accent: #000; /* Noir pur pour les actions */
            --accent-hover: #333;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            height: 100vh;
        }

        /* --- Header Minimaliste --- */
        header {
            padding: 20px 40px;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            background: var(--bg);
        }
        h1 { font-size: 1.2rem; font-weight: 600; letter-spacing: -0.5px; margin: 0; }
        .badge { font-size: 0.8rem; color: var(--text-light); font-family: monospace; }

        /* --- Layout --- */
        .container {
            display: flex;
            flex: 1;
            overflow: hidden;
        }

        /* --- Sidebar Clean --- */
        .controls {
            width: 360px;
            background-color: var(--surface);
            border-right: 1px solid var(--border);
            padding: 30px;
            display: flex;
            flex-direction: column;
            gap: 25px;
            overflow-y: auto;
        }

        /* --- Tabs (Style texte simple) --- */
        .tabs { display: flex; gap: 20px; border-bottom: 1px solid var(--border); padding-bottom: 10px; margin-bottom: 10px; }
        .tab-btn {
            background: none; border: none; padding: 0;
            cursor: pointer; font-size: 0.9rem; font-weight: 500; color: #999;
            transition: color 0.2s;
        }
        .tab-btn:hover { color: #666; }
        .tab-btn.active { color: var(--accent); font-weight: 700; border-bottom: 2px solid black; padding-bottom: 10px; margin-bottom: -12px;}

        /* --- Form Elements (Minimalistes) --- */
        .tab-content { display: none; flex-direction: column; gap: 15px; animation: fadeIn 0.2s ease; }
        .tab-content.active { display: flex; }
        
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

        .section-label {
            font-size: 0.7rem; text-transform: uppercase; letter-spacing: 1px; 
            font-weight: 700; color: #aaa; margin-top: 10px; margin-bottom: 5px;
        }

        select, input, textarea {
            width: 100%; padding: 10px;
            border: 1px solid var(--border); border-radius: 0; /* Carré */
            background: var(--bg); color: var(--text);
            font-family: inherit; font-size: 0.9rem;
            box-sizing: border-box; transition: border 0.2s;
        }
        select:focus, input:focus, textarea:focus { outline: none; border-color: var(--accent); }
        textarea { resize: vertical; min-height: 100px; font-family: 'Courier New', monospace; }

        /* Row pour aligner des éléments */
        .row { display: flex; gap: 10px; }
        .col { flex: 1; }
        .col-2 { flex: 2; }

        .checkbox-wrapper { display: flex; align-items: center; gap: 8px; font-size: 0.9rem; }
        .checkbox-wrapper input { width: auto; }

        button.action-btn {
            background-color: var(--accent); color: white;
            border: none; padding: 12px; cursor: pointer;
            font-weight: 600; font-size: 0.9rem; letter-spacing: 0.5px;
            margin-top: 10px;
            transition: opacity 0.2s;
        }
        button.action-btn:hover { opacity: 0.8; }

        /* --- Results Area --- */
        .results {
            flex: 1; padding: 0; overflow: auto;
            background: var(--bg);
        }

        /* Table Clean */
        table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
        th, td {
            padding: 12px 20px; text-align: left;
            border-bottom: 1px solid var(--border); white-space: nowrap;
        }
        th {
            background-color: var(--bg); position: sticky; top: 0;
            font-weight: 600; z-index: 10;
        }
        tr:hover td { background-color: #f5f5f5; }
        .null-val { color: #ccc; font-style: italic; }

        /* States */
        .empty-state {
            display: flex; align-items: center; justify-content: center; height: 100%;
            color: #ccc; font-weight: 300; letter-spacing: 1px;
        }
        .error-msg { padding: 20px; background: #000; color: #fff; font-family: monospace; }
        .success-bar { 
            padding: 10px 20px; background: #f0f0f0; color: #666; 
            font-size: 0.8rem; border-bottom: 1px solid var(--border); 
            display: flex; justify-content: space-between;
        }
    </style>
</head>
<body>

    <header>
        <h1>Explorateur SQL <span style="color:#999; font-weight:300;">/ Web</span></h1>
        <div class="badge">{{ db_name }}</div>
    </header>

    <div class="container">
        <!-- Sidebar -->
        <div class="controls">
            
            <div class="tabs">
                <button class="tab-btn active" onclick="switchTab('predef')">Prédéfinies</button>
                <button class="tab-btn" onclick="switchTab('builder')">Générateur</button>
                <button class="tab-btn" onclick="switchTab('sql')">Custom</button>
            </div>

            <!-- 1. Prédéfinies -->
            <div id="tab-predef" class="tab-content active">
                <div>
                    <div class="section-label">CHOISIR</div>
                    <select id="predef-select" onchange="updatePreview()">
                        {% for key, val in queries.items() %}
                        <option value="{{ key }}">{{ val.label }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div>
                    <div class="section-label">APERÇU</div>
                    <textarea id="predef-preview" readonly style="color:#666; border:none; background:transparent; padding:0; height:auto;"></textarea>
                </div>
                <button class="action-btn" onclick="runQuery('predef')">EXÉCUTER</button>
            </div>

            <!-- 2. Générateur (Fonctionnalités avancées, Design simple) -->
            <div id="tab-builder" class="tab-content">
                
                <!-- Base -->
                <div>
                    <div class="section-label">TABLE & COLONNES</div>
                    <select id="builder-table" onchange="loadColumns()" style="margin-bottom:10px;">
                        <option value="">Chargement...</option>
                    </select>
                    
                    <div class="row">
                        <div class="col-2">
                            <select id="builder-col">
                                <option value="*">* (Toutes)</option>
                            </select>
                        </div>
                        <div class="col" style="display:flex; align-items:center;">
                            <div class="checkbox-wrapper">
                                <input type="checkbox" id="builder-distinct"> <label>Unique</label>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Filtre -->
                <div>
                    <div class="section-label">FILTRER (WHERE)</div>
                    <div class="row" style="margin-bottom:5px;">
                        <div class="col-2">
                            <select id="builder-where-col"><option value="">(Aucune colonne)</option></select>
                        </div>
                        <div class="col">
                            <select id="builder-where-op">
                                <option value="=">=</option>
                                <option value="LIKE">contient</option>
                                <option value=">">&gt;</option>
                                <option value="<">&lt;</option>
                            </select>
                        </div>
                    </div>
                    <input type="text" id="builder-where-val" placeholder="Valeur...">
                </div>

                <!-- Tri -->
                <div>
                    <div class="section-label">TRIER (ORDER BY)</div>
                    <div class="row">
                        <div class="col-2">
                            <select id="builder-order-col"><option value="">(Aucun tri)</option></select>
                        </div>
                        <div class="col">
                            <select id="builder-order-dir">
                                <option value="ASC">A-Z</option>
                                <option value="DESC">Z-A</option>
                            </select>
                        </div>
                    </div>
                </div>

                <!-- Limite -->
                <div>
                    <div class="section-label">LIMITE</div>
                    <input type="number" id="builder-limit" value="50">
                </div>

                <button class="action-btn" onclick="runQuery('builder')">GÉNÉRER</button>
            </div>

            <!-- 3. SQL Libre -->
            <div id="tab-sql" class="tab-content">
                <div>
                    <div class="section-label">CONSOLE SQL</div>
                    <textarea id="sql-free" placeholder="SELECT * FROM ..." style="background:#fff; color:#000; border-color:#ccc;"></textarea>
                </div>
                <button class="action-btn" onclick="runQuery('free')">EXÉCUTER</button>
            </div>

        </div>

        <!-- Results -->
        <div class="results" id="results-area">
            <div class="empty-state">Aucune donnée affichée.</div>
        </div>
    </div>

    <script>
        const queries = {{ queries | tojson }};

        document.addEventListener('DOMContentLoaded', () => {
            updatePreview();
            loadTables();
        });

        function switchTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            
            document.getElementById('tab-' + tabId).classList.add('active');
            event.target.classList.add('active');
        }

        function updatePreview() {
            const key = document.getElementById('predef-select').value;
            document.getElementById('predef-preview').value = queries[key].sql;
        }

        async function loadTables() {
            try {
                const res = await fetch('/metadata/tables');
                const tables = await res.json();
                const select = document.getElementById('builder-table');
                select.innerHTML = '';
                tables.forEach(t => {
                    const opt = document.createElement('option');
                    opt.value = t;
                    opt.innerText = t;
                    select.appendChild(opt);
                });
                if(tables.length > 0) {
                    select.value = tables[0];
                    loadColumns();
                }
            } catch (e) { console.error("Err tables", e); }
        }

        async function loadColumns() {
            const table = document.getElementById('builder-table').value;
            if(!table) return;
            
            try {
                const res = await fetch('/metadata/columns/' + table);
                const cols = await res.json();
                
                const fillSelect = (id, includeDefault, defaultText) => {
                    const el = document.getElementById(id);
                    el.innerHTML = '';
                    if(includeDefault) {
                        const def = document.createElement('option');
                        def.value = "";
                        def.innerText = defaultText;
                        el.appendChild(def);
                    }
                    cols.forEach(c => {
                        const opt = document.createElement('option');
                        opt.value = c;
                        opt.innerText = c;
                        el.appendChild(opt);
                    });
                };

                const mainSelect = document.getElementById('builder-col');
                mainSelect.innerHTML = '<option value="*">* (Toutes)</option>';
                cols.forEach(c => {
                    const opt = document.createElement('option');
                    opt.value = c;
                    opt.innerText = c;
                    mainSelect.appendChild(opt);
                });

                fillSelect('builder-where-col', true, '(Pas de filtre)');
                fillSelect('builder-order-col', true, '(Pas de tri)');

            } catch (e) { console.error("Err cols", e); }
        }

        async function runQuery(mode) {
            const resultsArea = document.getElementById('results-area');
            resultsArea.innerHTML = '<div class="empty-state">Chargement...</div>';

            let sql = "";

            if (mode === 'predef') {
                sql = document.getElementById('predef-preview').value;
            } 
            else if (mode === 'builder') {
                const table = document.getElementById('builder-table').value;
                let col = document.getElementById('builder-col').value;
                const distinct = document.getElementById('builder-distinct').checked;
                const limit = document.getElementById('builder-limit').value;

                // Logic Avancée
                const whereCol = document.getElementById('builder-where-col').value;
                const whereOp = document.getElementById('builder-where-op').value;
                const whereVal = document.getElementById('builder-where-val').value;
                const orderCol = document.getElementById('builder-order-col').value;
                const orderDir = document.getElementById('builder-order-dir').value;

                if (col !== '*') col = `"${col}"`;
                
                sql = `SELECT ${distinct ? 'DISTINCT ' : ''}${col} FROM "${table}"`;

                if (whereCol && whereVal) {
                    let safeVal = whereVal;
                    if (isNaN(safeVal) || whereOp === 'LIKE') {
                         if (whereOp === 'LIKE' && !safeVal.includes('%')) safeVal = `'%${safeVal}%'`;
                         else safeVal = `'${safeVal}'`;
                    }
                    sql += ` WHERE "${whereCol}" ${whereOp} ${safeVal}`;
                }

                if (orderCol) {
                    sql += ` ORDER BY "${orderCol}" ${orderDir}`;
                }

                sql += ` LIMIT ${limit}`;
            } 
            else {
                sql = document.getElementById('sql-free').value;
            }

            try {
                const response = await fetch('/execute', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ sql: sql })
                });
                
                const data = await response.json();

                if (data.error) {
                    resultsArea.innerHTML = `<div class="error-msg">ERREUR SQL:<br>${data.error}</div>`;
                    return;
                }

                renderTable(data.columns, data.rows);

            } catch (e) {
                resultsArea.innerHTML = `<div class="error-msg">Erreur Serveur: ${e}</div>`;
            }
        }

        function renderTable(cols, rows) {
            const area = document.getElementById('results-area');
            if (rows.length === 0) {
                area.innerHTML = '<div class="empty-state">Aucun résultat.</div>';
                return;
            }

            let html = `
                <div class="success-bar">
                    <span>Résultat</span>
                    <span>${rows.length} lignes</span>
                </div>
                <table>
                    <thead>
                        <tr>${cols.map(c => `<th>${c}</th>`).join('')}</tr>
                    </thead>
                    <tbody>
            `;

            rows.forEach(row => {
                html += '<tr>';
                row.forEach(val => {
                    const displayVal = val === null ? '<span class="null-val">NULL</span>' : val;
                    html += `<td>${displayVal}</td>`;
                });
                html += '</tr>';
            });

            html += '</tbody></table>';
            area.innerHTML = html;
        }
    </script>
</body>
</html>
"""

# --- Routes Flask ---

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, db_name=DB_NAME, queries=PREDEFINED_QUERIES)

@app.route('/execute', methods=['POST'])
def execute_sql():
    data = request.json
    sql_query = data.get('sql')
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text(sql_query))
            
            if not result.returns_rows:
                return jsonify({"columns": [], "rows": []})
            
            columns = list(result.keys())
            rows = [list(row) for row in result.fetchall()]
            
            return jsonify({"columns": columns, "rows": rows})
            
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/metadata/tables')
def get_tables():
    insp = inspect(engine)
    tables = insp.get_table_names()
    return jsonify(tables)

@app.route('/metadata/columns/<table_name>')
def get_columns(table_name):
    insp = inspect(engine)
    try:
        cols = [c['name'] for c in insp.get_columns(table_name)]
        return jsonify(cols)
    except Exception:
        return jsonify([])

if __name__ == '__main__':
    PORT_WEB = 5001
    print(f"Serveur prêt : http://127.0.0.1:{PORT_WEB}")
    app.run(debug=True, port=PORT_WEB)
