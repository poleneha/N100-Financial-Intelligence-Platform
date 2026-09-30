"""
NIFTY 100 Financial Intelligence Platform
Sprint 6 - Day 36: KMeans Clustering

Creates:
    output/cluster_labels.csv
    reports/elbow_plot.png

Features:
    return_on_equity_pct
    debt_to_equity
    revenue_cagr_5yr
    fcf_cagr_5yr
    operating_profit_margin_pct
"""

from pathlib import Path
import re

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

FINANCIAL_FILE = PROJECT_ROOT / "output" / "financial_ratios.xlsx"
SECTOR_FILE = PROJECT_ROOT / "data" / "raw" / "sectors.xlsx"

OUTPUT_DIR = PROJECT_ROOT / "output"
REPORTS_DIR = PROJECT_ROOT / "reports"

CLUSTER_FILE = OUTPUT_DIR / "cluster_labels.csv"
ELBOW_FILE = REPORTS_DIR / "elbow_plot.png"


# ============================================================
# SETTINGS
# ============================================================

EXPECTED_COMPANIES = 92
N_CLUSTERS = 5
RANDOM_STATE = 42

FEATURES = [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "fcf_cagr_5yr",
    "operating_profit_margin_pct",
]


# ============================================================
# GENERAL HELPERS
# ============================================================

def normalize_company_id(value):
    """Return a normalized company identifier."""
    if pd.isna(value):
        return None

    return str(value).strip().upper()


def numeric(series):
    """Convert a pandas Series to numeric values."""
    return pd.to_numeric(series, errors="coerce")


def parse_year(value):
    """
    Extract the financial year from values such as:
    Mar 2024
    Sep 2024
    Dec 2023
    Jun 2015
    """
    if pd.isna(value):
        return np.nan

    text = str(value).strip()

    match = re.search(r"(19|20)\d{2}", text)

    if match:
        return int(match.group())

    return np.nan


def is_annual_year(value):
    """Return True for normal annual financial periods."""
    if pd.isna(value):
        return False

    text = str(value).strip()

    return bool(
        re.match(
            r"^(Mar|Sep|Dec|Jun)\s+(19|20)\d{2}$",
            text,
            flags=re.IGNORECASE,
        )
    )


# ============================================================
# LOAD DATA
# ============================================================

def load_data():
    """Load financial and sector datasets."""
    print("\nLoading financial data...")

    if not FINANCIAL_FILE.exists():
        raise FileNotFoundError(
            f"Financial file not found:\n{FINANCIAL_FILE}"
        )

    financial = pd.read_excel(FINANCIAL_FILE)

    print("Loading sector data...")

    if not SECTOR_FILE.exists():
        raise FileNotFoundError(
            f"Sector file not found:\n{SECTOR_FILE}"
        )

    sectors = pd.read_excel(SECTOR_FILE)

    required_financial = [
        "company_id",
        "year",
        "sales",
        "operating_profit",
        "operating_activity",
        "investing_activity",
        "return_on_equity_pct",
        "debt_to_equity",
        "opm_percentage",
    ]

    missing = [
        col for col in required_financial
        if col not in financial.columns
    ]

    if missing:
        raise ValueError(
            f"Missing financial columns: {missing}"
        )

    required_sector = [
        "company_id",
        "broad_sector",
    ]

    missing_sector = [
        col for col in required_sector
        if col not in sectors.columns
    ]

    if missing_sector:
        raise ValueError(
            f"Missing sector columns: {missing_sector}"
        )

    financial["company_id"] = (
        financial["company_id"]
        .map(normalize_company_id)
    )

    sectors["company_id"] = (
        sectors["company_id"]
        .map(normalize_company_id)
    )

    sectors = sectors.drop_duplicates(
        subset=["company_id"]
    )

    # Authoritative 92-company universe
    valid_companies = set(
        sectors["company_id"].dropna()
    )

    financial = financial[
        financial["company_id"].isin(valid_companies)
    ].copy()

    print(
        f"Financial companies after 92-company filter: "
        f"{financial['company_id'].nunique()}"
    )

    print(
        f"Financial rows after filter: {len(financial)}"
    )

    if financial["company_id"].nunique() != EXPECTED_COMPANIES:
        actual = set(financial["company_id"].dropna())
        expected = valid_companies

        missing_companies = sorted(expected - actual)
        extra_companies = sorted(actual - expected)

        raise ValueError(
            f"Expected {EXPECTED_COMPANIES} companies but found "
            f"{financial['company_id'].nunique()}.\n"
            f"Missing: {missing_companies}\n"
            f"Extra: {extra_companies}"
        )

    return financial, sectors


