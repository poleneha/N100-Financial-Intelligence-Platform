import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path


# ============================================================
# NIFTY 100 FINANCIAL INTELLIGENCE PLATFORM
# HOME DASHBOARD
# ============================================================

st.title("🏠 Home Dashboard")
st.caption("Nifty 100 Financial Intelligence Platform")


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"


# ============================================================
# LOAD DATA
# ============================================================

financial_file = OUTPUT_DIR / "financial_ratios.xlsx"
sector_file = Path("data/raw/sectors.xlsx")
scoring_file = OUTPUT_DIR / "portfolio_scoring.csv"


# ============================================================
# LOAD FINANCIAL DATA
# ============================================================

financial_df = None

if financial_file.exists():
    try:
        financial_df = pd.read_excel(financial_file)
    except Exception as e:
        st.error(f"Unable to load financial data: {e}")


# ============================================================
# LOAD SECTOR DATA
# ============================================================

sector_df = None

if sector_file.exists():
    try:
        sector_df = pd.read_excel(sector_file)
    except Exception as e:
        st.warning(f"Unable to load sector data: {e}")


# ============================================================
# LOAD PORTFOLIO SCORING
# ============================================================

scoring_df = None

if scoring_file.exists():
    try:
        scoring_df = pd.read_csv(scoring_file)
    except Exception as e:
        st.warning(f"Unable to load portfolio scoring data: {e}")


# ============================================================
# FILTER TO NIFTY 100 COMPANIES
# ============================================================

if sector_df is not None and financial_df is not None:

    if "company_id" in sector_df.columns and "company_id" in financial_df.columns:

        nifty_companies = (
            sector_df["company_id"]
            .dropna()
            .astype(str)
            .unique()
        )

        financial_df = financial_df[
            financial_df["company_id"]
            .astype(str)
            .isin(nifty_companies)
        ].copy()


# ============================================================
# PREPARE YEAR DATA
# ============================================================

available_years = []

if financial_df is not None and "year" in financial_df.columns:

    year_text = financial_df["year"].astype(str)

    extracted_years = pd.to_numeric(
        year_text.str.extract(r"(\d{4})")[0],
        errors="coerce"
    )

    available_years = sorted(
        extracted_years.dropna()
        .astype(int)
        .unique()
        .tolist()
    )


# Keep only proper annual years
available_years = [
    y for y in available_years
    if 2010 <= y <= 2030
]


if not available_years:
    available_years = [2019, 2020, 2021, 2022, 2023, 2024]


# ============================================================
# YEAR FILTER
# ============================================================

selected_year = st.sidebar.selectbox(
    "Select Year",
    available_years,
    index=len(available_years) - 1
)


st.info(
    f"Selected Year: {selected_year}"
)


# ============================================================
# PREPARE LATEST SELECTED YEAR DATA
# ============================================================

year_df = pd.DataFrame()

if financial_df is not None and "year" in financial_df.columns:

    financial_df["_year_num"] = pd.to_numeric(
        financial_df["year"]
        .astype(str)
        .str.extract(r"(\d{4})")[0],
        errors="coerce"
    )

    year_df = financial_df[
        financial_df["_year_num"] == selected_year
    ].copy()


# If selected year has no data, use latest available year
if year_df.empty and financial_df is not None:

    if "_year_num" not in financial_df.columns:

        financial_df["_year_num"] = pd.to_numeric(
            financial_df["year"]
            .astype(str)
            .str.extract(r"(\d{4})")[0],
            errors="coerce"
        )

    latest_year = int(
        financial_df["_year_num"]
        .dropna()
        .max()
    )

    selected_year = latest_year

    year_df = financial_df[
        financial_df["_year_num"] == selected_year
    ].copy()


# ============================================================
# KPI CALCULATIONS
# ============================================================

total_companies = (
    year_df["company_id"].nunique()
    if "company_id" in year_df.columns
    else 92
)


def numeric_series(df, column):

    if column not in df.columns:
        return pd.Series(dtype=float)

    return pd.to_numeric(
        df[column],
        errors="coerce"
    ).dropna()


roe = numeric_series(
    year_df,
    "return_on_equity_pct"
)


de = numeric_series(
    year_df,
    "debt_to_equity"
)


pe = numeric_series(
    year_df,
    "pe_ratio"
)


if pe.empty:
    pe = numeric_series(
        year_df,
        "price_to_earnings"
    )


revenue_cagr = numeric_series(
    year_df,
    "revenue_cagr_5yr"
)


# ============================================================
# KPI CARDS
# ============================================================

st.subheader("📊 Key Performance Indicators")


c1, c2, c3 = st.columns(3)


with c1:
    st.metric(
        "Total Companies",
        total_companies
    )


