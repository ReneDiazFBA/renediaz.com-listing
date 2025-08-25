# keywords/funcional_keywords_maestro.py
# Vista Maestra Raw — Unión completa sin deduplicar

import pandas as pd
import numpy as np
import streamlit as st


def build_master_raw(excel_data: pd.ExcelFile) -> pd.DataFrame:
    """
    Construye la vista cruda (raw) de las 3 hojas CustKW, CompKW, MiningKW sin deduplicar.
    """
    try:
        df_cust = excel_data.parse("CustKW", skiprows=2)
        df_comp = excel_data.parse("CompKW", skiprows=2)
        df_mining = excel_data.parse("MiningKW", skiprows=2)
    except Exception as e:
        st.error(f"Error al leer hojas del Excel: {e}")
        return pd.DataFrame()

    # --- CUSTKW ---
    cust = pd.DataFrame()
    cust["Search Terms"] = df_cust.iloc[:, 0]
    cust["Search Volume"] = df_cust.iloc[:, 15]
    cust["ASIN Click Share"] = df_cust.iloc[:, 1]
    cust["Comp Click Share"] = None
    cust["Niche Click Share"] = None
    cust["Comp Depth"] = None
    cust["Niche Depth"] = None
    cust["Relevancy"] = None
    cust["ABA Rank"] = df_cust.iloc[:, 14]
    cust["Fuente"] = "CustKW"

    # --- COMPKW ---
    comp = pd.DataFrame()
    comp["Search Terms"] = df_comp.iloc[:, 0]
    comp["Search Volume"] = df_comp.iloc[:, 8]
    comp["ASIN Click Share"] = None
    comp["Comp Click Share"] = df_comp.iloc[:, 2]
    comp["Niche Click Share"] = None
    comp["Comp Depth"] = df_comp.iloc[:, 5]
    comp["Niche Depth"] = None
    comp["Relevancy"] = None
    comp["ABA Rank"] = df_comp.iloc[:, 7]  # Columna H (índice 7)
    comp["Fuente"] = "CompKW"

    # --- MININGKW ---
    mining = pd.DataFrame()
    mining["Search Terms"] = df_mining.iloc[:, 0]
    mining["Search Volume"] = df_mining.iloc[:, 5]
    mining["ASIN Click Share"] = None
    mining["Comp Click Share"] = None
    mining["Niche Click Share"] = df_mining.iloc[:, 15]
    mining["Comp Depth"] = None
    mining["Niche Depth"] = df_mining.iloc[:, 12]
    mining["Relevancy"] = df_mining.iloc[:, 2]
    mining["ABA Rank"] = None
    mining["Fuente"] = "MiningKW"

    # Concatenar todo
    df = pd.concat([cust, comp, mining], ignore_index=True)

    # --- Limpieza: aplicar regla de valores ---
    columnas_numericas = [
        "Search Volume",
        "ASIN Click Share",
        "Comp Click Share",
        "Niche Click Share",
        "Comp Depth",
        "Niche Depth",
        "Relevancy",
        "ABA Rank"
    ]

    for col in columnas_numericas:
        df[col] = df[col].apply(lambda x: (
            np.nan if isinstance(x, str) and str(x).strip() == "" else
            0 if x == 0 else
            x
        ))

    return df
