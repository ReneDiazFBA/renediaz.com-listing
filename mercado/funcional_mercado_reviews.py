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


def analizar_reviews(excel_data: pd.ExcelFile, preguntas_rufus: list[str] = []) -> dict:
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

    # Unir título y contenido (máximo 100 reviews, 12k caracteres)
    reviews_consolidados = [
        f"{t.strip()}. {c.strip()}" for t, c in zip(titulos, contenidos)
    ]
    texto_reviews = "\n".join(reviews_consolidados[:100])
    texto_reviews = texto_reviews[:12000]

    # Ejecutar todos los prompts
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
