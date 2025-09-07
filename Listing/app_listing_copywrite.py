# listing/app_listing_copywrite.py

import json
import streamlit as st
import pandas as pd

from listing.funcional_listing_copywrite import (
    generar_listing_completo_desde_df,
    bytes_no_spaces,
    compliance_report,
    apply_auto_fixes,
)


def _get_inputs_df() -> pd.DataFrame:
    df = st.session_state.get("inputs_para_listing", pd.DataFrame())
    return df if isinstance(df, pd.DataFrame) else pd.DataFrame()


def mostrar_listing_copywrite(excel_data=None):
    st.subheader("Copywriting (EN)")
    st.caption("Generate Titles (desktop+mobile per variation), 5 Bullets, Description (1500–1800, multi-paragraph) and Backend in one shot, with compliance checks and auto-fixes.")

    df_inputs = _get_inputs_df()
    if df_inputs.empty:
        st.warning(
            "No inputs found. Go to **Mercado → Cliente / Tabla** to build 'inputs_para_listing'.")
        with st.expander("What should be here?", expanded=False):
            st.markdown(
                "- Rows like **Marca**, **Descripción breve**, **Beneficio/Beneficio valorado/Ventaja**, "
                "**Atributo**, **Variación**, **Emoción**, **Buyer persona**, **Léxico editorial**, "
                "and **SEO semántico (Core/Cluster)**."
            )
        return

    with st.expander("View source inputs (debug)", expanded=False):
        st.dataframe(df_inputs, use_container_width=True, hide_index=True)

    st.divider()
    model = st.selectbox("OpenAI model", [
                         "gpt-4o-mini"], index=0, help="Economical model for drafting.")
    if st.button("Generate full listing (EN)", type="primary", use_container_width=True):
        try:
            draft = generar_listing_completo_desde_df(df_inputs, model=model)
            st.session_state["draft_listing_full_en"] = draft
            st.success("Draft generated.")
        except Exception as e:
            st.error(f"Error generating listing: {e}")
            return

    draft = st.session_state.get("draft_listing_full_en", {})
    if not draft:
        st.info("No draft yet. Click **Generate full listing (EN)**.")
        return

    # ───────── Quality & Compliance Panel ─────────
    st.markdown("### Quality & Compliance")
    comp = draft.get("_compliance") or compliance_report(draft)

    # Titles
    if comp.get("titles"):
        for t in comp["titles"]:
            issues = t.get("issues", [])
            v = t.get("variation", "")
            color = "🟢" if not issues else "🟠"
            st.write(f"{color} **Title – variation:** {v or '(none)'}")
            if issues:
                for it in issues:
                    st.caption(f"• {it}")

    # Bullets
    if comp.get("bullets"):
        if len(comp["bullets"]) == 0:
            st.write("🟢 **Bullets:** OK")
        else:
            st.write("🟠 **Bullets:**")
            for it in comp["bullets"]:
                st.caption(f"• {it}")

    # Description
    if comp.get("description"):
        if len(comp["description"]) == 0:
            st.write("🟢 **Description:** OK")
        else:
            st.write("🟠 **Description:**")
            for it in comp["description"]:
                st.caption(f"• {it}")

    # Backend
    if comp.get("backend"):
        if len(comp["backend"]) == 0:
            st.write("🟢 **Backend:** OK")
        else:
            b = draft.get("search_terms", "")
            st.write(
                f"🟠 **Backend:** {bytes_no_spaces(b)} bytes (spaces removed)")
            for it in comp["backend"]:
                st.caption(f"• {it}")

    # Auto-fix toggles
    st.markdown("#### Auto-fix")
    c1, c2, c3 = st.columns(3)
    with c1:
        fix_titles = st.toggle("Auto-trim titles", value=True,
                               help="Trims desktop (>180) and mobile (>80) at safe boundaries.")
    with c2:
        fix_backend = st.toggle("Auto-trim backend", value=True,
                                help="Removes surface-duplicate tokens and trims to 243–249 bytes.")
    with c3:
        fix_description = st.toggle("Normalize description", value=True,
                                    help="Enforces 1500–1800 chars, multiple paragraphs, and <br><br> only.")

    if st.button("Apply fixes", use_container_width=True):
        fixed = apply_auto_fixes(
            draft,
            fix_titles=fix_titles,
            fix_backend=fix_backend,
            fix_description=fix_description,
        )
        st.session_state["draft_listing_full_en"] = fixed
        st.success("Fixes applied.")

    st.divider()

    # Titles
    st.markdown("### Titles (per variation)")
    titles = st.session_state["draft_listing_full_en"].get("titles", [])
    if titles:
        for t in titles:
            v = t.get("variation", "")
            d = t.get("desktop", "")
            m = t.get("mobile", "")
            with st.container(border=True):
                st.markdown(f"**Variation:** {v}")
                st.caption(f"Desktop ({len(d)} chars)")
                st.code(d, language=None)
                st.caption(f"Mobile ({len(m)} chars)")
                st.code(m, language=None)
    else:
        st.info("No titles returned.")

    # Bullets
    st.markdown("### Bullets (5)")
    bullets = st.session_state["draft_listing_full_en"].get(
        "bullets", []) or []
    for i, b in enumerate(bullets[:5], 1):
        st.write(f"{i}. {b}")
        st.caption(f"Length: {len(b)} chars")

    vb = st.session_state["draft_listing_full_en"].get(
        "variation_bullets", {}) or {}
    if vb:
        with st.expander("Per-variation bullets", expanded=False):
            for var, arr in vb.items():
                with st.container(border=True):
                    st.markdown(f"**{var}**")
                    for i, b in enumerate((arr or [])[:5], 1):
                        st.write(f"{i}. {b}")
                        st.caption(f"Length: {len(b)} chars")

    # Description
    st.markdown("### Description")
    desc = st.session_state["draft_listing_full_en"].get("description", "")
    st.write(desc, unsafe_allow_html=True)
    st.caption(f"Length: {len(desc)} chars")

    # Backend
    st.markdown("### Backend Search Terms")
    backend = st.session_state["draft_listing_full_en"].get("search_terms", "")
    st.code(backend)
    st.caption(f"Bytes (spaces removed): {bytes_no_spaces(backend)}")

    # Export
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "⬇️ Download JSON draft",
            data=json.dumps(
                st.session_state["draft_listing_full_en"], ensure_ascii=False, indent=2),
            file_name="listing_draft_en.json",
            mime="application/json",
            use_container_width=True,
        )
    with col2:
        st.download_button(
            "⬇️ Backend search terms (.txt)",
            data=backend,
            file_name="backend_search_terms.txt",
            mime="text/plain",
            use_container_width=True,
        )
