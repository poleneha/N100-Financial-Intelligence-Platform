import os
import pandas as pd
import numpy as np


OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

MARKET_CAP_FILE = "data/raw/market_cap.xlsx"
STOCK_PRICE_FILE = "data/raw/stock_prices.xlsx"


print("=" * 70)
print("NIFTY 100 - INVESTOR ANALYTICS")
print("SIP / INVESTOR CONTINUITY / COHORT ANALYSIS")
print("=" * 70)


# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

print("Loading market-cap data...")
market = pd.read_excel(MARKET_CAP_FILE)

print("Loading stock-price data...")
prices = pd.read_excel(STOCK_PRICE_FILE)

market["company_id"] = market["company_id"].astype(str).str.strip()
prices["company_id"] = prices["company_id"].astype(str).str.strip()

market["year"] = pd.to_numeric(market["year"], errors="coerce")
prices["date"] = pd.to_datetime(prices["date"], errors="coerce")

prices = prices.dropna(
    subset=["company_id", "date", "adjusted_close"]
)

prices = prices.sort_values(
    ["company_id", "date"]
)


# ---------------------------------------------------------
# MARKET CAP / INVESTOR COHORT
# ---------------------------------------------------------

latest_market = (
    market.sort_values(["company_id", "year"])
    .groupby("company_id")
    .tail(1)
    .copy()
)

latest_market["market_cap_crore"] = pd.to_numeric(
    latest_market["market_cap_crore"],
    errors="coerce"
)

def market_cap_cohort(value):
    if pd.isna(value):
        return "Unknown"

    if value >= 500000:
        return "Large Cap"

    if value >= 100000:
        return "Mid Cap"

    return "Small Cap"


latest_market["investor_cohort"] = (
    latest_market["market_cap_crore"]
    .apply(market_cap_cohort)
)


# ---------------------------------------------------------
# PRICE CONTINUITY
# ---------------------------------------------------------

continuity = (
    prices.groupby("company_id")
    .agg(
        first_date=("date", "min"),
        last_date=("date", "max"),
        observations=("date", "count"),
    )
    .reset_index()
)

continuity["coverage_years"] = (
    (continuity["last_date"] - continuity["first_date"])
    .dt.days / 365.25
)

continuity["continuity_pct"] = (
    continuity["observations"] / 60 * 100
).clip(upper=100)


# ---------------------------------------------------------
# RETURNS
# ---------------------------------------------------------

prices["monthly_return"] = (
    prices.groupby("company_id")["adjusted_close"]
    .pct_change()
)

return_stats = (
    prices.groupby("company_id")
    .agg(
        average_monthly_return=("monthly_return", "mean"),
        monthly_volatility=("monthly_return", "std"),
    )
    .reset_index()
)

return_stats["annualized_return_pct"] = (
    (1 + return_stats["average_monthly_return"]) ** 12 - 1
) * 100

return_stats["annualized_volatility_pct"] = (
    return_stats["monthly_volatility"] * np.sqrt(12) * 100
)


# ---------------------------------------------------------
# INVESTOR RISK PROFILE
# ---------------------------------------------------------

risk_data = return_stats.merge(
    continuity[
        [
            "company_id",
            "continuity_pct"
        ]
    ],
    on="company_id",
    how="left"
)


def risk_profile(row):

    volatility = row["annualized_volatility_pct"]
    continuity_value = row["continuity_pct"]

    if pd.isna(volatility):
        return "Unknown"

    if volatility >= 30:
        return "High Risk"

    if volatility >= 20:
        return "Moderate Risk"

    if pd.notna(continuity_value) and continuity_value < 80:
        return "Limited History"

    return "Lower Risk"


risk_data["risk_profile"] = risk_data.apply(
    risk_profile,
    axis=1
)


return_stats = risk_data

# ---------------------------------------------------------
# INVESTOR ANALYTICS MASTER TABLE
# ---------------------------------------------------------

investor = (
    latest_market[
        [
            "company_id",
            "year",
            "market_cap_crore",
            "investor_cohort",
        ]
    ]
    .merge(
        continuity[
            [
                "company_id",
                "first_date",
                "last_date",
                "observations",
                "coverage_years",
                "continuity_pct",
            ]
        ],
        on="company_id",
        how="left",
    )
    .merge(
        return_stats[
            [
                "company_id",
                "average_monthly_return",
                "monthly_volatility",
                "annualized_return_pct",
                "annualized_volatility_pct",
                "risk_profile",
            ]
        ],
        on="company_id",
        how="left",
    )
)

