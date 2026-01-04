import sqlite3, os

DB = os.path.join(os.path.dirname(__file__), "f1_telemetry.db")

conn = sqlite3.connect(DB)
cur = conn.cursor()

# lista todas as tabelas
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
tables = [r[0] for r in cur.fetchall()]

for t in tables:
    try:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        print(f"{t}: {cur.fetchone()[0]}")
    except Exception as e:
        print(f"{t}: erro -> {e}")

conn.close()
