# keywords/app_keywords_mining.py
# Mining de Keywords (MiningKW) — con filtros: volumen, relevancia, niche depth

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
        v = int(float(x) * 10000) / 100
        return f"{v:.2f}%"
    except Exception:
        return "—"


def mostrar_tabla_mining(excel_data: Optional[pd.ExcelFile] = None, sheet_name: str = "MiningKW"):
    xl = _obtener_excel(excel_data)
    if xl is None:
        return

    try:
        base = xl.parse(sheet_name, header=None)
        df = base.iloc[2:, [0, 5, 15, 12, 2]].copy()
        df.columns = ["Search Terms", "Search Volume",
                      "Niche Click Share", "Niche Depth", "Relevancy"]
        df_total = df.copy()
    except Exception as e:
        st.error(f"No se pudo leer la hoja '{sheet_name}': {e}")
        return

    df = df.dropna(subset=["Search Terms"]).reset_index(drop=True)

    for c in ["Search Volume", "Niche Click Share", "Niche Depth", "Relevancy"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    col1, col2, col3 = st.columns(3)
    with col1:
        vol_min_input = st.text_input(
            "Search Volume mínimo", placeholder="Ej: 5000", key="vol_min_mining")
    with col2:
        share_min_input = st.text_input(
            "Click Share mínimo (%)", placeholder="Ej: 5", key="click_min_mining")
    with col3:
        relevancia_min_input = st.text_input(
            "Relevancia mínima (%)", placeholder="Ej: 40", key="rel_min_mining")

    col4 = st.columns(1)[0]
    with col4:
        depth_min_input = st.text_input(
            "Niche Depth mínimo", placeholder="Ej: 500", key="depth_min_mining")

    vol_min = int(vol_min_input) if vol_min_input.strip().isdigit() else None
    share_min = float(share_min_input) if share_min_input.strip().replace(
        ".", "", 1).isdigit() else None
    relevancia_min = float(relevancia_min_input) if relevancia_min_input.strip(
    ).replace(".", "", 1).isdigit() else None
    depth_min = int(
        depth_min_input) if depth_min_input.strip().isdigit() else None

    df_filtrado = df.copy()
    if vol_min is not None:
        df_filtrado = df_filtrado[df_filtrado["Search Volume"] >= vol_min]
    if share_min is not None:
        df_filtrado = df_filtrado[df_filtrado["Niche Click Share"] >= (
            share_min / 100)]
    if relevancia_min is not None:
        df_filtrado = df_filtrado[df_filtrado["Relevancy"] >= (
            relevancia_min / 100)]
    if depth_min is not None:
        df_filtrado = df_filtrado[df_filtrado["Niche Depth"] >= depth_min]

    st.markdown("#### Mining de Keywords")
    st.markdown(f"**Total Registros:** {len(df_filtrado)}")

    df_filtrado["Niche Click Share"] = df_filtrado["Niche Click Share"].map(
        lambda x: _trunc_two_decimals(x) if pd.notna(x) else "—"
    )
    df_filtrado["Search Volume"] = df_filtrado["Search Volume"].map(
        lambda x: f"{int(x):,}" if pd.notna(x) else "—"
    )
    df_filtrado["Niche Depth"] = df_filtrado["Niche Depth"].map(
        lambda x: f"{int(x):,}" if pd.notna(x) else "—"
    )
    df_filtrado["Relevancy"] = df_filtrado["Relevancy"].map(
        lambda x: f"{x:.2f}" if pd.notna(x) else "—"
    )

    df_filtrado = df_filtrado[
        ["Search Terms", "Search Volume",
            "Niche Click Share", "Niche Depth", "Relevancy"]
    ]
    st.dataframe(df_filtrado, use_container_width=True)
