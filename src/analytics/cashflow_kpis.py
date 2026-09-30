import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path


# ============================================================
# CASH FLOW INTELLIGENCE
# NIFTY 100 FINANCIAL INTELLIGENCE PLATFORM
# ============================================================

print("=" * 70)
print("CASH FLOW INTELLIGENCE")
print("=" * 70)


# ============================================================
# PATHS
# ============================================================

DB_PATH = "data/db/nifty100.db"

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

EXCEL_OUTPUT = OUTPUT_DIR / "cashflow_intelligence.xlsx"
CSV_OUTPUT = OUTPUT_DIR / "capital_allocation.csv"


# ============================================================
# CASH FLOW KPI FUNCTIONS
# ============================================================
# These functions are also used by tests/test_cashflow.py
# ============================================================

def free_cash_flow(cfo, investing_cash_flow):
    """
    Free Cash Flow = CFO + Investing Cash Flow

    Example:
        CFO = 100
        Investing = -50
        FCF = 50
    """

    if cfo is None or investing_cash_flow is None:
        return None

    return cfo + investing_cash_flow


def capex_intensity(capex, cfo):
    """
    CapEx Intensity = |CapEx| / CFO * 100

    Example:
        CapEx = -50
        CFO = 1000
        Result = 5
    """

    if cfo is None or cfo == 0:
        return None

    if capex is None:
        return None

    return abs(capex) / cfo * 100


def fcf_conversion(fcf, operating_profit):
    """
    FCF Conversion = FCF / Operating Profit * 100
    """

    if operating_profit is None or operating_profit == 0:
        return None

    if fcf is None:
        return None

    return fcf / operating_profit * 100


def cfo_quality(cfo, pat):
    """
    Simple CFO quality classification.

    Used by unit tests.
    """

    if cfo is None:
        return None

    if cfo <= 0:
        return "Weak"

    if pat is None:
        return "Positive CFO"

    if pat <= 0:
        return "Positive CFO"

    ratio = cfo / pat

    if ratio >= 1.20:
        return "High Quality"

    if ratio >= 1.00:
        return "Strong"

    if ratio >= 0.80:
        return "Moderate"

    return "Weak"


# ============================================================
# LOAD DATABASE
# ============================================================

print("\nLoading database tables...")

if not Path(DB_PATH).exists():
    raise FileNotFoundError(
        f"Database not found: {DB_PATH}"
    )

conn = sqlite3.connect(DB_PATH)


cashflow = pd.read_sql(
    "SELECT * FROM cashflow",
    conn
)

profit_loss = pd.read_sql(
    "SELECT * FROM profitandloss",
    conn
)

companies = pd.read_sql(
    "SELECT * FROM companies",
    conn
)

conn.close()


print("Cash flow shape:", cashflow.shape)
print("Profit & Loss shape:", profit_loss.shape)
print("Companies shape:", companies.shape)


# ============================================================
# SHOW COLUMNS
# ============================================================

print("\nCash flow columns:")
print(cashflow.columns.tolist())

print("\nProfit & Loss columns:")
print(profit_loss.columns.tolist())


# ============================================================
# CLEAN COLUMN NAMES
# ============================================================

cashflow.columns = [
    str(c).strip().lower()
    for c in cashflow.columns
]

profit_loss.columns = [
    str(c).strip().lower()
    for c in profit_loss.columns
]

companies.columns = [
    str(c).strip().lower()
    for c in companies.columns
]


# ============================================================
# CHECK REQUIRED COMPANY COLUMNS
# ============================================================

if "id" not in companies.columns:
    raise ValueError(
        "Companies table must contain an 'id' column."
    )

if "company_id" not in cashflow.columns:
    raise ValueError(
        "Cash flow table must contain a 'company_id' column."
    )

if "company_id" not in profit_loss.columns:
    raise ValueError(
        "Profit & Loss table must contain a 'company_id' column."
    )


# ============================================================
# STANDARDIZE COMPANY IDS
# ============================================================

cashflow["company_id"] = (
    cashflow["company_id"]
    .astype(str)
    .str.upper()
    .str.strip()
)

