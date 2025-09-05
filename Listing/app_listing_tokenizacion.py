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
        df_tokens[["token", "frecuencia", "tier_origen"]], use_container_width=True)


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
        "¿Incluir tier: Diferenciación?", value=False, key="check_dif_lemmas")

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

    st.session_state["listing_tokens"] = df_lemas


def mostrar_embeddings_visualizacion(excel_data=None):
    st.subheader("Embeddings y Visualización Semántica")

    st.info("Este gráfico muestra la agrupación semántica de los tokens lematizados en 2D usando PCA.")

    # Reusar pipeline de tokens → lemas → vectores
    cuartiles_directa = ["Top 25%", "Top 50%"]
    cuartiles_especial = ["Top 25%"]
    cuartiles_diferenciacion = []

    df_tokens = priorizar_tokens(
        cuartiles_directa, cuartiles_especial, cuartiles_diferenciacion)

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


def plot_pca_embeddings(df: pd.DataFrame, color_by: str = "tier_origen"):
    """
    Visualiza los embeddings proyectados a 2D usando PCA.
    Puede colorear por 'tier_origen' o por 'cluster'.
    """
    if "vector" not in df.columns:
        st.warning("No se encuentran los vectores de embedding.")
        return

    # Reducción de dimensionalidad
    X = np.stack(df["vector"].values)
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X)

    df_plot = df.copy()
    df_plot["pca_1"] = X_pca[:, 0]
    df_plot["pca_2"] = X_pca[:, 1]

    # Plot
    fig, ax = plt.subplots(figsize=(8, 6))
    for grupo in df_plot[color_by].unique():
        subgrupo = df_plot[df_plot[color_by] == grupo]
        ax.scatter(subgrupo["pca_1"], subgrupo["pca_2"],
                   label=str(grupo), alpha=0.6)
        for _, row in subgrupo.iterrows():
            ax.text(row["pca_1"], row["pca_2"],
                    row["token_lema"], fontsize=7, alpha=0.6)

    ax.set_title("Tokens Lematizados Embebidos — Proyección PCA")
    ax.set_xlabel("Componente 1")
    ax.set_ylabel("Componente 2")
    ax.legend()
    st.pyplot(fig)


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
            label=f"Cluster {cluster_id}", s=60, alpha=0.7,
            color=cmap(cluster_id % 10)
        )
        for _, row in datos.iterrows():
            ax.text(row["x"] + 0.01, row["y"] + 0.01,
                    row["token_lema"], fontsize=8, alpha=0.5)

    ax.set_title("Clusters Semánticos de Tokens")
    ax.set_xlabel("PCA 1")
    ax.set_ylabel("PCA 2")
    ax.legend()
    st.pyplot(fig)

    # Guardar clusters en sesión y exponer alias esperado por Mercado
    st.session_state["listing_clusters"] = df_cluster
    _df = st.session_state.get("listing_clusters", pd.DataFrame())
    if isinstance(_df, pd.DataFrame) and not _df.empty:
        st.session_state["df_lemas_cluster"] = _df.copy()


