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

    # CustKW
    cust = pd.DataFrame()
    cust["Search Terms"] = df_cust.iloc[:, 0]
    cust["Search Volume"] = df_cust.iloc[:, 15]
    cust["ABA Rank"] = df_cust.iloc[:, 14]
    cust["ASIN Click Share"] = df_cust.iloc[:, 1].apply(
        lambda x: 0 if x == 0 else (np.nan if pd.isna(x) else x))
    cust["Comp Click Share"] = "NAF"
    cust["Niche Click Share"] = "NAF"
    cust["Comp Depth"] = "NAF"
    cust["Niche Depth"] = "NAF"
    cust["Relevancy"] = "NAF"
    cust["Fuente"] = "CustKW"

    # CompKW
    comp = pd.DataFrame()
    comp["Search Terms"] = df_comp.iloc[:, 0]
    comp["Search Volume"] = df_comp.iloc[:, 8]
    comp["ABA Rank"] = df_comp.iloc[:, 7]
    comp["ASIN Click Share"] = "NAF"
    comp["Comp Click Share"] = df_comp.iloc[:, 2].apply(
        lambda x: 0 if x == 0 else (np.nan if pd.isna(x) else x))
    comp["Niche Click Share"] = "NAF"
    comp["Comp Depth"] = df_comp.iloc[:, 5].apply(
        lambda x: 0 if x == 0 else (np.nan if pd.isna(x) else x))
    comp["Niche Depth"] = "NAF"
    comp["Relevancy"] = "NAF"
    comp["Fuente"] = "CompKW"

    # MiningKW
    mining = pd.DataFrame()
    mining["Search Terms"] = df_mining.iloc[:, 0]
    mining["Search Volume"] = df_mining.iloc[:, 5]
    mining["ABA Rank"] = "NAF"
    mining["ASIN Click Share"] = "NAF"
    mining["Comp Click Share"] = "NAF"
    mining["Niche Click Share"] = df_mining.iloc[:, 15].apply(
        lambda x: 0 if x == 0 else (np.nan if pd.isna(x) else x))
    mining["Comp Depth"] = "NAF"
    mining["Niche Depth"] = df_mining.iloc[:, 12].apply(
        lambda x: 0 if x == 0 else (np.nan if pd.isna(x) else x))
    mining["Relevancy"] = df_mining.iloc[:, 2].apply(
        lambda x: 0 if x == 0 else (np.nan if pd.isna(x) else x))
    mining["Fuente"] = "MiningKW"

    master_raw = pd.concat([cust, comp, mining], ignore_index=True)
    return master_raw


def build_master_deduplicated(excel_data: pd.ExcelFile) -> pd.DataFrame:
    df_raw = build_master_raw(excel_data)
    if df_raw.empty:
        return pd.DataFrame()

    def combinar_fuentes(x):
        return ",".join(sorted(set(",".join(x).split(","))))

    def pick_first_valid(x):
        vals = x[x != "NAF"].dropna()
        return vals.iloc[0] if not vals.empty else "NAF"

    def pick_max_valid(x):
        vals = pd.to_numeric(x[x != "NAF"], errors="coerce").dropna()
        return int(np.nanmax(vals)) if not vals.empty else "NAF"

    grouped = df_raw.groupby("Search Terms").agg({
        "Search Volume": pick_max_valid,
        "ASIN Click Share": pick_first_valid,
        "Comp Click Share": pick_first_valid,
        "Niche Click Share": pick_first_valid,
        "Comp Depth": pick_first_valid,
        "Niche Depth": pick_first_valid,
        "Relevancy": pick_first_valid,
        "Fuente": combinar_fuentes,
        "ABA Rank": pick_max_valid
    }).reset_index()

    return grouped


def formatear_columnas_tabla(df: pd.DataFrame) -> pd.DataFrame:
    df_format = df.copy()

    for col in df_format.columns:
        if col in ["ASIN Click Share", "Comp Click Share", "Niche Click Share"]:
            df_format[col] = df_format[col].apply(
                lambda x: f"{round(x * 100, 2)}%" if isinstance(x,
                                                                (int, float)) and not pd.isna(x) else x
            )
        elif col in ["Search Volume", "ABA Rank"]:
            df_format[col] = df_format[col].apply(
                lambda x: f"{int(x):,}" if isinstance(
                    x, (int, float)) and not pd.isna(x) else x
            )

    # Convertir valores None en 'NAF'
    df_format.replace({None: "NAF", np.nan: "NAF"}, inplace=True)

    return df_format
