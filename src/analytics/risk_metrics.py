"""
NIFTY 100 - RISK METRICS
Historical VaR, CVaR and Rolling Sharpe Ratio

Input:
    data/raw/stock_prices.xlsx

Outputs:
    output/risk_metrics.csv
    output/risk_summary.csv
    reports/risk_distribution.png
    reports/sharpe_ratio.png
"""

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "data" / "raw" / "stock_prices.xlsx"

OUTPUT_DIR = BASE_DIR / "output"
REPORT_DIR = BASE_DIR / "reports"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)


RISK_OUTPUT = OUTPUT_DIR / "risk_metrics.csv"
SUMMARY_OUTPUT = OUTPUT_DIR / "risk_summary.csv"

RISK_CHART = REPORT_DIR / "risk_distribution.png"
SHARPE_CHART = REPORT_DIR / "sharpe_ratio.png"


# ============================================================
# SETTINGS
# ============================================================

VAR_CONFIDENCE = 0.95
ROLLING_WINDOW = 12

# Monthly data -> approximately 12 observations/year
PERIODS_PER_YEAR = 12

# Annual risk-free rate assumption
RISK_FREE_RATE = 0.06

# Monthly risk-free rate
MONTHLY_RISK_FREE = (1 + RISK_FREE_RATE) ** (1 / 12) - 1


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    print("Loading stock-price data...")

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Stock price file not found: {INPUT_FILE}"
        )

    df = pd.read_excel(INPUT_FILE)

    required_columns = [
        "company_id",
        "date",
        "close_price",
        "adjusted_close"
    ]

    missing = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    df["adjusted_close"] = pd.to_numeric(
        df["adjusted_close"],
        errors="coerce"
    )

    df["close_price"] = pd.to_numeric(
        df["close_price"],
        errors="coerce"
    )

    df = df.dropna(
        subset=[
            "company_id",
            "date",
            "adjusted_close"
        ]
    )

    df = df.sort_values(
        ["company_id", "date"]
    )

    print(f"Rows: {len(df)}")
    print(f"Companies: {df['company_id'].nunique()}")
    print(
        f"Date range: "
        f"{df['date'].min().date()} "
        f"to "
        f"{df['date'].max().date()}"
    )

    return df


# ============================================================
# CALCULATE RETURNS
# ============================================================

def calculate_returns(df):

    print("\nCalculating monthly returns...")

    df = df.copy()

    df["return"] = (
        df.groupby("company_id")["adjusted_close"]
        .pct_change()
    )

    df = df.dropna(
        subset=["return"]
    )

    return df


# ============================================================
# HISTORICAL VAR
# ============================================================

def calculate_var(returns):

    """
    Historical VaR at 95%.

    VaR is represented as a positive loss percentage.
    """

    if len(returns) == 0:
        return np.nan

    percentile = (
        1 - VAR_CONFIDENCE
    ) * 100

    value = np.percentile(
        returns,
        percentile
    )

    return max(0, -value)


# ============================================================
# CONDITIONAL VAR / CVAR
# ============================================================

def calculate_cvar(returns):

    """
    Historical CVaR / Expected Shortfall.

    Average loss among observations
    worse than the 95% VaR threshold.
    """

    if len(returns) == 0:
        return np.nan

    percentile = (
        1 - VAR_CONFIDENCE
    ) * 100

    threshold = np.percentile(
        returns,
        percentile
    )

    tail_losses = returns[
        returns <= threshold
    ]

    if len(tail_losses) == 0:
        return np.nan

    return max(
        0,
        -tail_losses.mean()
    )


# ============================================================
# ROLLING SHARPE
# ============================================================

