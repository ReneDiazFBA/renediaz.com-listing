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
    Ejecuta el análisis completo de reviews y devuelve un diccionario estructurado.
    """

    try:
        df = excel_data.parse("Reviews", header=None)
    except Exception as e:
        st.error(f"Error al cargar hoja 'Reviews': {e}")
        return {}

    # Validación de columnas esperadas
    try:
        titulos = df.iloc[1:, 1].dropna().astype(str)   # Columna B
        contenidos = df.iloc[1:, 2].dropna().astype(str)  # Columna C
        autores = df.iloc[1:, 13].dropna().astype(str)  # Columna N
    except Exception as e:
        st.error(f"Error al acceder columnas B, C o N: {e}")
        return {}

    if titulos.empty or contenidos.empty:
        st.warning("No hay suficientes títulos o contenidos de reviews.")
        return {}

    # Armar texto combinado para IA
    reviews_consolidados = [
        f"{t.strip()}. {c.strip()}" for t, c in zip(titulos, contenidos)]
    texto_reviews = "\n".join(reviews_consolidados[:300])  # Máximo 300 reviews

    # Mostrar botón
    if st.button("Generar insights IA"):
        st.info("Analizando reviews con IA...")

        resultados = {
            "nombre_producto": prompt_nombre_producto(texto_reviews),
            "descripcion": prompt_descripcion_producto(texto_reviews),
            "beneficios": prompt_beneficios_desde_reviews(texto_reviews),
            "buyer_persona": prompt_buyer_persona(
                texto_reviews + "\n\nNombres de usuarios: " +
                ", ".join(autores.head(10))
            ),
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
        st.success("Análisis completado.")
    else:
        resultados = st.session_state.get("resultados_mercado", {})

    return resultados
