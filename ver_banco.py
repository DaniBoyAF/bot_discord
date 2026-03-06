import sqlite3
conn = sqlite3.connect('f1_telemetry.db')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tabelas = cur.fetchall()
for t in tabelas:
    print('\n==', t[0], '==')
    cur.execute(f"PRAGMA table_info({t[0]})")
    for col in cur.fetchall():
        print(col)
conn.close()
