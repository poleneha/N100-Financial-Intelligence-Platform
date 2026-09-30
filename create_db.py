import sqlite3

db_path = "data/db/nifty100.db"
schema_path = "db/schema.sql"

conn = sqlite3.connect(db_path)

with open(schema_path, "r") as file:
    schema = file.read()

conn.executescript(schema)

conn.commit()
conn.close()

print("Database created successfully")