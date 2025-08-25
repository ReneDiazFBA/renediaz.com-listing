import streamlit as st
import pandas as pd


def imputar_valores_vacios(df: pd.DataFrame) -> pd.DataFrame:
    """
    Reemplaza valores vacíos con:
    -1 si la columna sí corresponde a la fuente (es relevante)
    -2 si la columna no corresponde a la fuente (es irrelevante)
    """
    df = df.copy()

    mapeo_columnas = {
        "CustKW": ["ASIN Click Share", "Search Volume", "ABA Rank"],
        "CompKW": ["Comp Click Share", "Search Volume", "Comp Depth"],
        "MiningKW": ["Niche Click Share", "Search Volume", "Niche Depth", "Relevancy"]
    }

    columnas_numericas = df.select_dtypes(include=["number"]).columns

    for col in columnas_numericas:
        for fuente, columnas_relevantes in mapeo_columnas.items():
            mask = (df["Fuente"] == fuente) & (df[col].isna())
            if col in columnas_relevantes:
                df.loc[mask, col] = -1  # falta real
            else:
                df.loc[mask, col] = -2  # no aplica

    return df


def filtrar_por_sliders(df: pd.DataFrame) -> pd.DataFrame:
    """
    Dado un DataFrame, aplica filtros tipo slider para cada columna numérica.
    Devuelve el DataFrame filtrado dinámicamente.
    """
    df = imputar_valores_vacios(df)
    df_filtrado = df.copy()

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
