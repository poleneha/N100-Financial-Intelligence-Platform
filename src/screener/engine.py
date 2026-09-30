import pandas as pd
import numpy as np
import os


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_FILE = "output/financial_ratios.xlsx"
OUTPUT_FILE = "output/screener_output.xlsx"

os.makedirs("output", exist_ok=True)


# ============================================================
# LOAD FINANCIAL DATA
# ============================================================

print("=" * 70)
print("LOADING FINANCIAL DATA")
print("=" * 70)

df = pd.read_excel(INPUT_FILE)

print("Input shape:", df.shape)
print("Financial companies:", df["company_id"].nunique())


# ============================================================
# CLEAN BASIC FIELDS
# ============================================================

df["company_id"] = (
    df["company_id"]
    .astype(str)
    .str.strip()
    .str.upper()
)

df["year"] = (
    df["year"]
    .astype(str)
    .str.strip()
)


# ============================================================
# NUMERIC COLUMNS
# ============================================================

numeric_columns = [
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
    "operating_activity",
    "investing_activity",
    "financing_activity",
    "net_cash_flow",
    "shareholders_equity_cr",
    "return_on_equity_pct",
    "return_on_assets_pct",
    "debt_to_equity",
    "free_cash_flow_cr",
]

for col in numeric_columns:

    if col in df.columns:

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )


# ============================================================
# SAVE ALL 100 COMPANY IDs
# ============================================================

all_company_ids = sorted(
    df["company_id"].dropna().unique()
)

print()
print("Total company IDs:", len(all_company_ids))


# ============================================================
# REMOVE TTM FOR RATIO SELECTION
# ============================================================

historical = df[
    ~df["year"]
    .astype(str)
    .str.upper()
    .eq("TTM")
].copy()


# ============================================================
# VALID HISTORICAL RATIO DATA
# ============================================================

ratio_columns = [
    "return_on_equity_pct",
    "return_on_assets_pct",
    "debt_to_equity",
]


historical["_ratio_available"] = (
    historical[ratio_columns]
    .notna()
    .any(axis=1)
)


valid_history = historical[
    historical["_ratio_available"]
].copy()


# ============================================================
# SELECT LATEST VALID HISTORICAL YEAR
# ============================================================

print()
print("=" * 70)
print("SELECTING LATEST VALID FINANCIAL YEAR")
print("=" * 70)


# Give financial years an approximate chronological rank.
# This avoids alphabetical sorting such as:
# Mar 2024 < Dec 2023 < Sep 2024 being handled incorrectly.

def year_rank(value):

    text = str(value).strip().upper()

    if text.startswith("MAR "):
        month_rank = 3

    elif text.startswith("JUN "):
        month_rank = 6

    elif text.startswith("SEP "):
        month_rank = 9

    elif text.startswith("DEC "):
        month_rank = 12

    else:
        return -1

    try:
        year_number = int(text.split()[-1])
    except Exception:
        return -1

    return year_number * 100 + month_rank


valid_history["_year_rank"] = (
    valid_history["year"]
    .apply(year_rank)
)


# Keep latest valid historical row for each company

latest_valid = (
    valid_history
    .sort_values(
        ["company_id", "_year_rank"]
    )
    .groupby("company_id", as_index=False)
    .tail(1)
    .copy()
)


# ============================================================
# FIND COMPANIES WITHOUT HISTORICAL RATIOS
# ============================================================

selected_ids = set(
    latest_valid["company_id"]
)

missing_ids = sorted(
    set(all_company_ids) - selected_ids
)


print(
    "Companies with valid historical ratios:",
    len(selected_ids)
)

print(
    "Companies without valid historical ratios:",
    len(missing_ids)
)

if missing_ids:

    print(
        "Missing historical ratio companies:",
        missing_ids
    )


# ============================================================
# KEEP ALL 100 COMPANIES
# ============================================================

# Start from the complete company list.
# This guarantees that companies such as SBIN, VBL,
# VEDL, WIPRO, ZOMATO, etc. are NOT dropped.

company_base = pd.DataFrame({
    "company_id": all_company_ids
})


# Merge latest valid historical data

df = company_base.merge(
    latest_valid.drop(
        columns=["_ratio_available", "_year_rank"],
        errors="ignore"
    ),
    on="company_id",
    how="left"
)


