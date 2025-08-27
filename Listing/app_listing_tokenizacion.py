# listing/app_listing_datos.py

import streamlit as st
from typing import Optional

from listing.funcional_listing_tokenizacion import (
    mostrar_listing_tokenizacion,
    mostrar_tokens_priorizados
)


def mostrar_listing(excel_data: Optional[object] = None):
    st.title("ReneDiaz.com Dashboard — Listing")
    st.caption("Tokenización, copywriting, visuales, Brand Story y A+.")

    subvista = st.radio(
        "Secciones disponibles:",
        options=["tokenizacion", "copywrite",
                 "imagenes", "brandstory", "aplus"],
        format_func=lambda x: {
            "tokenizacion": "Tokenización",
            "copywrite": "Copywriting",
            "imagenes": "Imágenes",
            "brandstory": "Brand Story",
            "aplus": "A+ Content"
        }.get(x, x),
        horizontal=True,
        key="nav_listing"
    )

    st.divider()

    if subvista == "tokenizacion":
        mostrar_listing_tokenizacion(excel_data)
        st.divider()
        mostrar_tokens_priorizados(excel_data)
    elif subvista == "copywrite":
        from listing.app_listing_copywrite import mostrar_listing_copywrite
        mostrar_listing_copywrite(excel_data)
    elif subvista == "imagenes":
        from listing.app_listing_imagenes import mostrar_listing_imagenes
        mostrar_listing_imagenes(excel_data)
    elif subvista == "brandstory":
        from listing.app_listing_brandstory import mostrar_listing_brandstory
        mostrar_listing_brandstory(excel_data)
    elif subvista == "aplus":
        from listing.app_listing_aplus import mostrar_listing_aplus
        mostrar_listing_aplus(excel_data)
    else:
        st.error("Sección no reconocida en Listing.")
