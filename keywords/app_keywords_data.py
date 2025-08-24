# keywords/app_keywords_data.py

import streamlit as st
import pandas as pd
from typing import Optional

from keywords.app_keywords_referencial import mostrar_tabla_referencial
from keywords.app_keywords_competidores import mostrar_tabla_competidores
from keywords.app_keywords_mining import mostrar_tabla_mining
from utils.nav_utils import render_subnav_radio


def mostrar_keywords_data(excel_data: Optional[pd.ExcelFile] = None):
    st.markdown("### Keywords — Tablas de origen")

    opciones = [
        "Reverse ASIN Referencial",
        "Reverse ASIN Competidores",
        "Mining de Keywords"
    ]

    seleccion = render_subnav_radio("keywords", opciones)
    st.divider()

    if seleccion == "Reverse ASIN Referencial":
        mostrar_tabla_referencial(excel_data, sheet_name="CustKW")
    elif seleccion == "Reverse ASIN Competidores":
        mostrar_tabla_competidores(excel_data, sheet_name="CompKW")
    elif seleccion == "Mining de Keywords":
        mostrar_tabla_mining(excel_data, sheet_name="MiningKW")
