import streamlit as st
import pandas as pd
import requests

# ============================================================
# CONFIGURATION
# ============================================================

API_BASE_URL = "http://127.0.0.1:8000/api/v1"


# ============================================================
# API HELPER
# ============================================================

def api_get(endpoint):
    try:
        response = requests.get(
            f"{API_BASE_URL}{endpoint}",
            timeout=10
        )

        response.raise_for_status()
        return response.json()

    except requests.exceptions.ConnectionError:
        st.error(
            "Cannot connect to FastAPI backend. "
            "Make sure FastAPI is running on port 8000."
        )
        return None

    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {e}")
        return None


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Company Profile",
    page_icon="🏢",
    layout="wide"
)

st.title("🏢 Company Profile")
st.caption("Nifty 100 Financial Intelligence Platform")


# ============================================================
# COMPANY LIST
# ============================================================

companies_data = api_get("/companies")

if companies_data is None:
    st.stop()

companies = companies_data.get("data", [])

if not companies:
    st.warning("No companies found.")
    st.stop()


# Create company lookup
company_map = {}

for company in companies:
    company_id = company.get("id")

    if company_id:
        company_name = company.get(
            "company_name",
            company_id
        )

        company_map[company_id] = company_name


# ============================================================
# COMPANY SELECTOR
# ============================================================

company_ids = list(company_map.keys())

selected_company = st.selectbox(
    "Select Company",
    company_ids,
    format_func=lambda x: f"{x} - {company_map[x]}"
)


# ============================================================
# LOAD COMPANY DATA
# ============================================================

company = api_get(
    f"/companies/{selected_company}"
)

sector_data = api_get(
    f"/companies/{selected_company}/sector"
)

ratios_data = api_get(
    f"/companies/{selected_company}/ratios"
)

peers_data = api_get(
    f"/companies/{selected_company}/peers"
)

pros_cons_data = api_get(
    f"/companies/{selected_company}/pros-cons"
)

pl_data = api_get(
    f"/companies/{selected_company}/pl"
)

bs_data = api_get(
    f"/companies/{selected_company}/bs"
)

cashflow_data = api_get(
    f"/companies/{selected_company}/cashflow"
)


if company is None:
    st.stop()


# ============================================================
# COMPANY HEADER
# ============================================================

st.divider()

col1, col2 = st.columns([1, 4])

with col1:

    logo = company.get("company_logo")

    if logo:
        try:
            st.image(
                logo,
                width=140
            )
        except Exception:
            st.write("🏢")
    else:
        st.write("🏢")


with col2:

    st.header(
        company.get(
            "company_name",
            selected_company
        )
    )

    st.write(
        f"**Ticker:** {selected_company}"
    )

    about = company.get("about_company")

    if about:
        st.write(about)


# ============================================================
# COMPANY LINKS
# ============================================================

st.subheader("🔗 Company Links")

link_col1, link_col2, link_col3, link_col4 = st.columns(4)

with link_col1:

    website = company.get("website")

    if website:
        st.link_button(
            "🌐 Website",
            website
        )

with link_col2:

    nse = company.get("nse_profile")

    if nse:
        st.link_button(
            "📈 NSE",
            nse
        )

with link_col3:

    bse = company.get("bse_profile")

    if bse:
        st.link_button(
            "📊 BSE",
            bse
        )

with link_col4:

    chart = company.get("chart_link")

    if chart:
        st.link_button(
            "📉 TradingView",
            chart
        )


# ============================================================
# KEY METRICS
# ============================================================

st.divider()

st.subheader("📌 Key Metrics")

latest_ratios = company.get(
    "latest_ratios"
)

metric1, metric2, metric3, metric4, metric5 = st.columns(5)

with metric1:

    value = company.get("book_value")

    st.metric(
        "Book Value",
        f"₹{value}" if value is not None else "N/A"
    )

with metric2:

    value = company.get("roce_percentage")

    st.metric(
        "ROCE",
        f"{value:.2f}%" if isinstance(value, (int, float)) else "N/A"
    )

with metric3:

    value = company.get("roe_percentage")

    # Database value appears to be decimal for company-level ROE.
    if isinstance(value, (int, float)):
        display_value = value * 100 if value < 1 else value
        st.metric(
            "ROE",
            f"{display_value:.2f}%"
        )
    else:
        st.metric(
            "ROE",
            "N/A"
        )

with metric4:

    if latest_ratios:

        value = latest_ratios.get(
            "net_profit_margin_pct"
        )

        st.metric(
            "Net Profit Margin",
            f"{value:.2f}%" if isinstance(value, (int, float)) else "N/A"
        )