# ============================================================
# YEAR PREPARATION
# ============================================================

def prepare_financial_data(financial):
    """Prepare annual financial records and numeric fields."""
    df = financial.copy()

    df["year_num"] = df["year"].map(parse_year)

    # Keep only annual records.
    # Excludes TTM and special periods such as Mar 2023 15.
    df = df[
        df["year"].map(is_annual_year)
    ].copy()

    numeric_columns = [
        "sales",
        "operating_profit",
        "operating_activity",
        "investing_activity",
        "return_on_equity_pct",
        "debt_to_equity",
        "opm_percentage",
    ]

    for col in numeric_columns:
        df[col] = numeric(df[col])

    # Derive FCF.
    #
    # CFO is generally positive and investing activity is
    # generally negative for capital expenditure.
    #
    # Therefore:
    #
    # FCF = CFO + Investing Cash Flow
    #
    df["derived_fcf"] = (
        df["operating_activity"]
        + df["investing_activity"]
    )

    return df


# ============================================================
# CAGR
# ============================================================

def calculate_cagr(start_value, end_value, years=5):
    """Calculate CAGR only when both values are positive."""
    if pd.isna(start_value) or pd.isna(end_value):
        return np.nan

    if start_value <= 0 or end_value <= 0:
        return np.nan

    try:
        return (
            (end_value / start_value) ** (1 / years) - 1
        ) * 100
    except (ValueError, ZeroDivisionError, OverflowError):
        return np.nan


def get_cagr_from_history(group, value_column):
    """
    Calculate five-year CAGR using the latest annual record
    and the closest record at least five years earlier.
    """
    data = group[
        ["year_num", value_column]
    ].dropna(
        subset=["year_num"]
    ).copy()

    data = data.sort_values("year_num")

    if data.empty:
        return np.nan

    latest_year = data["year_num"].max()

    latest_rows = data[
        data["year_num"] == latest_year
    ]

    if latest_rows.empty:
        return np.nan

    latest_value = latest_rows.iloc[-1][value_column]

    # Find a record around five years before latest.
    target_year = latest_year - 5

    candidates = data[
        data["year_num"] <= target_year
    ].copy()

    if candidates.empty:
        return np.nan

    # Use the closest available historical year.
    start_row = candidates.iloc[-1]

    start_year = start_row["year_num"]
    start_value = start_row[value_column]

    actual_years = latest_year - start_year

    if actual_years < 4:
        return np.nan

    if pd.isna(start_value) or pd.isna(latest_value):
        return np.nan

    if start_value <= 0 or latest_value <= 0:
        return np.nan

    try:
        return (
            (latest_value / start_value)
            ** (1 / actual_years)
            - 1
        ) * 100
    except (
        ValueError,
        ZeroDivisionError,
        OverflowError,
    ):
        return np.nan


# ============================================================
# FEATURE CLEANING
# ============================================================

