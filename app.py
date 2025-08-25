# app.py

import streamlit as st
from streamlit_option_menu import option_menu

st.set_page_config(page_title="ReneDiaz.com Listing", layout="wide")

# 1. Menú lateral — sin íconos, sin submenús rotos
with st.sidebar:
    st.markdown("## Navegación")

    seccion_principal = option_menu(
        menu_title=None,
        options=[
            "Datos",
            "Keywords",
            "Mercado",
            "Listing"
        ],
        icons=[None] * 4,  # ❌ sin figuritas (rompen submenús)
        default_index=0,
        orientation="vertical",
        styles={
            "container": {"padding": "0!important", "background-color": "#f2f2f2"},
            "nav-link": {
                "font-size": "18px",
                "text-align": "left",
                "margin": "0px",
                "--hover-color": "#f7931e",
            },
            "nav-link-selected": {
                "background-color": "#f7931e",
                "color": "white",
            },
        }
    )

# 2. Navegación lógica — hijo simulado
if seccion_principal == "Datos":
    from datos.app_datos_upload import mostrar_carga_excel
    mostrar_carga_excel()

elif seccion_principal == "Keywords":
    submodulo = st.radio(
        "Selecciona submódulo de Keywords:",
        ["Tablas de origen", "Maestra deduplicada", "Datos Estadísticos"],
        horizontal=True
    )

    if submodulo == "Tablas de origen":
        from keywords.app_keywords_data import mostrar_keywords_data
        mostrar_keywords_data(st.session_state.excel_data)
    elif submodulo == "Maestra deduplicada":
        from keywords.app_keywords_deduplicado import mostrar_keywords_deduplicado
        mostrar_keywords_deduplicado(st.session_state.excel_data)
    elif submodulo == "Datos Estadísticos":
        from keywords.app_keywords_estadistica import mostrar_keywords_estadistica
        mostrar_keywords_estadistica(st.session_state.excel_data)


elif seccion_principal == "Mercado":
    st.title("Módulo: Mercado")
    st.info("Aquí irá el análisis de reviews. [Placeholder]")

elif seccion_principal == "Listing":
    st.title("Módulo: Listing")
    st.info("Aquí se construirá el listing final. [Placeholder]")
