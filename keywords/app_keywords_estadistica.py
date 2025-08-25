# keywords/app_keywords_estadistica.py
import streamlit as st
import pandas as pd
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
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

    if "master_deduped" not in st.session_state:
        st.error(
            "No se ha cargado la tabla deduplicada. Sube un archivo Excel en la sección Datos.")
        return

    if active == "descriptiva":
        st.subheader("Vista Descriptiva")

        from keywords.funcional_keywords_estadistica import (
            filtrar_por_sliders,
            calcular_descriptivos_extendidos,
            sugerir_log_transform,
            aplicar_log10_dinamico
        )
        from keywords.funcional_keywords_deduplicado import formatear_columnas_tabla

        # Cargar y filtrar
        df_original = st.session_state.master_deduped.copy()
        df_filtrado = filtrar_por_sliders(df_original)

        # Recomendación de log10
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

        # Aplicar log10 si corresponde
        df_transformado = aplicar_log10_dinamico(df_filtrado)

        # Mostrar tabla preview
        st.markdown(f"**Total Registros: {len(df_transformado):,}**")
        st.dataframe(df_transformado, use_container_width=True)

        # Estadística descriptiva
        st.subheader("Estadística descriptiva")
        df_descriptivos = calcular_descriptivos_extendidos(df_transformado)
        st.dataframe(df_descriptivos, use_container_width=True)

        if "Shapiro Normality" in df_descriptivos.columns:
            normales = df_descriptivos[df_descriptivos["Shapiro Normality"] == "Normal"]
            no_normales = df_descriptivos[df_descriptivos["Shapiro Normality"] != "Normal"]

            st.success(
                f"{len(normales)} columnas parecen seguir una distribución normal.")

            if not no_normales.empty:
                st.warning(
                    "Estas columnas **no** siguen una distribución normal:")
                st.markdown(", ".join(no_normales["Columna"].tolist()))

    elif active == "graficos":
        st.subheader("Gráficos")
        st.info(
            "Aquí se graficarán las distribuciones y relaciones. [Placeholder]")

    elif active == "correlaciones":
        st.subheader("Correlaciones entre métricas")
        from keywords.funcional_keywords_estadistica import (
            calcular_correlaciones,
        )

        df_original = st.session_state.master_deduped.copy()
        df_filtrado = filtrar_por_sliders(df_original)
        df_transformado = aplicar_log10_dinamico(df_filtrado)

        pearson, spearman = calcular_correlaciones(df_transformado)

        if pearson is None or spearman is None:
            st.warning(
                "No hay suficientes columnas numéricas para calcular correlaciones.")
            return

        st.markdown("#### Matriz de correlación (Pearson)")
        st.dataframe(pearson.style.background_gradient(
            cmap="Blues"), use_container_width=True)

        st.markdown("#### Matriz de correlación (Spearman)")
        st.dataframe(spearman.style.background_gradient(
            cmap="Purples"), use_container_width=True)

        # Interpretación automática
        st.markdown("#### Interpretación automática")
        umbral = 0.7
        textos = []

        for metodo, matriz in [("Pearson", pearson), ("Spearman", spearman)]:
            for i in matriz.columns:
                for j in matriz.columns:
                    if i != j:
                        val = matriz.loc[i, j]
                        if abs(val) > umbral:
                            tipo = "positiva" if val > 0 else "negativa"
                            textos.append(
                                f"- **{i}** y **{j}** tienen una correlación {tipo} fuerte ({metodo}: {val:.2f})")

        if textos:
            for linea in textos:
                st.markdown(linea)
        else:
            st.info(
                "No se encontraron correlaciones fuertes (>|0.70|) entre pares de columnas.")

    elif active == "ia":
        st.subheader("Análisis con IA")
        st.info("Aquí se generarán insights con IA. [Placeholder]")