profit_loss["company_id"] = (
    profit_loss["company_id"]
    .astype(str)
    .str.upper()
    .str.strip()
)

companies["id"] = (
    companies["id"]
    .astype(str)
    .str.upper()
    .str.strip()
)


# ============================================================
# CLEAN YEAR
# ============================================================

if "year" not in cashflow.columns:
    raise ValueError(
        "Cash flow table must contain a 'year' column."
    )

if "year" not in profit_loss.columns:
    raise ValueError(
        "Profit & Loss table must contain a 'year' column."
    )

cashflow["year"] = (
    cashflow["year"]
    .astype(str)
    .str.strip()
)

profit_loss["year"] = (
    profit_loss["year"]
    .astype(str)
    .str.strip()
)


# ============================================================
# REQUIRED CASH FLOW COLUMNS
# ============================================================

required_columns = [
    "company_id",
    "year",
    "operating_activity",
    "investing_activity",
    "financing_activity",
    "net_cash_flow"
]

missing_columns = [
    col
    for col in required_columns
    if col not in cashflow.columns
]

if missing_columns:
    raise ValueError(
        "Missing cash flow columns: "
        + str(missing_columns)
    )


# ============================================================
# NUMERIC CONVERSION
# ============================================================

cashflow_numeric = [
    "operating_activity",
    "investing_activity",
    "financing_activity",
    "net_cash_flow"
]

for col in cashflow_numeric:

    cashflow[col] = pd.to_numeric(
        cashflow[col],
        errors="coerce"
    )


if "net_profit" not in profit_loss.columns:
    raise ValueError(
        "Profit & Loss table must contain 'net_profit'."
    )


profit_loss["net_profit"] = pd.to_numeric(
    profit_loss["net_profit"],
    errors="coerce"
)


# ============================================================
# DETECTED COLUMN MAPPING
# ============================================================

print("\nDetected cash flow columns:")
print("CFO       : operating_activity")
print("Investing : investing_activity")
print("Financing : financing_activity")
print("Net Cash  : net_cash_flow")


# ============================================================
# REMOVE INVALID COMPANY IDS
# ============================================================

cashflow = cashflow[
    cashflow["company_id"].notna()
    & cashflow["company_id"].ne("")
    & cashflow["company_id"].ne("NAN")
].copy()


profit_loss = profit_loss[
    profit_loss["company_id"].notna()
    & profit_loss["company_id"].ne("")
    & profit_loss["company_id"].ne("NAN")
].copy()


# ============================================================
# DEDUPLICATE CASH FLOW
# ============================================================

print(
    "\nCash flow rows before deduplication:",
    len(cashflow)
)


cashflow = (
    cashflow
    .sort_values(
        ["company_id", "year"]
    )
    .drop_duplicates(
        subset=[
            "company_id",
            "year"
        ],
        keep="last"
    )
    .reset_index(drop=True)
)


print(
    "Cash flow rows after deduplication:",
    len(cashflow)
)


# ============================================================
# DEDUPLICATE PROFIT & LOSS
# ============================================================

profit_loss = (
    profit_loss
    .sort_values(
        ["company_id", "year"]
    )
    .drop_duplicates(
        subset=[
            "company_id",
            "year"
        ],
        keep="last"
    )
    .reset_index(drop=True)
)


# ============================================================
# YEAR PRIORITY
# ============================================================

def year_priority(value):

    text = str(value).strip().upper()

    priority = {
        "MAR 2024": 100,
        "SEP 2024": 95,
        "DEC 2024": 90,
        "MAR 2023": 85,
        "DEC 2023": 80,
        "SEP 2023": 75,
        "MAR 2022": 70,
        "DEC 2022": 65,
        "SEP 2022": 60,
    }

    return priority.get(text, 10)


# ============================================================
# HISTORICAL CASH FLOW
# ============================================================

historical_cashflow = cashflow[
    ~cashflow["year"]
    .astype(str)
    .str.upper()
    .eq("TTM")
].copy()


historical_cashflow["_priority"] = (
    historical_cashflow["year"]
    .apply(year_priority)
)


