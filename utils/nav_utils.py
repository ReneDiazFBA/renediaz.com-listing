# utils/nav_utils.py
# Subnavegación horizontal reutilizable para cualquier módulo

import streamlit as st


def render_subnav(default_key: str, secciones: dict) -> str:
    """
    Renderiza submenú horizontal con st.radio(), basado en claves y labels.

    Args:
        default_key (str): clave activa por defecto (ej. "referencial")
        secciones (dict): {clave: (label visible, hoja Excel)}

    Returns:
        str: clave activa seleccionada
    """
    qp = st.query_params
    active = qp.get("subview", [default_key])[0]

    claves = list(secciones.keys())
    labels = [secciones[k][0] for k in claves]
    label_to_key = {v: k for k, v in secciones.items()}
    default_label = secciones[active][0] if active in claves else labels[0]

    selected_label = st.radio(
        "Sección:",
        options=labels,
        index=labels.index(default_label),
        horizontal=True,
        key="radio_subnav"
    )

    new_key = label_to_key[selected_label]
    st.query_params["subview"] = new_key
    return new_key
