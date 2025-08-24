# keywords/app_keywords_data.py

import streamlit as st
import pandas as pd
from typing import Optional

from keywords.app_keywords_referencial import mostrar_tabla_referencial
from keywords.app_keywords_competidores import mostrar_tabla_competidores
from keywords.app_keywords_mining import mostrar_tabla_mining
from utils.nav_utils import render_subnav


def mostrar_keywords_data(excel_data: Optional[pd.ExcelFile] = None):
    st.markdown("### Keywords — Tablas de origen")

    secciones = {
        "referencial": ("Reverse ASIN Referencial", "CustKW"),
        "competidores": ("Reverse ASIN Competidores", "CompKW"),
        "mining": ("Mining de Keywords", "MiningKW")
    }

    active = render_subnav("referencial", secciones)
    st.divider()

    if active == "referencial":
        st.write("✅ Debug: cargando tabla referencial...")
        mostrar_tabla_referencial(excel_data, sheet_name="CustKW")

    elif active == "competidores":
        st.write("✅ Debug: cargando tabla competidores...")
        mostrar_tabla_competidores(excel_data, sheet_name="CompKW")

    elif active == "mining":
        st.write("✅ Debug: cargando tabla mining...")
        mostrar_tabla_mining(excel_data, sheet_name="MiningKW")
