# mercado/app_mercado_analisis.py

import streamlit as st
import pandas as pd
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
            resultados = analizar_reviews(
                excel_data, datos.get("preguntas_rufus", []))

            if resultados:
                st.success("Análisis completado con IA.")
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
                st.markdown("**Léxico editorial:**")
                st.markdown(resultados["lexico_editorial"])
                st.markdown("**Sugerencias visuales:**")
                st.markdown(resultados["visuales"])
                st.markdown("**Tokens diferenciadores:**")
                st.markdown(resultados["tokens_diferenciadores"])

                if "validacion_rufus" in resultados:
                    st.markdown("**Validación preguntas Rufus:**")
                    st.markdown(resultados["validacion_rufus"])
            else:
                st.warning("No se pudo completar el análisis.")

    elif subvista == "editorial":
        st.info("Vista: Léxico Editorial (placeholder)")
    elif subvista == "visual":
        st.info("Vista: Recomendaciones Visuales (placeholder)")

    elif subvista == "tabla":
        st.subheader("Tabla Final de Inputs extraídos del mercado")

        resultados = st.session_state.get("resultados_mercado", {})

        if not resultados:
            st.warning(
                "Primero debes generar los insights con el botón en 'Insights de Reviews'.")
        else:
            data = []

            def agregar(fuente, tipo, contenido, etiqueta=None):
                if not contenido:
                    return
                lineas = contenido.strip().split("\n")
                for linea in lineas:
                    linea = linea.strip().lstrip("-•").strip()
                    if linea:
                        data.append({
                            "Tipo": tipo,
                            "Contenido": linea,
                            "Etiqueta": etiqueta or "",
                            "Fuente": fuente
                        })

            agregar("Reviews", "Nombre sugerido",
                    resultados.get("nombre_producto"))
            agregar("Reviews", "Descripción breve",
                    resultados.get("descripcion"))
            agregar("Reviews", "Beneficio", resultados.get(
                "beneficios"), etiqueta="Positivo")
            agregar("Reviews", "Pros/Cons", resultados.get("pros_cons"))
            agregar("Reviews", "Emoción", resultados.get("emociones"))
            agregar("Reviews", "Léxico editorial",
                    resultados.get("lexico_editorial"))
            agregar("Reviews", "Visual", resultados.get("visuales"))
            agregar("Reviews", "Token", resultados.get(
                "tokens_diferenciadores"))
            agregar("Reviews", "Validación Rufus",
                    resultados.get("validacion_rufus"))

            df = pd.DataFrame(data)

            if df.empty:
                st.info("No hay datos para mostrar.")
            else:
                st.dataframe(df, use_container_width=True)

    # mercado/app_mercado_analisis.py


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
            resultados = analizar_reviews(
                excel_data, datos.get("preguntas_rufus", []))

            if resultados:
                st.success("Análisis completado con IA.")
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
                st.markdown("**Léxico editorial:**")
                st.markdown(resultados["lexico_editorial"])
                st.markdown("**Sugerencias visuales:**")
                st.markdown(resultados["visuales"])
                st.markdown("**Tokens diferenciadores:**")
                st.markdown(resultados["tokens_diferenciadores"])

                if "validacion_rufus" in resultados:
                    st.markdown("**Validación preguntas Rufus:**")
                    st.markdown(resultados["validacion_rufus"])
            else:
                st.warning("No se pudo completar el análisis.")

    elif subvista == "editorial":
        st.info("Vista: Léxico Editorial (placeholder)")

    elif subvista == "visual":
        st.info("Vista: Recomendaciones Visuales (placeholder)")

    elif subvista == "tabla":
        st.subheader("Tabla Final de Inputs extraídos del mercado")

        resultados = st.session_state.get("resultados_mercado", {})

        if not resultados:
            st.warning(
                "Primero debes generar los insights con el botón en 'Insights de Reviews'.")
        else:
            data = []

            def agregar(fuente, tipo, contenido, etiqueta=None):
                if not contenido:
                    return
                lineas = contenido.strip().split("\n")
                for linea in lineas:
                    linea = linea.strip().lstrip("-•").strip()
                    if linea:
                        data.append({
                            "Tipo": tipo,
                            "Contenido": linea,
                            "Etiqueta": etiqueta or "",
                            "Fuente": fuente
                        })

            agregar("Reviews", "Nombre sugerido",
                    resultados.get("nombre_producto"))
            agregar("Reviews", "Descripción breve",
                    resultados.get("descripcion"))
            agregar("Reviews", "Beneficio", resultados.get(
                "beneficios"), etiqueta="Positivo")
            agregar("Reviews", "Pros/Cons", resultados.get("pros_cons"))
            agregar("Reviews", "Emoción", resultados.get("emociones"))
            agregar("Reviews", "Léxico editorial",
                    resultados.get("lexico_editorial"))
            agregar("Reviews", "Visual", resultados.get("visuales"))
            agregar("Reviews", "Token", resultados.get(
                "tokens_diferenciadores"))
            agregar("Reviews", "Validación Rufus",
                    resultados.get("validacion_rufus"))

            df = pd.DataFrame(data)

            if df.empty:
                st.info("No hay datos para mostrar.")
            else:
                st.dataframe(df, use_container_width=True)

    elif subvista == "cliente":
        st.subheader("Contraste con Atributos del Cliente")

        if excel_data is None:
            st.warning(
                "Primero debes subir un archivo Excel en la sección Datos.")
        else:
            from mercado.funcional_mercado_contraste import obtener_atributos_cliente

            df_atrib = obtener_atributos_cliente(excel_data)

            if df_atrib.empty:
                st.warning(
                    "No se encontraron atributos relevantes en CustData.")
            else:
                st.success(
                    f"Se encontraron {len(df_atrib)} atributos del cliente.")
                for _, row in df_atrib.iterrows():
                    nombre = row["atributo"]
                    variacion = " (variación)" if row["es_variacion"] else ""
                    valores = ", ".join(row["valores"])
                    st.markdown(f"- **{nombre}{variacion}**: {valores}")