# ============================================================
# DATA QUALITY CHECK
# ============================================================

print()
print("=" * 70)
print("DATA QUALITY CHECK")
print("=" * 70)

for col in ratio_columns + ["free_cash_flow_cr"]:

    print(
        f"{col}:",
        df[col].isna().sum(),
        "missing"
    )


# ============================================================
# FILL NON-RATIO NUMERIC VALUES
# ============================================================

# We only fill ordinary financial fields with 0.
# Ratio fields remain NaN when unavailable.

non_ratio_columns = [
    col
    for col in numeric_columns
    if col not in ratio_columns
]

for col in non_ratio_columns:

    if col in df.columns:

        df[col] = df[col].fillna(0)


# ============================================================
# ROE QUALITY
# ============================================================

df["roe_quality"] = "Not Available"


roe = df["return_on_equity_pct"]

df.loc[
    roe.notna() & (roe < 0),
    "roe_quality"
] = "Weak"

df.loc[
    roe.notna() & (roe >= 0) & (roe < 10),
    "roe_quality"
] = "Moderate"

df.loc[
    roe.notna() & (roe >= 10) & (roe < 20),
    "roe_quality"
] = "Strong"

df.loc[
    roe.notna() & (roe >= 20) & (roe < 50),
    "roe_quality"
] = "Very Strong"

df.loc[
    roe.notna() & (roe >= 50),
    "roe_quality"
] = "Extreme"


# ============================================================
# ROE RELIABILITY
# ============================================================

df["roe_reliability"] = "Not Available"


# Normal ROE range:
# -200% to +200% is treated as usable
# Beyond that requires review.

reliable_mask = (
    roe.notna()
    & roe.between(-200, 200)
)

review_mask = (
    roe.notna()
    & ~roe.between(-200, 200)
)


df.loc[
    reliable_mask,
    "roe_reliability"
] = "Reliable"

df.loc[
    review_mask,
    "roe_reliability"
] = "Review"


# ============================================================
# SAFE ROE FOR SCORING
# ============================================================

# Extreme accounting ROE values should not dominate
# the entire screener score.

df["roe_for_score"] = (
    df["return_on_equity_pct"]
    .clip(
        lower=-20,
        upper=50
    )
)


# ============================================================
# SAFE ROA FOR SCORING
# ============================================================

df["roa_for_score"] = (
    df["return_on_assets_pct"]
    .clip(
        lower=-20,
        upper=40
    )
)


# ============================================================
# SAFE D/E FOR SCORING
# ============================================================

df["de_for_score"] = (
    df["debt_to_equity"]
    .clip(
        lower=0,
        upper=10
    )
)


# ============================================================
# CALCULATING SCREENER SCORE
# ============================================================

print()
print("=" * 70)
print("CALCULATING SCREENER SCORE")
print("=" * 70)


# FCF contribution is normalized using log1p.
# This prevents very large FCF companies from dominating.

fcf_positive = (
    df["free_cash_flow_cr"]
    .clip(lower=0)
)

df["fcf_score"] = np.log1p(
    fcf_positive
)


# Normalize FCF between 0 and 100

fcf_max = df["fcf_score"].max()

if pd.notna(fcf_max) and fcf_max > 0:

    df["fcf_score"] = (
        df["fcf_score"]
        / fcf_max
        * 100
    )

else:

    df["fcf_score"] = 0


# ============================================================
# SCORE COMPONENTS
# ============================================================

roe_component = (
    df["roe_for_score"]
    .fillna(0)
    .clip(lower=0)
    / 50
    * 50
)


roa_component = (
    df["roa_for_score"]
    .fillna(0)
    .clip(lower=0)
    / 40
    * 20
)


de_component = (
    20
    - (
        df["de_for_score"]
        .fillna(0)
        .clip(lower=0, upper=10)
        / 10
        * 20
    )
)


fcf_component = (
    df["fcf_score"]
    * 0.10
)


# ============================================================
# COMPOSITE QUALITY SCORE
# ============================================================

df["composite_quality_score"] = (
    roe_component
    + roa_component
    + de_component
    + fcf_component
)

# Companies with no ratios should not receive
# an artificial score.

ratio_missing_mask = (
    df[ratio_columns]
    .isna()
    .all(axis=1)
)

df.loc[
    ratio_missing_mask,
    "composite_quality_score"
] = 0


