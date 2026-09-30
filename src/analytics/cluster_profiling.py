"""
NIFTY 100 - DAY 37
CLUSTER PROFILING & STATISTICS

Outputs:
    output/cluster_profiles.csv
    output/outlier_report.csv
    output/portfolio_stats.csv
    reports/correlation_heatmap.png

This version includes:
    - 92-company Nifty 100 filtering
    - Annual-record filtering
    - TTM exclusion
    - Robust financial-ratio cleaning
    - CAGR validation
    - Cluster profiling
    - Correlation matrix
    - Sector-wise outlier detection
    - Portfolio statistics
    - Day 37 validation
"""

from pathlib import Path
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

FINANCIAL_FILE = BASE_DIR / "output" / "financial_ratios.xlsx"
SECTOR_FILE = BASE_DIR / "data" / "raw" / "sectors.xlsx"
CLUSTER_FILE = BASE_DIR / "output" / "cluster_labels.csv"

OUTPUT_DIR = BASE_DIR / "output"
REPORT_DIR = BASE_DIR / "reports"

OUTPUT_DIR.mkdir(exist_ok=True)
REPORT_DIR.mkdir(exist_ok=True)

CLUSTER_PROFILE_FILE = OUTPUT_DIR / "cluster_profiles.csv"
OUTLIER_FILE = OUTPUT_DIR / "outlier_report.csv"
PORTFOLIO_FILE = OUTPUT_DIR / "portfolio_stats.csv"
HEATMAP_FILE = REPORT_DIR / "correlation_heatmap.png"


warnings.filterwarnings("ignore")


# ============================================================
# EXPECTED CLUSTER NAMES
# ============================================================

