import sqlite3
import os

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "f1_telemetry.db"))
# ⚠️ ajuste o caminho relativo conforme a pasta do projeto
# Se o migra.py está na MESMA pasta do main.py, use:
# DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "f1_telemetry.db"))

def migrar_pneu_por_volta():
    """Cria tabela pneu_por_volta se não existir (desgaste a cada volta)."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS pneu_por_volta (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sessao_id   INTEGER NOT NULL,
                piloto_id   INTEGER NOT NULL,
                numero_volta INTEGER NOT NULL,
                stint_numero INTEGER,
                tipo_pneu   TEXT,
                idade_pneu  INTEGER,
                desgaste_rl REAL DEFAULT 0,
                desgaste_rr REAL DEFAULT 0,
                desgaste_fl REAL DEFAULT 0,
                desgaste_fr REAL DEFAULT 0,
                desgaste_medio REAL DEFAULT 0,
                timestamp   REAL,
                FOREIGN KEY (sessao_id) REFERENCES sessoes(id),
                FOREIGN KEY (piloto_id) REFERENCES pilotos(id),
                UNIQUE(sessao_id, piloto_id, numero_volta)
            )
        ''')
        conn.commit()
        conn.close()
        print("✅ Tabela pneu_por_volta pronta.")
    except Exception as e:
        print(f"Erro migrar_pneu_por_volta: {e}")

if __name__ == "__main__":
    migrar_pneu_por_volta()