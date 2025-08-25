# keywords/app_keywords_deduplicado.py
# ReneDiaz.com Dashboard — Módulo Keywords Deduplicado

import streamlit as st
import pandas as pd
from typing import Optional
from utils.nav_utils import render_subnav
from keywords.funcional_keywords_deduplicado import construir_tabla_maestra_raw


def mostrar_keywords_deduplicado(excel_data: Optional[pd.ExcelFile] = None):
    st.markdown("### Keywords — Maestra deduplicada")

    secciones = {
        "raw": ("Maestra Raw", None),
        "deduplicado": ("Maestra Deduplicada", None)
    }

    active = render_subnav("raw", secciones)
    st.divider()

    if active == "raw":
        st.subheader("Vista: Maestra Raw")
        st.caption(
            "Unión completa de todas las fuentes (CustKW, CompKW, MiningKW) sin deduplicar.")

        if excel_data is None:
            st.warning("Primero debes subir un archivo en la sección Datos.")
            return

        df = construir_tabla_maestra_raw(excel_data)
        if df.empty:
            st.error("No se pudo construir la tabla Raw.")
            return

        st.dataframe(df, use_container_width=True)
        st.success(f"{len(df):,} registros cargados.")

    elif active == "deduplicado":
        st.subheader("Vista: Maestra Deduplicada")
        st.info("Próximamente: lógica de deduplicación y consolidación.")
