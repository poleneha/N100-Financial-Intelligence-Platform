import pandas as pd
import sqlite3

# -------------------------------
# CONNECT DATABASE
# -------------------------------
conn = sqlite3.connect("data/db/nifty100.db")

# -------------------------------
# LOAD DATA
# -------------------------------
df = pd.read_sql("SELECT * FROM financial_ratios", conn)

# -------------------------------
# DATA CLEANING
# -------------------------------
df = df.dropna()

# Fix spacing issues in year
df["year"] = df["year"].astype(str).str.strip()

# Cap unrealistic values
df["return_on_equity_pct"] = df["return_on_equity_pct"].clip(upper=100)
df["net_profit_margin_pct"] = df["net_profit_margin_pct"].clip(upper=100)
df["revenue_cagr_5yr"] = df["revenue_cagr_5yr"].clip(upper=100)
df["pat_cagr_5yr"] = df["pat_cagr_5yr"].clip(upper=100)

# PE ratio cleaning
if "price_to_earnings_ratio" in df.columns:
    df["price_to_earnings_ratio"] = df["price_to_earnings_ratio"].clip(upper=100)

# -------------------------------
# SAFE NORMALIZATION FUNCTION
# -------------------------------
def normalize(series):
    if series.max() == series.min():
        return pd.Series(0, index=series.index)
    return (series - series.min()) / (series.max() - series.min())

# -------------------------------
# NORMALIZED METRICS
# -------------------------------
df["roe_score"] = normalize(df["return_on_equity_pct"])
df["margin_score"] = normalize(df["net_profit_margin_pct"])
df["rev_growth_score"] = normalize(df["revenue_cagr_5yr"])
df["pat_growth_score"] = normalize(df["pat_cagr_5yr"])

# PE score (LOW PE = BETTER)
if "price_to_earnings_ratio" in df.columns:
    df["pe_score"] = 1 - normalize(df["price_to_earnings_ratio"])
else:
    df["pe_score"] = 0.5  # fallback if column missing

# -------------------------------
# SCORING MODEL
# -------------------------------
# Quality
df["quality_score"] = (
    df["roe_score"] * 0.6 +
    df["margin_score"] * 0.4
)

# Growth
df["growth_score"] = (
    df["rev_growth_score"] * 0.5 +
    df["pat_growth_score"] * 0.5
)

# Value (REAL now)
df["value_score"] = df["pe_score"]

# Final Score
df["final_score"] = (
    df["quality_score"] * 0.4 +
    df["growth_score"] * 0.4 +
    df["value_score"] * 0.2
)

# -------------------------------
# FILTER LATEST YEAR
# -------------------------------
df_latest = df[df["year"] == "Mar 2024"].copy()

# Sort
df_latest = df_latest.sort_values(by="final_score", ascending=False)

# Rank
df_latest["rank"] = range(1, len(df_latest) + 1)

# -------------------------------
# OUTPUT (TOP 10)
# -------------------------------
print("\n🏆 TOP 10 STOCKS\n")

output = df_latest[["rank", "company_id", "final_score"]].head(10).copy()

# Format score
output["final_score"] = output["final_score"].round(3)

# Reset index
output = output.reset_index(drop=True)

# Print clean table
for _, row in output.iterrows():
    print(f"{int(row['rank']):>2} | {row['company_id']:<12} | {row['final_score']:.3f}")

# -------------------------------
# SAVE TO CSV
# -------------------------------
df_latest.to_csv("output/top_ranked_stocks.csv", index=False)

print("\n✅ Saved: output/top_ranked_stocks.csv")