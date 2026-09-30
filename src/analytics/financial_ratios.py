from pathlib import Path

import pandas as pd

# ============================================================
# REUSABLE FINANCIAL RATIO FUNCTIONS
# ============================================================

def net_profit_margin(net_profit, sales):
    if sales == 0:
        return None

    return net_profit / sales * 100


def return_on_equity(net_profit, equity):
    if equity <= 0:
        return None

    return net_profit / equity * 100


def debt_to_equity(debt, equity, cash=0):
    if equity == 0:
        return None

    return (debt - cash) / equity


def interest_coverage(ebit, interest):
    if interest == 0:
        return None

    return ebit / interest


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_DIR = PROJECT_ROOT / "output"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

P_AND_L_FILE = RAW_DIR / "profitandloss.xlsx"
BALANCE_SHEET_FILE = RAW_DIR / "balancesheet.xlsx"
CASH_FLOW_FILE = RAW_DIR / "cashflow.xlsx"

OUTPUT_EXCEL = OUTPUT_DIR / "financial_ratios.xlsx"
OUTPUT_CSV = OUTPUT_DIR / "financial_ratios.csv"


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def load_financial_excel(file_path):
    """
    Load Bluestock financial Excel files.

    The raw files contain:
        Row 1 = title
        Row 2 = actual column headers
        Row 3 onward = data

    Therefore header=1 is required.
    """

    df = pd.read_excel(
        file_path,
        header=1
    )

    # Remove completely empty rows
    df = df.dropna(
        how="all"
    ).copy()

    # Clean column names
    df.columns = [
        str(col).strip()
        for col in df.columns
    ]

    # Remove accidental unnamed columns if any
    df = df.loc[
        :,
        [
            col
            for col in df.columns
            if not str(col).startswith("Unnamed:")
        ]
    ]

    # Standardize company_id
    if "company_id" in df.columns:
        df["company_id"] = (
            df["company_id"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

    # Standardize year
    if "year" in df.columns:
        df["year"] = (
            df["year"]
            .astype(str)
            .str.strip()
        )

    return df


def convert_numeric(df, columns):
    """
    Safely convert financial columns to numeric.
    """

    for column in columns:

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    return df


# ============================================================
# LOAD PROFIT & LOSS
# ============================================================

print("=" * 70)
print("LOADING PROFIT & LOSS")
print("=" * 70)

pl = load_financial_excel(
    P_AND_L_FILE
)

pl_numeric = [
    "sales",
    "expenses",
    "operating_profit",
    "opm_percentage",
    "other_income",
    "interest",
    "depreciation",
    "profit_before_tax",
    "tax_percentage",
    "net_profit",
    "eps",
    "dividend_payout",
]

pl = convert_numeric(
    pl,
    pl_numeric
)

print("P&L shape:", pl.shape)
print("P&L columns:")
print(pl.columns.tolist())


# ============================================================
# LOAD BALANCE SHEET
# ============================================================

print()
print("=" * 70)
print("LOADING BALANCE SHEET")
print("=" * 70)

bs = load_financial_excel(
    BALANCE_SHEET_FILE
)

bs_numeric = [
    "equity_capital",
    "reserves",
    "borrowings",
    "other_liabilities",
    "total_liabilities",
    "fixed_assets",
    "cwip",
    "investments",
    "other_asset",
    "total_assets",
]

bs = convert_numeric(
    bs,
    bs_numeric
)

print("Balance Sheet shape:", bs.shape)
print("Balance Sheet columns:")
print(bs.columns.tolist())


# ============================================================
# LOAD CASH FLOW
# ============================================================

print()
print("=" * 70)
print("LOADING CASH FLOW")
print("=" * 70)

cf = load_financial_excel(
    CASH_FLOW_FILE
)

cf_numeric = [
    "operating_activity",
    "investing_activity",
    "financing_activity",
    "net_cash_flow",
]

cf = convert_numeric(
    cf,
    cf_numeric
)

print("Cash Flow shape:", cf.shape)
print("Cash Flow columns:")
print(cf.columns.tolist())


# ============================================================
# VALIDATE REQUIRED COLUMNS
# ============================================================

required_pl = [
    "company_id",
    "year",
    "net_profit",
]

required_bs = [
    "company_id",
    "year",
    "equity_capital",
    "reserves",
    "borrowings",
    "total_assets",
]

required_cf = [
    "company_id",
    "year",
    "operating_activity",
    "investing_activity",
]

missing_pl = [
    col for col in required_pl
    if col not in pl.columns
]

missing_bs = [
    col for col in required_bs
    if col not in bs.columns
]

missing_cf = [
    col for col in required_cf
    if col not in cf.columns
]

if missing_pl:
    raise ValueError(
        f"Missing P&L columns: {missing_pl}"
    )

if missing_bs:
    raise ValueError(
        f"Missing Balance Sheet columns: {missing_bs}"
    )

if missing_cf:
    raise ValueError(
        f"Missing Cash Flow columns: {missing_cf}"
    )


# ============================================================
# REMOVE DUPLICATES FROM SOURCE DATA
# ============================================================

pl = pl.drop_duplicates(
    subset=[
        "company_id",
        "year"
    ],
    keep="last"
)

bs = bs.drop_duplicates(
    subset=[
        "company_id",
        "year"
    ],
    keep="last"
)

cf = cf.drop_duplicates(
    subset=[
        "company_id",
        "year"
    ],
    keep="last"
)


# ============================================================
# SELECT BALANCE SHEET DATA
# ============================================================

bs_columns = [
    "company_id",
    "year",
    "equity_capital",
    "reserves",
    "borrowings",
    "other_liabilities",
    "total_liabilities",
    "fixed_assets",
    "cwip",
    "investments",
    "other_asset",
    "total_assets",
]

bs_small = bs[
    [
        col
        for col in bs_columns
        if col in bs.columns
    ]
].copy()


# ============================================================
# SELECT CASH FLOW DATA
# ============================================================

cf_columns = [
    "company_id",
    "year",
    "operating_activity",
    "investing_activity",
    "financing_activity",
    "net_cash_flow",
]

cf_small = cf[
    [
        col
        for col in cf_columns
        if col in cf.columns
    ]
].copy()


# ============================================================
# MERGE FINANCIAL DATA
# ============================================================

print()
print("=" * 70)
print("MERGING FINANCIAL DATA")
print("=" * 70)

df = pd.merge(
    pl,
    bs_small,
    on=[
        "company_id",
        "year"
    ],
    how="left"
)

df = pd.merge(
    df,
    cf_small,
    on=[
        "company_id",
        "year"
    ],
    how="left"
)


# ============================================================
# CALCULATING RATIOS
# ============================================================

print()
print("=" * 70)
print("CALCULATING RATIOS")
print("=" * 70)


# ============================================================
# SHAREHOLDERS' EQUITY
# ============================================================

df["shareholders_equity_cr"] = (
    df["equity_capital"].fillna(0)
    +
    df["reserves"].fillna(0)
)


# ============================================================
# RETURN ON EQUITY
# ============================================================

# Correct formula:
#
# ROE = Net Profit / Shareholders' Equity × 100
#
# IMPORTANT:
# Do NOT use total_assets here.
# Net Profit / Total Assets is ROA.

df["return_on_equity_pct"] = pd.NA

valid_equity = (
    df["shareholders_equity_cr"].notna()
    &
    (
        df["shareholders_equity_cr"] != 0
    )
)

df.loc[
    valid_equity,
    "return_on_equity_pct"
] = (
    df.loc[
        valid_equity,
        "net_profit"
    ]
    /
    df.loc[
        valid_equity,
        "shareholders_equity_cr"
    ]
) * 100

df["return_on_equity_pct"] = pd.to_numeric(
    df["return_on_equity_pct"],
    errors="coerce"
)


# ============================================================
# RETURN ON ASSETS
# ============================================================

# ROA = Net Profit / Total Assets × 100

df["return_on_assets_pct"] = pd.NA

valid_assets = (
    df["total_assets"].notna()
    &
    (
        df["total_assets"] != 0
    )
)

df.loc[
    valid_assets,
    "return_on_assets_pct"
] = (
    df.loc[
        valid_assets,
        "net_profit"
    ]
    /
    df.loc[
        valid_assets,
        "total_assets"
    ]
) * 100

df["return_on_assets_pct"] = pd.to_numeric(
    df["return_on_assets_pct"],
    errors="coerce"
)


# ============================================================
# DEBT TO EQUITY
# ============================================================

df["debt_to_equity"] = pd.NA

valid_equity = (
    df["shareholders_equity_cr"].notna()
    &
    (
        df["shareholders_equity_cr"] != 0
    )
)

df.loc[
    valid_equity,
    "debt_to_equity"
] = (
    df.loc[
        valid_equity,
        "borrowings"
    ]
    /
    df.loc[
        valid_equity,
        "shareholders_equity_cr"
    ]
)

df["debt_to_equity"] = pd.to_numeric(
    df["debt_to_equity"],
    errors="coerce"
)


# ============================================================
# FREE CASH FLOW
# ============================================================

# Cash Flow source contains:
#
# operating_activity
# investing_activity
# financing_activity
# net_cash_flow
#
# FCF proxy:
#
# Operating Cash Flow + Investing Activity
#
# Investing activity is normally negative when cash
# is spent on investments/capital expenditure.

df["free_cash_flow_cr"] = (
    df["operating_activity"].fillna(0)
    +
    df["investing_activity"].fillna(0)
)


# ============================================================
# ROE QUALITY
# ============================================================

def classify_roe_quality(roe):

    if pd.isna(roe):
        return "Not Available"

    if roe <= 0:
        return "Weak"

    if roe <= 15:
        return "Moderate"

    if roe <= 25:
        return "Strong"

    if roe <= 50:
        return "Very Strong"

    return "Extreme"


df["roe_quality"] = (
    df["return_on_equity_pct"]
    .apply(classify_roe_quality)
)


# ============================================================
# ROE RELIABILITY
# ============================================================

def classify_roe_reliability(row):

    roe = row["return_on_equity_pct"]
    equity = row["shareholders_equity_cr"]

    if pd.isna(roe):
        return "Not Available"

    if pd.isna(equity):
        return "Not Available"

    if equity <= 0:
        return "Review"

    # Extremely high ROE can happen because
    # the equity base is unusually small.
    if abs(roe) > 200:
        return "Review"

    return "Reliable"


df["roe_reliability"] = df.apply(
    classify_roe_reliability,
    axis=1
)

# ============================================================
# REMOVE DUPLICATES AFTER MERGE
# ============================================================

df = df.drop_duplicates(
    subset=[
        "company_id",
        "year"
    ],
    keep="last"
)


# ============================================================
# SORT
# ============================================================

df = df.sort_values(
    by=[
        "company_id",
        "year"
    ]
).reset_index(
    drop=True
)


# ============================================================
# SAVE EXCEL
# ============================================================

df.to_excel(
    OUTPUT_EXCEL,
    index=False
)


# ============================================================
# SAVE CSV
# ============================================================

df.to_csv(
    OUTPUT_CSV,
    index=False
)


# ============================================================
# SUCCESS SUMMARY
# ============================================================

print()
print("=" * 70)
print("FINANCIAL RATIOS GENERATED SUCCESSFULLY")
print("=" * 70)

print()
print("Shape:")
print(df.shape)

print()
print("Output Excel:")
print(OUTPUT_EXCEL)

print()
print("Output CSV:")
print(OUTPUT_CSV)

print()
print("Companies:")
print(
    df["company_id"].nunique()
)

print()
print("Rows per company:")
print(
    df.groupby("company_id")
    .size()
    .describe()
)


# ============================================================
# ROE VALIDATION
# ============================================================

print()
print("=" * 70)
print("ROE VALIDATION — MAR 2024")
print("=" * 70)

validation_companies = [
    "ABB",
    "BEL",
    "HAL",
    "INDIGO",
    "TCS",
]

validation = df[
    df["company_id"].isin(
        validation_companies
    )
    &
    df["year"].eq("Mar 2024")
].copy()

validation_columns = [
    "company_id",
    "year",
    "net_profit",
    "equity_capital",
    "reserves",
    "shareholders_equity_cr",
    "total_assets",
    "return_on_equity_pct",
    "return_on_assets_pct",
    "borrowings",
    "debt_to_equity",
    "free_cash_flow_cr",
    "roe_quality",
    "roe_reliability",
]

validation_columns = [
    col
    for col in validation_columns
    if col in validation.columns
]

if not validation.empty:

    print(
        validation[
            validation_columns
        ].to_string(
            index=False
        )
    )

else:

    print(
        "No Mar 2024 validation records found."
    )


# ============================================================
# EXTREME ROE CHECK
# ============================================================

print()
print("=" * 70)
print("EXTREME ROE CHECK")
print("=" * 70)

extreme_roe = df[
    df["return_on_equity_pct"]
    .abs()
    .gt(200)
].copy()

print(
    "Rows with |ROE| > 200%:",
    len(extreme_roe)
)

extreme_columns = [
    "company_id",
    "year",
    "net_profit",
    "equity_capital",
    "reserves",
    "shareholders_equity_cr",
    "return_on_equity_pct",
    "roe_quality",
    "roe_reliability",
]

extreme_columns = [
    col
    for col in extreme_columns
    if col in extreme_roe.columns
]

if not extreme_roe.empty:

    print(
        extreme_roe[
            extreme_columns
        ]
        .head(20)
        .to_string(
            index=False
        )
    )


# ============================================================
# FINAL ROE FORMULA CHECK
# ============================================================

print()
print("=" * 70)
print("FINAL ROE CHECK")
print("=" * 70)

for company in validation_companies:

    company_row = validation[
        validation["company_id"].eq(
            company
        )
    ]

    if company_row.empty:
        continue

    row = company_row.iloc[0]

    net_profit = row["net_profit"]
    equity = row["shareholders_equity_cr"]
    calculated_roe = row[
        "return_on_equity_pct"
    ]

    if pd.isna(equity) or equity == 0:

        print(
            f"{company}: ROE cannot be calculated"
        )

        continue

    expected_roe = (
        net_profit / equity
    ) * 100

    difference = abs(
        expected_roe
        -
        calculated_roe
    )

    print(
        f"{company}: "
        f"Expected={expected_roe:.4f}% | "
        f"Calculated={calculated_roe:.4f}% | "
        f"Difference={difference:.8f}"
    )


# ============================================================
# FINAL COLUMN CHECK
# ============================================================

print()
print("=" * 70)
print("FINAL COLUMN CHECK")
print("=" * 70)

required_output_columns = [
    "shareholders_equity_cr",
    "return_on_equity_pct",
    "return_on_assets_pct",
    "debt_to_equity",
    "free_cash_flow_cr",
    "roe_quality",
    "roe_reliability",
]

for column in required_output_columns:

    if column in df.columns:
        status = "OK"
    else:
        status = "MISSING"

    print(
        f"{column}: {status}"
    )


# ============================================================
# DONE
# ============================================================

print()
print("=" * 70)
print("DONE")
print("=" * 70)