"""
NIFTY 100 FINANCIAL INTELLIGENCE PLATFORM
Cluster Visualization & Insights

Inputs:
    output/cluster_labels.csv
    output/cluster_profiles.csv
    output/outlier_report.csv

Outputs:
    reports/cluster_distribution.png
    reports/cluster_financial_comparison.png
    reports/cluster_growth_comparison.png
    reports/cluster_risk_comparison.png
    output/cluster_insights.csv
"""

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# PROJECT PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

OUTPUT_DIR = ROOT / "output"
REPORTS_DIR = ROOT / "reports"

OUTPUT_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    print("=" * 70)
    print("NIFTY 100 - CLUSTER VISUALIZATION & INSIGHTS")
    print("=" * 70)

    labels_path = OUTPUT_DIR / "cluster_labels.csv"
    profiles_path = OUTPUT_DIR / "cluster_profiles.csv"
    outliers_path = OUTPUT_DIR / "outlier_report.csv"

    for path in [labels_path, profiles_path, outliers_path]:
        if not path.exists():
            raise FileNotFoundError(f"Required file not found: {path}")

    labels = pd.read_csv(labels_path)
    profiles = pd.read_csv(profiles_path)
    outliers = pd.read_csv(outliers_path)

    print(f"\nCluster companies : {labels['company_id'].nunique()}")
    print(f"Clusters          : {labels['cluster_id'].nunique()}")
    print(f"Outliers           : {len(outliers)}")

    return labels, profiles, outliers


# ============================================================
# SAVE PLOT
# ============================================================

def save_plot(filename):

    path = REPORTS_DIR / filename

    plt.tight_layout()
    plt.savefig(
        path,
        dpi=150,
        bbox_inches="tight"
    )

    plt.close()

    print(f"Saved: {path}")


# ============================================================
# CLUSTER DISTRIBUTION
# ============================================================

def create_cluster_distribution(labels):

    print("\nCreating cluster distribution...")

    data = (
        labels
        .groupby(["cluster_id", "cluster_name"])
        .size()
        .reset_index(name="company_count")
        .sort_values("cluster_id")
    )

    plt.figure(figsize=(11, 6))

    plt.bar(
        data["cluster_name"],
        data["company_count"]
    )

    plt.title("NIFTY 100 Companies by Cluster")
    plt.xlabel("Cluster")
    plt.ylabel("Number of Companies")

    plt.xticks(
        rotation=25,
        ha="right"
    )

    save_plot(
        "cluster_distribution.png"
    )


# ============================================================
# FINANCIAL COMPARISON
# ============================================================

def create_financial_comparison(profiles):

    print("\nCreating financial comparison...")

    required = [
        "cluster_name",
        "return_on_equity_pct_mean",
        "debt_to_equity_mean"
    ]

    missing = [
        column
        for column in required
        if column not in profiles.columns
    ]

    if missing:
        raise ValueError(
            f"Missing columns: {missing}"
        )

    x = range(len(profiles))

    width = 0.35

    plt.figure(figsize=(12, 6))

    plt.bar(
        [i - width / 2 for i in x],
        profiles["return_on_equity_pct_mean"],
        width=width,
        label="ROE (%)"
    )

    plt.bar(
        [i + width / 2 for i in x],
        profiles["debt_to_equity_mean"],
        width=width,
        label="Debt / Equity"
    )

    plt.xticks(
        list(x),
        profiles["cluster_name"],
        rotation=25,
        ha="right"
    )

    plt.title("Financial Profile by Cluster")
    plt.xlabel("Cluster")
    plt.ylabel("Value")
    plt.legend()

    save_plot(
        "cluster_financial_comparison.png"
    )


# ============================================================
# GROWTH COMPARISON
# ============================================================

def create_growth_comparison(profiles):

    print("\nCreating growth comparison...")

    required = [
        "cluster_name",
        "revenue_cagr_5yr_mean"
    ]

    missing = [
        column
        for column in required
        if column not in profiles.columns
    ]

    if missing:
        raise ValueError(
            f"Missing columns: {missing}"
        )

    plt.figure(figsize=(11, 6))

    plt.bar(
        profiles["cluster_name"],
        profiles["revenue_cagr_5yr_mean"]
    )

    plt.title(
        "Average 5-Year Revenue CAGR by Cluster"
    )

    plt.xlabel("Cluster")
    plt.ylabel("Revenue CAGR (%)")

    plt.xticks(
        rotation=25,
        ha="right"
    )

    save_plot(
        "cluster_growth_comparison.png"
    )


# ============================================================
# RISK COMPARISON
# ============================================================

