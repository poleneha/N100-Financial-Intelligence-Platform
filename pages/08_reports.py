import streamlit as st
import pandas as pd
from pathlib import Path


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Reports & Insights",
    page_icon="📄",
    layout="wide"
)


# ============================================================
# FIND PROJECT ROOT AUTOMATICALLY
# ============================================================

CURRENT_DIR = Path(__file__).resolve()

PROJECT_ROOT = None

for parent in CURRENT_DIR.parents:
    if (parent / "output").exists() and (parent / "data").exists():
        PROJECT_ROOT = parent
        break

if PROJECT_ROOT is None:
    PROJECT_ROOT = Path.cwd()

OUTPUT_DIR = PROJECT_ROOT / "output"
REPORTS_DIR = PROJECT_ROOT / "reports"

TEARSHEET_DIR = REPORTS_DIR / "tearsheets"
SECTOR_DIR = REPORTS_DIR / "sectors"
PORTFOLIO_DIR = REPORTS_DIR / "portfolio"


# ============================================================
# TITLE
# ============================================================

st.title("📄 Reports & Insights")

st.caption(
    "Nifty 100 company reports, analytics and investment insights"
)


# ============================================================
# LOAD CSV
# ============================================================

def load_csv(filename):

    path = OUTPUT_DIR / filename

    if not path.exists():
        return None

    try:
        return pd.read_csv(path)

    except Exception as e:
        st.error(f"Error reading {filename}: {e}")
        return None


# ============================================================
# DOWNLOAD CSV
# ============================================================

def csv_download(df, filename, label):

    if df is not None and not df.empty:

        st.download_button(
            label=label,
            data=df.to_csv(index=False).encode("utf-8"),
            file_name=filename,
            mime="text/csv"
        )


# ============================================================
# DOWNLOAD PDF
# ============================================================

def pdf_download(path, label):

    if path.exists():

        with open(path, "rb") as f:

            st.download_button(
                label=label,
                data=f.read(),
                file_name=path.name,
                mime="application/pdf"
            )

        return True

    return False


# ============================================================
# LOAD DATA
# ============================================================

portfolio_scores = load_csv(
    "portfolio_scoring.csv"
)

top_ranked = load_csv(
    "top_ranked_companies.csv"
)

cluster_labels = load_csv(
    "cluster_labels.csv"
)

cluster_profiles = load_csv(
    "cluster_profiles.csv"
)

cluster_insights = load_csv(
    "cluster_insights.csv"
)

outliers = load_csv(
    "outlier_report.csv"
)

portfolio_stats = load_csv(
    "portfolio_stats.csv"
)

investment_recommendations = load_csv(
    "investment_recommendations.csv"
)


# ============================================================
# REPORT OVERVIEW
# ============================================================

st.subheader("📊 Report Overview")


company_count = 0

if portfolio_scores is not None:
    company_count = len(portfolio_scores)

elif top_ranked is not None:
    company_count = len(top_ranked)


cluster_count = 0

if cluster_labels is not None:

    if "cluster_id" in cluster_labels.columns:

        cluster_count = (
            cluster_labels["cluster_id"]
            .nunique()
        )


company_files = []

if TEARSHEET_DIR.exists():

    company_files = list(
        TEARSHEET_DIR.glob("*.pdf")
    )


sector_files = []

if SECTOR_DIR.exists():

    sector_files = list(
        SECTOR_DIR.glob("*.pdf")
    )


col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "Companies",
        company_count
    )


with col2:

    st.metric(
        "Clusters",
        cluster_count
    )


with col3:

    st.metric(
        "Company Reports",
        len(company_files)
    )


with col4:

    st.metric(
        "Sector Reports",
        len(sector_files)
    )


# ============================================================
# TOP RANKED COMPANIES
# ============================================================

st.divider()

st.subheader("🏆 Top Ranked Companies")


if top_ranked is not None and not top_ranked.empty:

    st.dataframe(
        top_ranked,
        use_container_width=True,
        hide_index=True
    )

    csv_download(
        top_ranked,
        "top_ranked_companies.csv",
        "📥 Download Top Ranked Companies"
    )

else:

    st.warning(
        "Top ranked companies data is not available."
    )


# ============================================================
# INVESTMENT RECOMMENDATIONS
# ============================================================

