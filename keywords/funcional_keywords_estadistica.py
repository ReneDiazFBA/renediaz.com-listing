# keywords/funcional_keywords_estadistica.py
from scipy.stats import ttest_ind
from scipy.stats import skew, kurtosis, shapiro, ttest_ind, mannwhitneyu, levene
import streamlit as st
import pandas as pd
import numpy as np


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
            "Kurtosis": kurtosis(serie_valida) if len(serie_valida) >= 3 else None,
            "Z-Score Min": round(((serie_valida.min() - serie_valida.mean()) / serie_valida.std()), 2) if serie_valida.std() != 0 else None,
            "Z-Score Max": round(((serie_valida.max() - serie_valida.mean()) / serie_valida.std()), 2) if serie_valida.std() != 0 else None,
            "Coef. de Variación (%)": round((serie_valida.std() / serie_valida.mean()) * 100, 2) if serie_valida.mean() != 0 else None,
            "Shapiro Normality": (
                "Normal" if (len(serie_valida) >= 3 and shapiro(serie_valida).pvalue > 0.05)
                else "No normal"
            ) if len(serie_valida) >= 3 else "N/A",
        }

    return pd.DataFrame(descriptivos).T.reset_index().rename(columns={"index": "Columna"})


def sugerir_log_transform_robusto(df: pd.DataFrame) -> dict:
    """
    Sugiere aplicar log10 si se detecta distribución severamente sesgada.
    Criterios:
    - Skewness > 1 o < -1
    - Kurtosis > 3
    - Rango (max/min) > 1000x
    Se sugiere log10 si se cumplen al menos 2 criterios.
    """
    sugerencias = {}
    columnas_numericas = df.select_dtypes(include=["number"]).columns

    for col in columnas_numericas:
        datos = df[col].dropna()
        datos_validos = datos[datos > 0]  # log10 solo en positivos

        if len(datos_validos) < 3:
            sugerencias[col] = None
            continue

        skewness = skew(datos_validos)
        kurt = kurtosis(datos_validos)
        rango = datos_validos.max() / datos_validos.min() if datos_validos.min() > 0 else 0

        señales = sum([
            abs(skewness) > 1,
            kurt > 3,
            rango > 1000
        ])

        sugerencias[col] = round(skewness, 2) if señales >= 2 else None

    return sugerencias


def aplicar_log10_dinamico(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica log10 dinámicamente a las columnas marcadas como 'Aplicar log10' por el usuario.
    - Preserva los valores -1 y -2.
    - Renombra la columna visualmente: 'Search Volume (log10)'
    """
    df = df.copy()
    nuevas_columnas = {}

    for col in df.select_dtypes(include="number").columns:
        key = f"log_radio_{col}"
        if key in st.session_state and st.session_state[key] == "Aplicar log10":
            serie = df[col]
            transformada = serie.apply(lambda x: np.log10(x) if x > 0 else x)
            nuevo_nombre = f"{col} (log10)"
            nuevas_columnas[col] = nuevo_nombre
            df[col] = transformada

    df.rename(columns=nuevas_columnas, inplace=True)
    return df


def calcular_correlaciones(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Calcula matrices de correlación (Pearson y Spearman) sobre columnas numéricas,
    imputando -1 como 0 y excluyendo -2.
    """
    df_corr = df.copy()
    columnas_numericas = df_corr.select_dtypes(include="number").columns

    # Convertir -1 a 0 (faltantes reales) y eliminar -2 (irrelevante)
    df_corr = df_corr[columnas_numericas].replace(-1, 0)
    df_corr = df_corr[(df_corr != -2).all(axis=1)]

    if df_corr.shape[1] < 2:
        return None, None

    pearson = df_corr.corr(method="pearson")
    spearman = df_corr.corr(method="spearman")

    return pearson, spearman


def interpretar_correlaciones(matriz: pd.DataFrame, metodo: str = "Pearson") -> list:
    """
    Genera interpretación automática de una matriz de correlación.
    """
    interpretaciones = []
    umbrales = [
        (0.9, "muy fuerte"),
        (0.7, "fuerte"),
        (0.5, "moderada"),
        (0.3, "débil"),
        (0.1, "muy débil")
    ]

    ya_analizadas = set()

    for col1 in matriz.columns:
        for col2 in matriz.columns:
            if col1 == col2 or (col2, col1) in ya_analizadas:
                continue

            ya_analizadas.add((col1, col2))
            valor = matriz.loc[col1, col2]

            signo = "positiva (directa)" if valor > 0 else "negativa (inversa)"
            fuerza = "sin correlación"

            for umbral, etiqueta in umbrales:
                if abs(valor) >= umbral:
                    fuerza = etiqueta
                    break

            interpretacion = f"**{col1}** y **{col2}** tienen una correlación {signo} {fuerza} ({metodo}: {valor:.2f})"
            interpretaciones.append(interpretacion)

    return interpretaciones


def realizar_tests_inferenciales(df: pd.DataFrame) -> list:
    """
    Realiza pruebas inferenciales para comparar métricas entre grupos altos y bajos.
    - Aplica Shapiro-Wilk para verificar normalidad.
    - Usa T-Test si ambas muestras son normales, de lo contrario Mann-Whitney U.
    - Aplica Test de Levene para verificar homogeneidad de varianzas.
    """
    resultados = []
    columnas_numericas = df.select_dtypes(include=["number"]).columns

    for col in columnas_numericas:
        datos = df[col].copy()
        datos = datos[(datos != -1) & (datos != -2)]

        if len(datos) < 10:
            continue

        q25 = datos.quantile(0.25)
        q75 = datos.quantile(0.75)

        grupo_bajo = datos[datos <= q25]
        grupo_alto = datos[datos >= q75]

        if len(grupo_bajo) < 5 or len(grupo_alto) < 5:
            continue

        # Shapiro para ambos grupos
        normal_bajo = shapiro(grupo_bajo).pvalue > 0.05
        normal_alto = shapiro(grupo_alto).pvalue > 0.05

        # Levene: igualdad de varianzas
        try:
            p_levene = levene(grupo_bajo, grupo_alto).pvalue
        except Exception:
            p_levene = None

        # T-Test o Mann-Whitney
        if normal_bajo and normal_alto:
            p = ttest_ind(grupo_bajo, grupo_alto, equal_var=True).pvalue
            test = "T-Test"
        else:
            p = mannwhitneyu(grupo_bajo, grupo_alto,
                             alternative="two-sided").pvalue
            test = "Mann-Whitney U"

        if p < 0.05:
            resultados.append(
                f"Diferencia significativa en **{col}** ({test}, p = {p:.4f}, Levene p = {p_levene:.4f} {'✅' if p_levene and p_levene > 0.05 else '⚠️'})"
            )

    return resultados
