# keywords/funcional_keywords_deduplicado.py

import pandas as pd
import streamlit as st


def construir_tabla_maestra_raw(excel_data: pd.ExcelFile) -> pd.DataFrame:
    try:
        df_cust = excel_data.parse("CustKW", skiprows=2)
        df_comp = excel_data.parse("CompKW", skiprows=2)
        df_mining = excel_data.parse("MiningKW", skiprows=2)
    except Exception as e:
        st.error(f"No se pudieron leer las hojas: {e}")
        return pd.DataFrame()

    cust = pd.DataFrame()
    cust["Search Terms"] = df_cust.iloc[:, 0]
    cust["Search Volume"] = df_cust.iloc[:, 15]
    cust["ASIN Click Share"] = df_cust.iloc[:, 1]
    cust["ABA Rank"] = df_cust.iloc[:, 14]
    cust["Fuente"] = "CustKW"

    comp = pd.DataFrame()
    comp["Search Terms"] = df_comp.iloc[:, 0]
    comp["Search Volume"] = df_comp.iloc[:, 8]
    comp["Comp Click Share"] = df_comp.iloc[:, 2]
    comp["Comp Depth"] = df_comp.iloc[:, 5]
    comp["ABA Rank"] = df_comp.iloc[:, 13]  # Incluida también
    comp["Fuente"] = "CompKW"

    mining = pd.DataFrame()
    mining["Search Terms"] = df_mining.iloc[:, 0]
    mining["Search Volume"] = df_mining.iloc[:, 5]
    mining["Niche Click Share"] = df_mining.iloc[:, 15]
    mining["Niche Depth"] = df_mining.iloc[:, 12]
    mining["Relevancy"] = df_mining.iloc[:, 2]
    mining["Fuente"] = "MiningKW"

    df_total = pd.concat([cust, comp, mining], ignore_index=True)
    return df_total
