# keywords/funcional_keywords_maestro.py
# Construcción de tabla maestra raw para módulo deduplicado

import pandas as pd
import numpy as np
import streamlit as st


def build_master_raw(excel_data: pd.ExcelFile) -> pd.DataFrame:
    """
    Construye la tabla consolidada raw a partir de CustKW, CompKW y MiningKW sin deduplicar.
    """

    try:
        df_cust = excel_data.parse("CustKW", skiprows=2)
        df_comp = excel_data.parse("CompKW", skiprows=2)
        df_mining = excel_data.parse("MiningKW", skiprows=2)
    except Exception as e:
        st.error(f"Error al leer hojas del Excel: {e}")
        return pd.DataFrame()

    def col(df, index, applies=True, numeric=False):
        if not applies:
            return np.nan
        serie = df.iloc[:, index]
        if numeric:
            return pd.to_numeric(serie, errors="coerce")
        return serie

    # === CustKW ===
    cust = pd.DataFrame()
    cust["Search Terms"] = col(df_cust, 0)
    cust["Search Volume"] = col(df_cust, 15, numeric=True)
    cust["ASIN Click Share"] = col(df_cust, 1, numeric=True)
    cust["ABA Rank"] = col(df_cust, 14, numeric=True)
    cust["Fuente"] = "CustKW"
    cust["Comp Click Share"] = np.nan
    cust["Comp Depth"] = np.nan
    cust["Niche Click Share"] = np.nan
    cust["Niche Depth"] = np.nan
    cust["Relevancy"] = np.nan

    # === CompKW ===
    comp = pd.DataFrame()
    comp["Search Terms"] = col(df_comp, 0)
    comp["Search Volume"] = col(df_comp, 8, numeric=True)
    comp["ASIN Click Share"] = np.nan
    comp["ABA Rank"] = col(df_comp, 7, numeric=True)
    comp["Fuente"] = "CompKW"
    comp["Comp Click Share"] = col(df_comp, 2, numeric=True)
    comp["Comp Depth"] = col(df_comp, 5, numeric=True)
    comp["Niche Click Share"] = np.nan
    comp["Niche Depth"] = np.nan
    comp["Relevancy"] = np.nan

    # === MiningKW ===
    mining = pd.DataFrame()
    mining["Search Terms"] = col(df_mining, 0)
    mining["Search Volume"] = col(df_mining, 5, numeric=True)
    mining["ASIN Click Share"] = np.nan
    mining["ABA Rank"] = np.nan
    mining["Fuente"] = "MiningKW"
    mining["Comp Click Share"] = np.nan
    mining["Comp Depth"] = np.nan
    mining["Niche Click Share"] = col(df_mining, 15, numeric=True)
    mining["Niche Depth"] = col(df_mining, 12, numeric=True)
    mining["Relevancy"] = col(df_mining, 2, numeric=True)

    # Unir todo
    df_raw = pd.concat([cust, comp, mining], ignore_index=True)

    # Limpiar strings
    df_raw["Search Terms"] = df_raw["Search Terms"].astype(str).str.strip()

    # Truncar Click Shares a 2 decimales
    for colname in ["ASIN Click Share", "Comp Click Share", "Niche Click Share"]:
        if colname in df_raw.columns:
            df_raw[colname] = (df_raw[colname] * 100).apply(
                lambda x: np.floor(x * 100) / 100 if pd.notnull(x) else np.nan
            )

    return df_raw
