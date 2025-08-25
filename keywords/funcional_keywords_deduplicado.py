# keywords/funcional_keywords_deduplicado.py

import pandas as pd
import numpy as np
import streamlit as st


def build_master_raw(excel_data: pd.ExcelFile) -> pd.DataFrame:
    try:
        df_cust = excel_data.parse("CustKW", skiprows=2)
        df_comp = excel_data.parse("CompKW", skiprows=2)
        df_mining = excel_data.parse("MiningKW", skiprows=2)
    except Exception as e:
        st.error(f"Error al leer hojas del Excel: {e}")
        return pd.DataFrame()

    def naf(col, df, index):
        try:
            return df.iloc[:, index]
        except Exception:
            return pd.Series([None] * len(df), index=df.index)

    cust_df = pd.DataFrame()
    cust_df["Search Terms"] = df_cust.iloc[:, 0]
    cust_df["Search Volume"] = df_cust.iloc[:, 15]
    cust_df["ASIN Click Share"] = df_cust.iloc[:, 1]
    cust_df["Comp Click Share"] = [None] * len(df_cust)
    cust_df["Niche Click Share"] = [None] * len(df_cust)
    cust_df["Comp Depth"] = [None] * len(df_cust)
    cust_df["Niche Depth"] = [None] * len(df_cust)
    cust_df["Relevancy"] = [None] * len(df_cust)
    cust_df["Fuente"] = "CustKW"
    cust_df["ABA Rank"] = df_cust.iloc[:, 14]

    comp_df = pd.DataFrame()
    comp_df["Search Terms"] = df_comp.iloc[:, 0]
    comp_df["Search Volume"] = df_comp.iloc[:, 8]
    comp_df["ASIN Click Share"] = [None] * len(df_comp)
    comp_df["Comp Click Share"] = df_comp.iloc[:, 2]
    comp_df["Niche Click Share"] = [None] * len(df_comp)
    comp_df["Comp Depth"] = df_comp.iloc[:, 5]
    comp_df["Niche Depth"] = [None] * len(df_comp)
    comp_df["Relevancy"] = [None] * len(df_comp)
    comp_df["Fuente"] = "CompKW"
    comp_df["ABA Rank"] = [None] * len(df_comp)

    mining_df = pd.DataFrame()
    mining_df["Search Terms"] = df_mining.iloc[:, 0]
    mining_df["Search Volume"] = df_mining.iloc[:, 5]
    mining_df["ASIN Click Share"] = [None] * len(df_mining)
    mining_df["Comp Click Share"] = [None] * len(df_mining)
    mining_df["Niche Click Share"] = df_mining.iloc[:, 15]
    mining_df["Comp Depth"] = [None] * len(df_mining)
    mining_df["Niche Depth"] = df_mining.iloc[:, 12]
    mining_df["Relevancy"] = df_mining.iloc[:, 2]
    mining_df["Fuente"] = "MiningKW"
    mining_df["ABA Rank"] = [None] * len(df_mining)

    master_raw = pd.concat([cust_df, comp_df, mining_df],
                           axis=0, ignore_index=True)

    return master_raw


def build_master_deduplicated(excel_data: pd.ExcelFile) -> pd.DataFrame:
    df_raw = build_master_raw(excel_data)
    if df_raw is None or df_raw.empty:
        return pd.DataFrame()

    agg_dict = {
        "Search Volume": "max",
        "ASIN Click Share": "max",
        "Comp Click Share": "max",
        "Niche Click Share": "max",
        "Comp Depth": "max",
        "Niche Depth": "max",
        "Relevancy": "max",
        "ABA Rank": "max",
        "Fuente": lambda x: ", ".join(sorted(set(x.dropna())))
    }

    df_dedup = df_raw.groupby("Search Terms", as_index=False).agg(agg_dict)

    return df_dedup


def formatear_columnas_tabla(df: pd.DataFrame) -> pd.DataFrame:
    df_format = df.copy()

    for col in df_format.columns:
        if col in ["Search Volume", "ABA Rank"]:
            df_format[col] = df_format[col].apply(
                lambda x: f"{int(x):,}" if isinstance(x, (int, float)) and not pd.isna(
                    x) else ("NAF" if x is None else x)
            )
        elif "Click Share" in col:
            df_format[col] = df_format[col].apply(
                lambda x: f"{float(x) * 100:.2f}%" if isinstance(x, (int, float)
                                                                 ) and not pd.isna(x) else ("NAF" if x is None else x)
            )
        elif "Depth" in col or "Relevancy" in col:
            df_format[col] = df_format[col].apply(
                lambda x: f"{int(x)}" if isinstance(x, (int, float)) and not pd.isna(
                    x) else ("NAF" if x is None else x)
            )
        elif col == "Fuente":
            df_format[col] = df_format[col].fillna("NAF")

    return df_format
