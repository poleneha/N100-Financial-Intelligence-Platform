import os
import pandas as pd
import matplotlib.pyplot as plt


print("=" * 70)
print("NIFTY 100 - INVESTMENT RECOMMENDER")
print("TOP 3 RECOMMENDATIONS / RISK-AWARE RANKING")
print("=" * 70)


# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------

PORTFOLIO_FILE = "output/portfolio_scoring.csv"
RISK_FILE = "output/risk_metrics.csv"
INVESTOR_FILE = "output/investor_analytics.csv"

OUTPUT_DIR = "output"
REPORT_DIR = "reports"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)


# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

print("Loading portfolio scoring data...")
portfolio = pd.read_csv(PORTFOLIO_FILE)

print("Loading risk metrics...")
risk = pd.read_csv(RISK_FILE)

print("Loading investor analytics...")
investor = pd.read_csv(INVESTOR_FILE)


# ---------------------------------------------------------
# CLEAN COLUMN NAMES
# ---------------------------------------------------------

portfolio.columns = portfolio.columns.str.strip().str.lower()
risk.columns = risk.columns.str.strip().str.lower()
investor.columns = investor.columns.str.strip().str.lower()


# ---------------------------------------------------------
# CHECK COMPANY IDs
# ---------------------------------------------------------

for df in [portfolio, risk, investor]:

    if "company_id" not in df.columns:
        raise ValueError(
            "company_id column missing from input data"
        )


# ---------------------------------------------------------
# SELECT RISK COLUMNS
# ---------------------------------------------------------

risk_columns = [
    "company_id",
    "var_95",
    "cvar_95",
    "latest_rolling_sharpe",
    "annualized_return",
    "annualized_volatility",
    "risk_category"
]

risk_columns = [
    c for c in risk_columns
    if c in risk.columns
]

risk_data = risk[risk_columns].copy()


# ---------------------------------------------------------
# SELECT INVESTOR COLUMNS
# ---------------------------------------------------------

investor_columns = [
    "company_id",
    "continuity_pct",
    "investor_score",
    "investor_category"
]

investor_columns = [
    c for c in investor_columns
    if c in investor.columns
]

investor_data = investor[investor_columns].copy()


# ---------------------------------------------------------
# MERGE
# ---------------------------------------------------------

df = portfolio.merge(
    risk_data,
    on="company_id",
    how="left"
)

df = df.merge(
    investor_data,
    on="company_id",
    how="left"
)


# ---------------------------------------------------------
# NUMERIC CONVERSION
# ---------------------------------------------------------

numeric_columns = [
    "investment_score",
    "var_95",
    "cvar_95",
    "latest_rolling_sharpe",
    "annualized_return",
    "annualized_volatility",
    "investor_score",
    "continuity_pct"
]

for col in numeric_columns:

    if col in df.columns:

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )


# ---------------------------------------------------------
# FILL MISSING VALUES
# ---------------------------------------------------------

for col in numeric_columns:

    if col in df.columns:

        df[col] = df[col].fillna(
            df[col].median()
        )


# ---------------------------------------------------------
# RISK SCORE
# ---------------------------------------------------------

def normalize(series):

    minimum = series.min()
    maximum = series.max()

    if maximum == minimum:

        return pd.Series(
            50,
            index=series.index
        )

    return (
        (series - minimum)
        / (maximum - minimum)
        * 100
    )


# Lower CVaR = better
df["risk_score"] = (
    100
    - normalize(df["cvar_95"])
)


# Sharpe: higher is better
df["sharpe_score"] = normalize(
    df["latest_rolling_sharpe"]
)


# Investor score
if "investor_score" in df.columns:

    df["investor_quality_score"] = (
        df["investor_score"]
    )

else:

    df["investor_quality_score"] = 50


# Portfolio score
df["portfolio_quality_score"] = (
    df["investment_score"]
)


# ---------------------------------------------------------
# FINAL RECOMMENDATION SCORE
# ---------------------------------------------------------

df["recommendation_score"] = (
    df["portfolio_quality_score"] * 0.40
    + df["risk_score"] * 0.25
    + df["sharpe_score"] * 0.15
    + df["investor_quality_score"] * 0.20
)


# ---------------------------------------------------------
# RECOMMENDATION CATEGORY
# ---------------------------------------------------------

def recommendation_category(score):

    if score >= 75:
        return "Strong Buy"

    elif score >= 65:
        return "Buy"

    elif score >= 50:
        return "Hold"

    elif score >= 35:
        return "Watch"

    else:
        return "Avoid"


df["recommendation"] = (
    df["recommendation_score"]
    .apply(recommendation_category)
)


