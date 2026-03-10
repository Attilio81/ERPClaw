"""Migrazione one-shot: aggiunge tabella categorie, categoria_id e scorta_minima ad articoli."""
import sqlite3

conn = sqlite3.connect("erp.db")
cur = conn.cursor()

cur.execute("""
    CREATE TABLE IF NOT EXISTS categorie (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT UNIQUE NOT NULL
    )
""")

for sql in [
    "ALTER TABLE articoli ADD COLUMN categoria_id INTEGER REFERENCES categorie(id)",
    "ALTER TABLE articoli ADD COLUMN scorta_minima INTEGER DEFAULT 0",
]:
    try:
        cur.execute(sql)
    except Exception as e:
        print(f"Skip (già eseguita?): {e}")

conn.commit()
conn.close()
print("Migrazione completata.")
