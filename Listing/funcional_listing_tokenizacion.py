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
    df["tokens"] = df["Search Terms"].apply(
        lambda x: limpiar_texto(x, stopwords))
    return df