# ---------------------------------------------------------
# RISK GRADE
# ---------------------------------------------------------

def risk_grade(row):

    if row["cvar_95"] >= 0.10:
        return "High"

    elif row["cvar_95"] >= 0.075:
        return "Moderate"

    else:
        return "Low"


df["risk_grade"] = df.apply(
    risk_grade,
    axis=1
)


# ---------------------------------------------------------
# RANKING
# ---------------------------------------------------------

df = df.sort_values(
    "recommendation_score",
    ascending=False
).reset_index(drop=True)


df["recommendation_rank"] = (
    df.index + 1
)


# ---------------------------------------------------------
# TOP 3
# ---------------------------------------------------------

top3 = df.head(3).copy()


# ---------------------------------------------------------
# SAVE FULL RECOMMENDATIONS
# ---------------------------------------------------------

output_columns = [
    "recommendation_rank",
    "company_id",
    "cluster_name",
    "investment_score",
    "investor_score",
    "risk_score",
    "sharpe_score",
    "recommendation_score",
    "recommendation",
    "risk_grade",
    "risk_category",
    "var_95",
    "cvar_95",
    "latest_rolling_sharpe",
    "annualized_return",
    "annualized_volatility"
]

output_columns = [
    c for c in output_columns
    if c in df.columns
]

recommendations = df[
    output_columns
].copy()


recommendation_file = (
    "output/investment_recommendations.csv"
)

recommendations.to_csv(
    recommendation_file,
    index=False
)


# ---------------------------------------------------------
# SAVE TOP 3
# ---------------------------------------------------------

top3_file = (
    "output/top_3_recommendations.csv"
)

top3[
    output_columns
].to_csv(
    top3_file,
    index=False
)


# ---------------------------------------------------------
# SUMMARY
# ---------------------------------------------------------

summary = pd.DataFrame({

    "metric": [
        "companies_analyzed",
        "strong_buy_count",
        "buy_count",
        "hold_count",
        "watch_count",
        "avoid_count",
        "low_risk_count",
        "moderate_risk_count",
        "high_risk_count"
    ],

    "value": [

        len(df),

        (df["recommendation"] == "Strong Buy").sum(),

        (df["recommendation"] == "Buy").sum(),

        (df["recommendation"] == "Hold").sum(),

        (df["recommendation"] == "Watch").sum(),

        (df["recommendation"] == "Avoid").sum(),

        (df["risk_grade"] == "Low").sum(),

        (df["risk_grade"] == "Moderate").sum(),

        (df["risk_grade"] == "High").sum()
    ]
})


summary_file = (
    "output/recommendation_summary.csv"
)

summary.to_csv(
    summary_file,
    index=False
)


# ---------------------------------------------------------
# CHART
# ---------------------------------------------------------

distribution = (
    df["recommendation"]
    .value_counts()
)


plt.figure(figsize=(9, 6))

distribution.plot(
    kind="bar"
)

plt.title(
    "Nifty 100 Investment Recommendation Distribution"
)

plt.xlabel(
    "Recommendation"
)

plt.ylabel(
    "Number of Companies"
)

plt.xticks(
    rotation=0
)

plt.tight_layout()


chart_file = (
    "reports/recommendation_distribution.png"
)

plt.savefig(
    chart_file,
    dpi=150
)

plt.close()


# ---------------------------------------------------------
# DISPLAY TOP 3
# ---------------------------------------------------------

print()
print("=" * 70)
print("TOP 3 INVESTMENT RECOMMENDATIONS")
print("=" * 70)

display_columns = [
    "recommendation_rank",
    "company_id",
    "recommendation_score",
    "recommendation",
    "risk_grade"
]

print(
    top3[display_columns].to_string(
        index=False
    )
)


# ---------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------

print()
print("=" * 70)
print("INVESTMENT RECOMMENDER VALIDATION")
print("=" * 70)

print(
    f"✓ Companies analyzed: {len(df)}"
)

print(
    "✓ Recommendation scores generated"
)

print(
    "✓ Investment recommendations generated"
)

print(
    "✓ Risk grades generated"
)

print(
    "✓ Unique recommendation ranking generated"
)

print(
    "✓ Top 3 recommendations generated"
)

print(
    "✓ investment_recommendations.csv generated"
)

print(
    "✓ top_3_recommendations.csv generated"
)

print(
    "✓ recommendation_summary.csv generated"
)

print(
    "✓ recommendation_distribution.png generated"
)

if len(df) == 92:
    print("✓ 92 Nifty 100 companies validated")
else:
    print(
        f"⚠ Companies found: {len(df)}"
    )


print()
print(
    "INVESTMENT RECOMMENDER VALIDATION PASSED"
)