# keywords/funcional_keywords_deduplicado.py
# Construcción de tabla maestra raw para módulo deduplicado

import pandas as pd
import streamlit as st


def construir_tabla_maestra_raw(excel_data: pd.ExcelFile) -> pd.DataFrame:
    try:
        df_cust = excel_data.parse("CustKW", skiprows=2)
        df_comp = excel_data.parse("CompKW", skiprows=2)
        df_mining = excel_data.parse("MiningKW", skiprows=2)
    except Exception as e:
        st.error(f"Error al leer hojas del Excel: {e}")
        return pd.DataFrame()

    tablas = []

    # CustKW
    try:
        cust_df = pd.DataFrame()
        cust_df["Search Terms"] = df_cust.iloc[:, 0]
        cust_df["Search Volume"] = df_cust.iloc[:, 15]
        cust_df["ASIN Click Share"] = df_cust.iloc[:, 1]
        cust_df["ABA Rank"] = df_cust.iloc[:, 14]
        cust_df["Fuente"] = "CustKW"
        tablas.append(cust_df)
    except Exception as e:
        st.warning(f"No se pudo cargar CustKW: {e}")

    # CompKW
    try:
        comp_df = pd.DataFrame()
        comp_df["Search Terms"] = df_comp.iloc[:, 0]
        comp_df["Search Volume"] = df_comp.iloc[:, 8]
        comp_df["Comp Click Share"] = df_comp.iloc[:, 2]
        comp_df["Comp Depth"] = df_comp.iloc[:, 5]
        comp_df["ABA Rank"] = df_comp.iloc[:,
                                           14] if df_comp.shape[1] > 14 else None
        comp_df["Fuente"] = "CompKW"
        tablas.append(comp_df)
    except Exception as e:
        st.warning(f"No se pudo cargar CompKW: {e}")

    # MiningKW
    try:
        mining_df = pd.DataFrame()
        mining_df["Search Terms"] = df_mining.iloc[:, 0]
        mining_df["Search Volume"] = df_mining.iloc[:, 5]
        mining_df["Niche Click Share"] = df_mining.iloc[:, 15]
        mining_df["Niche Depth"] = df_mining.iloc[:, 12]
        mining_df["Relevancy"] = df_mining.iloc[:, 2]
        mining_df["ABA Rank"] = None
        mining_df["Fuente"] = "MiningKW"
        tablas.append(mining_df)
    except Exception as e:
        st.warning(f"No se pudo cargar MiningKW: {e}")

    if not tablas:
        return pd.DataFrame()

    df_final = pd.concat(tablas, ignore_index=True)
    return df_final
