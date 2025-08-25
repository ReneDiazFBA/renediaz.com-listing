# app_keywords_estadistica.py
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
            from keywords.funcional_keywords_estadistica import filtrar_por_sliders
            from keywords.funcional_keywords_deduplicado import formatear_columnas_tabla

            df_original = st.session_state.master_deduped.copy()
            df_filtrado = filtrar_por_sliders(df_original)
            df_formateado = df_filtrado

            st.markdown(f"**Total Registros: {len(df_filtrado):,}**")
            st.dataframe(df_formateado, use_container_width=True)

            # Descriptivos
            from keywords.funcional_keywords_estadistica import calcular_descriptivos_extendidos

            st.subheader("Estadística descriptiva")
            df_descriptivos = calcular_descriptivos_extendidos(df_filtrado)
            st.dataframe(df_descriptivos, use_container_width=True)

            # === SUGERENCIA DE LOG10 (basado en skewness)
            from keywords.funcional_keywords_estadistica import sugerir_log_transform
            st.subheader("Sugerencia de Transformación Logarítmica")
            sugerencias = sugerir_log_transform(df_filtrado)
            for col, valor_skew in sugerencias.items():
                if valor_skew is not None:
                    st.radio(
                        f"Columna '{col}' — skewness: {valor_skew:.2f}. ¿Aplicar log10?",
                        options=["Mantener original", "Aplicar log10"],
                        index=0,
                        key=f"log_radio_{col}"
                    )

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
