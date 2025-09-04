# mercado/funcional_mercado_reviews.py

from mercado.prompts_mercado_reviews import prompt_comparar_atributos_mercado_vs_cliente
import pandas as pd
import streamlit as st

from mercado.prompts_mercado_reviews import (
    prompt_nombre_producto,
    prompt_descripcion_producto,
    prompt_beneficios_desde_reviews,
    prompt_buyer_persona,
    prompt_pros_cons,
    prompt_emociones,
    prompt_lexico_editorial,
    prompt_visual_suggestions,
    prompt_tokens_diferenciadores,
    prompt_validar_preguntas_rufus,
    prompt_atributos_valorados
)

# ============================================
# >>> RD_FIX: utilidades ADITIVAS para bajar costo (compatibles 3.9)
# ============================================
from typing import Any, Dict, List, Optional, Union
import os
import hashlib


def _flag_true(val: Union[str, bool, None]) -> bool:
    if isinstance(val, bool):
        return val
    return str(val or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _get_secret(name: str, default: Optional[str] = None) -> Optional[str]:
    try:
        # intenta secrets primero
        if hasattr(st, "secrets") and name in st.secrets and st.secrets[name]:
            return st.secrets[name]
    except Exception:
        pass
    return os.environ.get(name, default)


def _cost_saver_on() -> bool:
    # Por defecto ON para abaratar pruebas
    return _flag_true(_get_secret("COST_SAVER", "true"))


def _truncate(text: str, max_chars: int) -> str:
    if not isinstance(text, str):
        return ""
    return text[:max_chars]


def _select_top_pairs(titulos: pd.Series, contenidos: pd.Series, limit: int, each_chars: int) -> List[str]:
    pares = []
    for t, c in zip(titulos.tolist(), contenidos.tolist()):
        t = str(t).strip()
        c = str(c).strip()
        if not t and not c:
            continue
        # recorte por review para evitar explosión
        review = f"{_truncate(t, each_chars)}. {_truncate(c, each_chars)}"
        pares.append(review)
        if len(pares) >= limit:
            break
    return pares


def _hash_key(*parts) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(str(p).encode("utf-8", errors="ignore"))
    return h.hexdigest()


def _maybe_set_openai_key():
    # No rompe nada si ya está; sólo lo setea si no existe
    api_key = _get_secret(
        "OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY", ""))
    if api_key and not os.environ.get("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = api_key

# Cache de resultados de análisis (por hash del texto base)


def _cache_get(cache_key: str) -> Optional[dict]:
    return st.session_state.get(f"cache_res_analisis_{cache_key}")


def _cache_put(cache_key: str, data: dict):
    st.session_state[f"cache_res_analisis_{cache_key}"] = data
# ============================================
# <<< RD_FIX
# ============================================


def analizar_reviews(excel_data: pd.ExcelFile, preguntas_rufus: List[str] = []) -> dict:
    """
    Ejecuta análisis completo de reviews y devuelve un diccionario estructurado.
    """

    try:
        df = excel_data.parse("Reviews", header=None)
    except Exception as e:
        st.error(f"Error loading 'Reviews' sheet: {e}")
        return {}

    try:
        titulos = df.iloc[1:, 1].dropna().astype(str)   # Columna B
        contenidos = df.iloc[1:, 2].dropna().astype(str)  # Columna C
        autores = df.iloc[1:, 13].dropna().astype(str)  # Columna N
    except Exception as e:
        st.error(f"Error accessing columns B, C or N: {e}")
        return {}

    if titulos.empty or contenidos.empty:
        st.warning("Not enough valid reviews found.")
        return {}

    # ============================================
    # >>> RD_FIX: modo ahorro de costo (menos reviews, recortes, y caché)
    # ============================================
    COST_SAVER = _cost_saver_on()

    # límites por defecto originales
    max_reviews = 100
    max_total_chars = 12000
    max_each_review_chars = 1200  # para el caso original no se recortaba por review

    # límites baratos cuando COST_SAVER
    if COST_SAVER:
        max_reviews = int(_get_secret("REVIEWS_LIMIT", "20"))          # ej. 20
        max_total_chars = int(_get_secret("REVIEWS_TOTAL_CHARS", "6000"))
        max_each_review_chars = int(_get_secret("REVIEW_EACH_CHARS", "600"))
    # Seleccionar y recortar por review cuando aplique
    reviews_consolidados = _select_top_pairs(
        titulos, contenidos, limit=max_reviews, each_chars=max_each_review_chars)

    # Unir y recortar total
    texto_reviews = "\n".join(reviews_consolidados)
    texto_reviews = _truncate(texto_reviews, max_total_chars)

    # clave de caché por contenido (y por si cambias parámetros)
    cache_key = _hash_key(texto_reviews, COST_SAVER, max_reviews,
                          max_total_chars, max_each_review_chars, tuple(preguntas_rufus or []))
    cached = _cache_get(cache_key)
    if COST_SAVER and cached:
        return cached

    # setear API key si está en secrets (no molesta si ya la tienes en env)
    _maybe_set_openai_key()
    # ============================================
    # <<< RD_FIX
    # ============================================

    # Ejecutar todos los prompts (tu lógica intacta)
    resultados = {
        "nombre_producto": prompt_nombre_producto(texto_reviews),
        "descripcion": prompt_descripcion_producto(texto_reviews),
        "beneficios": prompt_beneficios_desde_reviews(texto_reviews),
        "buyer_persona": prompt_buyer_persona(texto_reviews, autores.tolist()),
        "pros_cons": prompt_pros_cons(texto_reviews),
        "emociones": prompt_emociones(texto_reviews),
        "lexico_editorial": prompt_lexico_editorial(texto_reviews),
        "visuales": prompt_visual_suggestions(texto_reviews),
        "tokens_diferenciadores": prompt_tokens_diferenciadores(texto_reviews),
        "atributos_valorados": prompt_atributos_valorados(texto_reviews),
    }

    if preguntas_rufus:
        resultados["validacion_rufus"] = prompt_validar_preguntas_rufus(
            texto_reviews, preguntas_rufus
        )

    # ============================================
    # >>> RD_FIX: guarda cache si estás en modo ahorro
    # ============================================
    if COST_SAVER:
        _cache_put(cache_key, resultados)
    # ============================================
    # <<< RD_FIX
    # ============================================

    return resultados


def comparar_atributos_con_cliente(excel_data: pd.ExcelFile) -> str:
    """
    Contrasta los atributos valorados por el mercado con los que ofrece el cliente.
    Devuelve un texto estructurado con hallazgos.
    """
    if "resultados_mercado" not in st.session_state:
        st.warning("Primero debes generar los insights del mercado.")
        return ""

    resultados = st.session_state["resultados_mercado"]

    beneficios = resultados.get("beneficios", "")
    tokens = resultados.get("tokens_diferenciadores", "")
    visuales = resultados.get("visuales", "")

    try:
        df = excel_data.parse("CustData", header=None)
    except Exception as e:
        st.error(f"Error al cargar hoja 'CustData': {e}")
        return ""

    try:
        atributos = df.iloc[11:24, 4].dropna().astype(str).tolist()
    except Exception as e:
        st.error(f"Error al leer atributos del cliente desde CustData: {e}")
        return ""

    if not atributos:
        st.warning("No se encontraron atributos del cliente.")
        return ""

    resultado = prompt_comparar_atributos_mercado_vs_cliente(
        beneficios=beneficios,
        tokens=tokens,
        visuales=visuales,
        atributos_cliente=atributos
    )

    return resultado
