import streamlit as st
import pandas as pd


def filtrar_por_sliders(df: pd.DataFrame) -> pd.DataFrame:
    """
    Dado un DataFrame, aplica filtros tipo slider para cada columna numérica.
    Devuelve el DataFrame filtrado dinámicamente.
    """
    df_filtrado = df.copy()

    # Seleccionar columnas numéricas (excluyendo Search Terms y Fuente)
    columnas_numericas = df_filtrado.select_dtypes(
        include=["number"]).columns.tolist()

    if not columnas_numericas:
        st.info("No hay columnas numéricas para filtrar.")
        return df_filtrado

    st.markdown("### Filtros dinámicos")

    for col in columnas_numericas:
        min_val = float(df_filtrado[col].min())
        max_val = float(df_filtrado[col].max())

        step = 0.01 if "Click Share" in col else 1.0
        rango = st.slider(
            f"{col}:",
            min_value=min_val,
            max_value=max_val,
            value=(min_val, max_val),
            step=step,
            key=f"slider_{col}"
        )

        df_filtrado = df_filtrado[df_filtrado[col].between(rango[0], rango[1])]

    return df_filtrado
