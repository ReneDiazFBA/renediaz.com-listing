# listing/funcional_listing_tokenizacion.py

import streamlit as st
import pandas as pd
import spacy
import re

try:
    nlp_embed = spacy.load("en_core_web_md")
    _EMBEDD_OK = True
except Exception as e:
    _EMBEDD_OK = False
    _EMBEDD_ERR = str(e)

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
        palabras = (
            df_avoids.iloc[:, 1]
            .dropna()
            .astype(str)
            .str.strip()
            .str.lower()
        )
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
    tokens = [t for t in texto.split() if t and t not in stopwords]
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

    # Asegurar columnas necesarias (sin tocar el módulo de keywords)
    necesarias = ["Search Terms", "Search Volume", "Clasificación Estrategia"]
    faltantes = [c for c in necesarias if c not in df.columns]
    if faltantes:
        st.error(f"Faltan columnas obligatorias en matriz_tiers: {faltantes}")
        return pd.DataFrame()

    # Estandarizar columna para el módulo listing
    df["tier"] = df["Clasificación Estrategia"]

    # Normalización de nombres de estrategia a etiquetas compactas
    reemplazos = {
        "Core keyword": "Core",
        "Oportunidad crítica (subnicho+nicho)": "Oportunidad crítica",
        "Oportunidad directa (subnicho)": "Oportunidad directa",
        "Especialización (ASIN + subnicho)": "Especialización",
        "Diferenciación (ASIN + nicho)": "Diferenciación",
        "Outlier útil (ASIN)": "Outlier",
        "Oportunidad lejana (nicho)": "Oportunidad lejana",
        "Irrelevante total": "Irrelevante",
    }
    df["tier"] = df["tier"].replace(reemplazos).astype(str).str.strip()

    # Tokenización
    df["tokens"] = df["Search Terms"].apply(
        lambda x: limpiar_texto(x, stopwords))
    return df


def priorizar_tokens(
    cuartiles_directa: list,
    cuartiles_especial: list,
    cuartiles_diferenciacion: list
) -> pd.DataFrame:
    """
    Construye listado de tokens únicos priorizados por tier estratégico, volumen y cuartiles seleccionados.
    Reglas:
      - Volumen > 400 aplica a todos.
      - Core y Oportunidad crítica siempre entran (si superan volumen).
      - Oportunidad directa entra según cuartiles seleccionados.
      - Especialización entra según cuartiles seleccionados.
      - Diferenciación entra sólo si se selecciona y según cuartiles.
      - Si un token aparece en varios tiers, prevalece el de mayor prioridad y se acumula frecuencia.
    """
    df = tokenizar_keywords()
    if df.empty or "tier" not in df.columns:
        st.warning(
            "La tabla de keywords tokenizadas no está disponible o no tiene columna 'tier'.")
        return pd.DataFrame()

    # Filtro por volumen
    if "Search Volume" not in df.columns:
        st.error("Falta la columna 'Search Volume' para el filtrado por volumen.")
        return pd.DataFrame()
    df = df[df["Search Volume"] > 400].copy()
    if df.empty:
        return pd.DataFrame()

    # Asignación de cuartiles internos por tier objetivo
    def asignar_q(series_vol):
        try:
            return pd.qcut(series_vol, 4, labels=["Q1", "Q2", "Q3", "Q4"])
        except Exception:
            return pd.Series([None] * len(series_vol), index=series_vol.index)

    df["cuartil"] = None
    for tier_obj in ["Oportunidad directa", "Especialización", "Diferenciación"]:
        mask = df["tier"] == tier_obj
        if mask.sum() >= 4:
            df.loc[mask, "cuartil"] = asignar_q(df.loc[mask, "Search Volume"])

    # Mapeo a etiquetas legibles de UI
    mapa_cuartiles = {
        "Q1": "Bottom 25%",
        "Q2": "Medio 50%",
        "Q3": "Top 50%",
        "Q4": "Top 25%",
        None: None,
        "None": None,
    }

    def etiqueta_cuartil(val):
        if pd.isna(val):
            return None
        return mapa_cuartiles.get(str(val), None)

    df["cuartil_legible"] = df["cuartil"].apply(etiqueta_cuartil)

    # Reglas de inclusión dinámicas por selección de UI
    def es_valido(row):
        tier = row["tier"]
        cq = row.get("cuartil_legible")
        if tier in ["Core", "Oportunidad crítica"]:
            return True
        if tier == "Oportunidad directa" and (cq in cuartiles_directa):
            return True
        if tier == "Especialización" and (cq in cuartiles_especial):
            return True
        if tier == "Diferenciación" and (cq in cuartiles_diferenciacion):
            return True
        return False

    df_filtrada = df[df.apply(es_valido, axis=1)].copy()
    if df_filtrada.empty:
        return pd.DataFrame()

    # Priorización jerárquica
    prioridad = {
        "Core": 1,
        "Oportunidad crítica": 2,
        "Oportunidad directa": 3,
        "Especialización": 4,
        "Diferenciación": 5,
        "Outlier": 6,
        "Oportunidad lejana": 7,
        "Irrelevante": 8,
    }

    # Expandir tokens por fila
    df_filtrada["tokens"] = df_filtrada["tokens"].apply(
        lambda x: x if isinstance(x, list) else [])
    registros = []
    for _, row in df_filtrada.iterrows():
        t = row["tier"]
        for tok in row["tokens"]:
            registros.append((tok, t))

    if not registros:
        return pd.DataFrame()

    df_tokens = pd.DataFrame(registros, columns=["token", "tier"])
    df_tokens["prioridad"] = df_tokens["tier"].map(
        prioridad).fillna(999).astype(int)
    df_tokens.sort_values(["prioridad", "token"], inplace=True)

    # Consolidar por prioridad
    tokens_finales = {}
    for _, r in df_tokens.iterrows():
        tok = r["token"]
        t = r["tier"]
        if tok not in tokens_finales:
            tokens_finales[tok] = {"frecuencia": 1, "tier_origen": t}
        else:
            tokens_finales[tok]["frecuencia"] += 1

    df_resultado = pd.DataFrame(
        [{"token": k, "frecuencia": v["frecuencia"], "tier_origen": v["tier_origen"]}
         for k, v in tokens_finales.items()]
    )

    return df_resultado


