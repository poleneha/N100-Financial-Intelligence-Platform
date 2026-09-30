import sqlite3
import pandas as pd
from src.analytics.cagr import calculate_cagr

DB = "data/db/nifty100.db"
conn = sqlite3.connect(DB)

# LOAD DATA
pnl = pd.read_excel("data/raw/profitandloss.xlsx", header=1)
bs = pd.read_excel("data/raw/balancesheet.xlsx", header=1)
cf = pd.read_excel("data/raw/cashflow.xlsx", header=1)

# CLEAN COLUMNS
for data in [pnl, bs, cf]:
    data.columns = (
        data.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

# MERGE
df = pnl.merge(bs, on=["company_id", "year"]).merge(cf, on=["company_id", "year"])

# CREATE RATIO TABLE
ratio = pd.DataFrame()
ratio["company_id"] = df["company_id"]
ratio["year"] = df["year"]

# BASIC RATIOS
equity = df["equity_capital"].fillna(0) + df["reserves"].fillna(0)

ratio["net_profit_margin_pct"] = df["net_profit"] / df["sales"] * 100
ratio["operating_profit_margin_pct"] = df["operating_profit"] / df["sales"] * 100
ratio["return_on_equity_pct"] = df["net_profit"] / equity * 100
ratio["debt_to_equity"] = df["borrowings"] / equity
ratio["interest_coverage"] = (df["operating_profit"] + df["other_income"]) / df["interest"]
ratio["asset_turnover"] = df["sales"] / df["total_assets"]

ratio["free_cash_flow_cr"] = df["operating_activity"] + df["investing_activity"]
ratio["capex_cr"] = df["investing_activity"].abs()
ratio["cash_from_operations_cr"] = df["operating_activity"]

ratio["earnings_per_share"] = df["eps"]
ratio["book_value_per_share"] = equity
ratio["total_debt_cr"] = df["borrowings"]

# CAGR (FIXED)
ratio["revenue_cagr_5yr"] = 0.0
ratio["pat_cagr_5yr"] = 0.0
ratio["eps_cagr_5yr"] = 0.0

for company, group in df.groupby("company_id"):

    group = group.sort_values("year")
    idxs = group.index.tolist()

    for i in range(5, len(group)):

        start = group.iloc[i - 5]
        end = group.iloc[i]

        rev = calculate_cagr(start["sales"], end["sales"], 5)
        pat = calculate_cagr(start["net_profit"], end["net_profit"], 5)
        eps = calculate_cagr(start["eps"], end["eps"], 5)

        if isinstance(rev, tuple): rev = rev[0]
        if isinstance(pat, tuple): pat = pat[0]
        if isinstance(eps, tuple): eps = eps[0]

        ratio.loc[idxs[i], "revenue_cagr_5yr"] = rev or 0
        ratio.loc[idxs[i], "pat_cagr_5yr"] = pat or 0
        ratio.loc[idxs[i], "eps_cagr_5yr"] = eps or 0

# SCORE
ratio["composite_quality_score"] = ratio[
    [
        "return_on_equity_pct",
        "net_profit_margin_pct",
        "operating_profit_margin_pct",
        "revenue_cagr_5yr"
    ]
].fillna(0).mean(axis=1)

# SAVE
ratio.to_sql("financial_ratios", conn, if_exists="replace", index=False)
conn.close()

print("DONE:", len(ratio))