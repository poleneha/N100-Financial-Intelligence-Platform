"""
NIFTY 100 FINANCIAL INTELLIGENCE PLATFORM
Portfolio Scoring & Investment Ranking

Inputs:
    output/cluster_labels.csv
    output/outlier_report.csv
    output/cluster_profiles.csv
    output/financial_ratios.xlsx
    data/raw/sectors.xlsx

Outputs:
    output/portfolio_scoring.csv
    output/top_ranked_companies.csv
    reports/portfolio_score_distribution.png
    reports/cluster_score_comparison.png
"""

import os
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

FINANCIAL_FILE = os.path.join(
    BASE_DIR, "output", "financial_ratios.xlsx"
)

SECTOR_FILE = os.path.join(
    BASE_DIR, "data", "raw", "sectors.xlsx"
)

CLUSTER_FILE = os.path.join(
    BASE_DIR, "output", "cluster_labels.csv"
)

OUTLIER_FILE = os.path.join(
    BASE_DIR, "output", "outlier_report.csv"
)

CLUSTER_PROFILE_FILE = os.path.join(
    BASE_DIR, "output", "cluster_profiles.csv"
)

OUTPUT_DIR = os.path.join(BASE_DIR, "output")
REPORT_DIR = os.path.join(BASE_DIR, "reports")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)


# ============================================================
# HELPERS
# ============================================================

def safe_numeric(series):
    return pd.to_numeric(series, errors="coerce")


def minmax_score(series, higher_is_better=True):
    """
    Convert values into a 0-100 score.
    Uses percentile clipping to reduce the impact of extreme
    financial-data outliers.
    """

    x = safe_numeric(series).copy()

    if x.notna().sum() == 0:
        return pd.Series(50.0, index=series.index)

    lower = x.quantile(0.05)
    upper = x.quantile(0.95)

    if pd.isna(lower) or pd.isna(upper) or upper == lower:
        return pd.Series(50.0, index=series.index)

    x = x.clip(lower, upper)

    if higher_is_better:
        score = (x - lower) / (upper - lower) * 100
    else:
        score = (upper - x) / (upper - lower) * 100

    return score.fillna(50).clip(0, 100)


def latest_annual_records(df):
    """
    Select latest annual record for every company.

    Excludes TTM and malformed periods.
    """

    df = df.copy()

    df["year"] = df["year"].astype(str).str.strip()

    valid_pattern = r"^(Mar|Sep|Dec|Jun) \d{4}$"

    df = df[
        df["year"].str.match(valid_pattern, na=False)
    ].copy()

    # Extract year number for reliable chronological sorting.
    df["year_num"] = (
        df["year"]
        .str.extract(r"(\d{4})")[0]
        .astype(float)
    )

    latest = (
        df.sort_values(["company_id", "year_num"])
        .groupby("company_id", as_index=False)
        .tail(1)
        .copy()
    )

    latest.drop(columns=["year_num"], inplace=True)

    return latest


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    print("Loading financial data...")
    financial = pd.read_excel(FINANCIAL_FILE)

    print("Loading sector data...")
    sectors = pd.read_excel(SECTOR_FILE)

    print("Loading cluster labels...")
    clusters = pd.read_csv(CLUSTER_FILE)

    print("Loading outlier report...")
    if os.path.exists(OUTLIER_FILE):
        outliers = pd.read_csv(OUTLIER_FILE)
    else:
        outliers = pd.DataFrame(
            columns=["company_id", "metric", "severity"]
        )

    print("Loading cluster profiles...")
    if os.path.exists(CLUSTER_PROFILE_FILE):
        profiles = pd.read_csv(CLUSTER_PROFILE_FILE)
    else:
        profiles = pd.DataFrame()

    return financial, sectors, clusters, outliers, profiles


# ============================================================
# PREPARE FINANCIAL DATA
# ============================================================

def prepare_financial_data(financial, sectors):

    required_financial_columns = [
        "company_id",
        "year",
        "sales",
        "net_profit",
        "eps",
        "net_cash_flow",
        "operating_activity",
        "opm_percentage",
        "return_on_equity_pct",
        "debt_to_equity",
    ]

    for col in required_financial_columns:
        if col not in financial.columns:
            financial[col] = np.nan

    # Keep only companies belonging to the 92-company project universe.
    valid_companies = set(
        sectors["company_id"]
        .dropna()
        .astype(str)
        .str.strip()
    )

    financial["company_id"] = (
        financial["company_id"]
        .astype(str)
        .str.strip()
    )

    financial = financial[
        financial["company_id"].isin(valid_companies)
    ].copy()

    print(
        f"Financial companies after 92-company filter: "
        f"{financial['company_id'].nunique()}"
    )

    print(f"Financial rows after filter: {len(financial)}")

    latest = latest_annual_records(financial)

    print(
        f"Latest annual company records: "
        f"{latest['company_id'].nunique()}"
    )

    return latest


