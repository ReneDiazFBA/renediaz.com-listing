# utils/nav_utils.py
# Subnavegación reutilizable para cualquier módulo (Referencial, Competidores, etc.)

import streamlit as st


def render_subnav(default_key: str, secciones: dict) -> str:
    """
    Renderiza un submenú horizontal basado en secciones.

    Args:
        default_key (str): clave activa por defecto (ej. "referencial")
        secciones (dict): diccionario con estructura {clave: (label visible, hoja Excel)}

    Returns:
        str: clave activa seleccionada
    """
    qp = st.query_params
    active = qp.get("subview", [default_key])[0]

    tabs = list(secciones.keys())
    labels = [secciones[k][0] for k in tabs]
    label_to_key = {v: k for k, v in secciones.items()}

    selected_label = st.selectbox(
        "Sección",
        options=labels,
        index=tabs.index(active) if active in tabs else 0,
        key="subnav_selector"
    )

    new_key = label_to_key.get(selected_label, default_key)
    st.query_params["subview"] = new_key
    return new_key