def create_risk_comparison(profiles):

    print("\nCreating risk comparison...")

    required = [
        "cluster_name",
        "debt_to_equity_mean"
    ]

    missing = [
        column
        for column in required
        if column not in profiles.columns
    ]

    if missing:
        raise ValueError(
            f"Missing columns: {missing}"
        )

    plt.figure(figsize=(11, 6))

    plt.bar(
        profiles["cluster_name"],
        profiles["debt_to_equity_mean"]
    )

    plt.title(
        "Average Debt-to-Equity by Cluster"
    )

    plt.xlabel("Cluster")
    plt.ylabel("Debt-to-Equity")

    plt.xticks(
        rotation=25,
        ha="right"
    )

    save_plot(
        "cluster_risk_comparison.png"
    )


# ============================================================
# CLUSTER INSIGHTS
# ============================================================

def create_cluster_insights(profiles):

    print("\nGenerating cluster insights...")

    median_roe = profiles[
        "return_on_equity_pct_mean"
    ].median()

    median_growth = profiles[
        "revenue_cagr_5yr_mean"
    ].median()

    median_debt = profiles[
        "debt_to_equity_mean"
    ].median()

    results = []

    for _, row in profiles.iterrows():

        roe = row[
            "return_on_equity_pct_mean"
        ]

        growth = row[
            "revenue_cagr_5yr_mean"
        ]

        debt = row[
            "debt_to_equity_mean"
        ]

        opm = row[
            "operating_profit_margin_pct_mean"
        ]

        observations = []

        if roe >= median_roe:
            observations.append(
                "Above-median ROE"
            )
        else:
            observations.append(
                "Below-median ROE"
            )

        if growth >= median_growth:
            observations.append(
                "Above-median revenue growth"
            )
        else:
            observations.append(
                "Below-median revenue growth"
            )

        if debt >= median_debt:
            observations.append(
                "Higher leverage"
            )
        else:
            observations.append(
                "Lower leverage"
            )

        results.append({
            "cluster_id": row["cluster_id"],
            "cluster_name": row["cluster_name"],
            "company_count": row["company_count"],
            "roe_mean": round(roe, 2),
            "debt_to_equity_mean": round(debt, 2),
            "revenue_cagr_5yr_mean": round(growth, 2),
            "operating_profit_margin_mean": round(opm, 2),
            "insight": "; ".join(observations)
        })

    insights = pd.DataFrame(results)

    path = OUTPUT_DIR / "cluster_insights.csv"

    insights.to_csv(
        path,
        index=False
    )

    print(f"Saved: {path}")


# ============================================================
# VALIDATION
# ============================================================

def validate(labels, profiles):

    print("\n" + "=" * 70)
    print("CLUSTER VISUALIZATION VALIDATION")
    print("=" * 70)

    errors = []

    company_count = labels[
        "company_id"
    ].nunique()

    cluster_count = labels[
        "cluster_id"
    ].nunique()

    if company_count == 92:
        print("✓ 92 companies")
    else:
        errors.append(
            f"Expected 92 companies, found {company_count}"
        )

    if cluster_count == 5:
        print("✓ 5 clusters")
    else:
        errors.append(
            f"Expected 5 clusters, found {cluster_count}"
        )

    if labels["cluster_name"].notna().all():
        print("✓ All companies have cluster names")
    else:
        errors.append(
            "Missing cluster names"
        )

    if len(profiles) == 5:
        print("✓ 5 cluster profiles")
    else:
        errors.append(
            "Cluster profile count is not 5"
        )

    required_reports = [
        "cluster_distribution.png",
        "cluster_financial_comparison.png",
        "cluster_growth_comparison.png",
        "cluster_risk_comparison.png"
    ]

    for filename in required_reports:

        if (REPORTS_DIR / filename).exists():
            print(f"✓ {filename}")
        else:
            errors.append(
                f"Missing {filename}"
            )

    if (
        OUTPUT_DIR /
        "cluster_insights.csv"
    ).exists():

        print("✓ cluster_insights.csv")

    else:

        errors.append(
            "Missing cluster_insights.csv"
        )

    if errors:

        print("\nVALIDATION FAILED")

        for error in errors:
            print(f"✗ {error}")

        raise ValueError(
            "Cluster visualization validation failed."
        )

    print("\n" + "=" * 70)
    print("CLUSTER VISUALIZATION VALIDATION PASSED")
    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

def main():

    labels, profiles, outliers = load_data()

    create_cluster_distribution(
        labels
    )

    create_financial_comparison(
        profiles
    )

    create_growth_comparison(
        profiles
    )

    create_risk_comparison(
        profiles
    )

    create_cluster_insights(
        profiles
    )

    validate(
        labels,
        profiles
    )


if __name__ == "__main__":
    main()