# ============================================================
# LATEST CASH FLOW PER COMPANY
# ============================================================

latest_cashflow = (
    historical_cashflow
    .sort_values(
        [
            "company_id",
            "_priority"
        ],
        ascending=[
            True,
            False
        ]
    )
    .drop_duplicates(
        subset=["company_id"],
        keep="first"
    )
    .drop(
        columns=["_priority"]
    )
    .reset_index(drop=True)
)


print(
    "\nLatest historical cash flow rows:",
    len(latest_cashflow)
)

print(
    "Unique cash flow companies:",
    latest_cashflow["company_id"].nunique()
)


# ============================================================
# HISTORICAL PROFIT & LOSS
# ============================================================

historical_pl = profit_loss[
    ~profit_loss["year"]
    .astype(str)
    .str.upper()
    .eq("TTM")
].copy()


historical_pl["_priority"] = (
    historical_pl["year"]
    .apply(year_priority)
)


# ============================================================
# LATEST PROFIT & LOSS PER COMPANY
# ============================================================

latest_pl = (
    historical_pl
    .sort_values(
        [
            "company_id",
            "_priority"
        ],
        ascending=[
            True,
            False
        ]
    )
    .drop_duplicates(
        subset=["company_id"],
        keep="first"
    )
    .drop(
        columns=["_priority"]
    )
    .reset_index(drop=True)
)


# ============================================================
# COMPANY MASTER
# ============================================================

company_ids = (
    companies["id"]
    .dropna()
    .astype(str)
    .str.upper()
    .str.strip()
    .replace("NAN", np.nan)
    .dropna()
    .drop_duplicates()
    .tolist()
)


print(
    "\nTotal company IDs:",
    len(company_ids)
)


# ============================================================
# BASE DATAFRAME
# ============================================================

base = pd.DataFrame({
    "company_id": company_ids
})


# ============================================================
# MERGE CASH FLOW
# ============================================================

cashflow_columns = [
    "company_id",
    "year",
    "operating_activity",
    "investing_activity",
    "financing_activity",
    "net_cash_flow"
]


cashflow_latest = latest_cashflow[
    cashflow_columns
].copy()


base = base.merge(
    cashflow_latest,
    on="company_id",
    how="left"
)


# ============================================================
# MERGE PROFIT & LOSS
# ============================================================

pl_latest = latest_pl[
    [
        "company_id",
        "net_profit"
    ]
].copy()


base = base.merge(
    pl_latest,
    on="company_id",
    how="left"
)


# ============================================================
# RENAME COLUMNS
# ============================================================

base = base.rename(
    columns={
        "operating_activity": "cfo",
        "investing_activity": "investing_cash_flow",
        "financing_activity": "financing_cash_flow",
        "net_profit": "pat"
    }
)


# ============================================================
# NUMERIC CONVERSION
# ============================================================

numeric_columns = [
    "cfo",
    "pat",
    "investing_cash_flow",
    "financing_cash_flow",
    "net_cash_flow"
]


for col in numeric_columns:

    if col in base.columns:

        base[col] = pd.to_numeric(
            base[col],
            errors="coerce"
        )


# ============================================================
# YEAR
# ============================================================

base["year"] = base["year"].fillna(
    "Not Available"
)


# ============================================================
# CAPEX
# ============================================================
#
# The database does not contain a dedicated CapEx field.
#
# Therefore:
#
# Negative investing cash flow is used as a CapEx proxy.
#
# Example:
#
# Investing Cash Flow = -500
# CapEx Proxy = 500
#
# Positive investing cash flow:
# CapEx Proxy = 0
#
# Missing investing cash flow:
# CapEx = NaN
# ============================================================

base["capex_cr"] = np.where(
    base["investing_cash_flow"].notna(),

    np.where(
        base["investing_cash_flow"] < 0,
        -base["investing_cash_flow"],
        0
    ),

    np.nan
)


# ============================================================
# FREE CASH FLOW
# ============================================================
#
# FCF = CFO + Investing Cash Flow
# ============================================================

