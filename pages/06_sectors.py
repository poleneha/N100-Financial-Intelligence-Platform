import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
import plotly.express as px


st.title("🏭 Sector Analysis")
st.caption("Nifty 100 sector-wise financial analysis")


# ============================================================
# FIND DATABASE AUTOMATICALLY
# ============================================================

CURRENT_DIR = Path(__file__).resolve().parent

possible_paths = [
    CURRENT_DIR.parent / "data" / "db" / "nifty100.db",
    Path.cwd() / "data" / "db" / "nifty100.db",
    Path("data/db/nifty100.db"),
]

DB_PATH = None

for path in possible_paths:
    if path.exists():
        DB_PATH = path.resolve()
        break


# ============================================================
# DATABASE NOT FOUND
# ============================================================

if DB_PATH is None:

    st.error("Database not found.")

    st.write("Python searched these locations:")

    for path in possible_paths:
        st.code(str(path.resolve()))

    st.stop()


# ============================================================
# DATABASE CONNECTION
# ============================================================

try:

    conn = sqlite3.connect(str(DB_PATH))

except Exception as e:

    st.error(f"Could not open database: {e}")
    st.stop()


# ============================================================
# CHECK SECTORS TABLE
# ============================================================

try:

    tables = pd.read_sql_query(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        """,
        conn
    )

    table_names = tables["name"].tolist()

    if "sectors" not in table_names:

        conn.close()

        st.error(
            "The 'sectors' table does not exist in nifty100.db."
        )

        st.write("Available tables:")

        st.write(table_names)

        st.stop()


# ============================================================
# LOAD SECTOR DATA
# ============================================================

    data = pd.read_sql_query(
        """
        SELECT
            abb,
            industrials,
            capital_goods,
            "0.81",
            large_cap
        FROM sectors
        """,
        conn
    )

    conn.close()


except Exception as e:

    conn.close()

    st.error(
        f"Could not load sector data: {e}"
    )

    st.stop()


# ============================================================
# RENAME COLUMNS
# ============================================================

data.rename(
    columns={
        "abb": "Company",
        "industrials": "Sector",
        "capital_goods": "Industry",
        "0.81": "Weight",
        "large_cap": "Market Cap"
    },
    inplace=True
)


# ============================================================
# CLEAN DATA
# ============================================================

data["Company"] = data["Company"].astype(str)

data["Sector"] = data["Sector"].astype(str)

data["Industry"] = data["Industry"].astype(str)

data["Market Cap"] = data["Market Cap"].astype(str)

data["Weight"] = pd.to_numeric(
    data["Weight"],
    errors="coerce"
)


data = data[
    (data["Company"] != "")
    & (data["Company"] != "nan")
].copy()


# ============================================================
# SUCCESS MESSAGE
# ============================================================

st.success(
    f"Loaded {len(data)} companies from database."
)


# ============================================================
# OVERVIEW
# ============================================================

st.subheader("📊 Sector Overview")

col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        "Total Companies",
        data["Company"].nunique()
    )

with col2:

    st.metric(
        "Total Sectors",
        data["Sector"].nunique()
    )

with col3:

    st.metric(
        "Total Industries",
        data["Industry"].nunique()
    )


st.divider()


# ============================================================
# SELECT SECTOR
# ============================================================

sector_list = sorted(
    data["Sector"].dropna().unique().tolist()
)


selected_sector = st.selectbox(
    "Select Sector",
    sector_list
)


sector_data = data[
    data["Sector"] == selected_sector
].copy()


# ============================================================
# SELECTED SECTOR KPIs
# ============================================================

st.subheader(
    f"📌 {selected_sector}"
)

col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        "Companies",
        sector_data["Company"].nunique()
    )

with col2:

    st.metric(
        "Industries",
        sector_data["Industry"].nunique()
    )

with col3:

    st.metric(
        "Total Weight",
        f"{sector_data['Weight'].sum():.2f}"
    )


# ============================================================
# COMPANY TABLE
# ============================================================

st.subheader("🏢 Companies")

company_table = sector_data[
    [
        "Company",
        "Industry",
        "Weight",
        "Market Cap"
    ]
].sort_values(
    "Weight",
    ascending=False
)


st.dataframe(
    company_table,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# INDUSTRY CHART
# ============================================================

st.subheader("📊 Industry Distribution")

industry_data = (
    sector_data
    .groupby("Industry")
    .size()
    .reset_index(name="Companies")
)


fig1 = px.bar(
    industry_data,
    x="Industry",
    y="Companies",
    text="Companies",
    title=f"Companies by Industry — {selected_sector}"
)


st.plotly_chart(
    fig1,
    use_container_width=True
)


# ============================================================
# COMPANY WEIGHT CHART
# ============================================================

st.subheader("📈 Company Weight")

weight_data = sector_data[
    ["Company", "Weight"]
].sort_values(
    "Weight",
    ascending=False
)


fig2 = px.bar(
    weight_data,
    x="Company",
    y="Weight",
    text="Weight",
    title=f"Company Weight — {selected_sector}"
)


st.plotly_chart(
    fig2,
    use_container_width=True
)


# ============================================================
# MARKET CAP
# ============================================================

st.subheader("💰 Market Cap Distribution")

market_cap_data = (
    sector_data
    .groupby("Market Cap")
    .size()
    .reset_index(name="Companies")
)


fig3 = px.pie(
    market_cap_data,
    names="Market Cap",
    values="Companies",
    title=f"Market Cap Distribution — {selected_sector}"
)


st.plotly_chart(
    fig3,
    use_container_width=True
)


# ============================================================
# ALL SECTORS SUMMARY
# ============================================================

st.subheader("📋 All Sector Summary")

summary = (
    data
    .groupby("Sector")
    .agg(
        Companies=("Company", "nunique"),
        Total_Weight=("Weight", "sum")
    )
    .reset_index()
    .sort_values(
        "Companies",
        ascending=False
    )
)


st.dataframe(
    summary,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# DOWNLOAD
# ============================================================

csv = sector_data.to_csv(
    index=False
).encode("utf-8")


st.download_button(
    "📥 Download Sector Data",
    csv,
    "sector_analysis.csv",
    "text/csv"
)


st.divider()

st.caption(
    "Nifty 100 Financial Intelligence Platform | Sector Analysis"
)