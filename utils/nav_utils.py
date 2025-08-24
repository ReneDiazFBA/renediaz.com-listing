# utils/nav_utils.py
# Utilidades genéricas de navegación para el dashboard ReneDiaz.com

import streamlit as st
from typing import List


def render_subnav_radio(key: str, labels: List[str]) -> str:
    """
    Renderiza un submenú horizontal tipo st.radio universal,
    usando query_params para conservar el estado.

    Parámetros:
    - key: prefijo único del módulo (ej. "keywords", "mercado")
    - labels: lista de opciones visibles (ej. ["Tablas de origen", "Resumen"])

    Retorna:
    - label seleccionado (ej. "Tablas de origen")
    """
    query_key = f"{key}_subview"

    # Leer del query param si existe
    qp = st.query_params
    default_label = labels[0]
    active_label = qp.get(query_key, [default_label])[0]

    # Mostrar radio horizontal
    selected_label = st.radio(
        label="",
        options=labels,
        index=labels.index(active_label) if active_label in labels else 0,
        horizontal=True,
        key=f"radio_{key}"
    )

    # Actualizar query param si cambió
    if selected_label != active_label:
        st.query_params[query_key] = selected_label
        st.rerun()

    return selected_label
