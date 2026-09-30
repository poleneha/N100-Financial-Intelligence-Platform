import pandas as pd
import streamlit as st
import os

# -------------------------------
# PAGE CONFIG
# -------------------------------
st.set_page_config(page_title="Stock Ranking Dashboard", layout="wide")

st.title("📊 Nifty 100 Smart Ranking Dashboard")

# -------------------------------
# LOAD DATA (SAFE PATH)
# -------------------------------
file_path = "output/top_ranked_stocks.csv"

if not os.path.exists(file_path):
    st.error("❌ File not found: output/top_ranked_stocks.csv")
    st.stop()

df = pd.read_csv(file_path, dtype=str)

# -------------------------------
# CLEAN FUNCTION
# -------------------------------
def clean_number(x):
    if pd.isna(x):
        return None
    
    x = str(x).strip()
    x = x.replace(",", ".")
    x = x.replace(" ", "")

    # Fix special case
    if x == "05":
        return 0.5

    try:
        return float(x)
    except:
        return None

# -------------------------------
# CLEAN NUMERIC COLUMNS
# -------------------------------
numeric_cols = ["quality_score", "growth_score", "value_score", "final_score"]

for col in numeric_cols:
    if col in df.columns:
        df[col] = df[col].apply(clean_number)

df["rank"] = pd.to_numeric(df.get("rank"), errors="coerce")

# Remove bad rows
df = df.dropna(subset=numeric_cols + ["rank"])

# Round values
df[numeric_cols] = df[numeric_cols].round(3)

# Sort
df = df.sort_values("rank").reset_index(drop=True)

# -------------------------------
# COMPANY NAME MAPPING
# -------------------------------
name_map = {
    "INDIGO": "IndiGo Airlines",
    "BAJAJHLDNG": "Bajaj Holdings",
    "CANBK": "Canara Bank",
    "ICICIBANK": "ICICI Bank",
    "AXISBANK": "Axis Bank",
    "IRCTC": "IRCTC",
    "TRENT": "Trent Ltd",
    "LICI": "LIC India",
    "BAJFINANCE": "Bajaj Finance",
    "BANKBARODA": "Bank of Baroda"
}

if "company_id" in df.columns:
    df["company_name"] = df["company_id"].map(name_map)
    df["company_name"] = df["company_name"].fillna(df["company_id"])
else:
    df["company_name"] = "Unknown"

# -------------------------------
# FINAL COLUMNS
# -------------------------------
df = df[
    [
        "rank",
        "company_name",
        "quality_score",
        "growth_score",
        "value_score",
        "final_score",
    ]
]

# -------------------------------
# KPI CARDS
# -------------------------------
col1, col2, col3 = st.columns(3)

col1.metric("Total Stocks", len(df))
col2.metric("Top Score", f"{df['final_score'].max():.3f}")
col3.metric("Average Score", f"{df['final_score'].mean():.3f}")

# -------------------------------
# TOP 10 TABLE
# -------------------------------
st.subheader("🏆 Top 10 Stocks")
st.dataframe(df.head(10), use_container_width=True)

# -------------------------------
# BAR CHART
# -------------------------------
st.subheader("📈 Top 10 Scores")
st.bar_chart(df.head(10).set_index("company_name")["final_score"])

# -------------------------------
# FILTER
# -------------------------------
st.subheader("🔍 Filter by Score")

min_score = st.slider("Minimum Score", 0.0, 1.0, 0.3)

filtered = df[df["final_score"] >= min_score]

st.write(f"Showing {len(filtered)} stocks")
st.dataframe(filtered, use_container_width=True)

# -------------------------------
# DOWNLOAD BUTTON
# -------------------------------
st.download_button(
    "📥 Download Filtered Data",
    data=filtered.to_csv(index=False),
    file_name="filtered_stocks.csv",
    mime="text/csv"
)