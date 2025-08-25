##app_keywords_data.py
import streamlit as st
import pandas as pd
from typing import Optional

from keywords.app_keywords_referencial import mostrar_tabla_referencial
from keywords.app_keywords_competidores import mostrar_tabla_competidores
from keywords.app_keywords_mining import mostrar_tabla_mining
from keywords.app_keywords_deduplicado import mostrar_keywords_deduplicado
from keywords.app_keywords_estadistica import mostrar_keywords_estadistica
from utils.nav_utils import render_subnav


def mostrar_keywords_data(excel_data: Optional[pd.ExcelFile] = None):
    st.markdown("### Keywords — Navegación de submódulos")

    submodulo = st.radio(
        "Selecciona submódulo de Keywords:",
        ["Tablas de origen", "Maestra deduplicada", "Datos Estadísticos"],
        horizontal=True,
        key="kw_radio_submodulo"
    )

    st.divider()

    # Submódulo: TABLAS DE ORIGEN
    if submodulo == "Tablas de origen":
        st.markdown("### Keywords — Tablas de origen")

        secciones = {
            "referencial": ("Reverse ASIN Referencial", "CustKW"),
            "competidores": ("Reverse ASIN Competidores", "CompKW"),
            "mining": ("Mining de Keywords", "MiningKW"),
        }

        active = render_subnav("referencial", secciones)
        st.divider()

        if excel_data is None:
            st.warning("Primero debes subir un archivo en la sección Datos.")
            return

        if active == "referencial":
            mostrar_tabla_referencial(excel_data, sheet_name="CustKW")
        elif active == "competidores":
            mostrar_tabla_competidores(excel_data, sheet_name="CompKW")
        elif active == "mining":
            mostrar_tabla_mining(excel_data, sheet_name="MiningKW")

    # Submódulo: MAESTRA DEDUPLICADA
    elif submodulo == "Maestra deduplicada":
        st.markdown("### Keywords — Maestra deduplicada")
        if excel_data is None:
            st.warning("Primero debes subir un archivo en la sección Datos.")
            return
        mostrar_keywords_deduplicado(excel_data)

    # Submódulo: ESTADÍSTICA
    elif submodulo == "Datos Estadísticos":
        mostrar_keywords_estadistica(excel_data)
