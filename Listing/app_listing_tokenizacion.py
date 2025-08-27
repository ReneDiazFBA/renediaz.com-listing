# listing/app_listing_tokenizacion.py

import streamlit as st
from listing.funcional_listing_tokenizacion import tokenizar_keywords

def mostrar_listing_tokenizacion(excel_data=None):
    st.subheader("Tokenización de Keywords Estratégicas")

    df = tokenizar_keywords()

    if df.empty:
        st.warning("No se pudo cargar la tabla de keywords tokenizadas.")
        return

    st.caption("Vista previa de tokens generados por término:")
    st.dataframe(df[["Search Terms", "tokens"]], use_container_width=True)