# ============================================================
# FEATURE ENGINEERING
# ============================================================

def create_features(df):

    df = df.copy()

    numeric_columns = [
        "sales",
        "net_profit",
        "eps",
        "net_cash_flow",
        "operating_activity",
        "opm_percentage",
        "return_on_equity_pct",
        "debt_to_equity",
    ]

    for col in numeric_columns:
        df[col] = safe_numeric(df[col])

    # --------------------------------------------------------
    # Revenue / profit growth
    # --------------------------------------------------------

    # Use latest available historical record to calculate
    # approximate 5-year CAGR where possible.
    #
    # The main financial_ratios file contains irregular years,
    # so calculate CAGR from annual records separately.

    # Defaults. These will be overwritten where possible.
    df["revenue_cagr_5yr"] = np.nan
    df["profit_growth_5yr"] = np.nan

    return df


def calculate_growth(financial):

    df = financial.copy()

    df["year"] = df["year"].astype(str).str.strip()

    valid_pattern = r"^(Mar|Sep|Dec|Jun) \d{4}$"

    df = df[
        df["year"].str.match(valid_pattern, na=False)
    ].copy()

    df["year_num"] = (
        df["year"]
        .str.extract(r"(\d{4})")[0]
        .astype(float)
    )

    for col in ["sales", "net_profit"]:
        df[col] = safe_numeric(df[col])

    growth_rows = []

    for company, group in df.groupby("company_id"):

        group = (
            group
            .sort_values("year_num")
            .drop_duplicates("year_num", keep="last")
        )

        if len(group) < 2:
            growth_rows.append(
                {
                    "company_id": company,
                    "revenue_cagr_5yr": np.nan,
                    "profit_growth_5yr": np.nan,
                }
            )
            continue

        latest = group.iloc[-1]

        latest_year = latest["year_num"]

        # Prefer approximately 5 years earlier.
        target_year = latest_year - 5

        historical = group[
            group["year_num"] <= target_year
        ]

        if len(historical) > 0:
            start = historical.iloc[-1]
        else:
            start = group.iloc[0]

        start_sales = start["sales"]
        end_sales = latest["sales"]

        start_profit = start["net_profit"]
        end_profit = latest["net_profit"]

        years = max(
            latest_year - start["year_num"],
            1
        )

        # Revenue CAGR
        if (
            pd.notna(start_sales)
            and pd.notna(end_sales)
            and start_sales > 0
            and end_sales > 0
        ):
            revenue_cagr = (
                (end_sales / start_sales)
                ** (1 / years)
                - 1
            ) * 100
        else:
            revenue_cagr = np.nan

        # Profit CAGR
        if (
            pd.notna(start_profit)
            and pd.notna(end_profit)
            and start_profit > 0
            and end_profit > 0
        ):
            profit_growth = (
                (end_profit / start_profit)
                ** (1 / years)
                - 1
            ) * 100
        else:
            profit_growth = np.nan

        growth_rows.append(
            {
                "company_id": company,
                "revenue_cagr_5yr": revenue_cagr,
                "profit_growth_5yr": profit_growth,
            }
        )

    return pd.DataFrame(growth_rows)


# ============================================================
# SCORING
# ============================================================

