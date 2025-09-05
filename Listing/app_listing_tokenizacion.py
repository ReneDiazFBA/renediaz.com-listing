def mostrar_preview_inputs_listing():
    import re
    import pandas as pd
    import streamlit as st
    from mercado.loader_inputs_listing import construir_inputs_listing

    st.subheader("Inputs unificados para generación de Listing")

    # 1) Forzar a usar SIEMPRE la última edición de contraste
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
    st.markdown("### Solo Contraste (Atributos / Variaciones)")
    st.caption("Vista aislada, calculada directo desde tu edición en 'Cliente'.")

    # 2) Recuperar el df de contraste desde cualquier clave posible (robusto)
    def _as_df(x):
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

    df_contraste_src = pd.DataFrame()
    for cand in df_edit_candidates:
        df_try = _as_df(cand)
        if not df_try.empty:
            df_contraste_src = df_try.copy()
            break

    if df_contraste_src.empty:
        st.info("No encuentro una edición de Contraste en memoria. Ve a Mercado → Cliente y edita allí.")
        return

    # 3) Normalizar nombres de columnas Valor 1..4 (acepta Valor_1, value2, VALOR 3, etc.)
    def _normalize_val_cols(df0: pd.DataFrame) -> pd.DataFrame:
        df0 = df0.copy()
        colmap, seen = {}, set()
        for c in df0.columns:
            s = str(c).strip()
            m = re.search(r"(?:^|[^A-Za-z])(valor|value)\s*[_\-]?\s*([1-4])(?:[^0-9]|$)", s, flags=re.I)
            if m:
                idx = int(m.group(2))
                target = f"Valor {idx}"
                k = target
                while k in seen:
                    k = k + "_"
                colmap[c] = k
                seen.add(k)
        if colmap:
            df0 = df0.rename(columns=colmap)
        return df0

    dfe = _normalize_val_cols(df_contraste_src)

    # 4) Aplanar: si hay 1 valor ⇒ Atributo; si hay 2+ ⇒ Variación (todas)
    val_cols = [c for c in dfe.columns if re.match(r"^Valor\s+[1-4]_*$", str(c), flags=re.I)]
    val_cols = sorted(val_cols, key=lambda x: int(re.findall(r"[1-4]", x)[0])) if val_cols else []

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

    df_contraste_flat = pd.DataFrame(filas)

    if df_contraste_flat.empty:
        st.warning("Contraste no tiene valores en las columnas Valor 1..4.")
        with st.expander("Ver fuente cruda de Contraste (lo que viene del editor)", expanded=False):
            st.dataframe(dfe, use_container_width=True, hide_index=True)
        return

    tipos = df_contraste_flat["Tipo"].astype(str).str.lower()
    n_attr = int((tipos == "atributo").sum())
    n_var = int(((tipos == "variación") | (tipos == "variacion")).sum())
    st.caption(f"Atributos: {n_attr} · Variaciones: {n_var} · Total filas: {len(df_contraste_flat)}")

    st.dataframe(df_contraste_flat, use_container_width=True, hide_index=True)

    with st.expander("Ver fuente cruda de Contraste (lo que viene del editor)", expanded=False):
        st.dataframe(dfe, use_container_width=True, hide_index=True)
