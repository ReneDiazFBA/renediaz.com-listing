# keywords/app_keywords_data.py

import streamlit as st
import pandas as pd
from typing import Optional

from keywords.app_keywords_referencial import mostrar_tabla_referencial
from keywords.app_keywords_competidores import mostrar_tabla_competidores
from keywords.app_keywords_mining import mostrar_tabla_mining
from keywords.app_keywords_deduplicado import mostrar_keywords_deduplicado
from utils.nav_utils import render_subnav


def mostrar_keywords_data(excel_data: Optional[pd.ExcelFile] = None):
    st.markdown("### Keywords — Tablas de origen")

    secciones = {
        "referencial": ("Reverse ASIN Referencial", "CustKW"),
        "competidores": ("Reverse ASIN Competidores", "CompKW"),
        "mining": ("Mining de Keywords", "MiningKW"),
    }


def mostrar_keywords_estadistica(excel_data: Optional[pd.ExcelFile] = None):
    st.markdown("### Keywords — Datos Estadísticos")
    st.caption(
        "Explora las propiedades estadísticas de las keywords deduplicadas.")

    secciones = {
        "descriptiva": ("Descriptiva", "descriptiva"),
        "graficos": ("Gráficos", "graficos"),
        "correlaciones": ("Correlaciones", "correlaciones"),
        "ia": ("Análisis IA", "ia"),
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
        mostrar_keywords_deduplicado(excel_data)

    active = render_subnav("descriptiva", secciones)
    st.divider()

    if excel_data is None:
        st.warning("Primero debes subir un archivo en la sección Datos.")
        return
    if active == "descriptiva":
        st.subheader("📊 Vista Descriptiva")
        st.info(
            "Aquí se mostrará la tabla con estadísticos básicos. [Placeholder]")
    elif active == "graficos":
        st.subheader("📈 Gráficos")
        st.info(
            "Aquí se graficarán las distribuciones y relaciones. [Placeholder]")
    elif active == "correlaciones":
        st.subheader("🔗 Correlaciones")
        st.info("Aquí se mostrará la matriz de correlaciones. [Placeholder]")
    elif active == "ia":
        st.subheader("🤖 Análisis con IA")
        st.info(
            "Aquí se generarán insights inteligentes con IA. [Placeholder]")
