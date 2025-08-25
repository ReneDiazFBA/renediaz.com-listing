# keywords/app_keywords_data.py

import streamlit as st
import pandas as pd
from typing import Optional

from keywords.app_keywords_referencial import mostrar_tabla_referencial
from keywords.app_keywords_competidores import mostrar_tabla_competidores
from keywords.app_keywords_mining import mostrar_tabla_mining

# Este import es condicional (solo si el archivo existe con la función)
try:
    from keywords.app_keywords_deduplicado import mostrar_keywords_deduplicado
    _DEDUP_OK = True
except ImportError:
    _DEDUP_OK = False

from utils.nav_utils import render_subnav


def mostrar_keywords_data(excel_data: Optional[pd.ExcelFile] = None):
    st.markdown("### Keywords — Tablas de origen")

    secciones = {
        "referencial": ("Reverse ASIN Referencial", "CustKW"),
        "competidores": ("Reverse ASIN Competidores", "CompKW"),
        "mining": ("Mining de Keywords", "MiningKW"),
        "deduplicado": ("Maestra deduplicada", None)
    }

    active = render_subnav("referencial", secciones)
    st.divider()

    if active == "referencial":
        mostrar_tabla_referencial(excel_data, sheet_name="CustKW")
    elif active == "competidores":
        mostrar_tabla_competidores(excel_data, sheet_name="CompKW")
    elif active == "mining":
        mostrar_tabla_mining(excel_data, sheet_name="MiningKW")
    elif active == "deduplicado":
        if _DEDUP_OK:
            mostrar_keywords_deduplicado(excel_data)
        else:
            st.error("Vista deduplicada aún no implementada o con errores.")
