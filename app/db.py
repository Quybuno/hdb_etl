import os
import duckdb
import pandas as pd
import streamlit as st

DB_PATH = os.path.join("data", "warehouse", "warehouse.duckdb")

def get_connection():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Production database not found at {DB_PATH}. Please run pipeline first.")
    return duckdb.connect(DB_PATH, read_only=True)

@st.cache_data(ttl=3600)
def query_df(sql: str, params: tuple = None) -> pd.DataFrame:
    con = get_connection()
    try:
        if params:
            df = con.execute(sql, params).df()
        else:
            df = con.execute(sql).df()
        return df
    finally:
        con.close()

def get_latest_data_date() -> str:
    df = query_df("SELECT max(month) as latest_month FROM main_marts.fct_resale_transaction")
    return str(df["latest_month"].iloc[0]) if not df.empty else "N/A"

