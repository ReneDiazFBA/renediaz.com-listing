# listing/app_listing_copywrite.py
# UI: un botón → única llamada IA → títulos, bullets, descripción, backend.
# Verifica OPENAI_API_KEY por entorno (sin st.secrets).

import os
import json
import streamlit as st
import pandas as pd

from listing.funcional_listing_copywrite import (
    generate_listing_copy,
    compliance_report,
)


def _get_inputs_df() -> pd.DataFrame:
    df = st.session_state.get("inputs_para_listing", pd.DataFrame())
    return df if isinstance(df, pd.DataFrame) else pd.DataFrame()


def _no_space_bytes_len(s: str) -> int:
    return len((s or "").replace(" ", "").encode("utf-8"))


def mostrar_listing_copywrite(excel_data=None):
    st.subheader("Copywriting (EN)")
    st.caption(
        "Generate Titles (desktop & mobile per variation), 5 Bullets, Description, and Backend in one AI call.")

    # Prechequeo de API key por entorno
    if not os.environ.get("OPENAI_API_KEY"):
        st.error(
            "Missing OPENAI_API_KEY environment variable. Set it before running.")
        st.stop()

    df_inputs = _get_inputs_df()
    if df_inputs.empty:
        st.warning(
            "No hay inputs. Ve a Mercado → Cliente/Tabla para construir 'inputs_para_listing'.")
        with st.expander("Ver inputs esperados", expanded=False):
            st.markdown(
                "- Filas: **Marca**, **Descripción breve**, **Buyer persona**, "
                "**Beneficio/Beneficio valorado/Ventaja**, **Emoción**, "
                "**Atributo**, **Variación**, **Léxico editorial**, **SEO semántico/Core**."
            )
        return

    with st.expander("View source inputs (debug)", expanded=False):
        st.dataframe(df_inputs, use_container_width=True)

    st.divider()
    model = st.selectbox("Model", ["gpt-4o-mini"],
                         index=0, help="Lowest-cost for drafting.")

    if st.button("Generate listing", type="primary", use_container_width=True):
        try:
            draft = generate_listing_copy(df_inputs, model=model)
            st.session_state["draft_listing"] = draft
            st.success("Listing generated.")
        except Exception as e:
            st.error(f"Error generating listing: {e}")
            return

    draft = st.session_state.get("draft_listing", {})
    if not draft:
        st.info("Press **Generate listing**.")
        return

    st.markdown("### Titles (per variation)")
    for t in draft.get("titles", []):
        st.markdown(
            f"**Variation:** {t.get('variation','(none)') or '(none)'}")
        desk = t.get("desktop", "")
        mobi = t.get("mobile", "")
        st.code(desk)
        st.caption(f"Desktop length: {len(desk)} chars")
        st.code(mobi)
        st.caption(f"Mobile length: {len(mobi)} chars")

    st.markdown("### Bullets (5)")
    bullets = draft.get("bullets", []) or []
    for i, b in enumerate(bullets[:5], 1):
        st.write(f"{i}. {b}")
        st.caption(f"Length: {len(b)} chars")

    st.markdown("### Description")
    desc = draft.get("description", "")
    st.write(desc, unsafe_allow_html=True)
    st.caption(f"Length: {len(desc)} chars")

    st.markdown("### Backend Search Terms")
    backend = draft.get("search_terms", "")
    st.code(backend)
    st.caption(f"Bytes (no spaces): {_no_space_bytes_len(backend)}")

    st.divider()
    rep = compliance_report(draft)
    if rep["issues"]:
        st.error("Issues found:")
        for it in rep["issues"]:
            st.write(f"- {it}")
    else:
        st.success("All checks passed.")
