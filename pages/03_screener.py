import streamlit as st
import pandas as pd
import requests


# ============================================================
# CONFIGURATION
# ============================================================

API_BASE_URL = "http://127.0.0.1:8000/api/v1"


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Nifty 100 Screener",
    page_icon="🔎",
    layout="wide"
)


# ============================================================
# API FUNCTION
# ============================================================

@st.cache_data(ttl=300)
def get_companies():

    try:

        response = requests.get(
            f"{API_BASE_URL}/companies",
            timeout=10
        )

        response.raise_for_status()

        result = response.json()

        return result.get("data", [])

    except requests.exceptions.ConnectionError:

        st.error(
            "❌ Cannot connect to FastAPI.\n\n"
            "Make sure this is running:\n"
            "uvicorn src.api.main:app --reload --port 8000"
        )

        return []

    except requests.exceptions.RequestException as e:

        st.error(
            f"❌ API Error: {e}"
        )

        return []


# ============================================================
# LOAD DATA
# ============================================================

companies = get_companies()


if not companies:

    st.warning(
        "No company data available."
    )

    st.stop()


# ============================================================
# CREATE DATAFRAME
# ============================================================

df = pd.DataFrame(
    companies
)


# ============================================================
# GET FINANCIAL RATIOS
# ============================================================

