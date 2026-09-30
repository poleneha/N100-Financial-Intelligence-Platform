import pandas as pd
import os

root = "data"

for folder, _, files in os.walk(root):
    for file in files:
        if file.lower().endswith((".xlsx", ".xls", ".csv")):
            path = os.path.join(folder, file)

            try:
                if file.lower().endswith(".csv"):
                    df = pd.read_csv(path)
                    if df.astype(str).apply(
                        lambda col: col.str.contains("BEL", case=False, na=False)
                    ).any().any():
                        print("\nBEL FOUND:", path)
                        print(df.head())
                else:
                    sheets = pd.read_excel(path, sheet_name=None)

                    for sheet, df in sheets.items():
                        if df.astype(str).apply(
                            lambda col: col.str.contains("BEL", case=False, na=False)
                        ).any().any():
                            print("\nBEL FOUND:", path)
                            print("SHEET:", sheet)
                            print(df.head())

            except Exception:
                pass