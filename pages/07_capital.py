import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.express as px


st.set_page_config(
    page_title="Capital Allocation",
    page_icon="💰",
    layout="wide"
)

st.title("💰 Capital Allocation")
st.caption(
    "Nifty 100 company capital allocation and cash-flow intelligence"
)


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_DIR = Path.cwd()

OUTPUT_DIR = PROJECT_DIR / "output"


# ============================================================
# FILE PATHS
# ============================================================

CAPITAL_FILE = (
    OUTPUT_DIR / "capital_allocation.csv"
)

PATTERN_FILE = (
    OUTPUT_DIR / "capital_pattern_summary.csv"
)

CASHFLOW_FILE = (
    OUTPUT_DIR / "cashflow_intelligence.xlsx"
)


# ============================================================
# CAPITAL ALLOCATION
# ============================================================

st.subheader(
    "Capital Allocation Analysis"
)


if CAPITAL_FILE.exists():

    try:

        capital_df = pd.read_csv(
            CAPITAL_FILE
        )

        if capital_df.empty:

            st.warning(
                "Capital allocation file is empty."
            )

        else:

            st.dataframe(
                capital_df,
                use_container_width=True,
                hide_index=True
            )

            # -----------------------------------------------
            # FIND PATTERN COLUMN
            # -----------------------------------------------

            pattern_column = None

            possible_columns = [
                "pattern",
                "capital_pattern",
                "capital_allocation_pattern",
                "allocation_pattern",
                "category"
            ]

            for column in possible_columns:

                if column in capital_df.columns:

                    pattern_column = column
                    break


            # -----------------------------------------------
            # PATTERN CHART
            # -----------------------------------------------

            if pattern_column:

                pattern_counts = (
                    capital_df[
                        pattern_column
                    ]
                    .fillna("Unknown")
                    .astype(str)
                    .value_counts()
                    .reset_index()
                )

                pattern_counts.columns = [
                    "Pattern",
                    "Companies"
                ]

                st.subheader(
                    "Capital Allocation Patterns"
                )

                col1, col2 = st.columns(2)

                with col1:

                    fig_tree = px.treemap(
                        pattern_counts,
                        path=["Pattern"],
                        values="Companies",
                        title="Capital Allocation Map"
                    )

                    st.plotly_chart(
                        fig_tree,
                        use_container_width=True
                    )

                with col2:

                    fig_bar = px.bar(
                        pattern_counts,
                        x="Pattern",
                        y="Companies",
                        title="Companies by Pattern"
                    )

                    st.plotly_chart(
                        fig_bar,
                        use_container_width=True
                    )

            else:

                st.info(
                    "Pattern column not found in capital allocation data."
                )


            # -----------------------------------------------
            # COMPANY SELECTION
            # -----------------------------------------------

            if "company_id" in capital_df.columns:

                st.divider()

                st.subheader(
                    "Company Capital Allocation"
                )

                companies = sorted(
                    capital_df[
                        "company_id"
                    ]
                    .dropna()
                    .astype(str)
                    .unique()
                )

                selected_company = st.selectbox(
                    "Select Company",
                    companies
                )

                company_data = capital_df[
                    capital_df["company_id"].astype(str)
                    == selected_company
                ]

                st.dataframe(
                    company_data,
                    use_container_width=True,
                    hide_index=True
                )


            # -----------------------------------------------
            # DOWNLOAD
            # -----------------------------------------------

            st.download_button(
                "📥 Download Capital Allocation",
                data=capital_df.to_csv(
                    index=False
                ),
                file_name="capital_allocation.csv",
                mime="text/csv"
            )


    except Exception as e:

        st.error(
            f"Could not read capital allocation file: {e}"
        )

else:

    st.error(
        f"File not found: {CAPITAL_FILE}"
    )


# ============================================================
# CAPITAL PATTERN SUMMARY
# ============================================================

st.divider()

st.subheader(
    "📊 Capital Pattern Summary"
)


if PATTERN_FILE.exists():

    try:

        pattern_summary = pd.read_csv(
            PATTERN_FILE
        )

        st.dataframe(
            pattern_summary,
            use_container_width=True,
            hide_index=True
        )

    except Exception as e:

        st.error(
            f"Could not read pattern summary: {e}"
        )

else:

    st.info(
        "Capital pattern summary is not available."
    )


# ============================================================
# CASH FLOW INTELLIGENCE
# ============================================================

st.divider()

st.subheader(
    "💵 Cash Flow Intelligence"
)


if CASHFLOW_FILE.exists():

    try:

        cashflow_df = pd.read_excel(
            CASHFLOW_FILE
        )

        if cashflow_df.empty:

            st.warning(
                "Cash-flow intelligence file is empty."
            )

        else:

            st.dataframe(
                cashflow_df,
                use_container_width=True,
                hide_index=True
            )

            # -----------------------------------------------
            # DOWNLOAD
            # -----------------------------------------------

            with open(
                CASHFLOW_FILE,
                "rb"
            ) as f:

                st.download_button(
                    "📥 Download Cash Flow Intelligence",
                    data=f.read(),
                    file_name="cashflow_intelligence.xlsx",
                    mime=(
                        "application/vnd.openxmlformats-officedocument."
                        "spreadsheetml.sheet"
                    )
                )


            # -----------------------------------------------
            # COMPANY SEARCH
            # -----------------------------------------------

            if "company_id" in cashflow_df.columns:

                st.divider()

                st.subheader(
                    "Company Cash Flow Intelligence"
                )

                companies = sorted(
                    cashflow_df[
                        "company_id"
                    ]
                    .dropna()
                    .astype(str)
                    .unique()
                )

                selected_company = st.selectbox(
                    "Select Company",
                    companies,
                    key="cashflow_company"
                )

                selected_data = cashflow_df[
                    cashflow_df["company_id"].astype(str)
                    == selected_company
                ]

                st.dataframe(
                    selected_data,
                    use_container_width=True,
                    hide_index=True
                )


    except Exception as e:

        st.error(
            f"Could not read cash-flow Excel file: {e}"
        )

else:

    st.error(
        f"File not found: {CASHFLOW_FILE}"
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Nifty 100 Financial Intelligence Platform | "
    "Capital Allocation & Cash Flow Intelligence"
)