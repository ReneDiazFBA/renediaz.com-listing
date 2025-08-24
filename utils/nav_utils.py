# utils/nav_utils.py
# Subnavegación funcional con st.radio (reutilizable en cualquier módulo)

import streamlit as st


def render_subnav(active: str, secciones: dict) -> str:
    """
    Subnavegación funcional con st.radio.
    Recibe el activo actual y el diccionario de secciones.
    Devuelve la clave seleccionada.
    """
    label_map = {v[0]: k for k, v in secciones.items()}
    opciones = list(label_map.keys())
    idx = opciones.index(secciones[active][0]) if active in secciones else 0

    seleccion = st.radio(
        label="",
        options=opciones,
        index=idx,
        horizontal=True,
        label_visibility="collapsed"
    )

    return label_map[seleccion]
