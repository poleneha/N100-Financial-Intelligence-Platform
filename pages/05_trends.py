import streamlit as st
import pandas as pd
import requests
import plotly.express as px


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Trend Analysis",
    page_icon="📈",
    layout="wide"
)


# ============================================================
# API CONFIG
# ============================================================

API_BASE = "http://127.0.0.1:8000/api/v1"


# ============================================================
# API FUNCTIONS
# ============================================================

@st.cache_data(ttl=300)
def get_companies():

    try:

        response = requests.get(
            f"{API_BASE}/companies",
            timeout=10
        )

        response.raise_for_status()

        return response.json().get(
            "data",
            []
        )

    except requests.exceptions.RequestException as e:

        st.error(
            f"Unable to connect to FastAPI: {e}"
        )

        return []


@st.cache_data(ttl=300)
def get_profit_loss(ticker):

    try:

        response = requests.get(
            f"{API_BASE}/companies/{ticker}/pl",
            timeout=10
        )

        response.raise_for_status()

        return response.json().get(
            "history",
            []
        )

    except requests.exceptions.RequestException as e:

        st.error(
            f"Unable to load P&L data: {e}"
        )

        return []


@st.cache_data(ttl=300)
def get_ratios(ticker):

    try:

        response = requests.get(
            f"{API_BASE}/companies/{ticker}/ratios",
            timeout=10
        )

        response.raise_for_status()

        return response.json().get(
            "history",
            []
        )

    except requests.exceptions.RequestException as e:

        st.error(
            f"Unable to load ratio data: {e}"
        )

        return []


# ============================================================
# LOAD COMPANIES
# ============================================================

companies = get_companies()

if not companies:

    st.warning(
        "No company data available."
    )

    st.stop()


# ============================================================
# COMPANY LIST
# ============================================================

company_options = {}

for company in companies:

    ticker = company.get(
        "id"
    )

    if ticker:

        company_options[ticker] = company.get(
            "company_name",
            ticker
        )


# ============================================================
# TITLE
# ============================================================

st.title(
    "📈 Trend Analysis"
)

st.caption(
    "Analyze historical revenue, profit and financial performance."
)


# ============================================================
# COMPANY SELECTION
# ============================================================

selected_company = st.selectbox(

    "Select Company",

    options=list(
        company_options.keys()
    ),

    format_func=lambda x:
        f"{x} — {company_options[x]}"
)


# ============================================================
# METRIC SELECTION
# ============================================================

metric = st.multiselect(

    "Select Metrics",

    [
        "Revenue",
        "Operating Profit",
        "Net Profit",
        "EPS",
        "ROE",
        "Operating Margin"
    ],

    default=[
        "Revenue",
        "Net Profit"
    ]
)


if not metric:

    st.info(
        "Select at least one metric."
    )

    st.stop()


# ============================================================
# LOAD DATA
# ============================================================

pl_history = get_profit_loss(
    selected_company
)

ratio_history = get_ratios(
    selected_company
)


if not pl_history:

    st.warning(
        f"No P&L history found for {selected_company}."
    )

    st.stop()


# ============================================================
# P&L DATAFRAME
# ============================================================

pl_df = pd.DataFrame(
    pl_history
)


# Remove TTM for yearly trend

pl_yearly = pl_df[
    pl_df["year"].astype(str).str.upper() != "TTM"
].copy()


# Extract year number

pl_yearly["Year"] = (
    pl_yearly["year"]
    .astype(str)
    .str.extract(r"(\d{4})")[0]
)


pl_yearly["Year"] = pd.to_numeric(
    pl_yearly["Year"],
    errors="coerce"
)


# ============================================================
# RATIO DATAFRAME
# ============================================================

ratio_df = pd.DataFrame(
    ratio_history
)


if not ratio_df.empty:

    ratio_df["Year"] = (
        ratio_df["year"]
        .astype(str)
        .str.extract(r"(\d{4})")[0]
    )

    ratio_df["Year"] = pd.to_numeric(
        ratio_df["Year"],
        errors="coerce"
    )


# ============================================================
# MERGE DATA
# ============================================================

trend_df = pl_yearly[
    [
        "Year",
        "sales",
        "operating_profit",
        "net_profit",
        "eps",
        "opm_percentage"
    ]
].copy()


trend_df = trend_df.rename(

    columns={

        "sales":
            "Revenue",

        "operating_profit":
            "Operating Profit",

        "net_profit":
            "Net Profit",

        "eps":
            "EPS",

        "opm_percentage":
            "Operating Margin"
    }
)


# Add ROE

