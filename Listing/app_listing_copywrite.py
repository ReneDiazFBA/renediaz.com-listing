# listing/app_listing_copywrite.py
# UI de Copywriting para la pestaña "Copywriting" del Dashboard.
# Muestra Title, 5 Bullets (<150 chars), Description y Backend (≤249 bytes).
# Se alimenta de st.session_state["inputs_para_listing"] ya construido en Mercado->Cliente/Tabla.

import json
import streamlit as st
import pandas as pd

from listing.funcional_listing_copywrite import lafuncionqueejecuta_listing_copywrite


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
        # Export para backend search terms solos
        st.download_button(
            "⬇️ Backend Search Terms (.txt)",
            data=draft.get("search_terms", ""),
            file_name="backend_search_terms.txt",
            mime="text/plain",
            use_container_width=True,
        )


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

    # Controles mínimos (no intrusivos)
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        use_ai = st.toggle("Use AI (cheap)", value=True,
                           help="IA económica (gpt-4o-mini) si hay OPENAI_API_KEY. Si no, fallback 0$.")

    with c2:
        cost_saver = st.toggle(
            "Cost saver", value=True, help="Recorta el prompt/inputs para abaratar pruebas.")

    with c3:
        st.caption(
            "Bullets < 150 chars · Backend ≤ 249 bytes (sanitizer EN aplicado)")

    if st.button("Generate copy", type="primary", use_container_width=True):
        try:
            draft = lafuncionqueejecuta_listing_copywrite(
                inputs_df=df_inputs,
                use_ai=use_ai,
                # Modelos/params se toman de entorno si quieres: OPENAI_MODEL_COPY, etc.
                cost_saver=cost_saver,
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

    # Render del borrador
    st.markdown("### Draft (EN)")

    st.markdown("**Title**")
    st.code(draft.get("title", ""))

    st.markdown("**Bullets (5 · <150 chars)**")
    bullets = draft.get("bullets", []) or []
    for i, b in enumerate(bullets[:5], 1):
        st.write(f"{i}. {b}")

    st.markdown("**Description**")
    st.write(draft.get("description", ""))

    st.markdown("**Backend Search Terms (≤249 bytes)**")
    backend = draft.get("search_terms", "")
    st.code(backend)

    # Contadores útiles
    st.caption(
        f"Title chars: {len(draft.get('title',''))} | "
        f"Backend bytes: {len((backend or '').encode('utf-8'))}/249"
    )

    st.divider()
    _export_buttons(draft)
