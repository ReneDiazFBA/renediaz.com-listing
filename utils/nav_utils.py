# utils/nav_utils.py
# Componente visual reutilizable para navegación tipo header (cascarón visual puro)

import streamlit as st


def render_subnav_cascaron(active: str, secciones: dict):
    """
    Renderiza navegación horizontal tipo header (visual puro, sin lógica).
    """
    cols = st.columns(len(secciones))
    for i, (key, (label, _)) in enumerate(secciones.items()):
        if key == active:
            style = "color: #f7931e; font-weight: bold; border-bottom: 3px solid #f7931e;"
        else:
            style = "color: #0071bc; font-weight: normal;"
        cols[i].markdown(
            f"<div style='{style}'>{label}</div>", unsafe_allow_html=True)
