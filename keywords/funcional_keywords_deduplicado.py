# keywords/funcional_keywords_deduplicado.py
# Construye la tabla RAW consolidada y deduplicada desde CustKW, CompKW, MiningKW

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

    # CustKW
    cust = pd.DataFrame()
    cust["Search Terms"] = df_cust.iloc[:, 0]
    cust["Search Volume"] = df_cust.iloc[:, 15]
    cust["ASIN Click Share"] = df_cust.iloc[:, 1]
    cust["Comp Click Share"] = np.nan
    cust["Niche Click Share"] = np.nan
    cust["Comp Depth"] = np.nan
    cust["Niche Depth"] = np.nan
    cust["Relevancy"] = np.nan
    cust["ABA Rank"] = df_cust.iloc[:, 14]
    cust["Fuente"] = "CustKW"

    # CompKW
    comp = pd.DataFrame()
    comp["Search Terms"] = df_comp.iloc[:, 0]
    comp["Search Volume"] = df_comp.iloc[:, 8]
    comp["ASIN Click Share"] = np.nan
    comp["Comp Click Share"] = df_comp.iloc[:, 2]
    comp["Niche Click Share"] = np.nan
    comp["Comp Depth"] = df_comp.iloc[:, 5]
    comp["Niche Depth"] = np.nan
    comp["Relevancy"] = np.nan
    comp["ABA Rank"] = df_comp.iloc[:, 7]
    comp["Fuente"] = "CompKW"

    # MiningKW
    mining = pd.DataFrame()
    mining["Search Terms"] = df_mining.iloc[:, 0]
    mining["Search Volume"] = df_mining.iloc[:, 5]
    mining["ASIN Click Share"] = np.nan
    mining["Comp Click Share"] = np.nan
    mining["Niche Click Share"] = df_mining.iloc[:, 15]
    mining["Comp Depth"] = np.nan
    mining["Niche Depth"] = df_mining.iloc[:, 12]
    mining["Relevancy"] = df_mining.iloc[:, 2]
    mining["ABA Rank"] = np.nan
    mining["Fuente"] = "MiningKW"

    master_raw = pd.concat([cust, comp, mining], ignore_index=True)

    # Reemplazar ceros explícitos por 0 y vacíos por np.nan. Donde NO aplica, se pone 'NAF'
    for col in master_raw.columns:
        if col in ["ASIN Click Share", "Comp Click Share", "Niche Click Share",
                   "Comp Depth", "Niche Depth", "Relevancy", "ABA Rank", "Search Volume"]:
            if col in ["ASIN Click Share"]:
                master_raw.loc[master_raw["Fuente"] != "CustKW", col] = "NAF"
            elif col in ["Comp Click Share", "Comp Depth"]:
                master_raw.loc[master_raw["Fuente"] != "CompKW", col] = "NAF"
            elif col in ["Niche Click Share", "Niche Depth", "Relevancy"]:
                master_raw.loc[master_raw["Fuente"] != "MiningKW", col] = "NAF"
            elif col in ["ABA Rank"]:
                master_raw.loc[master_raw["Fuente"] == "MiningKW", col] = "NAF"

    return master_raw


def build_master_deduplicated(excel_data: pd.ExcelFile) -> pd.DataFrame:
    df_raw = build_master_raw(excel_data)
    if df_raw.empty:
        return pd.DataFrame()

    def combinar_fuentes(x):
        return ",".join(sorted(set(",".join(x).split(","))))

    def pick_first_valid(x):
        vals = x[(x != "NAF") & (pd.notna(x))]
        return vals.iloc[0] if not vals.empty else "NAF"

    def pick_max_valid(x):
        vals = pd.to_numeric(x[(x != "NAF") & (pd.notna(x))], errors="coerce")
        return int(np.nanmax(vals)) if not vals.empty else "NAF"

    grouped = df_raw.groupby("Search Terms").agg({
        "Search Volume": pick_max_valid,
        "ASIN Click Share": pick_first_valid,
        "Comp Click Share": pick_first_valid,
        "Niche Click Share": pick_first_valid,
        "Comp Depth": pick_first_valid,
        "Niche Depth": pick_first_valid,
        "Relevancy": pick_first_valid,
        "ABA Rank": pick_max_valid,
        "Fuente": combinar_fuentes
    }).reset_index()

    return grouped


def formatear_columnas_tabla(df: pd.DataFrame) -> pd.DataFrame:
    df_format = df.copy()

    for col in df_format.columns:
        if col in ["ASIN Click Share", "Comp Click Share", "Niche Click Share"]:
            df_format[col] = df_format[col].apply(
                lambda x: f"{np.floor(x*10000)/100:.2f}%" if isinstance(x,
                                                                        (float, int)) else x
            )
        elif col in ["Search Volume", "ABA Rank"]:
            df_format[col] = df_format[col].apply(
                lambda x: f"{int(x):,}" if isinstance(x, (float, int)) else x
            )
    return df_format