base["free_cash_flow_cr"] = np.where(
    base["cfo"].notna()
    & base["investing_cash_flow"].notna(),

    base["cfo"]
    + base["investing_cash_flow"],

    np.nan
)


# ============================================================
# CFO / PAT RATIO
# ============================================================

base["cfo_pat_ratio"] = np.where(
    base["cfo"].notna()
    & base["pat"].notna()
    & (base["pat"] != 0),

    base["cfo"] / base["pat"],

    np.nan
)


# ============================================================
# CAPEX INTENSITY
# ============================================================

base["capex_intensity"] = np.where(
    base["cfo"].notna()
    & (base["cfo"] != 0)
    & base["capex_cr"].notna(),

    base["capex_cr"] / base["cfo"],

    np.nan
)


# ============================================================
# FCF CONVERSION
# ============================================================

base["fcf_conversion"] = np.where(
    base["pat"].notna()
    & (base["pat"] != 0)
    & base["free_cash_flow_cr"].notna(),

    base["free_cash_flow_cr"]
    / base["pat"],

    np.nan
)


# ============================================================
# CASH FLOW DATA STATUS
# ============================================================

def data_status(row):

    cfo = row["cfo"]
    investing = row["investing_cash_flow"]
    financing = row["financing_cash_flow"]

    if (
        pd.notna(cfo)
        and pd.notna(investing)
        and pd.notna(financing)
    ):
        return "Complete"

    if (
        pd.notna(cfo)
        or pd.notna(investing)
        or pd.notna(financing)
    ):
        return "Partial"

    return "Not Available"


base["cashflow_data_status"] = (
    base.apply(
        data_status,
        axis=1
    )
)


# ============================================================
# CFO QUALITY
# ============================================================

def classify_cfo_quality(row):

    cfo = row["cfo"]
    pat = row["pat"]
    ratio = row["cfo_pat_ratio"]

    if pd.isna(cfo):
        return "Not Available"

    if cfo <= 0:
        return "Weak"

    if pd.isna(pat):
        return "Positive CFO"

    if pat <= 0:
        return "Positive CFO"

    if ratio >= 1.20:
        return "Excellent"

    if ratio >= 1.00:
        return "Strong"

    if ratio >= 0.80:
        return "Moderate"

    return "Weak"


base["cfo_quality"] = (
    base.apply(
        classify_cfo_quality,
        axis=1
    )
)


# ============================================================
# CAPITAL ALLOCATION
# ============================================================

def classify_capital_allocation(row):

    cfo = row["cfo"]
    capex = row["capex_cr"]
    fcf = row["free_cash_flow_cr"]
    financing = row["financing_cash_flow"]

    if pd.isna(cfo):
        return "Not Available"

    if cfo <= 0:
        return "Cash Flow Pressure"

    if pd.isna(capex):
        return "Operating Cash Generator"

    intensity = (
        capex / cfo
        if cfo != 0
        else np.nan
    )

    if intensity >= 1.00:
        return "Heavy Investment"

    if intensity >= 0.50:
        return "Growth Investment"

    if intensity >= 0.20:
        return "Balanced Investment"

    if pd.notna(financing) and financing < 0:
        return "Cash Generation / Debt Reduction"

    if pd.notna(fcf) and fcf > 0:
        return "Strong Cash Generation"

    return "Low Capital Intensity"


base["capital_allocation_pattern"] = (
    base.apply(
        classify_capital_allocation,
        axis=1
    )
)


# ============================================================
# CASH FLOW QUALITY SCORE
# ============================================================