def calculate_rolling_sharpe(returns):

    """
    Rolling 12-month Sharpe ratio.

    The source dataset is monthly, so 12 observations
    represent approximately one year.
    """

    excess_returns = (
        returns - MONTHLY_RISK_FREE
    )

    rolling_mean = (
        excess_returns
        .rolling(ROLLING_WINDOW)
        .mean()
    )

    rolling_std = (
        excess_returns
        .rolling(ROLLING_WINDOW)
        .std()
    )

    sharpe = (
        rolling_mean /
        rolling_std
    ) * np.sqrt(PERIODS_PER_YEAR)

    return sharpe


# ============================================================
# RISK CATEGORY
# ============================================================

def risk_category(var, cvar):

    if pd.isna(var) or pd.isna(cvar):
        return "Insufficient Data"

    combined = (
        0.5 * var +
        0.5 * cvar
    )

    if combined <= 0.05:
        return "Low Risk"

    if combined <= 0.10:
        return "Moderate Risk"

    if combined <= 0.20:
        return "High Risk"

    return "Very High Risk"


# ============================================================
# COMPANY RISK METRICS
# ============================================================

def generate_risk_metrics(df):

    print("\nCalculating company-level risk metrics...")

    records = []

    for company_id, group in df.groupby(
        "company_id"
    ):

        group = group.sort_values("date")

        returns = (
            group["return"]
            .dropna()
            .astype(float)
            .values
        )

        var_95 = calculate_var(
            returns
        )

        cvar_95 = calculate_cvar(
            returns
        )

        rolling_sharpe = calculate_rolling_sharpe(
            pd.Series(returns)
        )

        latest_sharpe = (
            rolling_sharpe.dropna().iloc[-1]
            if not rolling_sharpe.dropna().empty
            else np.nan
        )

        average_sharpe = (
            rolling_sharpe.dropna().mean()
            if not rolling_sharpe.dropna().empty
            else np.nan
        )

        annualized_return = (
            (1 + pd.Series(returns).mean())
            ** PERIODS_PER_YEAR
            - 1
        )

        annualized_volatility = (
            pd.Series(returns).std()
            * np.sqrt(PERIODS_PER_YEAR)
        )

        category = risk_category(
            var_95,
            cvar_95
        )

        records.append({

            "company_id": company_id,

            "observations": len(returns),

            "var_95": var_95,

            "cvar_95": cvar_95,

            "latest_rolling_sharpe":
                latest_sharpe,

            "average_rolling_sharpe":
                average_sharpe,

            "annualized_return":
                annualized_return,

            "annualized_volatility":
                annualized_volatility,

            "risk_category":
                category
        })

    result = pd.DataFrame(records)

    return result


# ============================================================
# SUMMARY
# ============================================================

def generate_summary(risk_df):

    print("\nGenerating risk summary...")

    summary = pd.DataFrame({

        "metric": [

            "Companies",

            "Average VaR 95%",

            "Median VaR 95%",

            "Average CVaR 95%",

            "Median CVaR 95%",

            "Average Sharpe",

            "Median Sharpe",

            "Average Annual Return",

            "Average Annual Volatility"
        ],

        "value": [

            len(risk_df),

            risk_df["var_95"].mean(),

            risk_df["var_95"].median(),

            risk_df["cvar_95"].mean(),

            risk_df["cvar_95"].median(),

            risk_df[
                "latest_rolling_sharpe"
            ].mean(),

            risk_df[
                "latest_rolling_sharpe"
            ].median(),

            risk_df[
                "annualized_return"
            ].mean(),

            risk_df[
                "annualized_volatility"
            ].mean()
        ]
    })

    return summary


# ============================================================
# RISK DISTRIBUTION CHART
# ============================================================

def create_risk_chart(risk_df):

    print("\nCreating risk distribution chart...")

    plt.figure(figsize=(10, 6))

    plt.hist(
        risk_df["var_95"].dropna(),
        bins=15
    )

    plt.xlabel("95% Historical VaR")
    plt.ylabel("Number of Companies")
    plt.title(
        "Nifty 100 - 95% Historical VaR Distribution"
    )

    plt.tight_layout()

    plt.savefig(
        RISK_CHART,
        dpi=150
    )

    plt.close()

    print(
        f"Saved: {RISK_CHART}"
    )


