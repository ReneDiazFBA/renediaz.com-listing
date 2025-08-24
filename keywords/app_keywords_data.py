# keywords/app_keywords_data.py
# Contenedor principal de navegación entre vistas de keywords

import streamlit as st
import pandas as pd
from typing import Optional
from utils.nav_utils import render_subnav_cascaron as render_subnav


def mostrar_keywords_data(excel_data: Optional[pd.ExcelFile] = None):
    """
    Contenedor principal de 'Tablas de origen' con navegación tipo header simplificada.
    """
    st.markdown("### Keywords — Tablas de origen")
    st.caption("Este módulo aloja las vistas de Reverse ASIN Referencial, Competidores y Mining. Navega por el menú superior.")

    secciones = {
        "referencial": ("Reverse ASIN Referencial", "CustKW"),
        "competidores": ("Reverse ASIN Competidores", "CompKW"),
        "mining": ("Mining de Keywords", "MiningKW")
    }

    qp = st.query_params
    active = qp.get("subview", ["referencial"])[0]

    render_subnav(active, secciones)
    st.divider()

    if active == "referencial":
        from keywords.app_keywords_referencial import mostrar_tabla_referencial
        mostrar_tabla_referencial(excel_data, sheet_name)
    elif active == "competidores":
        st.info("Reverse ASIN Competidores [pendiente]")
    elif active == "mining":
        st.info("Mining de Keywords [pendiente]")

    # Placeholder (sin cargar ningún módulo aún)
    label_visible, sheet_name = secciones.get(
        active, ("Vista no definida", None))
    st.info(f"Vista seleccionada: {label_visible}")
