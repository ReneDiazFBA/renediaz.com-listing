# app.py

import streamlit as st
from streamlit_option_menu import option_menu

st.set_page_config(page_title="ReneDiaz.com Listing", layout="wide")

# Menú lateral funcional sin íconos
with st.sidebar:
    st.markdown("## Navegación")

    seleccion = option_menu(
        menu_title=None,
        options=[
            "Datos",
            {"label": "Keywords", "submenu": ["Tablas de origen"]},
            "Mercado",
            "Listing"
        ],
        icons=[None] * 4,  # No usar íconos (rompen los submenús)
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

# Vista según sección seleccionada
if seleccion == "Datos":
    from datos.app_datos_upload import mostrar_carga_excel
    mostrar_carga_excel()

elif seleccion == "Tablas de origen":
    from keywords.app_keywords_data import mostrar_keywords_data
    mostrar_keywords_data()

elif seleccion == "Mercado":
    st.title("Módulo: Mercado")
    st.info("Aquí irá el análisis de reviews. [Placeholder]")

elif seleccion == "Listing":
    st.title("Módulo: Listing")
    st.info("Aquí se construirá el listing final. [Placeholder]")
