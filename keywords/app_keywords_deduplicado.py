# keywords/app_keywords_deduplicado.py

import streamlit as st
import pandas as pd
from typing import Optional
from utils.nav_utils import render_subnav
from keywords.funcional_keywords_maestro import build_master_raw


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
        st.dataframe(df_raw, use_container_width=True)

    elif subvista == "deduplicado":
        st.markdown("#### Maestra Deduplicada")
        st.caption(
            "Versión deduplicada consolidando métricas y fuentes (en construcción).")
        st.info("⚠️ Esta vista está en desarrollo.")
