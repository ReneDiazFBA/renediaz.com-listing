# keywords/app_keywords_estadistica.py
import streamlit as st
import pandas as pd
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
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
        st.subheader("Distribución de Métricas")

        from keywords.funcional_keywords_estadistica import (
            filtrar_por_sliders,
            aplicar_log10_dinamico
        )

        df_original = st.session_state.master_deduped.copy()
        df_filtrado = filtrar_por_sliders(df_original)
        df_transformado = aplicar_log10_dinamico(df_filtrado)

        columnas_numericas = df_transformado.select_dtypes(
            include=["number"]).columns.tolist()
        if not columnas_numericas:
            st.warning("No hay columnas numéricas disponibles para graficar.")
            return

        selected_col = st.selectbox(
            "Selecciona una métrica para visualizar:", columnas_numericas)

        serie = df_transformado[selected_col]
        serie_valida = serie[(serie != -1) & (serie != -2)]

        if serie_valida.empty:
            st.warning("No hay datos válidos para esta métrica.")
            return

        media = serie_valida.mean()
        std = serie_valida.std()

        with st.expander(f"Distribución de {selected_col}", expanded=True):
            st.markdown(
                f"**Media:** {media:.2f} &nbsp;&nbsp; | &nbsp;&nbsp; **Desviación estándar:** {std:.2f}")

            # 🎯 Histograma con línea Gauss
            fig, ax = plt.subplots()
            sns.histplot(serie_valida, bins=20, kde=False,
                         color="#0071bc", ax=ax)

            # 🔁 Superponer curva Gauss si STD > 0
            if std > 0:
                from scipy.stats import norm
                x = np.linspace(serie_valida.min(), serie_valida.max(), 100)
                y = norm.pdf(x, media, std)
                y_scaled = y * len(serie_valida) * \
                    (x[1] - x[0])  # Ajustar escala
                ax.plot(x, y_scaled, color="#f7931e",
                        linewidth=2, label="Distribución Normal")

            ax.set_title(f"Histograma de {selected_col}")
            ax.legend()
            st.pyplot(fig)

            # 📦 Boxplot
            fig2, ax2 = plt.subplots(figsize=(8, 1.5))
            sns.boxplot(x=serie_valida, color="#0071bc", ax=ax2)
            ax2.set_title(f"Boxplot de {selected_col}")
            st.pyplot(fig2)

    elif active == "correlaciones":
        st.subheader("Correlaciones entre métricas")

        from keywords.funcional_keywords_estadistica import (
            calcular_correlaciones,
            filtrar_por_sliders,
            aplicar_log10_dinamico,
            interpretar_correlaciones
        )

        df_original = st.session_state.master_deduped.copy()
        df_filtrado = filtrar_por_sliders(df_original)
        df_transformado = aplicar_log10_dinamico(df_filtrado)

        pearson, spearman = calcular_correlaciones(df_transformado)

        if pearson is None or spearman is None:
            st.warning(
                "No hay suficientes columnas numéricas para calcular correlaciones.")
            return

        # 🎨 Heatmap Pearson (azul corporativo)
        st.markdown("### Matriz de correlación (Pearson)")
        fig1, ax1 = plt.subplots(figsize=(12, 6))
        cmap_pearson = LinearSegmentedColormap.from_list(
            "pearson_brand", ["#d3e9f7", "#0071bc"]
        )
        sns.heatmap(pearson, cmap=cmap_pearson, annot=True, fmt=".2f",
                    linewidths=0.5, linecolor='white', ax=ax1)
        st.pyplot(fig1)

        # 🎨 Heatmap Spearman (naranja corporativo)
        st.markdown("### Matriz de correlación (Spearman)")
        fig2, ax2 = plt.subplots(figsize=(12, 6))
        cmap_spearman = LinearSegmentedColormap.from_list(
            "spearman_brand", ["#ffe5cc", "#f7931e"]
        )
        sns.heatmap(spearman, cmap=cmap_spearman, annot=True, fmt=".2f",
                    linewidths=0.5, linecolor='white', ax=ax2)
        st.pyplot(fig2)

        # 📊 Interpretación automática
        st.markdown("### Interpretación automática")
        interpretaciones_pearson = interpretar_correlaciones(
            pearson, metodo="Pearson")
        interpretaciones_spearman = interpretar_correlaciones(
            spearman, metodo="Spearman")

        for linea in interpretaciones_pearson + interpretaciones_spearman:
            st.markdown(f"- {linea}")

    elif active == "ia":
        st.subheader("Análisis con IA")
        st.info("Aquí se generarán insights con IA. [Placeholder]")
