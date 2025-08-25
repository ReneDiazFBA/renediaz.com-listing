# keywords/app_keywords_deduplicado.py
import streamlit as st
import pandas as pd
from typing import Optional

from keywords.funcional_keywords_deduplicado import construir_tabla_maestra_raw


def mostrar_keywords_deduplicado(excel_data: Optional[pd.ExcelFile] = None):
    st.markdown("### Vista: Maestra Raw")
    st.caption(
        "Unión completa de todas las fuentes (CustKW, CompKW, MiningKW) sin deduplicar.")

    if excel_data is None:
        st.warning("Primero debes subir un archivo en la sección Datos.")
        return

    try:
        df_raw = construir_tabla_maestra_raw(excel_data)
        st.dataframe(df_raw.head(100), use_container_width=True)
    except Exception as e:
        st.error(f"Error al construir la tabla maestra raw: {e}")