# ============================================================
# SHARPE CHART
# ============================================================

def create_sharpe_chart(risk_df):

    print("\nCreating Sharpe ratio chart...")

    chart_df = (
        risk_df
        .dropna(
            subset=[
                "latest_rolling_sharpe"
            ]
        )
        .sort_values(
            "latest_rolling_sharpe",
            ascending=False
        )
        .head(20)
    )

    plt.figure(figsize=(12, 7))

    plt.bar(
        chart_df["company_id"],
        chart_df[
            "latest_rolling_sharpe"
        ]
    )

    plt.xlabel("Company")
    plt.ylabel(
        "Latest Rolling Sharpe Ratio"
    )

    plt.title(
        "Top 20 Nifty 100 Companies - Rolling Sharpe"
    )

    plt.xticks(
        rotation=60,
        ha="right"
    )

    plt.tight_layout()

    plt.savefig(
        SHARPE_CHART,
        dpi=150
    )

    plt.close()

    print(
        f"Saved: {SHARPE_CHART}"
    )# ============================================================
# VALIDATION
# ============================================================

def validate(risk_df):

    print("\n" + "=" * 70)
    print("RISK METRICS VALIDATION")
    print("=" * 70)

    company_count = risk_df[
        "company_id"
    ].nunique()

    print(
        f"✓ Companies analyzed: {company_count}"
    )

    assert company_count == 92

    assert (
        risk_df["var_95"].notna().sum()
        == 92
    )

    print(
        "✓ 95% VaR calculated for all companies"
    )

    assert (
        risk_df["cvar_95"].notna().sum()
        == 92
    )

    print(
        "✓ 95% CVaR calculated for all companies"
    )

    sharpe_count = risk_df[
        "latest_rolling_sharpe"
    ].notna().sum()

    print(
        f"✓ Rolling Sharpe available: "
        f"{sharpe_count}/92"
    )

    assert (
        risk_df["risk_category"].notna().all()
    )

    print(
        "✓ Every company has a risk category"
    )

    assert RISK_OUTPUT.exists()

    print(
        "✓ risk_metrics.csv generated"
    )

    assert SUMMARY_OUTPUT.exists()

    print(
        "✓ risk_summary.csv generated"
    )

    assert RISK_CHART.exists()

    print(
        "✓ risk_distribution.png generated"
    )

    assert SHARPE_CHART.exists()

    print(
        "✓ sharpe_ratio.png generated"
    )

    print(
        "\nRISK METRICS VALIDATION PASSED"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print(
        "NIFTY 100 - RISK METRICS"
    )
    print(
        "VaR / CVaR / Rolling Sharpe"
    )
    print("=" * 70)

    df = load_data()

    df = calculate_returns(df)

    risk_df = generate_risk_metrics(
        df
    )

    summary_df = generate_summary(
        risk_df
    )

    risk_df.to_csv(
        RISK_OUTPUT,
        index=False
    )

    summary_df.to_csv(
        SUMMARY_OUTPUT,
        index=False
    )

    print(
        f"\nSaved: {RISK_OUTPUT}"
    )

    print(
        f"Saved: {SUMMARY_OUTPUT}"
    )

    create_risk_chart(
        risk_df
    )

    create_sharpe_chart(
        risk_df
    )

    print("\nTop risk metrics:")

    display_columns = [
        "company_id",
        "var_95",
        "cvar_95",
        "latest_rolling_sharpe",
        "annualized_return",
        "annualized_volatility",
        "risk_category"
    ]

    print(
        risk_df[
            display_columns
        ]
        .sort_values(
            "var_95"
        )
        .head(10)
        .to_string(index=False)
    )

    print("\nRisk category distribution:")

    print(
        risk_df[
            "risk_category"
        ]
        .value_counts()
        .to_string()
    )

    validate(
        risk_df
    )


if __name__ == "__main__":
    main()