with c2:

    if not roe.empty:
        st.metric(
            "Average ROE",
            f"{roe.mean():.2f}%"
        )
    else:
        st.metric(
            "Average ROE",
            "N/A"
        )


with c3:

    if not pe.empty:
        st.metric(
            "Median P/E",
            f"{pe.median():.2f}"
        )
    else:
        st.metric(
            "Median P/E",
            "N/A"
        )


c4, c5, c6 = st.columns(3)


with c4:

    if not de.empty:
        st.metric(
            "Median D/E",
            f"{de.median():.2f}"
        )
    else:
        st.metric(
            "Median D/E",
            "N/A"
        )


with c5:

    if not revenue_cagr.empty:
        st.metric(
            "Revenue CAGR 5Y",
            f"{revenue_cagr.median():.2f}%"
        )
    else:
        st.metric(
            "Revenue CAGR 5Y",
            "N/A"
        )


with c6:

    if not de.empty:

        debt_free = int(
            (de <= 0.05).sum()
        )

        st.metric(
            "Debt Free Companies",
            debt_free
        )

    else:

        st.metric(
            "Debt Free Companies",
            "N/A"
        )


# ============================================================
# SECTOR BREAKDOWN
# ============================================================

st.divider()

st.subheader("🏭 Sector Breakdown")


if sector_df is not None:

    sector_column = None

    for column in [
        "broad_sector",
        "sector",
        "Sector"
    ]:

        if column in sector_df.columns:
            sector_column = column
            break


    if sector_column:

        sector_chart = (
            sector_df[
                ["company_id", sector_column]
            ]
            .drop_duplicates()
            .groupby(sector_column)
            .size()
            .reset_index(name="Companies")
            .sort_values(
                "Companies",
                ascending=False
            )
        )


        fig = px.pie(
            sector_chart,
            names=sector_column,
            values="Companies",
            title=f"Nifty 100 Sector Distribution"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:

        st.info(
            "Sector column not found."
        )

else:

    st.warning(
        "Sector data not available."
    )


# ============================================================
# TOP COMPANIES
# ============================================================

st.divider()

st.subheader("🏆 Top 5 Quality Companies")


if scoring_df is not None and not scoring_df.empty:

    display_columns = [
        "rank",
        "company_id",
        "cluster_name",
        "investment_score",
        "investment_category"
    ]

    display_columns = [
        column
        for column in display_columns
        if column in scoring_df.columns
    ]


    top_companies = (
        scoring_df
        .sort_values(
            "rank"
        )
        .head(5)
    )


    st.dataframe(
        top_companies[display_columns],
        use_container_width=True,
        hide_index=True
    )

else:

    st.info(
        "Portfolio scoring data is not available."
    )


# ============================================================
# INVESTMENT CATEGORY DISTRIBUTION
# ============================================================

if scoring_df is not None and "investment_category" in scoring_df.columns:

    st.subheader(
        "💼 Investment Category Distribution"
    )


    category_data = (
        scoring_df[
            "investment_category"
        ]
        .value_counts()
        .reset_index()
    )

    category_data.columns = [
        "Investment Category",
        "Companies"
    ]


    fig_category = px.bar(
        category_data,
        x="Investment Category",
        y="Companies",
        title="Companies by Investment Category"
    )


    st.plotly_chart(
        fig_category,
        use_container_width=True
    )


# ============================================================
# CLUSTER DISTRIBUTION
# ============================================================

cluster_file = OUTPUT_DIR / "cluster_labels.csv"


if cluster_file.exists():

    cluster_df = pd.read_csv(
        cluster_file
    )


    if "cluster_name" in cluster_df.columns:

        st.subheader(
            "🔬 Cluster Distribution"
        )


        cluster_chart = (
            cluster_df[
                "cluster_name"
            ]
            .value_counts()
            .reset_index()
        )

        cluster_chart.columns = [
            "Cluster",
            "Companies"
        ]


        fig_cluster = px.bar(
            cluster_chart,
            x="Cluster",
            y="Companies",
            title="Nifty 100 Companies by Cluster"
        )


        st.plotly_chart(
            fig_cluster,
            use_container_width=True
        )


# ============================================================
# DATA QUALITY / STATUS
# ============================================================

st.divider()

st.subheader("✅ Platform Status")


status1, status2, status3 = st.columns(3)


with status1:

    if total_companies == 92:
        st.success("92 Nifty 100 companies loaded")
    else:
        st.warning(
            f"{total_companies} companies loaded"
        )


with status2:

    if scoring_df is not None:
        st.success("Portfolio scoring available")
    else:
        st.warning("Portfolio scoring unavailable")


with status3:

    if cluster_file.exists():
        st.success("Cluster analytics available")
    else:
        st.warning("Cluster analytics unavailable")


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Nifty 100 Financial Intelligence Platform | "
    "Data Analytics • Clustering • Portfolio Intelligence"
)