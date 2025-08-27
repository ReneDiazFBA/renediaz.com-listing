import streamlit as st
import pandas as pd
import re

from listing.loader_listing_keywords import get_tiers_table


def get_stopwords_from_excel() -> set:
    """
    Carga la columna B de la hoja Avoids como set de stopwords. Requiere que excel_data esté en sesión.
    """
    if "excel_data" not in st.session_state:
        st.warning("No se encontró el archivo Excel en sesión.")
        return set()

    try:
        df_avoids = st.session_state["excel_data"].parse("Avoids", skiprows=2)
        palabras = df_avoids.iloc[:, 1].dropna().astype(
            str).str.strip().str.lower()
        return set(palabras)
    except Exception as e:
        st.error(f"No se pudieron leer las stopwords desde 'Avoids': {e}")
        return set()


def limpiar_texto(texto: str, stopwords: set) -> list:
    """
    Limpieza básica: lower, quitar símbolos, quitar stopwords, dividir en tokens.
    """
    if not isinstance(texto, str):
        return []

    texto = texto.lower()
    texto = re.sub(r"[^a-z0-9\s]", " ", texto)
    tokens = [t.strip()
              for t in texto.split() if t.strip() and t not in stopwords]
    return tokens


def tokenizar_keywords() -> pd.DataFrame:
    """
    Carga la tabla estratégica (tiers), aplica tokenización y devuelve nueva tabla con columna 'tokens'.
    """
    df = get_tiers_table()
    if df.empty:
        return pd.DataFrame()

    stopwords = get_stopwords_from_excel()

    df = df.copy()

    # Asegurar columnas necesarias
    columnas_necesarias = ["Search Terms",
                           "Search Volume", "Clasificación Estrategia"]
    for col in columnas_necesarias:
        if col not in df.columns:
            st.error(
                f"Falta la columna obligatoria '{col}' en la matriz de tiers.")
            return pd.DataFrame()

    # Estandarizar columna para que el resto del módulo use siempre "tier"
    df["tier"] = df["Clasificación Estrategia"]

    df["tokens"] = df["Search Terms"].apply(
        lambda x: limpiar_texto(x, stopwords))
    return df


def priorizar_tokens() -> pd.DataFrame:
    """
    Construye listado de tokens únicos priorizados por tier estratégico y volumen.
    """
    df = tokenizar_keywords()
    if df.empty or "tier" not in df.columns:
        st.warning(
            "La tabla de keywords tokenizadas no está disponible o no tiene columna 'tier'.")
        return pd.DataFrame()

    # Filtrar por volumen > 400
    df = df[df["Search Volume"] > 400].copy()

    # Cuartiles internos
    def asignar_q(x, serie):
        try:
            return pd.qcut(serie, 4, labels=["Q1", "Q2", "Q3", "Q4"])[x.name]
        except Exception:
            return None

    df["cuartil"] = None
    for tier_objetivo in ["Oportunidad directa", "Especialización"]:
        mask = df["tier"] == tier_objetivo
        if mask.sum() > 4:  # al menos 4 valores para qcut
            df.loc[mask, "cuartil"] = df[mask].apply(
                lambda x: asignar_q(x, df[mask]["Search Volume"]), axis=1)

    # Reglas de inclusión
    def es_valido(row):
        if row["tier"] in ["Core", "Oportunidad crítica"]:
            return True
        if row["tier"] == "Oportunidad directa" and row["cuartil"] in ["Q3", "Q4"]:
            return True
        if row["tier"] == "Especialización" and row["cuartil"] == "Q4":
            return True
        return False

    df_filtrada = df[df.apply(es_valido, axis=1)].copy()

    # Priorización jerárquica
    prioridad = {
        "Core": 1,
        "Oportunidad crítica": 2,
        "Oportunidad directa": 3,
        "Especialización": 4
    }

    df_filtrada["tokens"] = df_filtrada["tokens"].apply(
        lambda x: x if isinstance(x, list) else [])
    registros = []

    for _, row in df_filtrada.iterrows():
        tier = row["tier"]
        for token in row["tokens"]:
            registros.append((token, tier))

    df_tokens = pd.DataFrame(registros, columns=["token", "tier"])

    # Prioridad y frecuencia
    df_tokens["prioridad"] = df_tokens["tier"].map(prioridad)
    df_tokens.sort_values("prioridad", inplace=True)

    tokens_finales = {}
    for _, row in df_tokens.iterrows():
        token = row["token"]
        tier = row["tier"]
        if token not in tokens_finales:
            tokens_finales[token] = {"frecuencia": 1, "tier_origen": tier}
        else:
            tokens_finales[token]["frecuencia"] += 1

    df_resultado = pd.DataFrame([
        {"token": k, "frecuencia": v["frecuencia"],
            "tier_origen": v["tier_origen"]}
        for k, v in tokens_finales.items()
    ])

    return df_resultado
