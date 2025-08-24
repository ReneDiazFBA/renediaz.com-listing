# keywords/app_keywords_referencial.py
# Reverse ASIN Referencial (CustKW)

import os
import pandas as pd
import streamlit as st
from typing import Optional


EXCEL_DISK_PATH = os.path.join("data", "raw", "optimizacion_listing.xlsx")


def _obtener_excel(excel_data: Optional[pd.ExcelFile]) -> Optional[pd.ExcelFile]:
    if isinstance(excel_data, pd.ExcelFile):
        return excel_data
    if "excel_data" in st.session_state and isinstance(st.session_state.excel_data, pd.ExcelFile):
        return st.session_state.excel_data
    if os.path.exists(EXCEL_DISK_PATH):
        try:
            return pd.ExcelFile(EXCEL_DISK_PATH)
        except Exception as e:
            st.error(f"Error al abrir el Excel desde disco: {e}")
            return None
    st.error("No se encontró archivo Excel cargado. Ve a la sección Datos y súbelo.")
    return None


def _trunc_two_decimals(x: float) -> str:
    try:
        v = int(float(x) * 10000) / 100  # truncado
        return f"{v:.2f}%"
    except Exception:
        return "—"


def mostrar_tabla_referencial(excel_data: Optional[pd.ExcelFile] = None, sheet_name: str = "CustKW"):
    xl = _obtener_excel(excel_data)
    if xl is None:
        return

    try:
        base = xl.parse(sheet_name, header=None)
        df = base.iloc[2:, [0, 15, 1, 14]].copy()
        df.columns = ["Search Terms", "Search Volume",
                      "ASIN Click Share", "ABA Rank"]
    except Exception as e:
        st.error(f"No se pudo leer la hoja '{sheet_name}': {e}")
        return

    df = df.dropna(subset=["Search Terms"]).reset_index(drop=True)

    for c in ["Search Volume", "ABA Rank", "ASIN Click Share"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df["ASIN Click Share"] = df["ASIN Click Share"].map(
        lambda x: _trunc_two_decimals(x) if pd.notna(x) else "—")
    df["Search Volume"] = df["Search Volume"].map(
        lambda x: f"{int(x):,}" if pd.notna(x) else "—")
    df["ABA Rank"] = df["ABA Rank"].map(
        lambda x: f"{int(x):,}" if pd.notna(x) else "—")

    df = df[["Search Terms", "Search Volume", "ASIN Click Share", "ABA Rank"]]

    st.markdown("#### Reverse ASIN Listing")
    st.markdown(f"**Total Registros:** {len(df)}")
    st.dataframe(df, use_container_width=True)