if not ratio_df.empty:

    roe_data = ratio_df[
        [
            "Year",
            "return_on_equity_pct"
        ]
    ].copy()

    roe_data = roe_data.rename(

        columns={
            "return_on_equity_pct":
                "ROE"
        }
    )

    trend_df = trend_df.merge(
        roe_data,
        on="Year",
        how="left"
    )

else:

    trend_df["ROE"] = None


# ============================================================
# SORT DATA
# ============================================================

trend_df = trend_df.sort_values(
    "Year"
)


# ============================================================
# DISPLAY COMPANY
# ============================================================

st.success(
    f"Showing trends for **{selected_company} — "
    f"{company_options[selected_company]}**"
)


# ============================================================
# KPI CARDS
# ============================================================

latest = trend_df.iloc[-1]

first = trend_df.iloc[0]


col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "Latest Revenue",
        f"₹{latest['Revenue']:,.0f} Cr"
    )


with col2:

    st.metric(
        "Latest Net Profit",
        f"₹{latest['Net Profit']:,.0f} Cr"
    )


with col3:

    st.metric(
        "Latest EPS",
        f"₹{latest['EPS']:,.2f}"
    )


with col4:

    if pd.notna(latest["ROE"]):

        st.metric(
            "Latest ROE",
            f"{latest['ROE']:.2f}%"
        )

    else:

        st.metric(
            "Latest ROE",
            "N/A"
        )


# ============================================================
# TREND CHART
# ============================================================

st.divider()

st.subheader(
    "📊 Historical Performance"
)


# Convert selected metrics into long format

chart_df = trend_df[
    ["Year"] + metric
].copy()


chart_long = chart_df.melt(

    id_vars="Year",

    var_name="Metric",

    value_name="Value"
)


fig = px.line(

    chart_long,

    x="Year",

    y="Value",

    color="Metric",

    markers=True,

    title=f"{selected_company} — Historical Trend"
)


fig.update_layout(

    xaxis_title="Year",

    yaxis_title="Value",

    hovermode="x unified"
)


st.plotly_chart(

    fig,

    use_container_width=True
)


# ============================================================
# REVENUE TREND
# ============================================================

if "Revenue" in metric:

    st.subheader(
        "💰 Revenue Trend"
    )

    revenue_df = trend_df[
        ["Year", "Revenue"]
    ].dropna()


    fig_revenue = px.area(

        revenue_df,

        x="Year",

        y="Revenue",

        markers=True,

        title="Revenue Growth"
    )


    fig_revenue.update_layout(

        xaxis_title="Year",

        yaxis_title="Revenue (₹ Cr)"
    )


    st.plotly_chart(

        fig_revenue,

        use_container_width=True
    )


# ============================================================
# PROFIT TREND
# ============================================================

if "Net Profit" in metric:

    st.subheader(
        "📈 Net Profit Trend"
    )

    profit_df = trend_df[
        ["Year", "Net Profit"]
    ].dropna()


    fig_profit = px.line(

        profit_df,

        x="Year",

        y="Net Profit",

        markers=True,

        title="Net Profit Growth"
    )


    fig_profit.update_layout(

        xaxis_title="Year",

        yaxis_title="Net Profit (₹ Cr)"
    )


    st.plotly_chart(

        fig_profit,

        use_container_width=True
    )


# ============================================================
# ROE TREND
# ============================================================

if "ROE" in metric:

    st.subheader(
        "📊 ROE Trend"
    )

    roe_df = trend_df[
        ["Year", "ROE"]
    ].dropna()


    if not roe_df.empty:

        fig_roe = px.line(

            roe_df,

            x="Year",

            y="ROE",

            markers=True,

            title="Return on Equity Trend"
        )


        fig_roe.update_layout(

            xaxis_title="Year",

            yaxis_title="ROE (%)"
        )


        st.plotly_chart(

            fig_roe,

            use_container_width=True
        )

    else:

        st.info(
            "ROE history is not available."
        )


# ============================================================
# DATA TABLE
# ============================================================

st.divider()

st.subheader(
    "📋 Historical Data"
)


display_df = trend_df.copy()


numeric_columns = display_df.select_dtypes(
    include="number"
).columns


display_df[numeric_columns] = (
    display_df[numeric_columns]
    .round(2)
)


st.dataframe(

    display_df,

    use_container_width=True,

    hide_index=True
)


# ============================================================
# DOWNLOAD
# ============================================================

csv = trend_df.to_csv(
    index=False
)


st.download_button(

    label="📥 Download Trend Data",

    data=csv,

    file_name=f"{selected_company}_trend_analysis.csv",

    mime="text/csv"
)