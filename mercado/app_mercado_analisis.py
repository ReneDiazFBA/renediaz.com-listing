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
    elif subvista == "insights":
        st.subheader("Insights del mercado (reviews)")

        if excel_data is None:
            st.warning(
                "Primero debes subir un archivo Excel en la sección Datos.")
        else:
            from mercado.loader_data_cliente import cargar_data_cliente
            from mercado.funcional_mercado_reviews import analizar_reviews

            datos = cargar_data_cliente(excel_data)
            resultados = analizar_reviews(
                excel_data, datos.get("preguntas_rufus", []))

            if resultados:
                st.success("Análisis completado con IA.")
                st.markdown(
                    f"**Nombre del producto:** {resultados['nombre_producto']}")
                st.markdown(
                    f"**Descripción breve:** {resultados['descripcion']}")
                st.markdown("** Beneficios valorados:**")
                st.markdown(resultados["beneficios"])
                st.markdown("**🧍 Buyer persona:**")
                st.markdown(resultados["buyer_persona"])
                st.markdown("**Pros / Cons:**")
                st.markdown(resultados["pros_cons"])
                st.markdown("** Emociones detectadas:**")
                st.markdown(resultados["emociones"])
                st.markdown("** Léxico editorial:**")
                st.markdown(resultados["lexico_editorial"])
                st.markdown("** Sugerencias visuales:**")
                st.markdown(resultados["visuales"])
                st.markdown("** Tokens diferenciadores:**")
                st.markdown(resultados["tokens_diferenciadores"])

                if "validacion_rufus" in resultados:
                    st.markdown("**🛡️ Validación preguntas Rufus:**")
                    st.markdown(resultados["validacion_rufus"])
            else:
                st.warning("No se pudo completar el análisis.")

    elif subvista == "editorial":
        st.info("Vista: Léxico Editorial (placeholder)")
    elif subvista == "visual":
        st.info("Vista: Recomendaciones Visuales (placeholder)")
    elif subvista == "tabla":
        st.info("Vista: Tabla Final de Inputs (placeholder)")
