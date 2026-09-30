import streamlit as st
import pandas as pd
import sqlite3


DB_PATH = "db/nifty100.db"


@st.cache_data(ttl=600)
def load_data():

    try:
        conn = sqlite3.connect(DB_PATH)

        df = pd.read_sql(
            "SELECT * FROM companies",
            conn
        )

        conn.close()

        return df


    except Exception as e:

        st.error(
            f"Database error: {e}"
        )

        return pd.DataFrame()



def get_companies():

    return load_data()



def get_ratios():

    return load_data()



def get_valuation():

    return load_data()