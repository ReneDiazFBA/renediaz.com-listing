# keywords/funcional_keywords_maestro.py
# Consolidación RAW de todas las fuentes de keywords

import pandas as pd
import numpy as np
import streamlit as st


def build_master_raw(excel_data: pd.ExcelFile) -> pd.DataFrame:
    """
    Une todas las hojas de keywords (CustKW, CompKW, MiningKW) sin deduplicar,
    aplicando lógica estandarizada de columnas y vacíos.
    """
    try:
        df_cust = excel_data.parse("CustKW", skiprows=2)
        df_comp = excel_data.parse("CompKW", skiprows=2)
        df_mining = excel_data.parse("MiningKW", skiprows=2)
    except Exception as e:
        st.error(f"Error al leer hojas del Excel: {e}")
        return pd.DataFrame()

    # ---------------------------
    # Función robusta para limpiar columnas numéricas
    # ---------------------------
    def limpiar_columna(valor):
        if pd.isna(valor):
            return np.nan
        if isinstance(valor, str) and valor.strip() == "":
            return np.nan
        if valor == 0:
            return 0
        return valor

    # ---------------------------
    # CustKW
    # ---------------------------
    cust = pd.DataFrame()
    cust["Search Terms"] = df_cust.iloc[:, 0]
    cust["Search Volume"] = df_cust.iloc[:, 15].apply(limpiar_columna)
    cust["ASIN Click Share"] = df_cust.iloc[:, 1].apply(limpiar_columna)
    cust["Comp Click Share"] = None
    cust["Niche Click Share"] = None
    cust["Comp Depth"] = None
    cust["Niche Depth"] = None
    cust["Relevancy"] = None
    cust["ABA Rank"] = df_cust.iloc[:, 14].apply(limpiar_columna)
    cust["Fuente"] = "CustKW"

    # ---------------------------
    # CompKW
    # ---------------------------
    comp = pd.DataFrame()
    comp["Search Terms"] = df_comp.iloc[:, 0]
    comp["Search Volume"] = df_comp.iloc[:, 8].apply(limpiar_columna)
    comp["ASIN Click Share"] = None
    comp["Comp Click Share"] = df_comp.iloc[:, 2].apply(limpiar_columna)
    comp["Niche Click Share"] = None
    comp["Comp Depth"] = df_comp.iloc[:, 5].apply(limpiar_columna)
    comp["Niche Depth"] = None
    comp["Relevancy"] = None
    comp["ABA Rank"] = df_comp.iloc[:, 7].apply(limpiar_columna)
    comp["Fuente"] = "CompKW"

    # ---------------------------
    # MiningKW
    # ---------------------------
    mining = pd.DataFrame()
    mining["Search Terms"] = df_mining.iloc[:, 0]
    mining["Search Volume"] = df_mining.iloc[:, 5].apply(limpiar_columna)
    mining["ASIN Click Share"] = None
    mining["Comp Click Share"] = None
    mining["Niche Click Share"] = df_mining.iloc[:, 15].apply(limpiar_columna)
    mining["Comp Depth"] = None
    mining["Niche Depth"] = df_mining.iloc[:, 12].apply(limpiar_columna)
    mining["Relevancy"] = df_mining.iloc[:, 2].apply(limpiar_columna)
    mining["ABA Rank"] = None
    mining["Fuente"] = "MiningKW"

    # ---------------------------
    # Unir todo
    # ---------------------------
    df_final = pd.concat([cust, comp, mining], ignore_index=True)
    return df_final