@st.cache_data(ttl=300)
def get_ratios(company_id):

    try:

        response = requests.get(
            f"{API_BASE_URL}/companies/{company_id}/ratios",
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        history = data.get(
            "history",
            []
        )

        if history:

            # API returns newest first
            return history[0]

        return {}

    except Exception:

        return {}


# ============================================================
# BUILD SCREENER DATA
# ============================================================

rows = []


progress = st.progress(
    0,
    text="Loading financial data..."
)


total = len(df)


for index, company in df.iterrows():

    company_id = company.get(
        "id"
    )

    if not company_id:
        continue

    ratios = get_ratios(
        company_id
    )

    rows.append({

        "Company ID":
            company_id,

        "Company":
            company.get(
                "company_name",
                company_id
            ),

        "Net Profit Margin":
            ratios.get(
                "net_profit_margin_pct"
            ),

        "ROE":
            ratios.get(
                "return_on_equity_pct"
            ),

        "Debt/Equity":
            ratios.get(
                "debt_to_equity"
            ),

        "Interest Coverage":
            ratios.get(
                "interest_coverage"
            ),

        "Revenue CAGR 5Y":
            ratios.get(
                "revenue_cagr_5yr"
            ),

        "PAT CAGR 5Y":
            ratios.get(
                "pat_cagr_5yr"
            ),

        "EPS CAGR 5Y":
            ratios.get(
                "eps_cagr_5yr"
            ),

        "Free Cash Flow":
            ratios.get(
                "free_cash_flow_cr"
            ),

        "Cash From Operations":
            ratios.get(
                "cash_from_operations_cr"
            ),

        "Capex":
            ratios.get(
                "capex_cr"
            ),

        "Quality Score":
            ratios.get(
                "composite_quality_score"
            )
    })

    progress.progress(
        int(((index + 1) / total) * 100),
        text=f"Loading {company_id}..."
    )


progress.empty()


screen_df = pd.DataFrame(
    rows
)


# ============================================================
# TITLE
# ============================================================

st.title(
    "🔎 Nifty 100 Screener"
)

st.caption(
    "Screen Nifty 100 companies using financial and quality metrics."
)


# ============================================================
# SIDEBAR FILTERS
# ============================================================

st.sidebar.header(
    "🎯 Filters"
)


# ROE

roe_min = st.sidebar.slider(
    "Minimum ROE (%)",
    min_value=0.0,
    max_value=100.0,
    value=10.0,
    step=1.0
)


# Debt/Equity

debt_max = st.sidebar.slider(
    "Maximum Debt/Equity",
    min_value=0.0,
    max_value=5.0,
    value=1.0,
    step=0.1
)


# P/E

pe_max = st.sidebar.slider(
    "Maximum P/E",
    min_value=0.0,
    max_value=150.0,
    value=50.0,
    step=5.0
)


# Revenue CAGR

revenue_cagr_min = st.sidebar.slider(
    "Minimum Revenue CAGR 5Y (%)",
    min_value=-20.0,
    max_value=50.0,
    value=0.0,
    step=1.0
)


# Quality Score

quality_min = st.sidebar.slider(
    "Minimum Quality Score",
    min_value=0.0,
    max_value=100.0,
    value=0.0,
    step=5.0
)


# ============================================================
# OPTIONAL SECTOR FILTER
# ============================================================

sector_options = [
    "All"
]

if "sector" in df.columns:

    sector_values = (
        df["sector"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    sector_options.extend(
        sorted(sector_values)
    )


selected_sector = st.sidebar.selectbox(
    "Sector",
    sector_options
)


# ============================================================
# FILTER DATA
# ============================================================

filtered = screen_df.copy()


# ROE

if "ROE" in filtered.columns:

    filtered = filtered[
        filtered["ROE"].fillna(-999)
        >= roe_min
    ]


# Debt / Equity

if "Debt/Equity" in filtered.columns:

    filtered = filtered[
        filtered["Debt/Equity"].fillna(999)
        <= debt_max
    ]


# Revenue CAGR

if "Revenue CAGR 5Y" in filtered.columns:

    filtered = filtered[
        filtered["Revenue CAGR 5Y"].fillna(-999)
        >= revenue_cagr_min
    ]


# Quality Score

if "Quality Score" in filtered.columns:

    filtered = filtered[
        filtered["Quality Score"].fillna(-999)
        >= quality_min
    ]


# Sector

if (
    selected_sector != "All"
    and "Company ID" in filtered.columns
):

    sector_map = (
        df[
            ["id", "sector"]
        ]
        .rename(
            columns={
                "id": "Company ID"
            }
        )
    )

    filtered = filtered.merge(
        sector_map,
        on="Company ID",
        how="left"
    )

    filtered = filtered[
        filtered["sector"]
        == selected_sector
    ]

    filtered = filtered.drop(
        columns=["sector"]
    )


# ============================================================
# COMPANY COUNT
# ============================================================

st.divider()

col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "Companies",
        len(filtered)
    )


with col2:

    st.metric(
        "ROE ≥",
        f"{roe_min:.1f}%"
    )


with col3:

    st.metric(
        "Debt/Equity ≤",
        f"{debt_max:.1f}"
    )


with col4:

    st.metric(
        "Quality Score ≥",
        f"{quality_min:.0f}"
    )


# ============================================================
# RESULTS
# ============================================================

st.subheader(
    f"📊 {len(filtered)} Companies Match Your Filters"
)


if filtered.empty:

    st.warning(
        "No companies match the selected filters."
    )

else:

    display_columns = [

        "Company ID",

        "Company",

        "ROE",

        "Debt/Equity",

        "Interest Coverage",

        "Revenue CAGR 5Y",

        "PAT CAGR 5Y",

        "EPS CAGR 5Y",

        "Free Cash Flow",

        "Quality Score"
    ]


    available_columns = [

        column
        for column in display_columns
        if column in filtered.columns
    ]


    display_df = filtered[
        available_columns
    ].copy()


    # Round numbers

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
# TOP COMPANIES
# ============================================================

if not filtered.empty:

    st.divider()

    st.subheader(
        "🏆 Top Companies by Quality Score"
    )

    if "Quality Score" in filtered.columns:

        top_df = (
            filtered
            .sort_values(
                "Quality Score",
                ascending=False
            )
            .head(10)
        )


        top_display = [

            "Company ID",

            "Company",

            "ROE",

            "Debt/Equity",

            "Revenue CAGR 5Y",

            "Quality Score"
        ]


        top_display = [

            col
            for col in top_display
            if col in top_df.columns
        ]


        st.dataframe(
            top_df[top_display].round(2),
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# DOWNLOAD
# ============================================================

st.divider()

csv = filtered.to_csv(
    index=False
)


st.download_button(

    label="📥 Download Screener Results",

    data=csv,

    file_name="nifty100_screener.csv",

    mime="text/csv"
)


# ============================================================
# FOOTER
# ============================================================

st.caption(
    "Nifty 100 Financial Intelligence Platform | "
    "Data powered by FastAPI + SQLite"
)