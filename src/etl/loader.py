import pandas as pd
import sqlite3
import os

RAW_PATH = "data/raw"
DB_PATH = "data/db/nifty100.db"

conn = sqlite3.connect(DB_PATH)

files = {
    "companies": "companies.xlsx",
    "profitandloss": "profitandloss.xlsx",
    "balancesheet": "balancesheet.xlsx",
    "cashflow": "cashflow.xlsx",
    "analysis": "analysis.xlsx",
    "documents": "documents.xlsx",
    "prosandcons": "prosandcons.xlsx",
    "market_cap": "market_cap.xlsx",
    "peer_groups": "peer_groups.xlsx",
    "sectors": "sectors.xlsx",
    "stock_prices": "stock_prices.xlsx"
}

for table, file in files.items():

    path = os.path.join(RAW_PATH, file)

    if os.path.exists(path):

        try:
            df = pd.read_excel(path, header=1)

            # clean column names
            df.columns = (
                df.columns
                .astype(str)
                .str.strip()
                .str.lower()
                .str.replace(" ", "_")
            )

            # replace NaN
            df = df.where(pd.notnull(df), None)

            df.to_sql(
                table,
                conn,
                if_exists="replace",
                index=False
            )

            print(table, "loaded:", len(df))

        except Exception as e:
            print(table, "ERROR:", e)

    else:
        print(file, "Not Found")


conn.close()

print("Database loading completed.")