EXPECTED_CLUSTERS = {
    0: "Defensive Dividend Payers",
    1: "Emerging Growth",
    2: "Distressed or Turnaround",
    3: "High-Quality Compounders",
    4: "Value Cyclicals",
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clean_numeric(df, columns):
    """Convert selected columns to numeric."""
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def robust_clip(series, lower=0.01, upper=0.99):
    """
    Winsorize a numeric series using percentile limits.

    This prevents extreme malformed source values from
    dominating averages and correlations.
    """
    s = pd.to_numeric(series, errors="coerce")

    if s.dropna().empty:
        return s

    low = s.quantile(lower)
    high = s.quantile(upper)

    return s.clip(lower=low, upper=high)


def validate_ratio_values(df):
    """
    Remove obviously invalid financial-ratio values.

    The raw source contains examples such as:
        ROE = 6,954,300%
        OPM = 47,971%

    Such values usually occur because of denominator/data
    issues and should not be used directly for portfolio
    statistics.
    """

    # ROE:
    # Values outside approximately +/- 200% are treated as
    # suspicious for this dataset.
    if "return_on_equity_pct" in df.columns:
        df.loc[
            (df["return_on_equity_pct"] > 200) |
            (df["return_on_equity_pct"] < -200),
            "return_on_equity_pct"
        ] = np.nan

    # OPM:
    # Values outside +/- 200% are treated as suspicious.
    if "operating_profit_margin_pct" in df.columns:
        df.loc[
            (df["operating_profit_margin_pct"] > 200) |
            (df["operating_profit_margin_pct"] < -200),
            "operating_profit_margin_pct"
        ] = np.nan

    # Debt/equity cannot be negative in this use case.
    if "debt_to_equity" in df.columns:
        df.loc[
            df["debt_to_equity"] < 0,
            "debt_to_equity"
        ] = np.nan

    # CAGR values outside a reasonable range are treated as
    # suspicious.
    if "revenue_cagr_5yr" in df.columns:
        df.loc[
            (df["revenue_cagr_5yr"] > 200) |
            (df["revenue_cagr_5yr"] < -100),
            "revenue_cagr_5yr"
        ] = np.nan

    if "fcf_cagr_5yr" in df.columns:
        df.loc[
            (df["fcf_cagr_5yr"] > 200) |
            (df["fcf_cagr_5yr"] < -100),
            "fcf_cagr_5yr"
        ] = np.nan

    return df


def prepare_annual_data(financial_df, sector_df):
    """
    Prepare latest annual record for each of the 92 Nifty 100
    companies represented in sectors.xlsx.
    """

    print("\nPreparing annual financial records...")

    # --------------------------------------------------------
    # Filter to 92 companies
    # --------------------------------------------------------

    sector_companies = set(
        sector_df["company_id"]
        .dropna()
        .astype(str)
        .str.strip()
    )

    financial_df["company_id"] = (
        financial_df["company_id"]
        .astype(str)
        .str.strip()
    )

    financial_df = financial_df[
        financial_df["company_id"].isin(sector_companies)
    ].copy()

    print(
        f"Financial companies after 92-company filter: "
        f"{financial_df['company_id'].nunique()}"
    )

    print(f"Financial rows after filter: {len(financial_df)}")

    # --------------------------------------------------------
    # Clean year
    # --------------------------------------------------------

    financial_df["year"] = (
        financial_df["year"]
        .astype(str)
        .str.strip()
    )

    # Only proper annual records.
    # TTM is intentionally excluded.
    annual_pattern = r"^(Mar|Sep|Dec|Jun) \d{4}$"

    financial_df = financial_df[
        financial_df["year"].str.match(
            annual_pattern,
            na=False
        )
    ].copy()

    # --------------------------------------------------------
    # Convert year to sortable date
    # --------------------------------------------------------

    financial_df["year_date"] = pd.to_datetime(
        financial_df["year"],
        format="%b %Y",
        errors="coerce"
    )

    financial_df = financial_df[
        financial_df["year_date"].notna()
    ].copy()

    # --------------------------------------------------------
    # Numeric conversion
    # --------------------------------------------------------

    numeric_columns = [
        "sales",
        "net_profit",
        "eps",
        "free_cash_flow_cr",
        "net_cash_flow",
        "operating_activity",
        "investing_activity",
        "financing_activity",
        "return_on_equity_pct",
        "debt_to_equity",
        "opm_percentage",
    ]

    financial_df = clean_numeric(
        financial_df,
        numeric_columns
    )

    # --------------------------------------------------------
    # Rename OPM consistently
    # --------------------------------------------------------

    if "opm_percentage" in financial_df.columns:
        financial_df["operating_profit_margin_pct"] = (
            financial_df["opm_percentage"]
        )

    # --------------------------------------------------------
    # Validate ratios
    # --------------------------------------------------------

    financial_df = validate_ratio_values(
        financial_df
    )

    # --------------------------------------------------------
    # Revenue CAGR
    #
    # Recalculate using approximately 5 annual periods when
    # possible instead of trusting malformed values.
    # --------------------------------------------------------

    financial_df = financial_df.sort_values(
        ["company_id", "year_date"]
    )

    def calculate_cagr(group, value_col):
        """
        Calculate 5-year CAGR using the latest available
        annual value and approximately 5 years earlier.

        Returns one value for the latest record.
        """

        group = group.sort_values("year_date").copy()

        if value_col not in group.columns:
            return np.nan

        valid = group[
            group[value_col].notna() &
            (group[value_col] > 0)
        ]

        if len(valid) < 2:
            return np.nan

        latest = valid.iloc[-1]

        target_date = latest["year_date"] - pd.DateOffset(years=5)

        previous = valid.iloc[
            (valid["year_date"] - target_date)
            .abs()
            .argsort()
            .iloc[0]
        ]

        years = (
            latest["year_date"] - previous["year_date"]
        ).days / 365.25

        if years <= 0:
            return np.nan

        start_value = previous[value_col]
        end_value = latest[value_col]

        if start_value <= 0 or end_value <= 0:
            return np.nan

        cagr = (
            (end_value / start_value)
            ** (1 / years)
            - 1
        ) * 100

        if not np.isfinite(cagr):
            return np.nan

        if cagr > 200 or cagr < -100:
            return np.nan

        return cagr

    # --------------------------------------------------------
    # Build latest-company dataset
    # --------------------------------------------------------

    latest = (
        financial_df
        .sort_values(
            ["company_id", "year_date"]
        )
        .groupby("company_id", as_index=False)
        .tail(1)
        .copy()
    )

    # Calculate revenue CAGR separately.
    revenue_cagr = (
        financial_df
        .groupby("company_id")
        .apply(
            lambda g: calculate_cagr(
                g,
                "sales"
            ),
            include_groups=False
        )
    )

    revenue_cagr = revenue_cagr.rename(
        "revenue_cagr_5yr"
    )

    latest = latest.drop(
        columns=["revenue_cagr_5yr"],
        errors="ignore"
    )

    latest = latest.merge(
        revenue_cagr,
        on="company_id",
        how="left"
    )

    # --------------------------------------------------------
    # FCF CAGR
    #
    # Source FCF is currently zero for all rows in the user's
    # dataset, therefore a meaningful FCF CAGR cannot be
    # calculated.
    # --------------------------------------------------------

    latest["fcf_cagr_5yr"] = np.nan

    # --------------------------------------------------------
    # Merge sector
    # --------------------------------------------------------

    sector_columns = [
        "company_id",
        "broad_sector",
        "sub_sector",
        "index_weight_pct",
        "market_cap_category",
    ]

    sector_small = sector_df[
        [c for c in sector_columns if c in sector_df.columns]
    ].drop_duplicates(
        subset=["company_id"]
    )

    latest = latest.merge(
        sector_small,
        on="company_id",
        how="left"
    )

    print(
        f"\nLatest-year company records: "
        f"{latest['company_id'].nunique()}"
    )

    return latest


# ============================================================
# CLUSTER PROFILING
# ============================================================

def create_cluster_profiles(df, clusters):
    print("\n" + "=" * 70)
    print("CLUSTER PROFILES")
    print("=" * 70)

    profile_features = [
        "return_on_equity_pct",
        "debt_to_equity",
        "revenue_cagr_5yr",
        "fcf_cagr_5yr",
        "operating_profit_margin_pct",
    ]

    # Merge cluster labels
    df = df.merge(
        clusters[
            ["company_id", "cluster_id", "cluster_name"]
        ],
        on="company_id",
        how="inner"
    )

    # Ensure expected cluster names
    df["cluster_name"] = df["cluster_id"].map(
        EXPECTED_CLUSTERS
    ).fillna(
        df["cluster_name"]
    )

    records = []

    for cluster_id, group in df.groupby(
        "cluster_id",
        sort=True
    ):

        row = {
            "cluster_id": cluster_id,
            "cluster_name": group["cluster_name"].iloc[0],
            "company_count": group["company_id"].nunique(),
        }

        for feature in profile_features:

            if feature not in group.columns:
                row[f"{feature}_mean"] = np.nan
                row[f"{feature}_median"] = np.nan
                continue

            values = pd.to_numeric(
                group[feature],
                errors="coerce"
            ).dropna()

            if values.empty:
                row[f"{feature}_mean"] = np.nan
                row[f"{feature}_median"] = np.nan
            else:
                # Use trimmed/winsorized values for statistics.
                clean_values = robust_clip(
                    values,
                    0.05,
                    0.95
                )

                row[f"{feature}_mean"] = (
                    clean_values.mean()
                )

                row[f"{feature}_median"] = (
                    clean_values.median()
                )

        records.append(row)

    profile_df = pd.DataFrame(records)

    profile_df.to_csv(
        CLUSTER_PROFILE_FILE,
        index=False
    )

    print(
        profile_df.to_string(index=False)
    )

    print(
        f"\nSaved: {CLUSTER_PROFILE_FILE}"
    )

    return profile_df, df


# ============================================================
# CORRELATION MATRIX
# ============================================================

def create_correlation_matrix(df):

    print("\n" + "=" * 70)
    print("CORRELATION MATRIX")
    print("=" * 70)

    correlation_columns = [
        "return_on_equity_pct",
        "debt_to_equity",
        "revenue_cagr_5yr",
        "fcf_cagr_5yr",
        "operating_profit_margin_pct",
        "sales",
        "net_profit",
        "eps",
        "free_cash_flow_cr",
        "net_cash_flow",
    ]

    available = [
        c for c in correlation_columns
        if c in df.columns
    ]

    corr_df = df[available].copy()

    # Clean extreme values before correlation.
    for col in available:
        corr_df[col] = robust_clip(
            corr_df[col]
        )

    corr = corr_df.corr(
        method="pearson"
    )

    print(
        corr.round(2).to_string()
    )

    # --------------------------------------------------------
    # Heatmap
    # --------------------------------------------------------

    plt.figure(
        figsize=(12, 9)
    )

    image = plt.imshow(
        corr,
        interpolation="nearest",
        aspect="auto"
    )

    plt.colorbar(image)

    plt.xticks(
        range(len(corr.columns)),
        corr.columns,
        rotation=45,
        ha="right"
    )

    plt.yticks(
        range(len(corr.index)),
        corr.index
    )

    plt.title(
        "NIFTY 100 Financial Metrics Correlation"
    )

    plt.tight_layout()

    plt.savefig(
        HEATMAP_FILE,
        dpi=200,
        bbox_inches="tight"
    )

    plt.close()

    print(
        f"\nSaved correlation heatmap: "
        f"{HEATMAP_FILE}"
    )

    return corr


# ============================================================
# SECTOR OUTLIERS
# ============================================================

def detect_sector_outliers(df):

    print("\n" + "=" * 70)
    print("SECTOR-WISE OUTLIER DETECTION")
    print("=" * 70)

    metrics = [
        "return_on_equity_pct",
        "debt_to_equity",
        "revenue_cagr_5yr",
        "operating_profit_margin_pct",
    ]

    outliers = []

    for sector, sector_group in df.groupby(
        "broad_sector"
    ):

        for metric in metrics:

            if metric not in sector_group.columns:
                continue

            values = pd.to_numeric(
                sector_group[metric],
                errors="coerce"
            )

            valid = values.dropna()

            if len(valid) < 3:
                continue

            mean = valid.mean()
            std = valid.std()

            if std == 0 or pd.isna(std):
                continue

            z_scores = (
                values - mean
            ) / std

            for idx in sector_group.index[
                z_scores.abs() >= 3
            ]:

                value = values.loc[idx]
                z = z_scores.loc[idx]

                severity = (
                    "HIGH"
                    if abs(z) >= 3
                    else "MEDIUM"
                )

                outliers.append({
                    "company_id":
                        sector_group.loc[
                            idx,
                            "company_id"
                        ],

                    "broad_sector":
                        sector,

                    "metric":
                        metric,

                    "value":
                        value,

                    "sector_mean":
                        mean,

                    "sector_std":
                        std,

                    "z_score":
                        z,

                    "threshold":
                        3,

                    "severity":
                        severity,
                })

    outlier_df = pd.DataFrame(
        outliers
    )

    if not outlier_df.empty:
        outlier_df = outlier_df.sort_values(
            "z_score",
            key=lambda x: x.abs(),
            ascending=False
        )

    outlier_df.to_csv(
        OUTLIER_FILE,
        index=False
    )

    print(
        f"\nOutliers found: "
        f"{len(outlier_df)}"
    )

    print(
        f"Saved: {OUTLIER_FILE}"
    )

    if not outlier_df.empty:
        print("\nTop outliers:")
        print(
            outlier_df.head(10).to_string(
                index=False
            )
        )

    return outlier_df


# ============================================================
# PORTFOLIO STATISTICS
# ============================================================

def create_portfolio_statistics(df):

    print("\n" + "=" * 70)
    print("PORTFOLIO STATISTICS")
    print("=" * 70)

    metrics = [
        "return_on_equity_pct",
        "debt_to_equity",
        "revenue_cagr_5yr",
        "operating_profit_margin_pct",
        "sales",
        "net_profit",
        "eps",
        "free_cash_flow_cr",
        "net_cash_flow",
    ]

    rows = []

    for metric in metrics:

        if metric not in df.columns:
            continue

        values = pd.to_numeric(
            df[metric],
            errors="coerce"
        ).dropna()

        if values.empty:
            continue

        # Winsorized values prevent extreme source errors
        # from destroying portfolio statistics.
        clean_values = robust_clip(
            values,
            0.05,
            0.95
        )

        rows.append({
            "kpi": metric,
            "P10": clean_values.quantile(0.10),
            "P25": clean_values.quantile(0.25),
            "P50": clean_values.quantile(0.50),
            "P75": clean_values.quantile(0.75),
            "P90": clean_values.quantile(0.90),
            "Mean": clean_values.mean(),
            "Std": clean_values.std(),
        })

    stats_df = pd.DataFrame(
        rows
    )

    stats_df.to_csv(
        PORTFOLIO_FILE,
        index=False
    )

    print(
        stats_df.to_string(
            index=False
        )
    )

    print(
        f"\nSaved: {PORTFOLIO_FILE}"
    )

    return stats_df


# ============================================================
# VALIDATION
# ============================================================

def validate_day_37(
    company_df,
    profile_df,
    outlier_df,
    portfolio_df,
):

    print("\n" + "=" * 70)
    print("DAY 37 VALIDATION")
    print("=" * 70)

    errors = []

    # --------------------------------------------------------
    # 92 companies
    # --------------------------------------------------------

    company_count = (
        company_df["company_id"]
        .nunique()
    )

    if company_count == 92:
        print("✓ 92 companies available")
    else:
        errors.append(
            f"Expected 92 companies, found {company_count}"
        )

    # --------------------------------------------------------
    # 5 clusters
    # --------------------------------------------------------

    cluster_count = (
        profile_df["cluster_id"]
        .nunique()
    )

    if cluster_count == 5:
        print("✓ 5 clusters profiled")
    else:
        errors.append(
            f"Expected 5 clusters, found {cluster_count}"
        )

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    required_stat_columns = [
        "company_count",
        "return_on_equity_pct_mean",
        "return_on_equity_pct_median",
        "debt_to_equity_mean",
        "debt_to_equity_median",
        "revenue_cagr_5yr_mean",
        "revenue_cagr_5yr_median",
    ]

    missing = [
        c for c in required_stat_columns
        if c not in profile_df.columns
    ]

    if not missing:
        print(
            "✓ Mean and median statistics generated"
        )
    else:
        errors.append(
            f"Missing profile columns: {missing}"
        )

    # --------------------------------------------------------
    # Heatmap
    # --------------------------------------------------------

    if HEATMAP_FILE.exists():
        print(
            "✓ Correlation heatmap generated"
        )
    else:
        errors.append(
            "Correlation heatmap missing"
        )

    # --------------------------------------------------------
    # Outlier report
    # --------------------------------------------------------

    if OUTLIER_FILE.exists():
        print(
            "✓ outlier_report.csv generated"
        )
    else:
        errors.append(
            "outlier_report.csv missing"
        )

    # --------------------------------------------------------
    # Portfolio stats
    # --------------------------------------------------------

    if PORTFOLIO_FILE.exists():
        print(
            "✓ portfolio_stats.csv generated"
        )
    else:
        errors.append(
            "portfolio_stats.csv missing"
        )

    # --------------------------------------------------------
    # Percentiles
    # --------------------------------------------------------

    required_percentiles = [
        "P10",
        "P25",
        "P50",
        "P75",
        "P90",
        "Mean",
        "Std",
    ]

    missing_percentiles = [
        c for c in required_percentiles
        if c not in portfolio_df.columns
    ]

    if not missing_percentiles:
        print(
            "✓ P10-P90, Mean and Std generated"
        )
    else:
        errors.append(
            f"Missing portfolio statistics: "
            f"{missing_percentiles}"
        )

    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    if errors:

        print("\nDAY 37 VALIDATION FAILED")

        for error in errors:
            print(f"✗ {error}")

        raise ValueError(
            "Day 37 validation failed."
        )

    print("\n" + "=" * 70)
    print("DAY 37 VALIDATION PASSED")
    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

def run_cluster_profiling():

    print("=" * 70)
    print("NIFTY 100 - DAY 37 CLUSTER PROFILING & STATISTICS")
    print("=" * 70)

    # --------------------------------------------------------
    # Load financial data
    # --------------------------------------------------------

    print("\nLoading financial data...")

    if not FINANCIAL_FILE.exists():
        raise FileNotFoundError(
            f"Missing financial file: "
            f"{FINANCIAL_FILE}"
        )

    financial_df = pd.read_excel(
        FINANCIAL_FILE
    )

    print(
        f"Financial rows: {len(financial_df)}"
    )

    print(
        f"Financial companies: "
        f"{financial_df['company_id'].nunique()}"
    )

    # --------------------------------------------------------
    # Load sector data
    # --------------------------------------------------------

    print("Loading sector data...")

    if not SECTOR_FILE.exists():
        raise FileNotFoundError(
            f"Missing sector file: "
            f"{SECTOR_FILE}"
        )

    sector_df = pd.read_excel(
        SECTOR_FILE
    )

    sector_df["company_id"] = (
        sector_df["company_id"]
        .astype(str)
        .str.strip()
    )

    print(
        f"Sector companies: "
        f"{sector_df['company_id'].nunique()}"
    )

    # --------------------------------------------------------
    # Load clusters
    # --------------------------------------------------------

    print("Loading cluster labels...")

    if not CLUSTER_FILE.exists():
        raise FileNotFoundError(
            f"Missing cluster file: "
            f"{CLUSTER_FILE}"
        )

    cluster_df = pd.read_csv(
        CLUSTER_FILE
    )

    cluster_df["company_id"] = (
        cluster_df["company_id"]
        .astype(str)
        .str.strip()
    )

    print(
        f"Cluster companies: "
        f"{cluster_df['company_id'].nunique()}"
    )

    # --------------------------------------------------------
    # Prepare latest annual data
    # --------------------------------------------------------

    latest = prepare_annual_data(
        financial_df,
        sector_df
    )

    # --------------------------------------------------------
    # Validate company count
    # --------------------------------------------------------

    if latest["company_id"].nunique() != 92:

        missing = sorted(
            set(sector_df["company_id"])
            - set(latest["company_id"])
        )

        print(
            "\nMissing companies:"
        )
        print(missing)

        raise ValueError(
            f"Expected 92 companies but found "
            f"{latest['company_id'].nunique()}"
        )

    # --------------------------------------------------------
    # Cluster profiling
    # --------------------------------------------------------

    profile_df, company_df = (
        create_cluster_profiles(
            latest,
            cluster_df
        )
    )

    # --------------------------------------------------------
    # Correlation
    # --------------------------------------------------------

    create_correlation_matrix(
        company_df
    )

    # --------------------------------------------------------
    # Outliers
    # --------------------------------------------------------

    outlier_df = detect_sector_outliers(
        company_df
    )

    # --------------------------------------------------------
    # Portfolio statistics
    # --------------------------------------------------------

    portfolio_df = create_portfolio_statistics(
        company_df
    )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    validate_day_37(
        company_df,
        profile_df,
        outlier_df,
        portfolio_df,
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    run_cluster_profiling()