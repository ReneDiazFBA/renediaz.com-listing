# keywords/funcional_keywords_deduplicado.py
# Construcción Maestra Raw de keywords (sin deduplicar)

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

    # --- CustKW ---
    cust_df = pd.DataFrame()
    cust_df["Search Terms"] = df_cust.iloc[:, 0]
    cust_df["Search Volume"] = df_cust.iloc[:, 15]
    cust_df["ASIN Click Share"] = df_cust.iloc[:, 1]
    cust_df["Comp Click Share"] = None
    cust_df["Niche Click Share"] = None
    cust_df["Comp Depth"] = None
    cust_df["Niche Depth"] = None
    cust_df["Relevancy"] = None
    cust_df["ABA Rank"] = df_cust.iloc[:, 14]
    cust_df["Fuente"] = "CustKW"

    # --- CompKW ---
    comp_df = pd.DataFrame()
    comp_df["Search Terms"] = df_comp.iloc[:, 0]
    comp_df["Search Volume"] = df_comp.iloc[:, 8]
    comp_df["ASIN Click Share"] = None
    comp_df["Comp Click Share"] = df_comp.iloc[:, 2]
    comp_df["Niche Click Share"] = None
    comp_df["Comp Depth"] = df_comp.iloc[:, 5]
    comp_df["Niche Depth"] = None
    comp_df["Relevancy"] = None
    comp_df["ABA Rank"] = df_comp.iloc[:,
                                       14] if df_comp.shape[1] > 14 else None
    comp_df["Fuente"] = "CompKW"

    # --- MiningKW ---
    mining_df = pd.DataFrame()
    mining_df["Search Terms"] = df_mining.iloc[:, 0]
    mining_df["Search Volume"] = df_mining.iloc[:, 5]
    mining_df["ASIN Click Share"] = None
    mining_df["Comp Click Share"] = None
    mining_df["Niche Click Share"] = df_mining.iloc[:, 15]
    mining_df["Comp Depth"] = None
    mining_df["Niche Depth"] = df_mining.iloc[:, 12]
    mining_df["Relevancy"] = df_mining.iloc[:, 2]
    mining_df["ABA Rank"] = None
    mining_df["Fuente"] = "MiningKW"

    df_final = pd.concat([cust_df, comp_df, mining_df], ignore_index=True)

    # Truncar % y formatear miles
    for col in ["ASIN Click Share", "Comp Click Share", "Niche Click Share"]:
        if col in df_final.columns:
            df_final[col] = df_final[col].apply(
                lambda x: f"{float(x)*100:.2f}%" if pd.notnull(x) else None
            )

    for col in ["Search Volume", "Comp Depth", "Niche Depth", "ABA Rank"]:
        if col in df_final.columns:
            df_final[col] = df_final[col].apply(
                lambda x: f"{int(x):,}" if pd.notnull(
                    x) and isinstance(x, (int, float)) else None
            )

    return df_final
