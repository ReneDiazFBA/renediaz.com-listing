# mercado/app_mercado_analisis.py

import streamlit as st
import pandas as pd
import numpy as np
from typing import Optional
from utils.nav_utils import render_subnav


def mostrar_analisis_mercado(excel_data: Optional[object] = None):
    st.markdown("### Análisis del Mercado")
    st.caption(
        "Insights, emociones, atributos valorados, estilo editorial y visual extraídos desde los reviews.")

    secciones = {
        "insights": ("Insights de Reviews", None),
        "cliente": ("Contraste con Cliente", None),
        "editorial": ("Léxico Editorial", None),
        "visual": ("Recomendaciones Visuales", None),
        "tabla": ("Tabla Final de Inputs", None)
    }

    subvista = render_subnav(default_key="insights", secciones=secciones)
    st.divider()


def mostrar_analisis_mercado(excel_data: Optional[object] = None):
    st.markdown("### Análisis del Mercado")
    st.caption(
        "Insights, emociones, atributos valorados, estilo editorial y visual extraídos desde los reviews.")

    secciones = {
        "insights": ("Insights de Reviews", None),
        "cliente": ("Contraste con Cliente", None),
        "editorial": ("Léxico Editorial", None),
        "visual": ("Recomendaciones Visuales", None),
        "tabla": ("Tabla Final de Inputs", None)
    }

    subvista = render_subnav(default_key="insights", secciones=secciones)
    st.divider()

    if subvista == "cliente":
        st.subheader("Contraste con Atributos del Cliente")

        if excel_data is None:
            st.warning(
                "Primero debes subir un archivo Excel en la sección Datos.")
        else:
            resultados = st.session_state.get("resultados_mercado", {})
            atributos_raw = resultados.get("tokens_diferenciadores", "")

            if not atributos_raw:
                st.warning(
                    "No se encontraron tokens de IA. Se usarán tokens de prueba para depurar.")
                atributos_mercado = ["color", "weight",
                                     "material", "dimensions", "label", "storage"]
            else:
                atributos_mercado = [
                    x.strip().lower()
                    for x in atributos_raw.split("\n") if x.strip()
                ]

            from mercado.funcional_mercado_contraste import comparar_atributos_mercado_cliente

            df_edit = comparar_atributos_mercado_cliente(
                excel_data, atributos_mercado)

            if df_edit.empty:
                st.warning(
                    "No se encontraron atributos relevantes en CustData.")
            else:
                st.caption(
                    "Puedes editar directamente esta tabla. Las columnas vacías o filas vacías serán ignoradas.")
                edited = st.data_editor(
                    df_edit,
                    use_container_width=True,
                    num_rows="dynamic",
                    hide_index=True,
                    key="tabla_editable_contraste"
                )

    elif subvista == "editorial":
        st.info("Vista: Léxico Editorial (placeholder)")

    elif subvista == "visual":
        st.info("Vista: Recomendaciones Visuales (placeholder)")

    elif subvista == "tabla":
        st.info("Vista: Tabla Final de Inputs (placeholder)")
