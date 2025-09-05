# listing/app_listing_semantico.py

import streamlit as st
import pandas as pd
from typing import Optional
from utils.nav_utils import render_subnav

from listing.app_listing_tokenizacion import (
    mostrar_tokens_lematizados,
    mostrar_embeddings_visualizacion,
    mostrar_clusters_semanticos
)

from mercado.loader_inputs_listing import construir_inputs_listing


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
        st.markdown("### Inputs enriquecidos para generación de listing")

        from mercado.loader_inputs_listing import construir_inputs_listing

        resultados = st.session_state.get("resultados_mercado", {})

        # 👉 Elegimos la primera edición de contraste NO vacía.
        import pandas as pd
        df_edit = None
        for k in ("df_contraste_edit", "df_edit", "df_edit_atributos"):
            _cand = st.session_state.get(k)
            if isinstance(_cand, pd.DataFrame) and not _cand.empty:
                df_edit = _cand
                break
        # Si no hay edición, dejamos df_edit = None para que el loader haga fallback (texto o fuente interna)

        # Nota: el constructor también lee st.session_state["contraste_texto"] si existe.
        df_final = construir_inputs_listing(
            resultados,
            df_edit,                           # puede ser None (ok)
            # opcional: pasa excel para 'Marca'
            st.session_state.get("excel_data")
        )

        # Diagnóstico de la fuente (opcional)
        fuente = "Texto de contraste confirmado" if st.session_state.get("contraste_texto") else (
            "Tabla de contraste" if isinstance(
                df_edit, pd.DataFrame) else "Fallback automático"
        )
        st.caption(f"Fuente de Atributo/Variación: **{fuente}**")

        if df_final.empty:
            st.warning("No se pudo construir la tabla final.")
        else:
            st.dataframe(df_final, use_container_width=True)
