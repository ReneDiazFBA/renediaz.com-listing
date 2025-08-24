# keywords/app_keywords_data.py

import streamlit as st
import pandas as pd
from typing import Optional

from keywords.app_keywords_referencial import mostrar_tabla_referencial
from keywords.app_keywords_competidores import mostrar_tabla_competidores
from utils.nav_utils import render_subnav


def mostrar_keywords_data(excel_data: Optional[pd.ExcelFile] = None):
    st.markdown("### Keywords — Tablas de origen")

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
        mostrar_tabla_referencial(excel_data, sheet_name="CustKW")
    elif active == "competidores":
        mostrar_tabla_competidores(excel_data, sheet_name="CompKW")
    else:
        st.info("Mining aún no implementado.")
