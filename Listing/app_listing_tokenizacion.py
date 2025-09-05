# listing/app_listing_tokenizacion.py  (solo la función de preview)

import streamlit as st
import pandas as pd

def mostrar_preview_inputs_listing():
    st.subheader("Vista previa — Inputs para Listing")

    # Leer la tabla publicada por Mercado/Tabla
    df = st.session_state.get("inputs_para_listing", pd.DataFrame())
    if not isinstance(df, pd.DataFrame) or df.empty:
        st.info("Aún no hay inputs. Abre Mercado → Tabla final de inputs para publicarla.")
        return

    # Normalizador para 'Tipo' (quita tildes y baja a minúsculas)
    def _norm(s: pd.Series) -> pd.Series:
        try:
            import unicodedata
            s = s.astype(str).str.strip()
            s = s.apply(lambda x: ''.join(c for c in unicodedata.normalize('NFKD', x) if not unicodedata.combining(c)))
            return s.str.lower()
        except Exception:
            return s.astype(str).str.strip().str.lower()

    tipo_norm = _norm(df["Tipo"]) if "Tipo" in df.columns else pd.Series([], dtype=str)

    # Conteo por Tipo (diagnóstico)
    st.caption("Conteo por Tipo (normalizado)")
    counts = tipo_norm.value_counts().reset_index()
    counts.columns = ["Tipo (norm)", "Cantidad"]
    st.dataframe(counts, use_container_width=True, hide_index=True)

    # Bloques: Marca / Atributos / Variaciones
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("**Marca**")
        df_m = df.loc[tipo_norm.eq("marca")]
        if not df_m.empty:
            cols = [c for c in ["Contenido", "Fuente"] if c in df_m.columns]
            st.dataframe(df_m[cols], use_container_width=True, hide_index=True)
        else:
            st.write("—")

        st.markdown("**Atributos**")
        df_a = df.loc[tipo_norm.eq("atributo")]
        if not df_a.empty:
            cols = [c for c in ["Contenido", "Etiqueta", "Fuente"] if c in df_a.columns]
            st.dataframe(df_a[cols], use_container_width=True, hide_index=True)
        else:
            st.write("—")

    with col2:
        st.markdown("**Variaciones**")
        df_v = df.loc[tipo_norm.eq("variacion")]  # "variación" normalizado -> "variacion"
        if not df_v.empty:
            cols = [c for c in ["Contenido", "Etiqueta", "Fuente"] if c in df_v.columns]
            st.dataframe(df_v[cols], use_container_width=True, hide_index=True)
        else:
            st.write("—")

    # Tabla completa (referencia)
    with st.expander("Ver tabla completa", expanded=False):
        st.dataframe(df, use_container_width=True)