def lemmatizar_tokens_priorizados(df_tokens: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica lematización al campo 'token' del dataframe priorizado, y agrupa por lemas.
    Conserva la frecuencia total y el tier de mayor prioridad.
    Devuelve un nuevo dataframe con columnas: token_original, token_lema, frecuencia, tier_origen.
    """
    import spacy

    # Cargar modelo en inglés
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        st.error("No se pudo cargar el modelo 'en_core_web_sm'. Ejecuta en terminal:\npython -m spacy download en_core_web_sm")
        return pd.DataFrame()

    # Validación
    if df_tokens.empty or "token" not in df_tokens.columns:
        st.warning("No hay tokens para lematizar.")
        return pd.DataFrame()

    # Mapear prioridad para conservar la más alta
    prioridad = {
        "Core": 1,
        "Oportunidad crítica": 2,
        "Oportunidad directa": 3,
        "Especialización": 4,
        "Diferenciación": 5,
        "Outlier": 6,
        "Oportunidad lejana": 7,
        "Irrelevante": 8,
    }

    # Lemmatizar cada token
    df_tokens["token_lema"] = df_tokens["token"].apply(
        lambda x: nlp(x)[0].lemma_ if isinstance(x, str) and len(x) > 0 else x
    )

    # Guardar token original para visual
    df_tokens["token_original"] = df_tokens["token"]

    # Asignar prioridad numérica
    df_tokens["prioridad"] = df_tokens["tier_origen"].map(
        prioridad).fillna(999).astype(int)

    # Agrupar por lema
    df_grouped = (
        df_tokens.groupby("token_lema")
        .agg({
            "frecuencia": "sum",
            "token_original": lambda x: ", ".join(sorted(set(x))),
            "prioridad": "min",
        })
        .reset_index()
    )

    # Volver a mapear el tier de mayor prioridad
    prioridad_inv = {v: k for k, v in prioridad.items()}
    df_grouped["tier_origen"] = df_grouped["prioridad"].map(prioridad_inv)

    # Renombrar columnas
    df_grouped = df_grouped.rename(columns={
        "token_lema": "token_lema",
        "token_original": "token_original",
        "frecuencia": "frecuencia",
        "tier_origen": "tier_origen"
    })

    # Orden final
    return df_grouped[["token_original", "token_lema", "frecuencia", "tier_origen"]]


def generar_embeddings(df_lemas: pd.DataFrame) -> pd.DataFrame:
    """
    Genera vectores embeddings para cada token_lema usando spaCy (en_core_web_md).
    Agrega columna 'vector' con numpy arrays.
    """
    if not _EMBEDD_OK:
        st.error(f"No se pudo cargar el modelo de embeddings: {_EMBEDD_ERR}")
        return pd.DataFrame()

    df = df_lemas.copy()
    vectores = []
    for lema in df["token_lema"]:
        doc = nlp_embed(lema)
        vectores.append(doc.vector)

    df["vector"] = vectores
    return df