def calculate_cashflow_score(row):

    score = 0.0

    cfo = row["cfo"]
    pat = row["pat"]
    ratio = row["cfo_pat_ratio"]
    fcf = row["free_cash_flow_cr"]
    capex_intensity_value = row["capex_intensity"]

    # --------------------------------------------------------
    # CFO QUALITY
    # Maximum 40 points
    # --------------------------------------------------------

    if pd.notna(cfo):

        if cfo > 0:
            score += 20

        if pd.notna(ratio):

            if ratio >= 1.20:
                score += 20

            elif ratio >= 1.00:
                score += 16

            elif ratio >= 0.80:
                score += 12

            elif ratio >= 0.50:
                score += 7

    # --------------------------------------------------------
    # FREE CASH FLOW
    # Maximum 20 points
    # --------------------------------------------------------

    if pd.notna(fcf):

        if fcf > 0:
            score += 20

        elif fcf == 0:
            score += 10

    # --------------------------------------------------------
    # CAPEX
    # Maximum 20 points
    # --------------------------------------------------------

    if pd.notna(capex_intensity_value):

        if capex_intensity_value <= 0.30:
            score += 20

        elif capex_intensity_value <= 0.60:
            score += 15

        elif capex_intensity_value <= 1.00:
            score += 10

        else:
            score += 5

    # --------------------------------------------------------
    # PAT
    # Maximum 10 points
    # --------------------------------------------------------

    if pd.notna(pat):

        if pat > 0:
            score += 10

    return round(
        min(score, 100),
        2
    )


base["cashflow_quality_score"] = (
    base.apply(
        calculate_cashflow_score,
        axis=1
    )
)


# ============================================================
# ROUND NUMBERS
# ============================================================

round_columns = [
    "cfo",
    "pat",
    "cfo_pat_ratio",
    "capex_cr",
    "capex_intensity",
    "free_cash_flow_cr",
    "fcf_conversion",
    "investing_cash_flow",
    "financing_cash_flow",
    "cashflow_quality_score"
]


for col in round_columns:

    if col in base.columns:

        base[col] = pd.to_numeric(
            base[col],
            errors="coerce"
        ).round(2)


# ============================================================
# FINAL COLUMN ORDER
# ============================================================

final_columns = [
    "company_id",
    "year",
    "cfo",
    "pat",
    "cfo_pat_ratio",
    "capex_cr",
    "capex_intensity",
    "free_cash_flow_cr",
    "fcf_conversion",
    "investing_cash_flow",
    "financing_cash_flow",
    "cfo_quality",
    "capital_allocation_pattern",
    "cashflow_quality_score",
    "cashflow_data_status"
]


base = base[
    [
        col
        for col in final_columns
        if col in base.columns
    ]
]


# ============================================================
# SORT BY SCORE
# ============================================================

cashflow_intelligence = (
    base
    .sort_values(
        "cashflow_quality_score",
        ascending=False,
        na_position="last"
    )
    .reset_index(drop=True)
)


# ============================================================
# CAPITAL ALLOCATION DATASET
# ============================================================

capital_allocation = cashflow_intelligence[
    [
        "company_id",
        "year",
        "cfo",
        "capex_cr",
        "capex_intensity",
        "free_cash_flow_cr",
        "investing_cash_flow",
        "financing_cash_flow",
        "capital_allocation_pattern",
        "cashflow_quality_score"
    ]
].copy()


# ============================================================
# HISTORICAL CASH FLOW DATASET
# ============================================================

historical_output = cashflow.copy()


historical_output = historical_output.rename(
    columns={
        "operating_activity": "cfo",
        "investing_activity": "investing_cash_flow",
        "financing_activity": "financing_cash_flow"
    }
)


# ============================================================
# SAVE EXCEL
# ============================================================

print("\n" + "=" * 70)
print("SAVING CASH FLOW OUTPUT")
print("=" * 70)


with pd.ExcelWriter(
    EXCEL_OUTPUT,
    engine="openpyxl"
) as writer:

    cashflow_intelligence.to_excel(
        writer,
        sheet_name="Cashflow_Intelligence",
        index=False
    )

    historical_output.to_excel(
        writer,
        sheet_name="Historical_Cashflow",
        index=False
    )

    capital_allocation.to_excel(
        writer,
        sheet_name="Capital_Allocation",
        index=False
    )


# ============================================================
# SAVE CAPITAL ALLOCATION CSV
# ============================================================

capital_allocation.to_csv(
    CSV_OUTPUT,
    index=False
)


print(
    f"\nExcel output: {EXCEL_OUTPUT}"
)

print(
    f"CSV output: {CSV_OUTPUT}"
)


