import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA

from listing.funcional_listing_tokenizacion import (
    tokenizar_keywords,
    priorizar_tokens,
    lemmatizar_tokens_priorizados,
    generar_embeddings,
    agrupar_embeddings_kmeans
)

# ------------------------------------------------------------
# 1) Tokenización base
# ------------------------------------------------------------


def mostrar_listing_tokenizacion(excel_data=None):
    st.subheader("Tokenización de Keywords Estratégicas")

    df = tokenizar_keywords()
    if df.empty:
        st.warning("No se pudo cargar la tabla de keywords tokenizadas.")
        return

    st.caption("Vista previa de tokens generados por término:")
    st.dataframe(df[["Search Terms", "tokens", "tier"]],
                 use_container_width=True)


# ------------------------------------------------------------
# 2) Tokens priorizados
# ------------------------------------------------------------
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
        "¿Incluir tier: Diferenciación?", value=False
    )

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
        df_tokens[["token", "frecuencia", "tier_origen"]], use_container_width=True)


# ------------------------------------------------------------
# 3) Lematización
# ------------------------------------------------------------
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
    st.dataframe(
        df_lemas[["token_original", "token_lema", "frecuencia", "tier_origen"]],
        use_container_width=True
    )

    st.session_state["listing_tokens"] = df_lemas


# ------------------------------------------------------------
# 4) Embeddings + PCA
# ------------------------------------------------------------
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
            datos["pca_x"], datos["pca_y"],
            label=tier, s=60, alpha=0.7,
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


# ------------------------------------------------------------
# 5) Clusters semánticos
# ------------------------------------------------------------
def mostrar_clusters_semanticos(excel_data=None):
    st.subheader("Clusterización Semántica de Tokens")

    n_clusters = st.slider(
        "Número de clusters K para agrupación semántica",
        min_value=2, max_value=15, value=6, step=1
    )

    # Reusar pipeline completo
    df_tokens = priorizar_tokens(["Top 25%", "Top 50%"], ["Top 25%"], [])
    if df_tokens.empty:
        st.warning("No hay tokens priorizados.")
        return

    df_lemas = lemmatizar_tokens_priorizados(df_tokens)
    df_embed = generar_embeddings(df_lemas)

    df_cluster = agrupar_embeddings_kmeans(df_embed, n_clusters=n_clusters)
    if df_cluster.empty:
        st.warning("No se pudo clusterizar.")
        return

    # Visualizar clusters en 2D
    fig, ax = plt.subplots(figsize=(10, 6))
    cmap = plt.get_cmap("tab10")

    for cluster_id in sorted(df_cluster["cluster"].unique()):
        datos = df_cluster[df_cluster["cluster"] == cluster_id]
        ax.scatter(
            datos["x"], datos["y"],
            label=f"Cluster {cluster_id}",
            s=60, alpha=0.7,
            color=cmap(cluster_id % 10)
        )
        for _, row in datos.iterrows():
            ax.text(row["x"] + 0.01, row["y"] + 0.01,
                    row["token_lema"], fontsize=8, alpha=0.5)

    ax.set_title("Clusters Semánticos de Tokens")
    ax.set_xlabel("PCA 1")
    ax.set_ylabel("PCA 2")
    st.pyplot(fig)

    # Guardar clusters en sesión (para Mercado que los consume)
    st.session_state["listing_clusters"] = df_cluster
    _df = st.session_state.get("listing_clusters", pd.DataFrame())
    if isinstance(_df, pd.DataFrame) and not _df.empty:
        st.session_state["df_lemas_cluster"] = _df.copy()


# ------------------------------------------------------------
# 6) VISTA PREVIA — lee DIRECTO la tabla final de Mercado
# ------------------------------------------------------------
# ------------------------------------------------------------
# 6) VISTA PREVIA — lee DIRECTO la tabla final de Mercado
# ------------------------------------------------------------
def mostrar_preview_inputs_listing():
    import pandas as pd
    import streamlit as st
    from mercado.loader_inputs_listing import cargar_inputs_para_listing

    st.subheader("Inputs unificados para generación de Listing")

    df = cargar_inputs_para_listing()

    if not isinstance(df, pd.DataFrame) or df.empty:
        st.info("No hay datos aún. Sube tu Excel (CustData) y, si quieres, genera insights en Mercado. "
                "Esta vista arma la tabla sin depender de 'Tabla final de Mercado'.")
        return

    # Conteo por Tipo (diagnóstico)
    if "Tipo" in df.columns:
        counts = (
            df["Tipo"].astype(str).str.strip()
            .value_counts().rename_axis("Tipo").reset_index(name="Filas")
        )
        st.caption("Conteo por Tipo")
        st.dataframe(counts, use_container_width=True, hide_index=True)

    # Render por bloques principales (lo que pediste)
    def _show(title, mask):
        st.markdown(f"**{title}**")
        cols = [c for c in ["Contenido", "Etiqueta", "Fuente"] if c in df.columns]
        sub = df.loc[mask, cols] if cols else df.loc[mask]
        if sub.empty:
            st.write("—")
        else:
            st.dataframe(sub, use_container_width=True, hide_index=True)

    tipo = df["Tipo"].astype(str).str.strip().str.lower(
    ) if "Tipo" in df.columns else pd.Series([], dtype=str)
    c1, c2 = st.columns(2)

    with c1:
        _show("Marca", tipo.eq("marca"))
        _show("Descripción breve", tipo.eq("descripción breve"))
        _show("Beneficios valorados", tipo.eq("beneficio"))
        _show("Buyer persona", tipo.eq("buyer persona"))
        _show("Pros", tipo.eq("pro"))
        _show("Emociones positivas", tipo.eq("emoción positiva"))
        _show("Tokens diferenciadores (+)", tipo.eq("token diferenciador (+)"))
        _show("Léxico editorial", tipo.eq("léxico editorial"))

    with c2:
        _show("Cons", tipo.eq("con"))
        _show("Emociones negativas", tipo.eq("emoción negativa"))
        _show("Tokens diferenciadores (–)", tipo.eq("token diferenciador (-)"))
        _show("Atributos (cliente)", tipo.eq("atributo"))
        _show("Variaciones (cliente)", tipo.eq(
            "variación") | tipo.eq("variacion"))
        _show("Recomendaciones visuales", tipo.eq("recomendación visual"))
        _show("Tokens semánticos (cluster)", tipo.eq("token semántico"))
        _show("Seeds Core", tipo.eq("seed core"))

    with st.expander("Ver tabla completa", expanded=False):
        st.dataframe(df, use_container_width=True, hide_index=True)