def calculate_scores(df, outliers):

    df = df.copy()

    print("\nCalculating investment scores...")

    # --------------------------------------------------------
    # Clean extreme / invalid financial ratios
    # --------------------------------------------------------

    # Unrealistic source-data ratios can distort rankings.
    df["return_on_equity_pct"] = (
        df["return_on_equity_pct"]
        .replace([np.inf, -np.inf], np.nan)
    )

    df["debt_to_equity"] = (
        df["debt_to_equity"]
        .replace([np.inf, -np.inf], np.nan)
    )

    df["opm_percentage"] = (
        df["opm_percentage"]
        .replace([np.inf, -np.inf], np.nan)
    )

    # Reasonable clipping for scoring.
    df["return_on_equity_pct"] = (
        df["return_on_equity_pct"].clip(-20, 100)
    )

    df["debt_to_equity"] = (
        df["debt_to_equity"].clip(0, 15)
    )

    df["opm_percentage"] = (
        df["opm_percentage"].clip(-50, 100)
    )

    # --------------------------------------------------------
    # Individual scores
    # --------------------------------------------------------

    df["roe_score"] = minmax_score(
        df["return_on_equity_pct"],
        higher_is_better=True
    )

    df["growth_score"] = minmax_score(
        df["revenue_cagr_5yr"],
        higher_is_better=True
    )

    df["profitability_score"] = minmax_score(
        df["opm_percentage"],
        higher_is_better=True
    )

    df["leverage_score"] = minmax_score(
        df["debt_to_equity"],
        higher_is_better=False
    )

    df["cashflow_score"] = minmax_score(
        df["net_cash_flow"],
        higher_is_better=True
    )

    # --------------------------------------------------------
    # Outlier penalty
    # --------------------------------------------------------

    outlier_companies = set()

    if not outliers.empty and "company_id" in outliers.columns:
        outlier_companies = set(
            outliers["company_id"]
            .dropna()
            .astype(str)
            .str.strip()
        )

    df["outlier_penalty"] = np.where(
        df["company_id"].isin(outlier_companies),
        10.0,
        0.0
    )

    # --------------------------------------------------------
    # Weighted investment score
    # --------------------------------------------------------

    df["investment_score"] = (
        df["roe_score"] * 0.20
        + df["growth_score"] * 0.20
        + df["profitability_score"] * 0.20
        + df["leverage_score"] * 0.15
        + df["cashflow_score"] * 0.25
        - df["outlier_penalty"]
    )

    df["investment_score"] = (
        df["investment_score"]
        .clip(0, 100)
        .round(2)
    )

    # --------------------------------------------------------
    # Investment category
    # --------------------------------------------------------

    def category(score):

        if score >= 75:
            return "Strong"

        if score >= 60:
            return "Good"

        if score >= 45:
            return "Moderate"

        if score >= 30:
            return "Weak"

        return "High Risk"

    df["investment_category"] = (
        df["investment_score"]
        .apply(category)
    )

    # --------------------------------------------------------
    # Rank
    # --------------------------------------------------------

    df = df.sort_values(
        "investment_score",
        ascending=False
    ).reset_index(drop=True)

    df["rank"] = np.arange(1, len(df) + 1)

    return df


# ============================================================
# OUTPUT
# ============================================================

def save_outputs(df):

    output_columns = [
        "company_id",
        "year",
        "cluster_id",
        "cluster_name",
        "return_on_equity_pct",
        "debt_to_equity",
        "revenue_cagr_5yr",
        "opm_percentage",
        "net_profit",
        "eps",
        "net_cash_flow",
        "roe_score",
        "growth_score",
        "profitability_score",
        "leverage_score",
        "cashflow_score",
        "outlier_penalty",
        "investment_score",
        "investment_category",
        "rank",
    ]

    for col in output_columns:
        if col not in df.columns:
            df[col] = np.nan

    portfolio = df[output_columns].copy()

    portfolio_file = os.path.join(
        OUTPUT_DIR,
        "portfolio_scoring.csv"
    )

    portfolio.to_csv(
        portfolio_file,
        index=False
    )

    print(f"\nSaved: {portfolio_file}")

    # Top 20 companies
    top_ranked = portfolio.head(20).copy()

    top_file = os.path.join(
        OUTPUT_DIR,
        "top_ranked_companies.csv"
    )

    top_ranked.to_csv(
        top_file,
        index=False
    )

    print(f"Saved: {top_file}")

    return portfolio

# ============================================================
# CHART 1
# ============================================================

def create_score_distribution(df):

    print("\nCreating score distribution...")

    plt.figure(figsize=(10, 6))

    plt.hist(
        df["investment_score"].dropna(),
        bins=15
    )

    plt.xlabel("Investment Score")
    plt.ylabel("Number of Companies")
    plt.title("Nifty 100 Investment Score Distribution")

    plt.tight_layout()

    file_path = os.path.join(
        REPORT_DIR,
        "portfolio_score_distribution.png"
    )

    plt.savefig(
        file_path,
        dpi=150
    )

    plt.close()

    print(f"Saved: {file_path}")


# ============================================================
# CHART 2
# ============================================================

def create_cluster_comparison(df):

    print("Creating cluster score comparison...")

    cluster_scores = (
        df.groupby(
            ["cluster_id", "cluster_name"],
            as_index=False
        )["investment_score"]
        .mean()
        .sort_values("investment_score", ascending=False)
    )

    plt.figure(figsize=(11, 6))

    labels = (
        cluster_scores["cluster_id"].astype(str)
        + " - "
        + cluster_scores["cluster_name"]
    )

    plt.bar(
        labels,
        cluster_scores["investment_score"]
    )

    plt.xlabel("Cluster")
    plt.ylabel("Average Investment Score")
    plt.title("Average Investment Score by Cluster")

    plt.xticks(
        rotation=25,
        ha="right"
    )

    plt.tight_layout()

    file_path = os.path.join(
        REPORT_DIR,
        "cluster_score_comparison.png"
    )

    plt.savefig(
        file_path,
        dpi=150
    )

    plt.close()

    print(f"Saved: {file_path}")