with metric5:

    if latest_ratios:

        value = latest_ratios.get(
            "debt_to_equity"
        )

        st.metric(
            "Debt / Equity",
            f"{value:.2f}" if isinstance(value, (int, float)) else "N/A"
        )


# ============================================================
# SECTOR
# ============================================================

st.divider()

st.subheader("🏭 Sector Information")

if sector_data:

    sector = sector_data.get(
        "sector",
        {}
    )

    if sector:

        s1, s2, s3, s4 = st.columns(4)

        with s1:
            st.metric(
                "Sector",
                sector.get(
                    "sector",
                    "N/A"
                )
            )

        with s2:
            st.metric(
                "Industry",
                sector.get(
                    "industry",
                    "N/A"
                )
            )

        with s3:

            weight = sector.get(
                "weight"
            )

            st.metric(
                "Nifty 100 Weight",
                f"{weight}%" if isinstance(weight, (int, float)) else "N/A"
            )

        with s4:
            st.metric(
                "Market Cap",
                sector.get(
                    "market_cap_category",
                    "N/A"
                )
            )

    else:
        st.info("Sector information not available.")


# ============================================================
# FINANCIAL RATIOS
# ============================================================

st.divider()

st.subheader("📊 Financial Ratios")

if ratios_data:

    ratios_history = ratios_data.get(
        "history",
        []
    )

    if ratios_history:

        ratios_df = pd.DataFrame(
            ratios_history
        )

        st.dataframe(
            ratios_df,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info(
            "Financial ratio history not available."
        )


# ============================================================
# PROS & CONS
# ============================================================

st.divider()

st.subheader("⚖️ Pros & Cons")

if pros_cons_data:

    pros = pros_cons_data.get(
        "pros",
        []
    )

    cons = pros_cons_data.get(
        "cons",
        []
    )

    pros_col, cons_col = st.columns(2)

    with pros_col:

        st.markdown("### ✅ Pros")

        if pros:

            for item in pros:

                text = item.get(
                    "text",
                    ""
                )

                if text:
                    st.success(
                        text
                    )

        else:
            st.info(
                "No pros available."
            )

    with cons_col:

        st.markdown("### ⚠️ Cons")

        if cons:

            for item in cons:

                text = item.get(
                    "text",
                    ""
                )

                if text:
                    st.warning(
                        text
                    )

        else:
            st.info(
                "No cons available."
            )


# ============================================================
# PEERS
# ============================================================

st.divider()

st.subheader("👥 Peer Companies")

if peers_data:

    peers = peers_data.get(
        "peers",
        []
    )

    if peers:

        peers_df = pd.DataFrame(
            peers
        )

        display_columns = [
            "company_id",
            "company_name",
            "peer_group",
            "book_value",
            "roce_percentage",
            "roe_percentage"
        ]

        available_columns = [
            col
            for col in display_columns
            if col in peers_df.columns
        ]

        st.dataframe(
            peers_df[available_columns],
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info(
            "No peer companies available."
        )


# ============================================================
# PROFIT & LOSS
# ============================================================

st.divider()

st.subheader("💰 Profit & Loss History")

if pl_data:

    pl_history = pl_data.get(
        "history",
        []
    )

    if pl_history:

        pl_df = pd.DataFrame(
            pl_history
        )

        st.dataframe(
            pl_df,
            use_container_width=True,
            hide_index=True
        )

        if "year" in pl_df.columns and "sales" in pl_df.columns:

            chart_df = pl_df.copy()

            chart_df["sales"] = pd.to_numeric(
                chart_df["sales"],
                errors="coerce"
            )

            chart_df = chart_df.dropna(
                subset=["sales"]
            )

            if not chart_df.empty:

                st.markdown(
                    "#### Revenue Trend"
                )

                st.line_chart(
                    chart_df.set_index("year")[
                        ["sales"]
                    ]
                )

    else:
        st.info(
            "P&L history not available."
        )


# ============================================================
# BALANCE SHEET
# ============================================================

st.divider()

st.subheader("🏦 Balance Sheet")

if bs_data:

    bs_history = bs_data.get(
        "history",
        []
    )

    if bs_history:

        bs_df = pd.DataFrame(
            bs_history
        )

        st.dataframe(
            bs_df,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info(
            "Balance Sheet history not available."
        )


# ============================================================
# CASH FLOW
# ============================================================

st.divider()

st.subheader("💵 Cash Flow")

if cashflow_data:

    cashflow_history = cashflow_data.get(
        "history",
        []
    )

    if cashflow_history:

        cashflow_df = pd.DataFrame(
            cashflow_history
        )

        st.dataframe(
            cashflow_df,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info(
            "Cash Flow history not available."
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Nifty 100 Financial Intelligence Platform | "
    "Data powered by FastAPI + SQLite"
)