# ============================================================
# FINAL VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("FINAL VALIDATION")
print("=" * 70)


total_companies = len(cashflow_intelligence)

row_count = len(cashflow_intelligence)

duplicate_ids = (
    cashflow_intelligence["company_id"]
    .duplicated()
    .sum()
)

missing_company_ids = (
    cashflow_intelligence["company_id"]
    .isna()
    .sum()
)


complete_count = (
    cashflow_intelligence[
        "cashflow_data_status"
    ]
    .eq("Complete")
    .sum()
)


partial_count = (
    cashflow_intelligence[
        "cashflow_data_status"
    ]
    .eq("Partial")
    .sum()
)


not_available_count = (
    cashflow_intelligence[
        "cashflow_data_status"
    ]
    .eq("Not Available")
    .sum()
)


print(
    f"\nCompanies: {total_companies}"
)

print(
    f"Rows: {row_count}"
)

print(
    f"Duplicate company IDs: {duplicate_ids}"
)

print(
    f"Missing company IDs: {missing_company_ids}"
)


# ============================================================
# CASH FLOW STATUS
# ============================================================

print("\nCash flow data status:")

print(
    cashflow_intelligence[
        "cashflow_data_status"
    ].value_counts()
)


# ============================================================
# CFO QUALITY
# ============================================================

print("\nCFO quality:")

print(
    cashflow_intelligence[
        "cfo_quality"
    ].value_counts()
)


# ============================================================
# CAPITAL ALLOCATION
# ============================================================

print("\nCapital allocation:")

print(
    cashflow_intelligence[
        "capital_allocation_pattern"
    ].value_counts()
)


# ============================================================
# SOURCE-DATA EXCEPTIONS
# ============================================================

not_available_companies = (
    cashflow_intelligence.loc[
        cashflow_intelligence[
            "cashflow_data_status"
        ] == "Not Available",
        "company_id"
    ]
    .tolist()
)


partial_companies = (
    cashflow_intelligence.loc[
        cashflow_intelligence[
            "cashflow_data_status"
        ] == "Partial",
        "company_id"
    ]
    .tolist()
)


if not_available_companies:

    print(
        "\nCash-flow data unavailable for:"
    )

    print(
        ", ".join(not_available_companies)
    )


if partial_companies:

    print(
        "\nPartial cash-flow data for:"
    )

    print(
        ", ".join(partial_companies)
    )


# ============================================================
# TOP 15 COMPANIES
# ============================================================

print(
    "\nTop 15 companies by cash flow quality:"
)


top_columns = [
    "company_id",
    "year",
    "cfo",
    "pat",
    "cfo_pat_ratio",
    "capex_cr",
    "capex_intensity",
    "free_cash_flow_cr",
    "cfo_quality",
    "capital_allocation_pattern",
    "cashflow_quality_score",
    "cashflow_data_status"
]


print(
    cashflow_intelligence[
        top_columns
    ]
    .head(15)
    .to_string(index=False)
)


# ============================================================
# VALIDATION RESULT
# ============================================================

validation_passed = (
    total_companies == 92
    and row_count == 92
    and duplicate_ids == 0
    and missing_company_ids == 0
)


if validation_passed:

    if not_available_count > 0:

        print(
            "\nValidation: PASSED "
            "(source-data exception)"
        )

        print(
            "The missing cash-flow records are "
            "preserved as Not Available."
        )

        print(
            "No financial values were imputed."
        )

    elif partial_count > 0:

        print(
            "\nValidation: PASSED "
            "(partial source-data exception)"
        )

        print(
            "No financial values were imputed."
        )

    else:

        print(
            "\nValidation: PASSED"
        )

else:

    print(
        "\nValidation: FAILED"
    )

    raise ValueError(
        "Cash flow validation failed. "
        "Check company count, duplicate IDs, "
        "or missing company IDs."
    )


# ============================================================
# COMPLETED
# ============================================================

print("\n" + "=" * 70)
print("CASH FLOW INTELLIGENCE COMPLETED SUCCESSFULLY")
print("=" * 70)