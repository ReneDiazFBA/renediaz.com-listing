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
        st.subheader("Matriz de Correlación")

        from keywords.funcional_keywords_estadistica import filtrar_por_sliders

        df_original = st.session_state.master_deduped.copy()
        df_filtrado = filtrar_por_sliders(df_original)
        df_corr = df_filtrado.select_dtypes(include="number").copy()
        df_corr = df_corr.replace([-1, -2], np.nan).dropna(axis=1)

        if df_corr.shape[1] < 2:
            st.warning(
                "No hay suficientes columnas numéricas para calcular correlaciones.")
            return

        corr_pearson = df_corr.corr(method="pearson")
        corr_spearman = df_corr.corr(method="spearman")

        st.markdown("##### Pearson (lineal)")
        st.dataframe(corr_pearson.round(2), use_container_width=True)

        st.markdown("##### Spearman (monótona)")
        st.dataframe(corr_spearman.round(2), use_container_width=True)

        st.markdown("##### Heatmap de correlaciones (Pearson)")
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.heatmap(corr_pearson, annot=True, cmap="coolwarm", center=0, ax=ax)
        st.pyplot(fig)

        st.markdown("##### Interpretación automática")
        umbral_alta = 0.85
        correlaciones_altas = []

        for i, col1 in enumerate(corr_pearson.columns):
            for j, col2 in enumerate(corr_pearson.columns):
                if i < j:
                    coef = corr_pearson.iloc[i, j]
                    if abs(coef) >= umbral_alta:
                        correlaciones_altas.append((col1, col2, coef))

        if not correlaciones_altas:
            st.success("No se detectaron correlaciones fuertes entre columnas.")
        else:
            for col1, col2, coef in correlaciones_altas:
                tipo = "positivamente" if coef > 0 else "negativamente"
                st.markdown(
                    f"- **{col1}** y **{col2}** están **{tipo} correladas** (ρ = {coef:.2f})")

            st.info(
                "Considera filtrar o priorizar solo una de estas columnas para evitar redundancia.")

    elif active == "ia":
        st.subheader("Análisis con IA")
        st.info("Aquí se generarán insights con IA. [Placeholder]")