st.divider()

st.subheader("💡 Investment Recommendations")


if (
    investment_recommendations is not None
    and not investment_recommendations.empty
):

    st.dataframe(
        investment_recommendations,
        use_container_width=True,
        hide_index=True
    )

    csv_download(
        investment_recommendations,
        "investment_recommendations.csv",
        "📥 Download Investment Recommendations"
    )

else:

    st.info(
        "Investment recommendations are not available."
    )


# ============================================================
# PORTFOLIO SCORING
# ============================================================

st.divider()

st.subheader("💼 Portfolio Scoring")


if portfolio_scores is not None and not portfolio_scores.empty:

    st.dataframe(
        portfolio_scores,
        use_container_width=True,
        hide_index=True
    )

    csv_download(
        portfolio_scores,
        "portfolio_scoring.csv",
        "📥 Download Portfolio Scoring"
    )

else:

    st.info(
        "Portfolio scoring data is not available."
    )


# ============================================================
# CLUSTER INSIGHTS
# ============================================================

st.divider()

st.subheader("🔬 Cluster Insights")


if cluster_insights is not None and not cluster_insights.empty:

    st.dataframe(
        cluster_insights,
        use_container_width=True,
        hide_index=True
    )

    csv_download(
        cluster_insights,
        "cluster_insights.csv",
        "📥 Download Cluster Insights"
    )

else:

    st.info(
        "Cluster insights are not available."
    )


# ============================================================
# CLUSTER PROFILES
# ============================================================

st.subheader("📈 Cluster Profiles")


if cluster_profiles is not None and not cluster_profiles.empty:

    st.dataframe(
        cluster_profiles,
        use_container_width=True,
        hide_index=True
    )

    csv_download(
        cluster_profiles,
        "cluster_profiles.csv",
        "📥 Download Cluster Profiles"
    )

else:

    st.info(
        "Cluster profiles are not available."
    )


# ============================================================
# OUTLIER REPORT
# ============================================================

st.divider()

st.subheader("⚠️ Sector-Wise Outliers")


if outliers is not None and not outliers.empty:

    st.dataframe(
        outliers,
        use_container_width=True,
        hide_index=True
    )

    csv_download(
        outliers,
        "outlier_report.csv",
        "📥 Download Outlier Report"
    )

else:

    st.success(
        "No significant sector-wise outliers detected."
    )


# ============================================================
# PORTFOLIO STATISTICS
# ============================================================

st.divider()

st.subheader("📊 Portfolio Statistics")


if portfolio_stats is not None and not portfolio_stats.empty:

    st.dataframe(
        portfolio_stats,
        use_container_width=True,
        hide_index=True
    )

    csv_download(
        portfolio_stats,
        "portfolio_stats.csv",
        "📥 Download Portfolio Statistics"
    )

else:

    st.info(
        "Portfolio statistics are not available."
    )


# ============================================================
# COMPANY TEAR SHEETS
# ============================================================

st.divider()

st.subheader("📑 Company Tear Sheets")


if company_files:

    company_names = sorted(
        [
            p.stem.replace("_tearsheet", "")
            for p in company_files
        ]
    )

    selected_company = st.selectbox(
        "Select Company",
        company_names
    )

    selected_pdf = (
        TEARSHEET_DIR
        / f"{selected_company}_tearsheet.pdf"
    )

    pdf_download(
        selected_pdf,
        "📥 Download Company Tear Sheet"
    )

else:

    st.info(
        "No company tear sheets found."
    )


# ============================================================
# SECTOR REPORTS
# ============================================================

st.divider()

st.subheader("🏭 Sector Reports")


if sector_files:

    sector_names = sorted(
        [
            p.stem.replace("_report", "").replace("_", " ")
            for p in sector_files
        ]
    )

    selected_sector = st.selectbox(
        "Select Sector",
        sector_names
    )

    sector_filename = (
        selected_sector.replace(" ", "_")
        + "_report.pdf"
    )

    selected_pdf = (
        SECTOR_DIR
        / sector_filename
    )

    pdf_download(
        selected_pdf,
        "📥 Download Sector Report"
    )

else:

    st.info(
        "No sector reports found."
    )
    # ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Nifty 100 Financial Intelligence Platform | "
    "Reports, Analytics & Investment Insights"
)