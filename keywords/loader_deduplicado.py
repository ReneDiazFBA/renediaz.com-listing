# keywords/loader_deduplicados.py

import streamlit as st
import pandas as pd
from typing import Optional
from keywords.funcional_keywords_deduplicado import build_master_deduplicated


def cargar_deduplicados(excel_data: Optional[pd.ExcelFile]) -> None:
    """
    Carga y guarda la tabla deduplicada oficial en session_state.

    Esta tabla se considera la versión limpia y central, y no debe modificarse
    directamente desde otros módulos (como Estadística). 
    Se debe usar st.session_state.master_deduped como referencia única.
    """
    if excel_data is None:
        st.warning("Primero debes subir un archivo Excel en la sección Datos.")
        return

    if "master_deduped" not in st.session_state:
        df_dedup = build_master_deduplicated(excel_data)
        st.session_state.master_deduped = df_dedup