# ============================================================
# VALIDATION
# ============================================================

def validate_results(df):

    print("\n" + "=" * 70)
    print("PORTFOLIO SCORING VALIDATION")
    print("=" * 70)

    company_count = df["company_id"].nunique()

    cluster_count = df["cluster_id"].nunique()

    print(f"✓ Companies scored: {company_count}")
    print(f"✓ Clusters available: {cluster_count}")

    required_columns = [
        "company_id",
        "cluster_id",
        "cluster_name",
        "investment_score",
        "investment_category",
        "rank",
    ]

    for col in required_columns:

        if col in df.columns:
            print(f"✓ {col}")
        else:
            raise ValueError(
                f"Missing required column: {col}"
            )

    if company_count != 92:
        raise ValueError(
            f"Expected 92 companies but found {company_count}"
        )

    if df["investment_score"].isna().any():
        raise ValueError(
            "Investment score contains missing values"
        )

    if df["investment_score"].min() < 0:
        raise ValueError(
            "Investment score below 0 detected"
        )

    if df["investment_score"].max() > 100:
        raise ValueError(
            "Investment score above 100 detected"
        )

    if df["rank"].nunique() != 92:
        raise ValueError(
            "Ranking validation failed"
        )

    print("✓ 92 companies scored")
    print("✓ Investment scores between 0 and 100")
    print("✓ Every company has a category")
    print("✓ Every company has a unique rank")
    print("✓ Portfolio scoring CSV generated")
    print("✓ Top-ranked companies CSV generated")
    print("✓ Score distribution generated")
    print("✓ Cluster score comparison generated")

    print("\n" + "=" * 70)
    print("PORTFOLIO SCORING VALIDATION PASSED")
    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

def run_portfolio_scoring():

    print("=" * 70)
    print("NIFTY 100 - PORTFOLIO SCORING & INVESTMENT RANKING")
    print("=" * 70)

    financial, sectors, clusters, outliers, profiles = load_data()
    # --------------------------------------------------------
    # Financial data
    # --------------------------------------------------------

    latest = prepare_financial_data(
        financial,
        sectors
    )

    # --------------------------------------------------------
    # Growth calculations
    # --------------------------------------------------------

    growth = calculate_growth(financial)

    latest = latest.merge(
        growth,
        on="company_id",
        how="left"
    )

    # --------------------------------------------------------
    # Cluster labels
    # --------------------------------------------------------

    clusters["company_id"] = (
        clusters["company_id"]
        .astype(str)
        .str.strip()
    )

    latest["company_id"] = (
        latest["company_id"]
        .astype(str)
        .str.strip()
    )

    latest = latest.merge(
        clusters[
            [
                "company_id",
                "cluster_id",
                "cluster_name",
            ]
        ],
        on="company_id",
        how="left"
    )

    # --------------------------------------------------------
    # Validation before scoring
    # --------------------------------------------------------

    missing_clusters = latest[
        latest["cluster_id"].isna()
    ]["company_id"].tolist()

    if missing_clusters:
        raise ValueError(
            f"Companies missing cluster labels: "
            f"{missing_clusters}"
        )

    print(
        f"\nCompanies ready for scoring: "
        f"{latest['company_id'].nunique()}"
    )

    # --------------------------------------------------------
    # Calculate scores
    # --------------------------------------------------------

    scored = calculate_scores(
        latest,
        outliers
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    portfolio = save_outputs(scored)

    # --------------------------------------------------------
    # Charts
    # --------------------------------------------------------

    create_score_distribution(
        portfolio
    )

    create_cluster_comparison(
        portfolio
    )

    # --------------------------------------------------------
    # Show top companies
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TOP 20 RANKED COMPANIES")
    print("=" * 70)

    print(
        portfolio[
            [
                "rank",
                "company_id",
                "cluster_name",
                "investment_score",
                "investment_category",
            ]
        ]
        .head(20)
        .to_string(index=False)
    )

    # --------------------------------------------------------
    # Category distribution
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("INVESTMENT CATEGORY DISTRIBUTION")
    print("=" * 70)

    print(
        portfolio["investment_category"]
        .value_counts()
        .to_string()
    )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    validate_results(
        portfolio
    )


if __name__ == "__main__":
    run_portfolio_scoring()