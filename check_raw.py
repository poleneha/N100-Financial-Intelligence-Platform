import pandas as pd

file = "data/raw/balancesheet.xlsx"

# Row 1 contains the actual column names
df = pd.read_excel(file, header=1)

print("RAW SHAPE:", df.shape)

print("\n=== COLUMNS ===")
print(df.columns.tolist())

for company in ["BEL", "HAL", "INDIGO", "TCS", "ABB"]:

    print(f"\n{'=' * 60}")
    print(company)
    print("=" * 60)

    x = df[
        df["company_id"]
        .astype(str)
        .str.strip()
        .eq(company)
    ]

    print(
        x[
            [
                "company_id",
                "year",
                "equity_capital",
                "reserves",
                "borrowings",
                "other_liabilities",
                "total_liabilities",
                "total_assets",
            ]
        ].tail(5).to_string(index=False)
    )