# Remove any accidental duplicate columns
investor = investor.loc[
    :,
    ~investor.columns.duplicated()
]

investor = investor.sort_values(
    "annualized_return_pct",
    ascending=False
)


# ---------------------------------------------------------
# INVESTOR SCORE
# ---------------------------------------------------------

def investor_score(row):

    score = 50

    # Continuity contribution
    score += min(
        row["continuity_pct"] * 0.25,
        25
    )

    # Return contribution
    if pd.notna(row["annualized_return_pct"]):
        score += np.clip(
            row["annualized_return_pct"],
            -20,
            20
        ) * 0.5

    # Risk penalty
    if row["risk_profile"] == "High Risk":
        score -= 15
    elif row["risk_profile"] == "Moderate Risk":
        score -= 5

    return round(
        float(np.clip(score, 0, 100)),
        2
    )


investor["investor_score"] = investor.apply(
    investor_score,
    axis=1
)


# ---------------------------------------------------------
# INVESTOR CATEGORY
# ---------------------------------------------------------

def investor_category(score):

    if score >= 75:
        return "Strong Investor Profile"

    if score >= 60:
        return "Good Investor Profile"

    if score >= 45:
        return "Moderate Investor Profile"

    return "Weak Investor Profile"


investor["investor_category"] = (
    investor["investor_score"]
    .apply(investor_category)
)


investor["investor_rank"] = (
    investor["investor_score"]
    .rank(
        ascending=False,
        method="first"
    )
    .astype(int)
)


# ---------------------------------------------------------
# SAVE MASTER OUTPUT
# ---------------------------------------------------------

master_file = (
    f"{OUTPUT_DIR}/investor_analytics.csv"
)

investor.to_csv(
    master_file,
    index=False
)

print(f"Saved: {os.path.abspath(master_file)}")


# ---------------------------------------------------------
# COHORT SUMMARY
# ---------------------------------------------------------

cohort_summary = (
    investor.groupby("investor_cohort")
    .agg(
        company_count=("company_id", "count"),
        average_score=("investor_score", "mean"),
        median_score=("investor_score", "median"),
        average_return_pct=("annualized_return_pct", "mean"),
        average_volatility_pct=("annualized_volatility_pct", "mean"),
        average_continuity_pct=("continuity_pct", "mean"),
    )
    .reset_index()
)

cohort_summary.to_csv(
    f"{OUTPUT_DIR}/investor_cohort_summary.csv",
    index=False
)

print(
    f"Saved: {os.path.abspath(OUTPUT_DIR + '/investor_cohort_summary.csv')}"
)
# ---------------------------------------------------------
# TOP INVESTOR PROFILES
# ---------------------------------------------------------

top_investors = investor[
    [
        "investor_rank",
        "company_id",
        "investor_cohort",
        "investor_score",
        "investor_category",
        "annualized_return_pct",
        "annualized_volatility_pct",
        "continuity_pct",
    ]
].head(20)

top_investors.to_csv(
    f"{OUTPUT_DIR}/top_investor_profiles.csv",
    index=False
)

print(
    f"Saved: {os.path.abspath(OUTPUT_DIR + '/top_investor_profiles.csv')}"
)


# ---------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------

print()
print("=" * 70)
print("INVESTOR ANALYTICS VALIDATION")
print("=" * 70)

print(f"✓ Companies analyzed: {len(investor)}")
print(
    f"✓ Investor cohorts: "
    f"{investor['investor_cohort'].nunique()}"
)
print("✓ Investor continuity calculated")
print("✓ Annualized returns calculated")
print("✓ Annualized volatility calculated")
print("✓ Investor scores generated")
print("✓ Investor categories generated")
print("✓ Cohort summary generated")
print("✓ Top investor profiles generated")

required_columns = [
    "company_id",
    "investor_cohort",
    "continuity_pct",
    "annualized_return_pct",
    "annualized_volatility_pct",
    "investor_score",
    "investor_category",
    "investor_rank",
]

missing = [
    col for col in required_columns
    if col not in investor.columns
]

if missing:
    raise ValueError(
        f"Missing required columns: {missing}"
    )

if len(investor) != 92:
    raise ValueError(
        f"Expected 92 companies, found {len(investor)}"
    )

if not investor["investor_score"].between(
    0, 100
).all():
    raise ValueError(
        "Investor score outside 0-100 range"
    )

print("✓ 92 companies validated")
print("✓ Investor scores between 0 and 100")
print("✓ All required columns present")

print()
print("=" * 70)
print("INVESTOR ANALYTICS VALIDATION PASSED")
print("=" * 70)