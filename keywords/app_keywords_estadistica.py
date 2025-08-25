import streamlit as st
import pandas as pd
from typing import Optional
from utils.nav_utils import render_subnav


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

    active = render_subnav("descriptiva", secciones)
    st.divider()

    if excel_data is None:
        st.warning("Primero debes subir un archivo en la sección Datos.")
        return

    if active == "descriptiva":
        st.subheader("Vista Descriptiva")

        if "master_deduped" not in st.session_state:
            st.error(
                "No se ha cargado la tabla deduplicada. Sube un archivo Excel en la sección Datos.")
        else:
            df = st.session_state.master_deduped.copy()
            st.dataframe(df, use_container_width=True)

    elif active == "graficos":
        st.subheader("Gráficos")
        st.info(
            "Aquí se graficarán las distribuciones y relaciones. [Placeholder]")

    elif active == "correlaciones":
        st.subheader("Correlaciones")
        st.info("Aquí se mostrará la matriz de correlaciones. [Placeholder]")

    elif active == "ia":
        st.subheader("Análisis con IA")
        st.info("Aquí se generarán insights con IA. [Placeholder]")
