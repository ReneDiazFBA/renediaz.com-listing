# listing/app_listing_copywrite.py
# Streamlit UI — one-click generation (AI) + rendering + compliance panel.

import json
import streamlit as st
import pandas as pd

from listing.funcional_listing_copywrite import (
    build_inputs_from_df,
    generate_listing_json,
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
        "Generate Titles (per variation), 5 Bullets, Description and Backend in one pass.")

    df_inputs = _get_inputs_df()
    if df_inputs.empty:
        st.warning(
            "No inputs available. Go to Mercado → build 'inputs_para_listing' first.")
        with st.expander("What should I see here?", expanded=False):
            st.markdown(
                "- Rows like **Marca**, **Descripción breve**, **Beneficio / Ventaja**, **Atributo**, **Variación**, "
                "**Emoción**, **Buyer persona**, **Léxico editorial**, **SEO semántico (Core/Cluster)**."
            )
        return

    with st.expander("View source inputs (debug)", expanded=False):
        st.dataframe(df_inputs, use_container_width=True)

    st.divider()

    # Controls
    c1, c2 = st.columns([1, 1])
    with c1:
        model = st.selectbox(
            "Model", options=["gpt-4o-mini"], index=0, help="Economical model.")
    with c2:
        temp = st.slider("Creativity (temperature)", 0.0, 1.0, 0.2, 0.1)

    if st.button("Generate listing (AI)", type="primary", use_container_width=True):
        try:
            inputs = build_inputs_from_df(df_inputs)
            # override temperature within generate call if you add it later
            draft = generate_listing_json(inputs=inputs, model=model)
            st.session_state["draft_listing"] = draft
            st.success("Listing generated.")
        except Exception as e:
            st.error(f"Error generating listing: {e}")
            return

    draft = st.session_state.get("draft_listing", {})
    if not draft:
        st.info("No draft yet. Click **Generate listing (AI)**.")
        return

    # Render
    st.markdown("### Titles (per variation)")
    titles = draft.get("titles", [])
    if not titles:
        st.write("No titles returned.")
    else:
        for t in titles:
            st.markdown(f"- **Variation:** {t.get('variation', 'default')}")
            st.code(t.get("desktop", ""), language="text")
            st.caption(f"Desktop length: {len(t.get('desktop',''))} chars")
            st.code(t.get("mobile", ""), language="text")
            st.caption(f"Mobile length: {len(t.get('mobile',''))} chars")
            st.write("---")

    st.markdown("### Bullets (5)")
    bullets = draft.get("bullets", []) or []
    for i, b in enumerate(bullets[:5], 1):
        st.write(f"{i}. {b}")
        st.caption(f"Length: {len(b)} chars")

    st.markdown("### Description")
    description = draft.get("description", "")
    st.write(description, unsafe_allow_html=True)
    st.caption(f"Length: {len(description)} chars")

    st.markdown("### Backend Search Terms")
    backend = draft.get("search_terms", "")
    st.code(backend, language="text")
    st.caption(f"Bytes (no spaces): {_no_space_bytes_len(backend)}")

    st.divider()

    # Compliance panel
    st.markdown("### Compliance Report")
    report = compliance_report(draft)
    if report["ok"]:
        st.success("PASS — All hard constraints satisfied.")
    else:
        st.error("FAIL — Some constraints not satisfied.")
    if report["issues"]:
        for issue in report["issues"]:
            st.write(f"- {issue}")

    # Export
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
