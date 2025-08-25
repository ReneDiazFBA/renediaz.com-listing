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

    # Utilidad para obtener columna numérica o dejar como None si no aplica
    def safe_numeric(series):
        return pd.to_numeric(series, errors="coerce")

    def nan_if_applicable(df, idx, apply=True):
        if not apply:
            return [None] * len(df)
        return safe_numeric(df.iloc[:, idx])

    # ========== CustKW ==========
    cust = pd.DataFrame()
    cust["Search Terms"] = df_cust.iloc[:, 0].astype(str).str.strip()
    cust["Search Volume"] = nan_if_applicable(df_cust, 15, apply=True)
    cust["ABA Rank"] = nan_if_applicable(df_cust, 14, apply=True)
    cust["ASIN Click Share"] = nan_if_applicable(df_cust, 1, apply=True)
    cust["Comp Click Share"] = [None] * len(df_cust)
    cust["Comp Depth"] = [None] * len(df_cust)
    cust["Niche Click Share"] = [None] * len(df_cust)
    cust["Niche Depth"] = [None] * len(df_cust)
    cust["Relevancy"] = [None] * len(df_cust)
    cust["Fuente"] = "CustKW"

    # ========== CompKW ==========
    comp = pd.DataFrame()
    comp["Search Terms"] = df_comp.iloc[:, 0].astype(str).str.strip()
    comp["Search Volume"] = nan_if_applicable(df_comp, 8, apply=True)
    comp["ABA Rank"] = nan_if_applicable(df_comp, 7, apply=True)
    comp["ASIN Click Share"] = [None] * len(df_comp)
    comp["Comp Click Share"] = nan_if_applicable(df_comp, 2, apply=True)
    comp["Comp Depth"] = nan_if_applicable(df_comp, 5, apply=True)
    comp["Niche Click Share"] = [None] * len(df_comp)
    comp["Niche Depth"] = [None] * len(df_comp)
    comp["Relevancy"] = [None] * len(df_comp)
    comp["Fuente"] = "CompKW"

    # ========== MiningKW ==========
    mining = pd.DataFrame()
    mining["Search Terms"] = df_mining.iloc[:, 0].astype(str).str.strip()
    mining["Search Volume"] = nan_if_applicable(df_mining, 5, apply=True)
    mining["ABA Rank"] = [None] * len(df_mining)
    mining["ASIN Click Share"] = [None] * len(df_mining)
    mining["Comp Click Share"] = [None] * len(df_mining)
    mining["Comp Depth"] = [None] * len(df_mining)
    mining["Niche Click Share"] = nan_if_applicable(df_mining, 15, apply=True)
    mining["Niche Depth"] = nan_if_applicable(df_mining, 12, apply=True)
    mining["Relevancy"] = nan_if_applicable(df_mining, 2, apply=True)
    mining["Fuente"] = "MiningKW"

    # Unir todo en orden correcto
    df_raw = pd.concat([cust, comp, mining], ignore_index=True)[[
        "Search Terms", "Search Volume", "ABA Rank", "ASIN Click Share",
        "Comp Click Share", "Comp Depth", "Niche Click Share", "Niche Depth",
        "Relevancy", "Fuente"
    ]]

    # Truncar shares (%)
    for col in ["ASIN Click Share", "Comp Click Share", "Niche Click Share"]:
        df_raw[col] = df_raw[col].apply(
            lambda x: np.floor(x * 10000) / 100 if isinstance(x, float) else x
        )

    return df_raw
