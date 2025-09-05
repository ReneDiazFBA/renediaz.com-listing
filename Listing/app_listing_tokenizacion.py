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


# 6) VISTA PREVIA — lee DIRECTO la tabla final de Mercado
# ------------------------------------------------------------

def mostrar_preview_inputs_listing():
    from mercado.loader_inputs_listing import construir_inputs_listing

    st.subheader("Inputs unificados para generación de Listing")

    # 👇 aquí forzamos a usar siempre la última edición de contraste
    df_edit = st.session_state.get("df_contraste_edit",
                                   st.session_state.get("df_edit",
                                                        st.session_state.get("df_edit_atributos", pd.DataFrame())))

    df = construir_inputs_listing(
        st.session_state.get("resultados_mercado", {}),
        df_edit,
        st.session_state.get("excel_data")
    )

    if not isinstance(df, pd.DataFrame) or df.empty:
        st.info("No hay datos aún. Ve a Mercado → Cliente, edita contraste y vuelve.")
        return

    st.dataframe(df, use_container_width=True, hide_index=True)
 
    # ─────────────────────────────────────────────────────────────
#  EXTRA: “Solo Contraste” (Atributos / Variaciones)
#  No toca tu tabla actual. Esto es una segunda tabla abajo.
# ─────────────────────────────────────────────────────────────
import re

st.markdown("### Solo Contraste (Atributos / Variaciones)")
st.caption("Vista aislada, calculada directo desde tu edición en 'Cliente'.")

# 1) Recuperar el df de contraste desde cualquier clave posible (robusto)
def _as_df(x):
    import pandas as pd
    if isinstance(x, pd.DataFrame):
        return x
    if isinstance(x, dict):
        try:
            return pd.DataFrame(x)
        except Exception:
            return pd.DataFrame()
    if isinstance(x, list):
        try:
            return pd.DataFrame(x)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

df_edit_candidates = [
    st.session_state.get("df_contraste_edit"),
    st.session_state.get("df_edit"),
    st.session_state.get("df_edit_atributos"),
    st.session_state.get("tabla_editable_contraste"),
    st.session_state.get("tabla_editable_contraste.data"),
    st.session_state.get("tabla_editable_contraste.value"),
]

df_contraste_src = None
for cand in df_edit_candidates:
    df_try = _as_df(cand)
    if not df_try.empty:
        df_contraste_src = df_try.copy()
        break

if df_contraste_src is None or df_contraste_src.empty:
    st.info("No encuentro una edición de Contraste en memoria. Ve a Mercado → Cliente y edita allí.")
else:
    # 2) Normalizar nombres de columnas Valor 1..4 (acepta Valor_1, value2, VALOR 3, etc.)
    def _normalize_val_cols(df):
        df = df.copy()
        colmap = {}
        seen = set()
        for c in df.columns:
            s = str(c).strip()
            m = re.search(r"(?:^|[^A-Za-z])(valor|value)\s*[_\-]?\s*([1-4])(?:[^0-9]|$)", s, flags=re.I)
            if m:
                idx = int(m.group(2))
                target = f"Valor {idx}"
                k = target
                while k in seen:  # evita colisiones raras
                    k = k + "_"
                colmap[c] = k
                seen.add(k)
        if colmap:
            df = df.rename(columns=colmap)
        return df

    dfe = _normalize_val_cols(df_contraste_src)

    # 3) Aplanar en filas: si hay 1 valor => Atributo; si hay 2+ => Variación (todas)
    val_cols = [c for c in dfe.columns if re.match(r"^Valor\s+[1-4]_*$", str(c), flags=re.I)]
    val_cols = sorted(val_cols, key=lambda x: int(re.findall(r"[1-4]", x)[0]))

    filas = []
    for _, row in dfe.iterrows():
        values = []
        for c in val_cols:
            v = str(row.get(c, "")).strip()
            if v and v.lower() not in ("nan", "none", "—", "-", "n/a", "na", ""):
                values.append(v)
        if not values:
            continue
        if len(values) == 1:
            filas.append({
                "Tipo": "Atributo",
                "Contenido": values[0],
                "Etiqueta": "Atributo Cliente",
                "Fuente": "Contraste",
            })
        else:
            for v in values:
                filas.append({
                    "Tipo": "Variación",
                    "Contenido": v,
                    "Etiqueta": "Atributo Cliente",
                    "Fuente": "Contraste",
                })

    import pandas as pd
    df_contraste_flat = pd.DataFrame(filas)

    if df_contraste_flat.empty:
        st.warning("Contraste no tiene valores en las columnas Valor 1..4.")
    else:
        # métricas rápidas
        tipos = df_contraste_flat["Tipo"].astype(str).str.lower()
        n_attr = int((tipos == "atributo").sum())
        n_var = int(((tipos == "variación") | (tipos == "variacion")).sum())
        st.caption(f"Atributos: {n_attr} · Variaciones: {n_var} · Total filas: {len(df_contraste_flat)}")

        st.dataframe(df_contraste_flat, use_container_width=True, hide_index=True)

        with st.expander("Ver fuente cruda de Contraste (lo que viene del editor)", expanded=False):
            st.dataframe(dfe, use_container_width=True, hide_index=True)