def clean_clustering_features(df):
    """
    Convert features to numeric and remove clearly invalid
    extreme financial-ratio values.

    Invalid/extreme values are converted to NaN and subsequently
    replaced using sector-median imputation.
    """
    df = df.copy()

    for col in FEATURES:
        df[col] = numeric(df[col])

    # ROE
    #
    # Values such as 6,954,300% are clearly invalid for
    # cross-company clustering and are treated as missing.
    df.loc[
        (df["return_on_equity_pct"] < -100)
        | (df["return_on_equity_pct"] > 200),
        "return_on_equity_pct",
    ] = np.nan

    # Debt / Equity
    #
    # Extremely high values are treated as outliers.
    df.loc[
        (df["debt_to_equity"] < 0)
        | (df["debt_to_equity"] > 20),
        "debt_to_equity",
    ] = np.nan

    # OPM
    #
    # Values such as 47,971% or 6,291% are clearly invalid.
    df.loc[
        (df["operating_profit_margin_pct"] < -100)
        | (df["operating_profit_margin_pct"] > 200),
        "operating_profit_margin_pct",
    ] = np.nan

    # CAGR
    for col in [
        "revenue_cagr_5yr",
        "fcf_cagr_5yr",
    ]:
        df.loc[
            ~np.isfinite(df[col]),
            col,
        ] = np.nan

        df.loc[
            df[col].abs() > 200,
            col,
        ] = np.nan

    return df


# ============================================================
# BUILD FEATURE DATASET
# ============================================================

def build_feature_dataset(financial, sectors):
    """Build one clustering feature row for every company."""
    df = prepare_financial_data(financial)

    records = []

    for company_id, group in df.groupby(
        "company_id",
        sort=True,
    ):
        group = group.sort_values("year_num")

        if group.empty:
            continue

        latest_year = group["year_num"].max()

        latest = group[
            group["year_num"] == latest_year
        ].iloc[-1]

        revenue_cagr = get_cagr_from_history(
            group,
            "sales",
        )

        fcf_cagr = get_cagr_from_history(
            group,
            "derived_fcf",
        )

        record = {
            "company_id": company_id,
            "return_on_equity_pct":
                latest["return_on_equity_pct"],
            "debt_to_equity":
                latest["debt_to_equity"],
            "revenue_cagr_5yr":
                revenue_cagr,
            "fcf_cagr_5yr":
                fcf_cagr,
            "operating_profit_margin_pct":
                latest["opm_percentage"],
            "latest_year":
                latest_year,
        }

        records.append(record)

    feature_df = pd.DataFrame(records)
    # Add sector information.
    feature_df = feature_df.merge(
        sectors[
            [
                "company_id",
                "broad_sector",
            ]
        ],
        on="company_id",
        how="left",
        validate="one_to_one",
    )

    if len(feature_df) != EXPECTED_COMPANIES:
        raise ValueError(
            f"Feature dataset should contain "
            f"{EXPECTED_COMPANIES} companies but contains "
            f"{len(feature_df)}."
        )

    if feature_df["company_id"].nunique() != EXPECTED_COMPANIES:
        raise ValueError(
            "Feature dataset contains duplicate or missing "
            "company IDs."
        )

    print(
        f"\nFeature dataset companies: "
        f"{feature_df['company_id'].nunique()}"
    )

    return feature_df


# ============================================================
# SECTOR MEDIAN IMPUTATION
# ============================================================

def sector_median_imputation(df):
    """Impute missing features using broad-sector medians."""
    df = df.copy()

    for feature in FEATURES:

        # First calculate sector medians.
        sector_medians = (
            df.groupby("broad_sector")[feature]
            .transform("median")
        )

        # Replace missing values with sector median.
        df[feature] = df[feature].fillna(
            sector_medians
        )

        # If an entire sector is missing the feature,
        # use the overall median as fallback.
        overall_median = df[feature].median()

        df[feature] = df[feature].fillna(
            overall_median
        )

    return df


# ============================================================
# ELBOW PLOT
# ============================================================

