# listing/app_listing_semantico.py

import streamlit as st
from typing import Optional
from utils.nav_utils import render_subnav

from listing.app_listing_tokenizacion import (
    mostrar_tokens_lematizados,
    mostrar_embeddings_visualizacion,
    mostrar_clusters_semanticos
)

from listing.loader_listing_mercado import cargar_inputs_listing_enriquecido


def mostrar_listing_semantico(excel_data: Optional[object] = None):
    """
    Contenedor principal para la vista de SEO semántico (lemmatización, embeddings, clusters, inputs enriquecidos).
    """
    st.caption(
        "Explora y estructura tokens estratégicos con agrupación semántica para listings optimizados.")

    secciones = {
        "lemmas": ("Lematización", "lemmas"),
        "embedding": ("Embeddings y PCA", "embedding"),
        "clusters": ("Clusters semánticos", "clusters"),
        "preview": ("Vista previa para listing", "preview")
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

    elif subvista == "preview":
        st.markdown("#### Inputs enriquecidos para generación de listing")
        df_final = cargar_inputs_listing_enriquecido()
        if df_final.empty:
            st.warning("No se pudo generar la tabla final de inputs.")
        else:
            st.dataframe(df_final, use_container_width=True)