df["composite_quality_score"] = (
    df["composite_quality_score"]
    .round(2)
)


# ============================================================
# DATA QUALITY FLAG
# ============================================================

df["ratio_data_status"] = np.where(
    df[ratio_columns]
    .notna()
    .all(axis=1),
    "Complete",
    np.where(
        df[ratio_columns]
        .notna()
        .any(axis=1),
        "Partial",
        "Not Available"
    )
)


# ============================================================
# PREPARE DISPLAY COLUMNS
# ============================================================

df["year"] = (
    df["year"]
    .fillna("Not Available")
    .astype(str)
)


print()
print(
    "Complete ratio records:",
    (df["ratio_data_status"] == "Complete").sum()
)

print(
    "Partial ratio records:",
    (df["ratio_data_status"] == "Partial").sum()
)

print(
    "Unavailable ratio records:",
    (df["ratio_data_status"] == "Not Available").sum()
)

# ============================================================
# SCREENER FUNCTIONS
# ============================================================

def quality_compounder(data):

    return data[
        data["return_on_equity_pct"].notna()
        &
        data["debt_to_equity"].notna()
        &
        (data["return_on_equity_pct"] >= 15)
        &
        (data["debt_to_equity"] < 3)
        &
        (data["roe_reliability"] == "Reliable")
    ].copy()


def value_pick(data):

    return data[
        data["debt_to_equity"].notna()
        &
        (data["debt_to_equity"] < 5)
    ].copy()


def growth_accelerator(data):

    return data[
        data["return_on_equity_pct"].notna()
        &
        (data["return_on_equity_pct"] >= 10)
        &
        (data["roe_reliability"] == "Reliable")
    ].copy()


def dividend_champion(data):

    return data[
        data["dividend_payout"].notna()
        &
        (data["dividend_payout"] > 0)
    ].copy()


def debt_free_bluechip(data):

    return data[
        data["debt_to_equity"].notna()
        &
        (data["debt_to_equity"] <= 0.10)
        &
        (data["return_on_equity_pct"].notna())
        &
        (data["return_on_equity_pct"] >= 15)
    ].copy()


def turnaround_watch(data):

    return data[
        data["return_on_equity_pct"].notna()
        &
        (data["return_on_equity_pct"] >= 5)
        &
        (data["return_on_equity_pct"] < 15)
    ].copy()


# ============================================================
# SCREENER DICTIONARY
# ============================================================

screeners = {

    "Quality_Compounder":
        quality_compounder,

    "Value_Pick":
        value_pick,

    "Growth_Accelerator":
        growth_accelerator,

    "Dividend_Champion":
        dividend_champion,

    "Debt_Free_Bluechip":
        debt_free_bluechip,

    "Turnaround_Watch":
        turnaround_watch,
}


# ============================================================
# PRIMARY CATEGORY
# ============================================================

print()
print("=" * 70)
print("ASSIGNING PRIMARY CATEGORIES")
print("=" * 70)


df["category"] = "Other"


# Use priority order so a company receives
# one primary category only.

category_rules = [

    (
        "Quality_Compounder",
        quality_compounder
    ),

    (
        "Dividend_Champion",
        dividend_champion
    ),

    (
        "Debt_Free_Bluechip",
        debt_free_bluechip
    ),

    (
        "Growth_Accelerator",
        growth_accelerator
    ),

    (
        "Turnaround_Watch",
        turnaround_watch
    ),
]


assigned = pd.Series(
    False,
    index=df.index
)


for category_name, function in category_rules:

    result = function(df)

    available_index = (
        result.index
        .intersection(df.index)
    )

    new_index = available_index[
        ~assigned.loc[available_index]
    ]

    df.loc[
        new_index,
        "category"
    ] = category_name

    assigned.loc[
        new_index
    ] = True


# ============================================================
# FORCE UNAVAILABLE COMPANIES TO OTHER
# ============================================================

df.loc[
    df["ratio_data_status"] == "Not Available",
    "category"
] = "Other"


# ============================================================
# CATEGORY COUNTS
# ============================================================

print()
print("CATEGORY COUNTS")

print(
    df["category"]
    .value_counts()
    .to_string()
)


# ============================================================
# REMOVE INTERNAL SCORING COLUMNS
# ============================================================

