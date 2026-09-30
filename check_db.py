import sqlite3

db = "data/db/nifty100.db"

conn = sqlite3.connect(db)
cur = conn.cursor()

print("\n=== TABLES ===")
print(cur.execute(
    "SELECT name FROM sqlite_master WHERE type = ?",
    ("table",)
).fetchall())

print("\n=== BALANCESHEET COLUMNS ===")
print(cur.execute("PRAGMA table_info(balancesheet)").fetchall())

for company in ["BEL", "HAL", "INDIGO", "TCS", "ABB"]:
    print(f"\n=== {company} ===")

    rows = cur.execute(
        """
        SELECT company_id, year, equity_capital, reserves,
               borrowings, total_liabilities, total_assets
        FROM balancesheet
        WHERE company_id = ?
        ORDER BY year DESC
        LIMIT 3
        """,
        (company,)
    ).fetchall()

    for row in rows:
        print(row)

conn.close()