# listing/loader_listing_keywords.py
# Loader para tabla estratégica de keywords (tiers)

import streamlit as st
import pandas as pd


def get_tiers_table() -> pd.DataFrame:
    """
    Devuelve la tabla estratégica de tiers ya generada desde la vista principal.
    Si no existe en sesión, lanza error controlado.
    """
    if "matriz_tiers" not in st.session_state:
        st.error("La tabla de tiers aún no ha sido generada.")
        return pd.DataFrame()
    return st.session_state["matriz_tiers"]
