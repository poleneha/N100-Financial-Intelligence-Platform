import streamlit as st
import pandas as pd
import requests
import plotly.express as px


# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------

st.set_page_config(
    page_title="Peer Comparison",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Peer Comparison")
st.caption("Compare a Nifty 100 company with companies in the same peer group.")


# ---------------------------------------------------------
# API CONFIG
# ---------------------------------------------------------

API_BASE = "http://127.0.0.1:8000/api/v1"


# ---------------------------------------------------------
# API FUNCTIONS
# ---------------------------------------------------------

@st.cache_data(ttl=300)
def get_companies():
    try:
        response = requests.get(
            f"{API_BASE}/companies",
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        return data.get("data", [])

    except requests.exceptions.RequestException as e:
        st.error(f"Unable to connect to API: {e}")
        return []


@st.cache_data(ttl=300)
def get_peers(ticker):
    try:
        response = requests.get(
            f"{API_BASE}/companies/{ticker}/peers",
            timeout=10
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as e:
        st.error(f"Unable to load peer data: {e}")
        return None


# ---------------------------------------------------------
# LOAD COMPANIES
# ---------------------------------------------------------

companies = get_companies()

if not companies:
    st.warning("No companies found.")
    st.stop()


company_options = {}

for company in companies:
    ticker = company.get("id")

    if ticker:
        company_options[ticker] = company.get(
            "company_name",
            ticker
        )


# ---------------------------------------------------------
# COMPANY SELECTOR
# ---------------------------------------------------------

selected_ticker = st.selectbox(
    "Select Company",
    options=list(company_options.keys()),
    format_func=lambda x: f"{x} — {company_options[x]}"
)


# ---------------------------------------------------------
# LOAD PEERS
# ---------------------------------------------------------

peer_result = get_peers(selected_ticker)

if not peer_result:
    st.warning("No peer data available.")
    st.stop()


peer_group = peer_result.get(
    "peer_group",
    "Not Available"
)

peers = peer_result.get(
    "peers",
    []
)


# ---------------------------------------------------------
# PEER GROUP INFORMATION
# ---------------------------------------------------------

st.info(
    f"**Peer Group:** {peer_group}  |  "
    f"**Peer Companies:** {len(peers)}"
)


if not peers:
    st.warning(
        f"No peer companies found for {selected_ticker}."
    )
    st.stop()


# ---------------------------------------------------------
# PEER DATAFRAME
# ---------------------------------------------------------

rows = []

for peer in peers:

    rows.append({
        "Company": peer.get("company_name"),
        "Ticker": peer.get("company_id"),
        "Peer Group": peer.get("peer_group"),
        "Book Value": peer.get("book_value"),
        "ROCE (%)": peer.get("roce_percentage"),
        "ROE (%)": peer.get("roe_percentage")
    })


peer_df = pd.DataFrame(rows)


# ---------------------------------------------------------
# PEER TABLE
# ---------------------------------------------------------

st.subheader("Peer Companies")

st.dataframe(
    peer_df,
    use_container_width=True,
    hide_index=True
)


# ---------------------------------------------------------
# METRIC CARDS
# ---------------------------------------------------------

st.subheader("Peer Metrics")

col1, col2, col3 = st.columns(3)

avg_roce = peer_df["ROCE (%)"].mean()
avg_roe = peer_df["ROE (%)"].mean()
avg_book_value = peer_df["Book Value"].mean()


with col1:
    st.metric(
        "Average ROCE",
        f"{avg_roce:.2f}%"
    )


with col2:
    st.metric(
        "Average ROE",
        f"{avg_roe:.2f}%"
    )


with col3:
    st.metric(
        "Average Book Value",
        f"₹{avg_book_value:.2f}"
    )


# ---------------------------------------------------------
# ROE COMPARISON
# ---------------------------------------------------------

st.subheader("ROE Comparison")

roe_df = peer_df[
    ["Ticker", "ROE (%)"]
].copy()

roe_df = roe_df.sort_values(
    "ROE (%)",
    ascending=False
)


fig_roe = px.bar(
    roe_df,
    x="Ticker",
    y="ROE (%)",
    text="ROE (%)",
    title="Return on Equity — Peer Comparison"
)

fig_roe.update_traces(
    texttemplate="%{text:.2f}%",
    textposition="outside"
)

fig_roe.update_layout(
    xaxis_title="Company",
    yaxis_title="ROE (%)"
)

st.plotly_chart(
    fig_roe,
    use_container_width=True
)


# ---------------------------------------------------------
# ROCE COMPARISON
# ---------------------------------------------------------

st.subheader("ROCE Comparison")

roce_df = peer_df[
    ["Ticker", "ROCE (%)"]
].copy()

roce_df = roce_df.sort_values(
    "ROCE (%)",
    ascending=False
)


fig_roce = px.bar(
    roce_df,
    x="Ticker",
    y="ROCE (%)",
    text="ROCE (%)",
    title="Return on Capital Employed — Peer Comparison"
)

fig_roce.update_traces(
    texttemplate="%{text:.2f}%",
    textposition="outside"
)

fig_roce.update_layout(
    xaxis_title="Company",
    yaxis_title="ROCE (%)"
)

st.plotly_chart(
    fig_roce,
    use_container_width=True
)


# ---------------------------------------------------------
# BOOK VALUE COMPARISON
# ---------------------------------------------------------

st.subheader("Book Value Comparison")

book_df = peer_df[
    ["Ticker", "Book Value"]
].copy()

book_df = book_df.sort_values(
    "Book Value",
    ascending=False
)


fig_book = px.bar(
    book_df,
    x="Ticker",
    y="Book Value",
    text="Book Value",
    title="Book Value — Peer Comparison"
)

fig_book.update_traces(
    texttemplate="₹%{text:.2f}",
    textposition="outside"
)

fig_book.update_layout(
    xaxis_title="Company",
    yaxis_title="Book Value"
)

st.plotly_chart(
    fig_book,
    use_container_width=True
)


# ---------------------------------------------------------
# PERFORMANCE SUMMARY
# ---------------------------------------------------------

st.subheader("Performance Summary")

if not peer_df.empty:

    best_roe = peer_df.loc[
        peer_df["ROE (%)"].idxmax()
    ]

    best_roce = peer_df.loc[
        peer_df["ROCE (%)"].idxmax()
    ]

    highest_book = peer_df.loc[
        peer_df["Book Value"].idxmax()
    ]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.success(
            f"🏆 Highest ROE\n\n"
            f"**{best_roe['Ticker']}** — "
            f"{best_roe['ROE (%)']:.2f}%"
        )

    with col2:
        st.success(
            f"🏆 Highest ROCE\n\n"
            f"**{best_roce['Ticker']}** — "
            f"{best_roce['ROCE (%)']:.2f}%"
        )

    with col3:
        st.success(
            f"🏆 Highest Book Value\n\n"
            f"**{highest_book['Ticker']}** — "
            f"₹{highest_book['Book Value']:.2f}"
        )