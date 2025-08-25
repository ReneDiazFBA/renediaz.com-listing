# keywords/app_keywords_deduplicado.py

import streamlit as st
import pandas as pd
from typing import Optional
from utils.nav_utils import render_subnav
from keywords.funcional_keywords_deduplicado import build_master_raw, formatear_columnas_tabla


def mostrar_keywords_deduplicado(excel_data: Optional[pd.ExcelFile] = None):
    """
    Contenedor visual para vista Maestra Deduplicada.
    """
    st.markdown("### Keywords — Maestra deduplicada")
    st.caption(
        "Unificación y deduplicación inteligente de términos provenientes de todas las fuentes.")

    secciones = {
        "raw": ("Maestra Raw", "raw"),
        "deduplicado": ("Maestra Deduplicada", "dedup")
    }

    subvista = render_subnav(default_key="raw", secciones=secciones)
    st.divider()

    if excel_data is None:
        st.warning("Primero debes subir un archivo en la sección Datos.")
        return

    if subvista == "raw":
        st.markdown("#### Maestra Raw")
        st.caption(
            "Unión completa de todas las fuentes (CustKW, CompKW, MiningKW) sin deduplicar.")

        df_raw = build_master_raw(excel_data)

        st.markdown(f"**Total Registros: {len(df_raw):,}**")
        from keywords.funcional_keywords_deduplicado import formatear_columnas_tabla
        st.dataframe(formatear_columnas_tabla(
            df_raw), use_container_width=True)

    elif subvista == "deduplicado":
        from keywords.funcional_keywords_deduplicado import build_master_deduplicated
        st.markdown("#### Maestra Deduplicada")
        st.caption("Versión deduplicada consolidando métricas y fuentes comunes.")

        df_dedup = build_master_deduplicated(excel_data)

        if df_dedup is None or df_dedup.empty:
            st.error("No se pudo construir la vista deduplicada.")
            return

        st.markdown(f"**Total Registros: {len(df_dedup):,}**")
        from keywords.funcional_keywords_deduplicado import formatear_columnas_tabla
        st.dataframe(formatear_columnas_tabla(
            df_dedup), use_container_width=True)
