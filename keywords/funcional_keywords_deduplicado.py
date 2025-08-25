# keywords/funcional_keywords_deduplicado.py
# Construye tabla Maestra Deduplicada a partir de CustKW, CompKW y MiningKW

import pandas as pd
import streamlit as st


def build_master_deduped(excel_data: pd.ExcelFile) -> pd.DataFrame:
    try:
        df_cust = excel_data.parse("CustKW", skiprows=2)
        df_comp = excel_data.parse("CompKW", skiprows=2)
        df_mining = excel_data.parse("MiningKW", skiprows=2)
    except Exception as e:
        st.error(f"Error al leer hojas del Excel: {e}")
        return pd.DataFrame()

    # 1. CustKW
    cust_df = pd.DataFrame()
    cust_df["Search Terms"] = df_cust.iloc[:, 0]
    cust_df["Search Volume"] = df_cust.iloc[:, 15]
    cust_df["ASIN Click Share"] = df_cust.iloc[:, 1]
    cust_df["ABA Rank"] = df_cust.iloc[:, 14]
    cust_df["Fuente"] = "CustKW"

    # 2. CompKW
    comp_df = pd.DataFrame()
    comp_df["Search Terms"] = df_comp.iloc[:, 0]
    comp_df["Search Volume"] = df_comp.iloc[:, 8]
    comp_df["Comp Click Share"] = df_comp.iloc[:, 2]
    comp_df["Comp Depth"] = df_comp.iloc[:, 5]
    comp_df["ABA Rank"] = df_comp.iloc[:, 7]
    comp_df["Fuente"] = "CompKW"

    # 3. MiningKW
    mining_df = pd.DataFrame()
    mining_df["Search Terms"] = df_mining.iloc[:, 0]
    mining_df["Search Volume"] = df_mining.iloc[:, 5]
    mining_df["Relevancy"] = df_mining.iloc[:, 2]
    mining_df["Niche Depth"] = df_mining.iloc[:, 12]
    mining_df["Niche Click Share"] = df_mining.iloc[:, 15]
    mining_df["Fuente"] = "MiningKW"

    # Unir las tres
    full_df = pd.concat([cust_df, comp_df, mining_df],
                        axis=0, ignore_index=True)

    # Agrupar por Search Terms, consolidar valores
    def consolidar(grupo):
        resultado = {}
        resultado["Search Terms"] = grupo["Search Terms"].iloc[0]
        resultado["Search Volume"] = grupo["Search Volume"].max(skipna=True)
        resultado["ASIN Click Share"] = grupo.get("ASIN Click Share", pd.Series(
        )).dropna().max() if "ASIN Click Share" in grupo else None
        resultado["Comp Click Share"] = grupo.get("Comp Click Share", pd.Series(
        )).dropna().max() if "Comp Click Share" in grupo else None
        resultado["Niche Click Share"] = grupo.get("Niche Click Share", pd.Series(
        )).dropna().max() if "Niche Click Share" in grupo else None
        resultado["Comp Depth"] = grupo.get(
            "Comp Depth", pd.Series()).dropna().max() if "Comp Depth" in grupo else None
        resultado["Niche Depth"] = grupo.get(
            "Niche Depth", pd.Series()).dropna().max() if "Niche Depth" in grupo else None
        resultado["Relevancy"] = grupo.get(
            "Relevancy", pd.Series()).dropna().max() if "Relevancy" in grupo else None
        resultado["ABA Rank"] = grupo["ABA Rank"].max(skipna=True)
        resultado["Fuente"] = ",".join(
            sorted(grupo["Fuente"].dropna().unique()))
        return pd.Series(resultado)

    dedup = full_df.groupby("Search Terms", as_index=False).apply(consolidar)

    # Reordenar columnas
    final_cols = [
        "Search Terms", "Search Volume",
        "ASIN Click Share", "Comp Click Share", "Niche Click Share",
        "Comp Depth", "Niche Depth", "Relevancy",
        "ABA Rank", "Fuente"
    ]
    dedup = dedup[final_cols]

    return dedup
