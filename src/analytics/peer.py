import pandas as pd
import sqlite3

# -------------------------------
# CONNECT DATABASE
# -------------------------------
conn = sqlite3.connect("data/db/nifty100.db")

# -------------------------------
# LOAD TABLES
# -------------------------------
ratios = pd.read_sql(
    "SELECT * FROM financial_ratios",
    conn
)

peer_groups = pd.read_sql(
    "SELECT * FROM peer_groups",
    conn
)

# -------------------------------
# FIX PEER GROUP COLUMNS
# -------------------------------
peer_groups.columns = [
    "peer_group_id",
    "peer_group_name",
    "company_id",
    "is_benchmark"
]

# Clean values
peer_groups["company_id"] = (
    peer_groups["company_id"]
    .astype(str)
    .str.upper()
    .str.strip()
)

ratios["company_id"] = (
    ratios["company_id"]
    .astype(str)
    .str.upper()
    .str.strip()
)

# -------------------------------
# MERGE
# -------------------------------
df = ratios.merge(
    peer_groups[
        ["peer_group_name", "company_id"]
    ],
    on="company_id",
    how="left"
)

df["peer_group_name"] = df["peer_group_name"].fillna(
    "No peer group assigned"
)

# -------------------------------
# METRICS
# -------------------------------
metrics = [
    "return_on_equity_pct",
    "operating_profit_margin_pct",
    "net_profit_margin_pct",
    "debt_to_equity",
    "free_cash_flow_cr",
    "pat_cagr_5yr",
    "revenue_cagr_5yr",
    "eps_cagr_5yr",
    "interest_coverage",
    "asset_turnover"
]

output = []

# -------------------------------
# PERCENTILE CALCULATION
# -------------------------------
for metric in metrics:

    if metric not in df.columns:
        continue

    temp = df[
        [
            "company_id",
            "peer_group_name",
            "year",
            metric
        ]
    ].copy()

    temp = temp.dropna()

    temp["percentile_rank"] = (
        temp.groupby("peer_group_name")[metric]
        .rank(pct=True)
    )

    # Lower debt is better
    if metric == "debt_to_equity":
        temp["percentile_rank"] = (
            1 - temp["percentile_rank"]
        )

    temp.rename(
        columns={metric: "value"},
        inplace=True
    )

    temp["metric"] = metric

    output.append(temp)


# -------------------------------
# SAVE TABLE
# -------------------------------
final = pd.concat(output)

final = final[
    [
        "company_id",
        "peer_group_name",
        "metric",
        "value",
        "percentile_rank",
        "year"
    ]
]


final.to_sql(
    "peer_percentiles",
    conn,
    if_exists="replace",
    index=False
)

conn.close()

print("✅ Peer percentile calculation completed")
print("Rows inserted:", len(final))