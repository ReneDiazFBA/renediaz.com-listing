# keywords/app_keywords_deduplicado.py

import streamlit as st
from utils.nav_utils import render_subnav


def mostrar_keywords_deduplicado():
    st.markdown("### Keywords — Vista Maestra")

    secciones = {
        "raw": ("Maestra (raw)", "raw"),
        "deduplicada": ("Maestra deduplicada", "deduplicada")
    }

    active = render_subnav("raw", secciones)
    st.divider()

    if active == "raw":
        st.warning("Vista RAW aún no implementada.")
    elif active == "deduplicada":
        st.warning("Vista DEDUPLICADA aún no implementada.")
