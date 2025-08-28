# listing/app_listing_tokenizacion.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from listing.funcional_listing_tokenizacion import (
    tokenizar_keywords,
    priorizar_tokens,
    lemmatizar_tokens_priorizados,
    generar_embeddings
)


def mostrar_listing_tokenizacion(excel_data=None):
    st.subheader("Tokenización de Keywords Estratégicas")

    df = tokenizar_keywords()
    if df.empty:
        st.warning("No se pudo cargar la tabla de keywords tokenizadas.")
        return

    st.caption("Vista previa de tokens generados por término:")
    st.dataframe(df[["Search Terms", "tokens", "tier"]],
                 use_container_width=True)


def mostrar_tokens_priorizados(excel_data=None):
    st.subheader("Tokenización priorizada de keywords estratégicas")

    cuartiles_directa = st.multiselect(
        "Cuartiles a incluir — Oportunidad directa",
        options=["Top 25%", "Top 50%", "Medio 50%", "Bottom 25%"],
        default=["Top 25%", "Top 50%"]
    )

    cuartiles_especial = st.multiselect(
        "Cuartiles a incluir — Especialización",
        options=["Top 25%", "Top 50%", "Medio 50%", "Bottom 25%"],
        default=["Top 25%"]
    )

    incluir_diferenciacion = st.checkbox(
        "¿Incluir tier: Diferenciación?", value=False)

    cuartiles_diferenciacion = []
    if incluir_diferenciacion:
        cuartiles_diferenciacion = st.multiselect(
            "Cuartiles a incluir — Diferenciación",
            options=["Top 25%", "Top 50%", "Medio 50%", "Bottom 25%"],
            default=["Top 25%"]
        )

    df_tokens = priorizar_tokens(
        cuartiles_directa,
        cuartiles_especial,
        cuartiles_diferenciacion if incluir_diferenciacion else []
    )
    if df_tokens.empty:
        st.warning("No se pudo generar el listado de tokens priorizados.")
        return

    orden_tiers = {
        "Core": 1,
        "Oportunidad crítica": 2,
        "Oportunidad directa": 3,
        "Especialización": 4,
        "Diferenciación": 5
    }

    df_tokens["orden"] = df_tokens["tier_origen"].map(orden_tiers)
    df_tokens.sort_values(["orden", "token"], inplace=True)

    st.caption("Tokens únicos priorizados por tier estratégico. Si un token aparece más de una vez, se muestra su frecuencia.")
    st.dataframe(
        df_tokens[["token", "frecuencia", "tier_origen"]],
        use_container_width=True
    )


def mostrar_tokens_lematizados(excel_data=None):
    st.subheader("Lematización de tokens priorizados")

    # Filtros de cuartiles y diferenciación
    cuartiles_directa = st.multiselect(
        "Cuartiles a incluir — Oportunidad directa",
        options=["Top 25%", "Top 50%", "Medio 50%", "Bottom 25%"],
        default=["Top 25%", "Top 50%"],
        key="directa_lemmas"
    )

    cuartiles_especial = st.multiselect(
        "Cuartiles a incluir — Especialización",
        options=["Top 25%", "Top 50%", "Medio 50%", "Bottom 25%"],
        default=["Top 25%"],
        key="especial_lemmas"
    )

    incluir_diferenciacion = st.checkbox(
        "¿Incluir tier: Diferenciación?", value=False, key="check_dif_lemmas"
    )

    cuartiles_diferenciacion = []
    if incluir_diferenciacion:
        cuartiles_diferenciacion = st.multiselect(
            "Cuartiles a incluir — Diferenciación",
            options=["Top 25%", "Top 50%", "Medio 50%", "Bottom 25%"],
            default=["Top 25%"],
            key="dif_lemmas_multiselect"
        )

    # Priorizar y lematizar tokens
    df_tokens = priorizar_tokens(
        cuartiles_directa,
        cuartiles_especial,
        cuartiles_diferenciacion if incluir_diferenciacion else []
    )
    if df_tokens.empty:
        st.warning("No se pudo generar el listado de tokens priorizados.")
        return

    df_lemas = lemmatizar_tokens_priorizados(df_tokens)

    if df_lemas.empty:
        st.warning("No se pudo lematizar la lista.")
        return

    st.caption("Tokens lematizados consolidados por prioridad y frecuencia:")
    st.dataframe(df_lemas[["token_original", "token_lema", "frecuencia", "tier_origen"]],
                 use_container_width=True)


def mostrar_embeddings_visualizacion(excel_data=None):
    st.subheader("Embeddings y Visualización Semántica")

    st.info("Este gráfico muestra la agrupación semántica de los tokens lematizados en 2D usando PCA.")

    # Reusar pipeline de tokens → lemas → vectores
    cuartiles_directa = ["Top 25%", "Top 50%"]
    cuartiles_especial = ["Top 25%"]
    cuartiles_diferenciacion = []

    df_tokens = priorizar_tokens(
        cuartiles_directa,
        cuartiles_especial,
        cuartiles_diferenciacion
    )

    if df_tokens.empty:
        st.warning("No hay tokens priorizados para visualizar.")
        return

    df_lemas = lemmatizar_tokens_priorizados(df_tokens)
    df_embed = generar_embeddings(df_lemas)

    if df_embed.empty or "vector" not in df_embed.columns:
        st.warning("No se pudieron generar embeddings para los tokens.")
        return

    # Reducción PCA
    vectores = df_embed["vector"].tolist()
    pca = PCA(n_components=2)
    puntos_2d = pca.fit_transform(vectores)

    df_embed["pca_x"] = puntos_2d[:, 0]
    df_embed["pca_y"] = puntos_2d[:, 1]

    # Gráfico
    fig, ax = plt.subplots(figsize=(10, 6))
    colores = {
        "Core": "#0071bc",
        "Oportunidad crítica": "#f7931e",
        "Oportunidad directa": "#28a745",
        "Especialización": "#6f42c1",
        "Diferenciación": "#dc3545"
    }

    for tier in df_embed["tier_origen"].unique():
        datos = df_embed[df_embed["tier_origen"] == tier]
        ax.scatter(
            datos["pca_x"],
            datos["pca_y"],
            label=tier,
            s=60,
            alpha=0.7,
            color=colores.get(tier, "gray")
        )

    for _, row in df_embed.iterrows():
        ax.text(row["pca_x"] + 0.01, row["pca_y"] + 0.01,
                row["token_lema"], fontsize=8, alpha=0.6)

    ax.set_title("Tokens Lematizados Embebidos — Proyección PCA")
    ax.set_xlabel("Componente 1")
    ax.set_ylabel("Componente 2")
    ax.legend()
    st.pyplot(fig)
