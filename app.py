# app.py

import streamlit as st
from streamlit_option_menu import option_menu

st.set_page_config(page_title="ReneDiaz.com Listing", layout="wide")

# Menú lateral personalizado
with st.sidebar:
    st.markdown("## Navegación")

    seleccion = option_menu(
        menu_title=None,
        options=[
            "Datos",
            "Keywords",
            "Mercado",
            "Listing"
        ],
        icons=[
            "cloud-upload",      # Datos
            "search",            # Keywords
            "bar-chart",         # Mercado
            "file-earmark-text"  # Listing
        ],
        menu_icon="cast",
        default_index=0,
        orientation="vertical",
        styles={
            "container": {"padding": "0!important", "background-color": "#f2f2f2"},
            "icon": {"color": "#0071bc", "font-size": "18px"},
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

elif seleccion == "Keywords":
    from keywords.app_keywords_data import mostrar_keywords_data
    mostrar_keywords_data()

elif seleccion == "Mercado":
    st.title("Módulo: Mercado")
    st.info("Aquí irá el análisis de reviews. [Placeholder]")

elif seleccion == "Listing":
    st.title("Módulo: Listing")
    st.info("Aquí se construirá el listing final. [Placeholder]")
