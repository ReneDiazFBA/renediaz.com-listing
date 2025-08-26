# mercado/funcional_mercado_reviews.py

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
    prompt_validar_preguntas_rufus
)


def analizar_reviews(excel_data: pd.ExcelFile, preguntas_rufus: list[str] = []) -> dict:
    """
    Realiza el análisis completo de reviews desde la hoja 'Reviews'.

    Returns:
        dict con todos los insights generados
    """
    try:
        df = excel_data.parse("Reviews", header=None)
    except Exception as e:
        st.error(f"Error al cargar hoja 'Reviews': {e}")
        return {}

    # 1. Preproceso básico: concatenar los primeros 300 reviews no vacíos
    texto_reviews = "\n".join(
        df[0].dropna().astype(str).head(300).tolist()
    ).strip()

    if not texto_reviews:
        st.warning("No se encontraron reviews válidos.")
        return {}

    st.info("Analizando reviews con IA...")

    # 2. Ejecutar prompts
    resultados = {
        "nombre_producto": prompt_nombre_producto(texto_reviews),
        "descripcion": prompt_descripcion_producto(texto_reviews),
        "beneficios": prompt_beneficios_desde_reviews(texto_reviews),
        "buyer_persona": prompt_buyer_persona(texto_reviews),
        "pros_cons": prompt_pros_cons(texto_reviews),
        "emociones": prompt_emociones(texto_reviews),
        "lexico_editorial": prompt_lexico_editorial(texto_reviews),
        "visuales": prompt_visual_suggestions(texto_reviews),
        "tokens_diferenciadores": prompt_tokens_diferenciadores(texto_reviews),
    }

    # 3. Preguntas Rufus si se reciben
    if preguntas_rufus:
        resultados["validacion_rufus"] = prompt_validar_preguntas_rufus(
            texto_reviews, preguntas_rufus
        )

    return resultados