internal_columns = [
    "roe_for_score",
    "roa_for_score",
    "de_for_score",
    "fcf_score",
]

# Keep them out of the final Excel,
# but only after all calculations are complete.

final_df = df.drop(
    columns=internal_columns,
    errors="ignore"
).copy()


# ============================================================
# SORT ALL COMPANIES
# ====================================
final_df = final_df.sort_values(
    "composite_quality_score",
    ascending=False
).reset_index(drop=True)


# ============================================================
# SAVE SCREENER OUTPUT
# ============================================================

print()
print("=" * 70)
print("SAVING SCREENER OUTPUT")
print("=" * 70)


with pd.ExcelWriter(
    OUTPUT_FILE,
    engine="openpyxl"
) as writer:

    # --------------------------------------------------------
    # ALL COMPANIES
    # --------------------------------------------------------

    final_df.to_excel(
        writer,
        sheet_name="All_Companies",
        index=False
    )


    # --------------------------------------------------------
    # INDIVIDUAL SCREENER SHEETS
    # --------------------------------------------------------

    for name, function in screeners.items():

        result = function(df).copy()

        result = result.drop(
            columns=internal_columns,
            errors="ignore"
        )

        result = result.sort_values(
            "composite_quality_score",
            ascending=False
        )

        result.to_excel(
            writer,
            sheet_name=name[:31],
            index=False
        )

        print(
            f"{name}: "
            f"{result['company_id'].nunique()} stocks"
        )


# ============================================================
# FINAL VALIDATION
# ============================================================

print()
print("=" * 70)
print("FINAL VALIDATION")
print("=" * 70)


print(
    "Companies:",
    final_df["company_id"].nunique()
)

print(
    "Rows:",
    len(final_df)
)

print(
    "Duplicate company IDs:",
    final_df["company_id"].duplicated().sum()
)


print()
print("Category counts:")

print(
    final_df["category"]
    .value_counts()
    .to_string()
)


print()
print("ROE reliability:")

print(
    final_df["roe_reliability"]
    .value_counts(dropna=False)
    .to_string()
)


# ============================================================
# CHECK REQUIRED 7 COMPANIES
# ============================================================

required_missing_companies = [
    "SBIN",
    "UNITDSPR",
    "VBL",
    "VEDL",
    "WIPRO",
    "ZOMATO",
    "ZYDUSLIFE",
]


print()
print("=" * 70)
print("MISSING-RATIO COMPANY CHECK")
print("=" * 70)


check = final_df[
    final_df["company_id"]
    .isin(required_missing_companies)
][
    [
        "company_id",
        "year",
        "return_on_equity_pct",
        "return_on_assets_pct",
        "debt_to_equity",
        "free_cash_flow_cr",
        "roe_quality",
        "roe_reliability",
        "ratio_data_status",
        "composite_quality_score",
        "category",
    ]
]


print(
    check.to_string(index=False)
)


# ============================================================
# KEY COMPANY CHECK
# ============================================================

print()
print("=" * 70)
print("KEY COMPANY CHECK")
print("=" * 70)


key_companies = [
    "ABB",
    "BEL",
    "HAL",
    "INDIGO",
    "TCS",
]


key_check = final_df[
    final_df["company_id"]
    .isin(key_companies)
][
    [
        "company_id",
        "year",
        "return_on_equity_pct",
        "return_on_assets_pct",
        "debt_to_equity",
        "free_cash_flow_cr",
        "roe_quality",
        "roe_reliability",
        "composite_quality_score",
        "category",
    ]
]


print(
    key_check.to_string(index=False)
)


# ============================================================
# FINAL REQUIRED CHECKS
# ============================================================

assert (
    final_df["company_id"].nunique()
    == len(all_company_ids)
), (
    "ERROR: Some companies were dropped!"
)


assert (
    len(final_df)
    == len(all_company_ids)
), (
    "ERROR: Final row count does not match company count!"
)


assert (
    final_df["company_id"].duplicated().sum()
    == 0
), (
    "ERROR: Duplicate company IDs found!"
)


# ============================================================
# COMPLETED
# =================
print()
print("=" * 70)
print("SCREENER COMPLETED SUCCESSFULLY")
print("=" * 70)

print(
    "Companies:",
    final_df["company_id"].nunique()
)

print(
    "Saved:",
    OUTPUT_FILE
)