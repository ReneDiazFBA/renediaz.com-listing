# keywords/funcional_keywords_maestro.py
# Construcción de la tabla maestra RAW sin deduplicar

import pandas as pd
import streamlit as st


def build_master_raw(excel_data: pd.ExcelFile) -> pd.DataFrame:
    """
    Une todas las hojas relevantes (CustKW, CompKW, MiningKW) sin deduplicar,
    asigna valores vacíos o None según relevancia por hoja.
    """
    try:
        df_cust = excel_data.parse("CustKW", skiprows=2)
        df_comp = excel_data.parse("CompKW", skiprows=2)
        df_mining = excel_data.parse("MiningKW", skiprows=2)
    except Exception as e:
        st.error(f"Error al leer hojas del Excel: {e}")
        return pd.DataFrame()

    # CUSTKW — Search Terms (A), ASIN Click Share (B), ABA Rank (O), Search Volume (P)
    df1 = pd.DataFrame()
    df1["Search Terms"] = df_cust.iloc[:, 0]
    df1["Search Volume"] = df_cust.iloc[:, 15]
    df1["ASIN Click Share"] = df_cust.iloc[:, 1]
    df1["ABA Rank"] = df_cust.iloc[:, 14]
    df1["Fuente"] = "CustKW"

    # Columnas que no aplican en esta fuente → None
    df1["Comp Click Share"] = None
    df1["Comp Depth"] = None
    df1["Niche Click Share"] = None
    df1["Niche Depth"] = None
    df1["Relevancy"] = None

    # COMPKW — Search Terms (A), Comp Click Share (C), Comp Depth (F), Search Volume (I), ABA Rank (H)
    df2 = pd.DataFrame()
    df2["Search Terms"] = df_comp.iloc[:, 0]
    df2["Search Volume"] = df_comp.iloc[:, 8]
    df2["Comp Click Share"] = df_comp.iloc[:, 2]
    df2["Comp Depth"] = df_comp.iloc[:, 5]
    df2["ABA Rank"] = df_comp.iloc[:, 7]  # ABA Rank de CompKW: columna H
    df2["Fuente"] = "CompKW"

    # Columnas que no aplican → None
    df2["ASIN Click Share"] = None
    df2["Niche Click Share"] = None
    df2["Niche Depth"] = None
    df2["Relevancy"] = None

    # MININGKW — Search Terms (A), Relevancy (C), Search Volume (F), Niche Depth (M), Niche Click Share (P)
    df3 = pd.DataFrame()
    df3["Search Terms"] = df_mining.iloc[:, 0]
    df3["Search Volume"] = df_mining.iloc[:, 5]
    df3["Relevancy"] = df_mining.iloc[:, 2]
    df3["Niche Depth"] = df_mining.iloc[:, 12]
    df3["Niche Click Share"] = df_mining.iloc[:, 15]
    df3["Fuente"] = "MiningKW"

    # Columnas que no aplican → None
    df3["ASIN Click Share"] = None
    df3["Comp Click Share"] = None
    df3["Comp Depth"] = None
    df3["ABA Rank"] = None

    # Unir todo
    df_final = pd.concat([df1, df2, df3], ignore_index=True)

    # Reordenar columnas
    columnas_orden = [
        "Search Terms",
        "Search Volume",
        "ASIN Click Share",
        "Comp Click Share",
        "Niche Click Share",
        "Comp Depth",
        "Niche Depth",
        "Relevancy",
        "ABA Rank",
        "Fuente"
    ]
    df_final = df_final[columnas_orden]

    return df_final
