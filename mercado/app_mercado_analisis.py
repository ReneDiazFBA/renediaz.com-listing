import streamlit as st
import pandas as pd
import numpy as np
from typing import Optional
from mercado.loader_inputs_listing import construir_inputs_listing
from utils.nav_utils import render_subnav

# >>> RD_FIX: bandera para desactivar el simulador
USAR_SIMULADOR_IA = False
# <<< RD_FIX


def mostrar_analisis_mercado(excel_data: Optional[object] = None):
    st.markdown("### Análisis del Mercado")
    st.caption(
        "Insights, emociones, atributos valorados, estilo editorial y visual extraídos desde los reviews."
    )

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

            # Botón IA (opcional)
            if st.button("Generar insights con IA"):
                try:
                    import os
                    if "OPENAI_API_KEY" in st.secrets and st.secrets["OPENAI_API_KEY"]:
                        os.environ.setdefault(
                            "OPENAI_API_KEY", st.secrets["OPENAI_API_KEY"])
                except Exception:
                    pass

                st.info("Analizando reviews con IA...")
                try:
                    resultados = analizar_reviews(
                        excel_data, datos.get("preguntas_rufus", []))
                    st.session_state["resultados_mercado"] = resultados
                    st.success("Análisis completado.")
                except Exception as e:
                    st.error(f"Error al analizar con IA: {e}")

            # Simulador (desactivado por bandera)
            if USAR_SIMULADOR_IA and st.button("Simular insights sin IA"):
                resultados = {
                    "nombre_producto": "Privacy Folders para Estudiantes – Paneles de Escritorio",
                    "descripcion": "Separadores plegables de cartón para mejorar la concentración y privacidad durante pruebas o tareas escolares.",
                    "beneficios": "- Reduce distracciones en el aula\n- Ideal para exámenes\n- Ligero y fácil de almacenar\n- Fomenta la concentración\n- Económico y reutilizable",
                    "buyer_persona": "Profesores de primaria que buscan herramientas económicas para mejorar el enfoque de sus estudiantes durante actividades evaluativas.",
                    "pros_cons": "PROS:\n- Fácil de usar\n- Mejora la concentración\n- Buena relación calidad/precio\nCONS:\n- Puede doblarse con el uso\n- No resiste humedad",
                    "emociones": "- Enfoque\n- Orden\n- Tranquilidad\n- Autoridad\n- Control",
                    "atributos_valorados": "- Material\n- Tamaño\n- Plegable\n- Color neutro\n- Reutilizable",
                    "tokens_diferenciadores": "",
                    "lexico_editorial": "Quiet learning • Focused environment • Classroom control • Reusable cardboard panels • Budget-friendly solution",
                    "visuales": "Mostrar a varios estudiantes sentados en escritorios individuales con los privacy folders abiertos durante una prueba, ambiente ordenado y silencioso."
                }
                st.session_state["resultados_mercado"] = resultados
                st.success("Simulación cargada con éxito.")

            resultados = st.session_state.get("resultados_mercado", {})
            if resultados:
                st.markdown(
                    f"**Nombre del producto:** {resultados.get('nombre_producto','')}")
                st.markdown(
                    f"**Descripción breve:** {resultados.get('descripcion','')}")
                st.markdown("**Beneficios valorados:**")
                st.markdown(resultados.get("beneficios", ""))
                st.markdown("**Buyer persona:**")
                st.markdown(resultados.get("buyer_persona", ""))
                st.markdown("**Pros / Cons:**")
                st.markdown(resultados.get("pros_cons", ""))
                st.markdown("**Emociones detectadas:**")
                st.markdown(resultados.get("emociones", ""))
                st.markdown("**Tokens diferenciadores:**")
                st.markdown(resultados.get("tokens_diferenciadores", ""))

                if "validacion_rufus" in resultados:
                    st.markdown("**Validación preguntas Rufus:**")
                    st.markdown(resultados["validacion_rufus"])
            else:
                st.info("Genera los insights con IA para continuar.")

    elif subvista == "cliente":
        st.subheader("Contraste con Atributos del Cliente")

        if excel_data is None:
            st.warning(
                "Primero debes subir un archivo Excel en la sección Datos.")
        else:
            # 1) Atributos del mercado (desde resultados de IA si existen; si no, fallback)
            resultados = st.session_state.get("resultados_mercado", {})
            atributos_raw = resultados.get("atributos_valorados", "")

            if not atributos_raw or not isinstance(atributos_raw, str):
                st.warning(
                    "No se encontraron atributos valorados por IA. Se usarán atributos de prueba.")
                atributos_mercado = ["color", "weight",
                                     "material", "dimensions", "label", "storage"]
            else:
                atributos_mercado = [
                    x.strip("-• ").lower()
                    for x in atributos_raw.split("\n")
                    if isinstance(x, str) and x.strip()
                ]

            # 2) Construir/recuperar la tabla de contraste (con columna Tipo automática)
            from mercado.funcional_mercado_contraste import (
                comparar_atributos_mercado_cliente,
                _recompute_tipo,
            )

            try:
                df_edit = comparar_atributos_mercado_cliente(
                    excel_data, atributos_mercado)
            except Exception as e:
                st.error(f"Error al generar tabla de contraste: {e}")
                return

            if df_edit is None or df_edit.empty:
                st.warning(
                    "No se encontraron atributos relevantes en CustData.")
                edited = pd.DataFrame()
            else:
                st.caption(
                    "Edita libremente. La columna **Tipo** (Atributo/Variación) se ajusta sola según los valores (Valor 1..4). Tus cambios persisten aunque cambies de módulo.")
                edited = st.data_editor(
                    df_edit,
                    use_container_width=True,
                    num_rows="dynamic",
                    hide_index=True,
                    key="tabla_editable_contraste",
                )

        # 3) Recalcular Tipo tras edición y PERSISTIR (sin botones)
        edited = _recompute_tipo(edited)
        # persistente entre vistas
        st.session_state["df_contraste_edit"] = edited.copy()
        # compatibilidad con otros módulos
        st.session_state["df_edit"] = edited.copy()

        # 4) (Opcional) Construir inputs para Listing con lo EDITADO (Tipo ya correcto)
        st.session_state["inputs_para_listing"] = construir_inputs_listing(
            st.session_state.get("resultados_mercado", {}),
            edited,
            excel_data=excel_data,
        )

        # 5) Snapshot (pequeño diagnóstico)
        if not edited.empty:
            try:
                tipos = edited.get("Tipo", pd.Series(
                    [], dtype=str)).astype(str).str.lower()
                n_attr = int((tipos == "atributo").sum())
                n_var = int(((tipos == "variación") |
                            (tipos == "variacion")).sum())
                st.caption(
                    f"Snapshot: Atributos = {n_attr} · Variaciones = {n_var} · Filas = {len(edited)}")
            except Exception:
                pass

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
            # ⬇️ Trae la tabla final de Mercado y la copia DIRECTO a Listing (sin botones ni reconstrucciones)
            from mercado.loader_inputs_listing import cargar_inputs_para_listing
            df_final = cargar_inputs_para_listing()

            if isinstance(df_final, pd.DataFrame) and not df_final.empty:
                st.session_state["inputs_para_listing"] = df_final.copy()

            # (Diagnóstico opcional)
            st.caption(
                f"Filas (Mercado): {len(df_final)} | Filas que ve Listing ahora: "
                f"{len(st.session_state.get('inputs_para_listing', pd.DataFrame()))}"
            )

            if df_final.empty:
                st.info(
                    "Aún no se ha generado la tabla. Corre primero los análisis previos.")
            else:
                st.dataframe(df_final, use_container_width=True)

        except Exception as e:
            st.error(f"Error al cargar tabla final de inputs: {e}")
