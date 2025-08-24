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
            "cloud-upload",  # Datos
            "search",        # Keywords
            "bar-chart",     # Mercado
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

# Renderizado condicional según selección
if seleccion == "Datos":
    st.title("Sección: Datos")
    st.info("Aquí irá la carga del Excel.")
elif seleccion == "Keywords":
    st.title("Sección: Keywords")
    st.info("Aquí irán las tablas de origen (Referencial, Competidores, Mining).")
elif seleccion == "Mercado":
    st.title("Sección: Mercado")
    st.info("Aquí irá el análisis de reviews.")
elif seleccion == "Listing":
    st.title("Sección: Listing")
    st.info("Aquí irá el generador del listing final.")