def generate_elbow_plot(X_scaled):
    """Generate KMeans elbow plot for k=2 through k=10."""
    print("\nGenerating elbow plot...")

    inertias = []
    ks = range(2, 11)

    for k in ks:
        model = KMeans(
            n_clusters=k,
            random_state=RANDOM_STATE,
            n_init=20,
        )

        model.fit(X_scaled)

        inertias.append(model.inertia_)

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    plt.figure(figsize=(9, 6))

    plt.plot(
        list(ks),
        inertias,
        marker="o",
    )

    plt.axvline(
        x=5,
        linestyle="--",
        label="k = 5",
    )

    plt.title(
        "KMeans Elbow Plot - Nifty 100"
    )

    plt.xlabel("Number of Clusters (k)")
    plt.ylabel("Inertia")

    plt.xticks(list(ks))
    plt.legend()

    plt.tight_layout()

    plt.savefig(
        ELBOW_FILE,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close()

    print(
        f"Saved elbow plot: {ELBOW_FILE}"
    )

    return inertias


# ============================================================
# CLUSTER NAMES
# ============================================================

def assign_cluster_names(profile):
    """
    Assign descriptive names based on cluster financial profiles.

    The labels are determined from the actual profile statistics
    rather than assuming cluster IDs have a fixed meaning.
    """
    names = {}

    # Defensive / low leverage
    defensive = (
        profile["debt_to_equity"].idxmin()
    )

    names[defensive] = "Defensive Dividend Payers"

    remaining = [
        c for c in profile.index
        if c not in names
    ]

    # Distressed / turnaround:
    # highest leverage and weakest profitability
    if remaining:
        distressed_score = (
            profile.loc[remaining, "debt_to_equity"].rank(
                ascending=False
            )
            + profile.loc[remaining, "return_on_equity_pct"].rank(
                ascending=True
            )
            + profile.loc[remaining, "fcf_cagr_5yr"].rank(
                ascending=True
            )
        )

        distressed = distressed_score.idxmax()

        names[distressed] = "Distressed or Turnaround"

    remaining = [
        c for c in profile.index
        if c not in names
    ]

    # Emerging growth:
    # strongest revenue and FCF growth.
    if remaining:
        growth_score = (
            profile.loc[remaining, "revenue_cagr_5yr"].rank(
                ascending=False
            )
            + profile.loc[remaining, "fcf_cagr_5yr"].rank(
                ascending=False
            )
        )

        growth = growth_score.idxmax()

        names[growth] = "Emerging Growth"

    remaining = [
        c for c in profile.index
        if c not in names
    ]

    # High-quality compounders:
    # strongest ROE + OPM + growth.
    if remaining:
        quality_score = (
            profile.loc[remaining, "return_on_equity_pct"].rank(
                ascending=False
            )
            + profile.loc[remaining, "operating_profit_margin_pct"].rank(
                ascending=False
            )
            + profile.loc[remaining, "revenue_cagr_5yr"].rank(
                ascending=False
            )
        )

        quality = quality_score.idxmax()

        names[quality] = "High-Quality Compounders"

    remaining = [
        c for c in profile.index
        if c not in names
    ]

    # Last remaining cluster.
    if remaining:
        names[remaining[0]] = "Value Cyclicals"

    return names


# ============================================================
# MAIN CLUSTERING
# ============================================================

def run_clustering():
    """Execute the complete Day 36 clustering workflow."""

    print("=" * 70)
    print("NIFTY 100 - DAY 36 KMEANS CLUSTERING")
    print("=" * 70)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # 1. Load
    # --------------------------------------------------------

    financial, sectors = load_data()

    # --------------------------------------------------------
    # 2. Build features
    # --------------------------------------------------------

    feature_df = build_feature_dataset(
        financial,
        sectors,
    )

    # --------------------------------------------------------
    # 3. Clean invalid values
    # --------------------------------------------------------

    print(
        "\nApplying sector-median imputation..."
    )

    feature_df = clean_clustering_features(
        feature_df
    )

    # --------------------------------------------------------
    # 4. Sector median imputation
    # --------------------------------------------------------

    feature_df = sector_median_imputation(
        feature_df
    )

    print("\nMissing values after imputation:")

    print(
        feature_df[FEATURES].isna().sum()
    )

    remaining_missing = (
        feature_df[FEATURES]
        .isna()
        .sum()
    )

    if remaining_missing.any():
        bad_features = list(
            remaining_missing[
                remaining_missing > 0
            ].index
        )

        raise ValueError(
            f"Missing feature values remain: "
            f"{bad_features}"
        )

    # --------------------------------------------------------
    # 5. Final numerical validation
    # --------------------------------------------------------

    for feature in FEATURES:

        if not np.isfinite(
            feature_df[feature].to_numpy()
        ).all():

            raise ValueError(
                f"Non-finite values remain in "
                f"{feature}"
            )

    # --------------------------------------------------------
    # 6. StandardScaler
    # --------------------------------------------------------

    print(
        "\nApplying StandardScaler..."
    )

    scaler = StandardScaler()

    X = feature_df[FEATURES].copy()

    X_scaled = scaler.fit_transform(X)

    # --------------------------------------------------------
    # 7. Elbow plot
    # --------------------------------------------------------

    generate_elbow_plot(
        X_scaled
    )

    # --------------------------------------------------------
    # 8. KMeans
    # --------------------------------------------------------

    print(
        "\nRunning KMeans with k=5..."
    )

    model = KMeans(
        n_clusters=N_CLUSTERS,
        random_state=RANDOM_STATE,
        n_init=20,
    )

    labels = model.fit_predict(
        X_scaled
    )

    feature_df["cluster_id"] = labels

    # Distance from centroid.
    distances = model.transform(
        X_scaled
    )

    feature_df["distance_from_centroid"] = (
        distances[
            np.arange(len(feature_df)),
            labels,
        ]
    )
    # --------------------------------------------------------
    # 9. Cluster profiles
    # --------------------------------------------------------

    profile = (
        feature_df
        .groupby("cluster_id")[FEATURES]
        .mean()
        .round(2)
    )

    cluster_names = assign_cluster_names(
        profile
    )

    feature_df["cluster_name"] = (
        feature_df["cluster_id"]
        .map(cluster_names)
    )

    # --------------------------------------------------------
    # 10. Display results
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("CLUSTER RESULTS")
    print("=" * 70)

    result_names = pd.DataFrame(
        {
            "cluster_id": list(
                sorted(cluster_names.keys())
            ),
            "cluster_name": [
                cluster_names[c]
                for c in sorted(cluster_names.keys())
            ],
        }
    )

    print(
        result_names.to_string(
            index=False
        )
    )

    print("\nCompanies per cluster:")

    print(
        feature_df["cluster_id"]
        .value_counts()
        .sort_index()
    )

    print("\nCluster profiles:")

    print(profile.to_string())

    # --------------------------------------------------------
    # 11. Save cluster labels
    # --------------------------------------------------------

    output = feature_df[
        [
            "company_id",
            "cluster_id",
            "cluster_name",
            "distance_from_centroid",
        ]
    ].copy()

    output["cluster_id"] = (
        output["cluster_id"]
        .astype(int)
    )

    output["distance_from_centroid"] = (
        output["distance_from_centroid"]
        .round(6)
    )

    output = output.sort_values(
        [
            "cluster_id",
            "company_id",
        ]
    )

    output.to_csv(
        CLUSTER_FILE,
        index=False,
    )

    print(
        f"\nSaved: {CLUSTER_FILE}"
    )

    print(
        f"Saved: {ELBOW_FILE}"
    )

    # --------------------------------------------------------
    # 12. Final validation
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("DAY 36 VALIDATION")
    print("=" * 70)

    checks = {
        "92 companies assigned":
            len(output) == EXPECTED_COMPANIES,

        "5 clusters created":
            output["cluster_id"].nunique()
            == N_CLUSTERS,

        "Every company has a cluster":
            output["cluster_id"].notna().all(),

        "Every company has a cluster name":
            output["cluster_name"].notna().all(),

        "Elbow plot generated":
            ELBOW_FILE.exists(),

        "cluster_labels.csv generated":
            CLUSTER_FILE.exists(),

        "Required output columns":
            list(output.columns)
            == [
                "company_id",
                "cluster_id",
                "cluster_name",
                "distance_from_centroid",
            ],
    }

    failed = False

    for check_name, passed in checks.items():

        if passed:
            print(f"✓ {check_name}")
        else:
            print(f"✗ {check_name}")
            failed = True

    if failed:
        raise ValueError(
            "Day 36 validation failed."
        )

    print(
        "\nDay 36 validation passed."
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    run_clustering()