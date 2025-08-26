# mercado/app_mercado_analisis.py

import streamlit as st
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

    if subvista == "insights":
        st.info("Vista: Insights de Reviews (placeholder)")
    elif subvista == "cliente":
        st.subheader("📥 Data real del cliente")

        if excel_data is None:
            st.warning(
                "Primero debes subir un archivo Excel en la sección Datos.")
        else:
            from mercado.loader_data_cliente import cargar_data_cliente

            data_cliente = cargar_data_cliente(excel_data)
            if not data_cliente:
                st.error("No se pudo cargar la información del cliente.")
            else:
                st.success("Información cargada correctamente.")
                st.json(data_cliente)

    elif subvista == "editorial":
        st.info("Vista: Léxico Editorial (placeholder)")
    elif subvista == "visual":
        st.info("Vista: Recomendaciones Visuales (placeholder)")
    elif subvista == "tabla":
        st.info("Vista: Tabla Final de Inputs (placeholder)")
