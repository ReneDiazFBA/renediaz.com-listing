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
    Executes full review analysis and returns a structured dict.
    """

    try:
        df = excel_data.parse("Reviews", header=None)
    except Exception as e:
        st.error(f"Error loading 'Reviews' sheet: {e}")
        return {}

    try:
        titulos = df.iloc[1:, 1].dropna().astype(str)   # Column B
        contenidos = df.iloc[1:, 2].dropna().astype(str)  # Column C
        autores = df.iloc[1:, 13].dropna().astype(str)  # Column N
    except Exception as e:
        st.error(f"Error accessing columns B, C or N: {e}")
        return {}

    if titulos.empty or contenidos.empty:
        st.warning("Not enough valid reviews found.")
        return {}

    # Combine title + body
    reviews_consolidados = [
        f"{t.strip()}. {c.strip()}" for t, c in zip(titulos, contenidos)]
    texto_reviews = "\n".join(reviews_consolidados[:300])  # Max 300 reviews

    if st.button("Generate AI insights"):
        st.info("Analyzing reviews using AI...")

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
        }

        if preguntas_rufus:
            resultados["validacion_rufus"] = prompt_validar_preguntas_rufus(
                texto_reviews, preguntas_rufus
            )

        st.session_state.resultados_mercado = resultados
        st.success("Analysis completed.")
    else:
        resultados = st.session_state.get("resultados_mercado", {})

    return resultados