# -------------------------------------------------------------------
# Vista previa de tabla final de inputs (lee DIRECTO desde Mercado)
def mostrar_preview_inputs_listing():
    st.subheader("Vista previa — Inputs para Listing")

    # 1) BASE: viene DIRECTO desde Mercado (sin reconstruir)
    base_df = st.session_state.get("inputs_para_listing", pd.DataFrame())
    if not isinstance(base_df, pd.DataFrame) or base_df.empty:
        st.info("Aún no hay inputs. Revisa 'Mercado → Tabla final de inputs'.")
        return

    # 2) EXTRAS DE LISTING (opcional): Tokens Semánticos + Seeds Core (sólo si existen)
    extras = []

    # 2.1) Tokens semánticos desde df_lemas_cluster / listing_clusters
    df_sem = st.session_state.get("df_lemas_cluster", pd.DataFrame())
    if (not isinstance(df_sem, pd.DataFrame)) or df_sem.empty:
        df_sem = st.session_state.get("listing_clusters", pd.DataFrame())

    if isinstance(df_sem, pd.DataFrame) and not df_sem.empty:
        df_sem = df_sem.copy()

        # columna token_lema robusta
        token_col = "token_lema"
        if token_col not in df_sem.columns:
            posibles = [c for c in df_sem.columns if c.lower() in (
                "token", "lemma", "lema", "token_lema")]
            token_col = posibles[0] if posibles else df_sem.columns[0]

        # columna cluster robusta
        cluster_col = "cluster" if "cluster" in df_sem.columns else None
        if cluster_col is None:
            if "Cluster" in df_sem.columns:
                cluster_col = "Cluster"

        # bloque de "Token Semántico" si tenemos al menos el token
        if token_col:
            tok = df_sem[token_col].astype(str)
            if cluster_col:
                cl = "Cluster " + df_sem[cluster_col].astype(str)
            else:
                cl = pd.Series(["Cluster ?"] * len(df_sem))

            bloque_tokens = pd.DataFrame({
                "Tipo": "Token Semántico",
                "Contenido": tok,
                "Etiqueta": cl,
                "Fuente": "Clustering"
            }).drop_duplicates()
            extras.append(bloque_tokens)

        # 2.2) Seeds Core (si hay alguna columna que contenga "core")
        core_mask = pd.Series([False] * len(df_sem))
        for col in df_sem.columns:
            try:
                core_mask = core_mask | df_sem[col].astype(
                    str).str.contains(r"\bcore\b", case=False, regex=True)
            except Exception:
                pass

        if core_mask.any():
            seeds = df_sem.loc[core_mask, token_col].dropna().astype(
                str).unique().tolist()
            if seeds:
                bloque_seeds = pd.DataFrame({
                    "Tipo": "seed",
                    "Contenido": seeds,
                    "Etiqueta": "lemma",
                    "Fuente": "core"
                })
                extras.append(bloque_seeds)

    # 3) Tabla final PARA VISTA (base + extras en memoria)
    if extras:
        df_view = pd.concat([base_df] + extras, ignore_index=True)
        df_view.drop_duplicates(
            subset=[c for c in ["Tipo", "Contenido",
                                "Etiqueta", "Fuente"] if c in df_view.columns],
            inplace=True
        )
    else:
        df_view = base_df.copy()

    # 4) Normalizador de Tipo para filtrar secciones (marca/atributo/variación)
    def _norm_series(s: pd.Series) -> pd.Series:
        try:
            import unicodedata
            s = s.astype(str).str.strip()
            s = s.apply(lambda x: ''.join(c for c in unicodedata.normalize(
                'NFKD', x) if not unicodedata.combining(c)))
            return s.str.lower()
        except Exception:
            return s.astype(str).str.strip().str.lower()

    tipo_norm = _norm_series(
        df_view["Tipo"]) if "Tipo" in df_view.columns else pd.Series([], dtype=str)

    # 5) Conteo por Tipo (diagnóstico)
    st.caption("Conteo por Tipo (normalizado)")
    counts = tipo_norm.value_counts().reset_index()
    counts.columns = ["Tipo (norm)", "Cantidad"]
    st.dataframe(counts, use_container_width=True, hide_index=True)

    # 6) Bloques clave: Marca / Atributos / Variaciones (sin tocar datos base)
    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("**Marca**")
        mask_marca = tipo_norm.eq("marca")
        df_m = df_view.loc[mask_marca]
        if not df_m.empty:
            cols = [c for c in ["Contenido", "Fuente"] if c in df_m.columns]
            st.dataframe(df_m[cols], use_container_width=True, hide_index=True)
        else:
            st.write("—")

        st.markdown("**Atributos**")
        mask_attr = tipo_norm.eq("atributo")
        df_a = df_view.loc[mask_attr]
        if not df_a.empty:
            cols = [c for c in ["Contenido", "Etiqueta",
                                "Fuente"] if c in df_a.columns]
            st.dataframe(df_a[cols], use_container_width=True, hide_index=True)
        else:
            st.write("—")

    with col2:
        st.markdown("**Variaciones**")
        mask_var = tipo_norm.eq("variacion")  # “variación” normalizada
        df_v = df_view.loc[mask_var]
        if not df_v.empty:
            cols = [c for c in ["Contenido", "Etiqueta",
                                "Fuente"] if c in df_v.columns]
            st.dataframe(df_v[cols], use_container_width=True, hide_index=True)
        else:
            st.write("—")

    # 7) Tabla completa (para inspección)
    with st.expander("Ver tabla completa (base + extras Listing en memoria)", expanded=False):
        st.dataframe(df_view, use_container_width=True)
