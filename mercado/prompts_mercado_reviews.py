# mercado/prompts_mercado_reviews.py

import os
from typing import Optional

try:
    from openai import OpenAI
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    _OPENAI_OK = True
except Exception as e:
    _OPENAI_OK = False
    _OPENAI_ERR = str(e)


def _call(prompt: str, role: str = "product expert", temp: float = 0.7) -> str:
    if not _OPENAI_OK:
        return f"[ERROR API] { _OPENAI_ERR }"
    try:
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": f"Eres un {role} para listings de Amazon."},
                {"role": "user", "content": prompt}
            ],
            temperature=temp
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        return f"[ERROR PROMPT] {str(e)}"


# 1. Nombre del producto
def prompt_nombre_producto(texto: str) -> str:
    return _call(f"""Dado este texto de reviews reales, genera un nombre de producto atractivo y funcional. 
Solo devuelve el nombre, sin comillas ni explicación.

TEXT:
{texto}
""")


# 2. Descripción breve
def prompt_descripcion_producto(texto: str) -> str:
    return _call(f"""Resume este producto en 2 líneas máximo, en inglés, capturando su funcionalidad principal y diferenciadores. 
No uses bullet points ni encabezados.

REVIEWS:
{texto}
""")


# 3. Beneficios valorados
def prompt_beneficios_desde_reviews(texto: str) -> str:
    return _call(f"""Identifica los beneficios clave valorados por los usuarios en estos reviews. 
Devuélvelos en formato lista con viñetas. En inglés.

REVIEWS:
{texto}
""")


# 4. Buyer persona
def prompt_buyer_persona(texto: str) -> str:
    return _call(f"""Basado en estos reviews, describe quién es el buyer persona (edad, tipo de usuario, intereses, emociones, perfil de compra).
Usa formato texto libre, no bullet points.

REVIEWS:
{texto}
""")


# 5. Pros y Cons
def prompt_pros_cons(texto: str) -> str:
    return _call(f"""Extrae una tabla de 2 columnas: PROS y CONS, con base en estos reviews. 
Devuelve máximo 5 por lado. En inglés.

REVIEWS:
{texto}
""")


# 6. Emociones dominantes
def prompt_emociones(texto: str) -> str:
    return _call(f"""Resume las emociones positivas y negativas que expresan los usuarios en estos reviews. 
Devuélvelas en formato de lista separada.

REVIEWS:
{texto}
""")


# 7. Estilo editorial y léxico
def prompt_lexico_editorial(texto: str) -> str:
    return _call(f"""Detecta el estilo editorial que predomina en estos reviews (formal, informal, técnico, emocional, etc.) 
y extrae una lista de frases comunes o impactantes que podrían usarse en el copy del listing.

REVIEWS:
{texto}
""")


# 8. Recomendaciones visuales
def prompt_visual_suggestions(texto: str) -> str:
    return _call(f"""Extrae sugerencias para el contenido visual del listing basadas en los reviews: colores preferidos, materiales mencionados, 
contextos de uso, estilo deseado. Devuelve en bullet points.

REVIEWS:
{texto}
""")


# 9. Tokens de diferenciación
def prompt_tokens_diferenciadores(texto: str) -> str:
    return _call(f"""Extrae frases cortas o palabras clave que sirvan como diferenciadores únicos del producto según los reviews. 
Úsalas luego para destacar beneficios únicos en bullets o A+. Lista corta en inglés.

REVIEWS:
{texto}
""")


# 10. Validación de preguntas Rufus
def prompt_validar_preguntas_rufus(texto: str, preguntas: list[str]) -> str:
    joined = "\n".join([f"- {p}" for p in preguntas])
    return _call(f"""Con base en estos reviews, responde si es posible responder estas preguntas (sí/no y justificación breve por cada una):

{joined}

REVIEWS:
{texto}
""")
