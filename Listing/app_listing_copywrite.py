# listing/app_listing_copywrite.py
# UI de Copywriting para la pestaña "Copywriting" del Dashboard.
# Muestra Title, 5 Bullets, Description y Backend, con conteos exactos.
# Backend: cuenta bytes ignorando espacios.

import json
import streamlit as st
import pandas as pd

from listing.funcional_listing_copywrite import lafuncionqueejecuta_listing_copywrite

# ---- Auto-load copy rules from code (so you don't need PDFs at runtime) ----
try:
    from listing.rules_listing_copywrite import COPY_RULES_GENERAL as _DEFAULT_COPY_RULES
except Exception:
    _DEFAULT_COPY_RULES = {}

if "copy_rules" not in st.session_state or not st.session_state.get("copy_rules"):
    st.session_state["copy_rules"] = _DEFAULT_COPY_RULES
# ---------------------------------------------------------------------------


def _get_inputs_df() -> pd.DataFrame:
    df = st.session_state.get("inputs_para_listing", pd.DataFrame())
    if not isinstance(df, pd.DataFrame):
        return pd.DataFrame()
    return df


def _export_buttons(draft: dict):
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "⬇️ Descargar JSON",
            data=json.dumps(draft, ensure_ascii=False, indent=2),
            file_name="listing_draft_en.json",
            mime="application/json",
            use_container_width=True,
        )
    with col2:
        st.download_button(
            "⬇️ Backend Search Terms (.txt)",
            data=draft.get("search_terms", ""),
            file_name="backend_search_terms.txt",
            mime="text/plain",
            use_container_width=True,
        )


def _no_space_bytes_len(s: str) -> int:
    """Cuenta bytes en UTF-8 ignorando espacios."""
    return len((s or "").replace(" ", "").encode("utf-8"))


def mostrar_listing_copywrite(excel_data=None):
    st.subheader("Copywriting")
    st.caption(
        "Genera Title, Bullets, Description y Backend (EN) desde los inputs consolidados.")

    df_inputs = _get_inputs_df()

    if df_inputs.empty:
        st.warning(
            "No hay inputs disponibles. Ve a **Mercado → Cliente / Tabla** para construir 'inputs_para_listing'.")
        with st.expander("¿Qué debería ver aquí?", expanded=False):
            st.markdown(
                "- Filas como **Nombre sugerido**, **Descripción breve**, **Beneficio**, **Atributo**, **Variación**, "
                "**Emoción**, **Buyer persona**, **Léxico editorial**, y **Token Semántico** (Fuente: Clustering)."
            )
        return

    with st.expander("Ver inputs fuente (debug)", expanded=False):
        st.dataframe(df_inputs, use_container_width=True)

    st.divider()

    # Controles
    c1, c2 = st.columns([1, 2])
    with c1:
        use_ai = st.toggle("Use AI (cheap)", value=True,
                           help="IA económica (gpt-4o-mini) si hay OPENAI_API_KEY. Si no, fallback 0$.")
    with c2:
        cost_saver = st.toggle(
            "Cost saver", value=True, help="Recorta el prompt/inputs para abaratar pruebas.")

    if st.button("Generate copy", type="primary", use_container_width=True):
        try:
            draft = lafuncionqueejecuta_listing_copywrite(
                inputs_df=df_inputs,
                use_ai=use_ai,
                cost_saver=cost_saver,
                rules=st.session_state.get("copy_rules"),
            )
            st.success("Borrador generado.")
            st.session_state["draft_listing"] = draft
        except Exception as e:
            st.error(f"Error al generar copy: {e}")
            return

    draft = st.session_state.get("draft_listing", {})
    if not draft:
        st.info("Aún no hay borrador. Haz clic en **Generate copy**.")
        return

    # --- Render del borrador ---
    st.markdown("### Draft (EN)")

    # Title
    st.markdown("**Title**")
    title_data = draft.get("title", "")
    if isinstance(title_data, dict):
        st.markdown("**Parent**")
        st.caption(
            f"Desktop ({len(title_data.get('parent',{}).get('desktop',''))} chars)")
        st.code(title_data.get("parent", {}).get("desktop", ""))
        st.caption(
            f"Mobile ({len(title_data.get('parent',{}).get('mobile',''))} chars)")
        st.code(title_data.get("parent", {}).get("mobile", ""))
        var_keys = [k for k in title_data.keys() if k != "parent"]
        if var_keys:
            st.markdown("**Variations**")
        for vk in var_keys:
            st.markdown(f"- **{vk}**")
            st.caption(
                f"Desktop ({len(title_data[vk].get('desktop',''))} chars)")
            st.code(title_data[vk].get("desktop", ""))
            st.caption(
                f"Mobile ({len(title_data[vk].get('mobile',''))} chars)")
            st.code(title_data[vk].get("mobile", ""))
    else:
        st.code(title_data)
        st.caption(f"Length: {len(title_data)} chars")

    # Bullets
    st.markdown("**Bullets (5)**")
    bullets_data = draft.get("bullets", [])
    if isinstance(bullets_data, dict):
        st.markdown("**Parent**")
        parent = bullets_data.get("parent", []) or []
        for i, b in enumerate(parent[:5], 1):
            st.write(f"{i}. {b}")
            st.caption(f"Length: {len(b)} chars")
        var_keys = [k for k in bullets_data.keys() if k != "parent"]
        if var_keys:
            st.markdown("**Variations**")
        for vk in var_keys:
            st.markdown(f"- **{vk}**")
            vlist = bullets_data.get(vk, []) or []
            for i, b in enumerate(vlist[:5], 1):
                st.write(f"{i}. {b}")
                st.caption(f"Length: {len(b)} chars")
    else:
        for i, b in enumerate(bullets_data[:5], 1):
            st.write(f"{i}. {b}")
            st.caption(f"Length: {len(b)} chars")

    # Description
    st.markdown("**Description**")
    description = draft.get("description", "")
    st.write(description)
    st.caption(f"Length: {len(description)} chars")

    # Backend
    st.markdown("**Backend Search Terms**")
    backend = draft.get("search_terms", "")
    st.code(backend)
    backend_bytes = _no_space_bytes_len(backend)
    st.caption(f"Length: {backend_bytes} bytes (spaces not counted)")

    st.divider()
    _export_buttons(draft)
