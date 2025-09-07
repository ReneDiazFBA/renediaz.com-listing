# listing/app_listing_copywrite.py
# UI: IA-only (gpt-4o-mini). Un botón “Generate copy”.

import json
import streamlit as st
import pandas as pd

from listing.funcional_listing_copywrite import lafuncionqueejecuta_listing_copywrite


def _get_inputs_df() -> pd.DataFrame:
    df = st.session_state.get("inputs_para_listing", pd.DataFrame())
    return df if isinstance(df, pd.DataFrame) else pd.DataFrame()


def _no_space_bytes_len(s: str) -> int:
    return len((s or "").replace(" ", "").encode("utf-8"))


def _export_buttons(draft: dict):
    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "⬇️ Descargar JSON",
            data=json.dumps(draft, ensure_ascii=False, indent=2),
            file_name="listing_draft_en.json",
            mime="application/json",
            use_container_width=True,
        )
    with c2:
        st.download_button(
            "⬇️ Backend Search Terms (.txt)",
            data=draft.get("search_terms", ""),
            file_name="backend_search_terms.txt",
            mime="text/plain",
            use_container_width=True,
        )


def mostrar_listing_copywrite(excel_data=None):
    st.subheader("Copywriting (IA)")
    st.caption(
        "Genera Title, Bullets, Description y Backend (EN) desde los inputs consolidados (IA-only).")

    df_inputs = _get_inputs_df()
    if df_inputs.empty:
        st.warning(
            "No hay inputs. Ve a Mercado → Cliente / Tabla para construir 'inputs_para_listing'.")
        with st.expander("¿Qué debería ver aquí?", expanded=False):
            st.markdown(
                "- Filas como **Marca**, **Descripción breve**, **Buyer persona**, **Beneficio valorado**, **Ventaja/Obstáculo**, "
                "**Emoción**, **Atributo/Variación**, **Léxico editorial**, **SEO semántico**."
            )
        return

    with st.expander("Ver inputs fuente (debug)", expanded=False):
        st.dataframe(df_inputs, use_container_width=True)

    st.divider()

    if st.button("Generate copy", type="primary", use_container_width=True):
        try:
            draft = lafuncionqueejecuta_listing_copywrite(inputs_df=df_inputs)
            st.session_state["draft_listing"] = draft
            st.success("Borrador generado con IA.")
        except Exception as e:
            st.error(f"Error al generar copy con IA: {e}")
            return

    draft = st.session_state.get("draft_listing", {})
    if not draft:
        st.info("Aún no hay borrador. Haz clic en **Generate copy**.")
        return

    # Render
    st.markdown("### Draft (EN)")

    # Title
    st.markdown("**Title**")
    title = draft.get("title", "")
    st.code(title)
    st.caption(f"Length: {len(title)} chars")

    # Bullets
    st.markdown("**Bullets (5)**")
    bullets = draft.get("bullets", []) or []
    for i, b in enumerate(bullets[:5], 1):
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
    st.caption(
        f"Length: {_no_space_bytes_len(backend)} bytes (spaces not counted)")

    st.divider()
    _export_buttons(draft)
