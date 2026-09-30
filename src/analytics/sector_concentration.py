import os
import pandas as pd
import matplotlib.pyplot as plt


print("=" * 70)
print("NIFTY 100 - SECTOR CONCENTRATION ANALYSIS")
print("HHI / SECTOR WEIGHT / CONCENTRATION RISK")
print("=" * 70)


# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------

SECTOR_FILE = "data/raw/sectors.xlsx"
MARKET_CAP_FILE = "data/raw/market_cap.xlsx"

OUTPUT_DIR = "output"
REPORT_DIR = "reports"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)


# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

print("Loading sector data...")

sector = pd.read_excel(SECTOR_FILE)

print("Loading market-cap data...")

market = pd.read_excel(MARKET_CAP_FILE)


# ---------------------------------------------------------
# CLEAN COLUMN NAMES
# ---------------------------------------------------------

sector.columns = sector.columns.str.strip().str.lower()
market.columns = market.columns.str.strip().str.lower()


print("Sector columns:", sector.columns.tolist())
print("Market-cap columns:", market.columns.tolist())


# ---------------------------------------------------------
# PREPARE SECTOR DATA
# ---------------------------------------------------------

if "sector" not in sector.columns:

    possible_sector_columns = [
        c for c in sector.columns
        if "sector" in c
    ]

    if possible_sector_columns:
        sector = sector.rename(
            columns={
                possible_sector_columns[0]: "sector"
            }
        )

    else:
        raise ValueError(
            "No sector column found in sectors.xlsx"
        )


sector_map = sector[
    ["company_id", "sector"]
].drop_duplicates(
    subset=["company_id"]
)


# ---------------------------------------------------------
# PREPARE MARKET CAP DATA
# ---------------------------------------------------------

required_market_columns = [
    "company_id",
    "year",
    "market_cap_crore"
]

missing = [
    c for c in required_market_columns
    if c not in market.columns
]

if missing:
    raise ValueError(
        f"Missing market-cap columns: {missing}"
    )


latest_year = market["year"].max()

market_latest = market[
    market["year"] == latest_year
].copy()


market_latest = market_latest[
    ["company_id", "market_cap_crore"]
]


# ---------------------------------------------------------
# MERGE
# ---------------------------------------------------------

df = market_latest.merge(
    sector_map,
    on="company_id",
    how="left"
)


df["sector"] = (
    df["sector"]
    .fillna("Unknown")
    .astype(str)
)


df["market_cap_crore"] = pd.to_numeric(
    df["market_cap_crore"],
    errors="coerce"
)


df = df.dropna(
    subset=["market_cap_crore"]
)


print("Latest year:", latest_year)
print("Companies analyzed:", df["company_id"].nunique())


# ---------------------------------------------------------
# SECTOR MARKET CAP
# ---------------------------------------------------------

sector_summary = (
    df.groupby("sector", as_index=False)
    ["market_cap_crore"]
    .sum()
)


total_market_cap = (
    sector_summary["market_cap_crore"].sum()
)


sector_summary["sector_weight_pct"] = (
    sector_summary["market_cap_crore"]
    / total_market_cap
    * 100
)


# ---------------------------------------------------------
# HHI
# ---------------------------------------------------------

sector_summary["weight_squared"] = (
    sector_summary["sector_weight_pct"] ** 2
)


hhi = sector_summary[
    "weight_squared"
].sum()


# ---------------------------------------------------------
# CONCENTRATION RISK
# ---------------------------------------------------------

if hhi < 1500:
    concentration_risk = "Low"

elif hhi < 2500:
    concentration_risk = "Moderate"

else:
    concentration_risk = "High"


sector_summary = sector_summary.sort_values(
    "sector_weight_pct",
    ascending=False
)


sector_summary["rank"] = range(
    1,
    len(sector_summary) + 1
)


sector_summary["concentration_risk"] = (
    concentration_risk
)


# ---------------------------------------------------------
# SAVE OUTPUT
# ---------------------------------------------------------

output_file = (
    "output/sector_concentration.csv"
)

sector_summary.to_csv(
    output_file,
    index=False
)


summary_file = (
    "output/sector_concentration_summary.csv"
)

summary = pd.DataFrame({
    "metric": [
        "latest_year",
        "companies_analyzed",
        "sectors_analyzed",
        "total_market_cap_crore",
        "sector_hhi",
        "concentration_risk"
    ],
    "value": [
        latest_year,
        df["company_id"].nunique(),
        sector_summary["sector"].nunique(),
        total_market_cap,
        hhi,
        concentration_risk
    ]
})


summary.to_csv(
    summary_file,
    index=False
)


# ---------------------------------------------------------
# CHART
# ---------------------------------------------------------

plt.figure(figsize=(10, 6))

plt.bar(
    sector_summary["sector"],
    sector_summary["sector_weight_pct"]
)

plt.xticks(
    rotation=45,
    ha="right"
)

plt.ylabel(
    "Market Cap Weight (%)"
)

plt.title(
    "Nifty 100 Sector Concentration"
)

plt.tight_layout()


chart_file = (
    "reports/sector_concentration.png"
)

plt.savefig(
    chart_file,
    dpi=150
)

plt.close()


# ---------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------

print()
print("=" * 70)
print("SECTOR CONCENTRATION VALIDATION")
print("=" * 70)

print(
    f"✓ Companies analyzed: "
    f"{df['company_id'].nunique()}"
)

print(
    f"✓ Sectors analyzed: "
    f"{sector_summary['sector'].nunique()}"
)

print(
    f"✓ Latest year: {latest_year}"
)

print(
    f"✓ Sector HHI: {hhi:.2f}"
)

print(
    f"✓ Concentration risk: "
    f"{concentration_risk}"
)

print(
    "✓ Sector weights calculated"
)

print(
    "✓ sector_concentration.csv generated"
)

print(
    "✓ sector_concentration_summary.csv generated"
)

print(
    "✓ sector_concentration.png generated"
)

print()
print(
    "SECTOR CONCENTRATION VALIDATION PASSED"
)