# listing/app_listing_semantico.py

import streamlit as st
from typing import Optional
from utils.nav_utils import render_subnav

from listing.app_listing_tokenizacion import (
    mostrar_tokens_lematizados,
    mostrar_embeddings_visualizacion,
    mostrar_clusters_semanticos
)


def mostrar_listing_semantico(excel_data: Optional[object] = None):
    """
    Contenedor principal para la vista de SEO semántico (lemmatización, embeddings, clusters).
    """
    st.caption(
        "Explora y estructura tokens estratégicos con agrupación semántica para listings optimizados.")

    secciones = {
        "lemmas": ("Lematización", "lemmas"),
        "embedding": ("Embeddings y PCA", "embedding"),
        "clusters": ("Clusters semánticos", "clusters")
    }

    subvista = render_subnav(default_key="lemmas", secciones=secciones)
    st.divider()

    if excel_data is None:
        st.warning("Primero debes subir un archivo en la sección Datos.")
        return

    if subvista == "lemmas":
        mostrar_tokens_lematizados(excel_data)

    elif subvista == "embedding":
        mostrar_embeddings_visualizacion(excel_data)

    elif subvista == "clusters":
        mostrar_clusters_semanticos(excel_data)
