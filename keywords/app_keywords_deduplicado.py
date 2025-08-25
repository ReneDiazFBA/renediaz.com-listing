# keywords/app_keywords_deduplicado.py
# ReneDiaz.com Dashboard — Módulo Keywords Maestra Deduplicada (Raw y luego deduplicado)

import streamlit as st
import pandas as pd
from typing import Optional
from utils.nav_utils import render_subnav
from keywords.funcional_keywords_deduplicado import build_master_raw


def mostrar_keywords_deduplicado(excel_data: Optional[pd.ExcelFile] = None):
    st.markdown("### Keywords — Maestra deduplicada")
    st.caption(
        "Este módulo consolida todas las fuentes de keywords (CustKW, CompKW, MiningKW) para análisis estratégico.")

    secciones = {
        "raw": ("Maestra Raw", None),
        "dedup": ("Maestra Deduplicada", None),
    }

    active = render_subnav("raw", secciones)
    st.divider()

    if excel_data is None:
        st.warning("Primero debes subir un archivo en la sección Datos.")
        return

    if active == "raw":
        st.markdown("**Maestra Raw**")
        st.caption(
            "Unión completa de todas las fuentes (CustKW, CompKW, MiningKW) sin deduplicar.")

        df = build_master_raw(excel_data)

        st.markdown(
            f"<div style='font-size:20px; font-weight:bold;'>Total Registros: {len(df):,}</div>",
            unsafe_allow_html=True
        )

        st.dataframe(df, use_container_width=True)

    elif active == "dedup":
        st.markdown("**Maestra Deduplicada**")
        st.caption("Consolidación deduplicada de las fuentes. [Próximamente]")
        st.info(
            "Esta vista está en desarrollo. Pronto podrás analizar keywords consolidadas.")
