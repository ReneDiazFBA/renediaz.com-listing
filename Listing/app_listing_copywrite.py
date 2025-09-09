# listing/app_listing_copywrite.py
# UI de Copywriting con generación por ETAPA: Titles, Bullets, Description, Backend.
# - Cada botón genera SOLO su bloque y lo guarda en session_state["draft_listing"] sin tocar los demás.
# - Muestra conteos exactos (chars / bytes sin espacios para backend).
# - Soporta 'rules' en session, pero NO impone reglas extras (el prompt ya contiene SOP/Brief).

import json
import streamlit as st
import pandas as pd

from listing.funcional_listing_copywrite import run_listing_stage

# ---- Auto-load copy rules from code (opcional; no obligatorio para títulos) ----
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


def _no_space_bytes_len(s: str) -> int:
    return len((s or "").replace(" ", "").encode("utf-8"))


def _export_buttons(draft: dict):
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "⬇️ Descargar JSON (draft completo)",
            data=json.dumps(draft, ensure_ascii=False, indent=2),
            file_name="listing_draft_en.json",
            mime="application/json",
            use_container_width=True,
        )
    with col2:
        backend = ""
        # permite exportar backend si existe en el draft
        if isinstance(draft.get("search_terms"), str):
            backend = draft.get("search_terms") or ""
        st.download_button(
            "⬇️ Backend Search Terms (.txt)",
            data=backend,
            file_name="backend_search_terms.txt",
            mime="text/plain",
            use_container_width=True,
        )


def mostrar_listing_copywrite(excel_data=None):
    st.subheader("Copywriting")
    st.caption(
        "Genera por ETAPA: Titles, Bullets, Description y Backend (EN) desde 'inputs_para_listing'.")

    df_inputs = _get_inputs_df()

    if df_inputs.empty:
        st.warning(
            "No hay inputs disponibles. Ve a **Mercado → Cliente / Tabla** para construir 'inputs_para_listing'."
        )
        with st.expander("¿Qué debería ver aquí?", expanded=False):
            st.markdown(
                "- Filas como **Nombre sugerido**, **Descripción breve**, **Beneficio**, **Atributo**, **Variación**, "
                "**Emoción**, **Buyer persona**, **Léxico editorial**, y **Token Semántico (SEO Core)**."
            )
        return

    with st.expander("Ver inputs fuente (debug)", expanded=False):
        st.dataframe(df_inputs, use_container_width=True)

    st.divider()

    # Controles globales
    c1, c2 = st.columns([1, 2])
    with c1:
        use_ai = st.toggle("Use AI (cheap)", value=True,
                           help="IA económica (gpt-4o-mini) si hay OPENAI_API_KEY.")
    with c2:
        cost_saver = st.toggle("Cost saver", value=True,
                               help="Recorta filas por tipo para abaratar pruebas (no cambia semántica).")

    if "draft_listing" not in st.session_state:
        st.session_state["draft_listing"] = {}

    # ------------------ Botones por ETAPA ------------------
    st.markdown("### Generación por etapa")

    bcol1, bcol2, bcol3, bcol4 = st.columns(4)
    with bcol1:
        if st.button("Generate Titles", use_container_width=True):
            try:
                part = run_listing_stage(
                    df_inputs, "title", cost_saver=cost_saver, rules=st.session_state.get("copy_rules"))
                st.session_state["draft_listing"].update(part)
                st.success("Titles generados.")
            except Exception as e:
                st.error(f"Error en Titles: {e}")

    with bcol2:
        if st.button("Generate Bullets", use_container_width=True):
            try:
                part = run_listing_stage(
                    df_inputs, "bullets", cost_saver=cost_saver, rules=st.session_state.get("copy_rules"))
                st.session_state["draft_listing"].update(part)
                st.success("Bullets generados.")
            except Exception as e:
                st.error(f"Error en Bullets: {e}")

    with bcol3:
        if st.button("Generate Description", use_container_width=True):
            try:
                part = run_listing_stage(
                    df_inputs, "description", cost_saver=cost_saver, rules=st.session_state.get("copy_rules"))
                st.session_state["draft_listing"].update(part)
                st.success("Description generada.")
            except Exception as e:
                st.error(f"Error en Description: {e}")

    with bcol4:
        if st.button("Generate Backend", use_container_width=True):
            try:
                part = run_listing_stage(
                    df_inputs, "backend", cost_saver=cost_saver, rules=st.session_state.get("copy_rules"))
                st.session_state["draft_listing"].update(part)
                st.success("Backend generado.")
            except Exception as e:
                st.error(f"Error en Backend: {e}")

    draft = st.session_state.get("draft_listing", {})
    if not draft:
        st.info("Aún no hay borrador. Genera al menos una etapa.")
        return

    # ------------------ RENDER DEL BORRADOR ------------------
    st.markdown("### Draft (EN)")

    # Titles (parent + variaciones; desktop/mobile)
    if "title" in draft and isinstance(draft["title"], dict):
        st.markdown("**Title**")
        title_map = draft["title"]

        # Parent
        parent = title_map.get("parent", {})
        st.write("**Parent**")
        st.caption(f'Desktop ({len(parent.get("desktop",""))} chars)')
        st.code(parent.get("desktop", ""))
        st.caption(f'Mobile ({len(parent.get("mobile",""))} chars)')
        st.code(parent.get("mobile", ""))

        # Variations
        var_keys = [k for k in title_map.keys() if k != "parent"]
        if var_keys:
            st.write("**Variations**")
            for vk in var_keys:
                pair = title_map.get(vk, {})
                st.markdown(f"- {vk}")
                st.caption(f'Desktop ({len(pair.get("desktop",""))} chars)')
                st.code(pair.get("desktop", ""))
                st.caption(f'Mobile ({len(pair.get("mobile",""))} chars)')
                st.code(pair.get("mobile", ""))

        st.divider()

    # Bullets
    if "bullets" in draft:
        st.markdown("**Bullets (5)**")
        bmap = draft.get("bullets", {})
        # Parent
        parent_b = bmap.get("parent", [])
        st.write("**Parent**")
        for i, b in enumerate(parent_b[:5], 1):
            st.write(f"{i}. {b}")
            st.caption(f"Length: {len(b)} chars")
        # Variations
        var_keys = [k for k in bmap.keys() if k != "parent"]
        if var_keys:
            st.write("**Variations**")
            for vk in var_keys:
                st.markdown(f"- {vk}")
                items = bmap.get(vk, [])
                for i, b in enumerate(items[:5], 1):
                    st.write(f"{i}. {b}")
                    st.caption(f"Length: {len(b)} chars")
        st.divider()

    # Description
    if "description" in draft and isinstance(draft.get("description"), str):
        st.markdown("**Description**")
        description = draft.get("description", "")
        st.write(description)
        st.caption(
            f"Length: {len(description)} chars | Words: {len(description.replace('<br><br>',' ').split())}")
        st.divider()

    # Backend
    if "search_terms" in draft and isinstance(draft.get("search_terms"), str):
        st.markdown("**Backend Search Terms**")
        backend = draft.get("search_terms", "")
        st.code(backend)
        backend_bytes = _no_space_bytes_len(backend)
        st.caption(f"Length: {backend_bytes} bytes (spaces not counted)")
        st.divider()

    _export_buttons(draft)
