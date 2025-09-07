# listing/app_listing_copywrite.py
# UI for a SINGLE BUTTON that generates the whole listing with AI.
# Shows lengths/bytes and basic compliance notes.

import json
import streamlit as st
import pandas as pd

from listing.funcional_listing_copywrite import (
    lafuncionqueejecuta_listing_copywrite,
    compliance_report,
)


def _get_inputs_df() -> pd.DataFrame:
    df = st.session_state.get("inputs_para_listing", pd.DataFrame())
    if not isinstance(df, pd.DataFrame):
        return pd.DataFrame()
    return df


def _no_space_bytes_len(s: str) -> int:
    return len((s or "").replace(" ", "").encode("utf-8"))


def mostrar_listing_copywrite(excel_data=None):
    st.subheader("Copywriting (EN)")
    st.caption(
        "Generate Titles (desktop & mobile per variation), 5 Bullets, Description, and Backend in one AI call.")

    df_inputs = _get_inputs_df()
    if df_inputs.empty:
        st.warning(
            "No inputs available. Build them in **Mercado → Cliente / Tabla** first.")
        with st.expander("Expected inputs (debug)"):
            st.text("Rows like: Marca, Descripción breve, Buyer persona, Beneficio valorado/Ventaja,\n"
                    "Atributo, Variación, Emoción, Léxico editorial, SEO semántico (Core/Cluster).")
        return

    with st.expander("View source inputs (debug)", expanded=False):
        st.dataframe(df_inputs, use_container_width=True)

    st.divider()

    model = st.selectbox("Model", options=[
                         "gpt-4o-mini"], index=0, help="Cheapest suitable OpenAI chat model.")

    if st.button("Generate full listing (AI)", type="primary", use_container_width=True):
        try:
            draft = lafuncionqueejecuta_listing_copywrite(
                inputs_df=df_inputs,
                model=model,
            )
            st.session_state["draft_listing"] = draft
            st.success("Listing generated.")
        except Exception as e:
            st.error(f"Error generating listing: {e}")
            return

    draft = st.session_state.get("draft_listing", {})
    if not draft:
        st.info("No draft yet. Click the button above to generate.")
        return

    # Render
    st.markdown("### Titles (per variation)")
    for t in draft.get("titles", []) or []:
        st.write(f"**Variation:** {t.get('variation','')}")
        desk = t.get("desktop", "")
        mob = t.get("mobile", "")
        st.code(desk)
        st.caption(f"Desktop length: {len(desk)} chars")
        st.code(mob)
        st.caption(f"Mobile length: {len(mob)} chars")
        st.divider()

    st.markdown("### Bullets (5)")
    bullets = draft.get("bullets", []) or []
    for i, b in enumerate(bullets, 1):
        st.write(f"{i}. {b}")
        st.caption(f"Length: {len(b)} chars")

    st.markdown("### Description")
    desc = draft.get("description", "") or ""
    st.write(desc)
    st.caption(f"Length: {len(desc)} chars")

    st.markdown("### Backend Search Terms")
    backend = draft.get("search_terms", "") or ""
    st.code(backend)
    st.caption(f"Bytes (no spaces): {_no_space_bytes_len(backend)}")

    # Compliance snapshot
    rep = compliance_report(draft)
    if rep.get("ok"):
        st.success("Basic compliance checks passed.")
    else:
        st.warning("Issues found:")
        for issue in rep.get("issues", []):
            st.write(f"- {issue}")

    # Export
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "⬇️ Download JSON",
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
