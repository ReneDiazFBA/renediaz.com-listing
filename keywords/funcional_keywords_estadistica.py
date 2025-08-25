# keywords/funcional_keywords_estadistica.py
from scipy.stats import skew
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
        "CompKW": ["Comp Click Share", "Search Volume", "Comp Depth", "ABA Rank"],
        "MiningKW": ["Niche Click Share", "Search Volume", "Niche Depth", "Relevancy"]
    }

 # 🔧 Forzar conversión de columnas numéricas por seguridad
    todas_columnas = set()
    for columnas in mapeo_columnas.values():
        todas_columnas.update(columnas)

    for col in todas_columnas:
        if col in df.columns:
            # Elimina %, comas y convierte a número
            df[col] = (
                df[col]
                .astype(str)
                .str.replace("%", "", regex=False)
                .str.replace(",", "", regex=False)
                .replace("NAF", pd.NA)
                .replace("None", pd.NA)
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")

    columnas_numericas = df.select_dtypes(include=["number"]).columns

    for col in columnas_numericas:
        for fuente, columnas_relevantes in mapeo_columnas.items():
            mask = df["Fuente"].str.contains(fuente) & (df[col].isna())
            if col in columnas_relevantes:
                df.loc[mask, col] = -1  # falta real
            else:
                df.loc[mask, col] = -2  # no aplica

    return df


def filtrar_por_sliders(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica filtros tipo slider para columnas numéricas.
    - -2 siempre se muestra.
    - -1 se filtra solo si el checkbox está activado.
    - Slider aplica solo sobre valores >= 0.
    """
    df = imputar_valores_vacios(df)
    df_filtrado = df.copy()

    columnas_numericas = df_filtrado.select_dtypes(
        include=["number"]).columns.tolist()
    if not columnas_numericas:
        st.info("No hay columnas numéricas para filtrar.")
        return df_filtrado

    st.markdown("### Filtros dinámicos")

    filtros = []

    for col in columnas_numericas:
        col_data = df_filtrado[col]

        col_validos = col_data[col_data >= 0]
        if col_validos.empty:
            continue

        min_val = float(col_validos.min())
        max_val = float(col_validos.max())
        step = 0.001 if "Click Share" in col else 1.0

        excluir_faltantes = st.checkbox(
            f"Excluir registros con valor faltante en '{col}' (-1)",
            value=False,
            key=f"check_{col}"
        )

        # Protección contra sliders sin rango
        if min_val == max_val:
            rango = (min_val, max_val)
        else:
            rango = st.slider(
                f"{col}:",
                min_value=min_val,
                max_value=max_val,
                value=(min_val, max_val),
                step=step,
                key=f"slider_{col}"
            )

        filtro_col = (
            (col_data == -2) |
            (col_data.between(rango[0], rango[1]))
        )

        if not excluir_faltantes:
            filtro_col |= (col_data == -1)

        filtros.append(filtro_col)

    if filtros:
        filtro_total = filtros[0]
        for f in filtros[1:]:
            filtro_total &= f
        df_filtrado = df_filtrado[filtro_total]

    return df_filtrado


def calcular_descriptivos_extendidos(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula estadísticas descriptivas extendidas para columnas numéricas,
    excluyendo valores -1 y -2.
    """
    df_numeric = df.select_dtypes(include="number").copy()

    # Excluir valores -1 (faltantes) y -2 (irrelevantes)
    df_clean = df_numeric[(df_numeric > -1).all(axis=1)]

    descriptivos = {}

    for col in df_numeric.columns:
        serie = df_numeric[col]
        serie_valida = serie[(serie != -1) & (serie != -2)]

        if serie_valida.empty:
            continue

        q1 = serie_valida.quantile(0.25)
        q2 = serie_valida.quantile(0.50)
        q3 = serie_valida.quantile(0.75)
        moda = serie_valida.mode()

        descriptivos[col] = {
            "Count": serie_valida.count(),
            "Mean": serie_valida.mean(),
            "Median": serie_valida.median(),
            "Mode": ", ".join(map(str, moda.tolist())) if not moda.empty else "N/A",
            "Std": serie_valida.std(),
            "Variance": serie_valida.var(),
            "Min": serie_valida.min(),
            "Max": serie_valida.max(),
            "Range": serie_valida.max() - serie_valida.min(),
            "Q1 (25%)": q1,
            "Q2 (50%)": q2,
            "Q3 (75%)": q3,
            "IQR": q3 - q1,
            "Sum": serie_valida.sum(),
            "Skewness": skew(serie_valida) if len(serie_valida) >= 3 else None,
            "Curtosis": curtosis(serie_valida) if len(serie_valida) >= 3 else None,
        }

    return pd.DataFrame(descriptivos).T.reset_index().rename(columns={"index": "Columna"})


def sugerir_log_transform(df: pd.DataFrame) -> dict:
    """
    Analiza skewness para columnas numéricas y sugiere aplicar log10 si skew > 1 o < -1.
    """
    sugerencias = {}
    columnas_numericas = df.select_dtypes(include=["number"]).columns

    for col in columnas_numericas:
        datos = df[col].dropna()
        datos_validos = datos[datos > 0]  # log10 solo válido en positivos

        if len(datos_validos) < 3:
            sugerencias[col] = None
            continue

        valor_skew = skew(datos_validos)
        sugerencias[col] = valor_skew if abs(valor_skew) > 1 else None

    return sugerencias
