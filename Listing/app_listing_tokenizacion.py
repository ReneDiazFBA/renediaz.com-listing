def mostrar_preview_inputs_listing():
    import pandas as pd
    import streamlit as st
    from mercado.loader_inputs_listing import construir_inputs_listing

    st.subheader("Inputs unificados para generación de Listing")

    # 👇 aquí forzamos a usar siempre la última edición de contraste
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
