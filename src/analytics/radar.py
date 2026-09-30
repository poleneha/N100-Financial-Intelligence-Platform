import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import numpy as np
import os

# -------------------------------
# CONNECT DATABASE
# -------------------------------
conn = sqlite3.connect("data/db/nifty100.db")

# Load data
df = pd.read_sql(
    "SELECT * FROM financial_ratios",
    conn
)

peer = pd.read_sql(
    "SELECT * FROM peer_percentiles",
    conn
)

conn.close()

# -------------------------------
# OUTPUT FOLDER
# -------------------------------
output_dir = "reports/radar_charts"
os.makedirs(output_dir, exist_ok=True)

# -------------------------------
# METRICS FOR RADAR
# -------------------------------
metrics = [
    "return_on_equity_pct",
    "operating_profit_margin_pct",
    "net_profit_margin_pct",
    "debt_to_equity",
    "free_cash_flow_cr",
    "pat_cagr_5yr",
    "revenue_cagr_5yr",
    "composite_quality_score"
]

# Keep latest year
df = df[df["year"] == "Mar 2024"].copy()

# -------------------------------
# NORMALIZE FUNCTION
# -------------------------------
def normalize(col):
    minimum = col.min()
    maximum = col.max()

    if maximum == minimum:
        return col * 0

    return (col - minimum) / (maximum - minimum)


for m in metrics:
    if m in df.columns:
        df[m] = normalize(df[m])


# -------------------------------
# CREATE RADAR CHARTS
# -------------------------------
for _, row in df.head(20).iterrows():

    company = row["company_id"]

    values = []

    for m in metrics:
        if m in row:
            values.append(row[m])
        else:
            values.append(0)

    values.append(values[0])

    angles = np.linspace(
        0,
        2 * np.pi,
        len(values)
    )

    fig = plt.figure(figsize=(6,6))

    ax = plt.subplot(
        111,
        polar=True
    )

    ax.plot(
        angles,
        values
    )

    ax.fill(
        angles,
        values,
        alpha=0.25
    )

    ax.set_xticks(
        angles[:-1]
    )

    ax.set_xticklabels(
        [
            "ROE",
            "OPM",
            "NPM",
            "D/E",
            "FCF",
            "PAT CAGR",
            "REV CAGR",
            "QUALITY"
        ],
        fontsize=8
    )

    ax.set_title(
        f"{company} Radar Chart"
    )

    file = os.path.join(
        output_dir,
        f"{company}_radar.png"
    )

    plt.savefig(
        file,
        bbox_inches="tight"
    )

    plt.close()


print("✅ Radar charts generated")
print("Saved in reports/radar_charts/")