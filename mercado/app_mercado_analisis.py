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

    if subvista == "insights":
        st.subheader("Insights del mercado (reviews)")

        if excel_data is None:
            st.warning(
                "Primero debes subir un archivo Excel en la sección Datos.")
        else:
            from mercado.loader_data_cliente import cargar_data_cliente
            from mercado.funcional_mercado_reviews import analizar_reviews

            datos = cargar_data_cliente(excel_data)

            if st.button("Generate AI insights"):
                st.info("Analizando reviews con IA...")
                resultados = analizar_reviews(
                    excel_data, datos.get("preguntas_rufus", []))
                st.session_state["resultados_mercado"] = resultados
                st.success("Análisis completado.")
            else:
                resultados = st.session_state.get("resultados_mercado", {})

            if resultados:
                st.markdown(
                    f"**Nombre del producto:** {resultados['nombre_producto']}")
                st.markdown(
                    f"**Descripción breve:** {resultados['descripcion']}")
                st.markdown("**Beneficios valorados:**")
                st.markdown(resultados["beneficios"])
                st.markdown("**Buyer persona:**")
                st.markdown(resultados["buyer_persona"])
                st.markdown("**Pros / Cons:**")
                st.markdown(resultados["pros_cons"])
                st.markdown("**Emociones detectadas:**")
                st.markdown(resultados["emociones"])
                st.markdown("**Tokens diferenciadores:**")
                st.markdown(resultados["tokens_diferenciadores"])

                if "validacion_rufus" in resultados:
                    st.markdown("**Validación preguntas Rufus:**")
                    st.markdown(resultados["validacion_rufus"])
            else:
                st.info("Haz clic en el botón para generar los insights.")

    elif subvista == "cliente":
        st.subheader("Contraste con Atributos del Cliente")

        if excel_data is None:
            st.warning(
                "Primero debes subir un archivo Excel en la sección Datos.")
        else:
            resultados = st.session_state.get("resultados_mercado", {})
            atributos_raw = resultados.get("atributos_valorados", "")

            if not atributos_raw:
                st.warning(
                    "No se encontraron atributos valorados por IA. Se usarán atributos de prueba.")
                atributos_mercado = ["color", "weight",
                                     "material", "dimensions", "label", "storage"]
            else:
                atributos_mercado = [
                    x.strip("-• ").lower()
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
        st.subheader("Léxico Editorial extraído de los reviews")

        resultados = st.session_state.get("resultados_mercado", {})

        if not resultados:
            st.warning(
                "Primero debes generar los insights en la pestaña 'Insights de Reviews'.")
        else:
            contenido = resultados.get("lexico_editorial", "")
            if contenido:
                st.markdown(contenido)
            else:
                st.info("No se encontró contenido de léxico editorial.")

    elif subvista == "visual":
        st.subheader("Recomendaciones visuales (brief)")
        resultados = st.session_state.get("resultados_mercado", {})
        if not resultados:
            st.warning(
                "Primero debes generar los insights en la pestaña 'Insights de Reviews'.")
        else:
            contenido = resultados.get("visuales", "")
            if contenido:
                st.markdown(contenido)
            else:
                st.info("No se encontró contenido de recomendaciones visuales.")

    elif subvista == "tabla":
        st.subheader("Tabla final de inputs para el Listing")

        try:
            from mercado.loader_inputs_listing import cargar_inputs_para_listing
            df_final = cargar_inputs_para_listing()

            if df_final.empty:
                st.info(
                    "Aún no se ha generado la tabla. Corre primero los análisis previos.")
            else:
                st.dataframe(df_final, use_container_width=True)
        except Exception as e:
            st.error(f"Error al cargar tabla final de inputs: {e}")
