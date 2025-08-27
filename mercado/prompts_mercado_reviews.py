# mercado/prompts_mercado_reviews.py

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

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
                {"role": "system",
                    "content": f"You are a {role} specialized in Amazon listings."},
                {"role": "user", "content": prompt}
            ],
            temperature=temp
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        return f"[ERROR PROMPT] {str(e)}"


def prompt_nombre_producto(texto: str) -> str:
    return _call(f"""Based on the following product reviews, generate a concise and appealing product name. 
Only return the name, no explanation or formatting.

TEXT:
{texto}
""")


def prompt_descripcion_producto(texto: str) -> str:
    return _call(f"""Summarize the product in no more than 2 short lines, in English. 
Capture functionality and differentiation. No bullet points.

REVIEWS:
{texto}
""")


def prompt_beneficios_desde_reviews(texto: str) -> str:
    return _call(f"""Extract the key benefits users value most based on these reviews. 
Return them in bullet point format. English only.

REVIEWS:
{texto}
""")


def prompt_buyer_persona(texto: str, nombres_autores: list[str]) -> str:
    autores_str = ", ".join(nombres_autores[:10])
    return _call(f"""Based on the following reviews and usernames, describe the buyer persona: 
age range, user type, interests, emotions, buying behavior. 
You may infer gender, culture, or age group from the names.

REVIEWS:
{texto}

USERNAMES:
{autores_str}
""")


def prompt_pros_cons(texto: str) -> str:
    return _call(f"""Extract a two-column list: PROS and CONS (max 5 each) based on the following reviews.
Return in plain text format. English only.

REVIEWS:
{texto}
""")


def prompt_emociones(texto: str) -> str:
    return _call(f"""List the main emotions expressed in these reviews — both positive and negative. 
Group them clearly.

REVIEWS:
{texto}
""")


def prompt_lexico_editorial(texto: str) -> str:
    return _call(f"""Analyze the writing style and tone in these reviews (e.g., emotional, technical, casual). 
Also extract a list of frequently used or persuasive phrases for Amazon copywriting.

REVIEWS:
{texto}
""")


def prompt_visual_suggestions(texto: str) -> str:
    return _call(f"""Based on these reviews, suggest visual directions for the product listing (images, A+ content): 
color preferences, materials, usage context, desired aesthetic.

REVIEWS:
{texto}
""")


def prompt_tokens_diferenciadores(texto: str) -> str:
    return _call(f"""From the following product reviews, extract two separate lists of tokens or short key phrases:

1. **Positive differentiators** – Things that users mention as valuable, unique, or desirable.
2. **Negative mentions** – Issues, flaws, or disappointments that are commonly noted.

Format the output clearly in English, like:

POSITIVE TOKENS:
- ...

NEGATIVE TOKENS:
- ...

REVIEWS:
{texto}
""")


def prompt_validar_preguntas_rufus(texto: str, preguntas: list[str]) -> str:
    joined = "\n".join([f"- {p}" for p in preguntas])
    return _call(f"""For each of the following questions, indicate whether it can be answered based on the reviews, 
and provide a short justification in English.

QUESTIONS:
{joined}

REVIEWS:
{texto}
""")

 # mercado/prompts_mercado_reviews.py (agregar al final)


def prompt_comparar_atributos_mercado_vs_cliente(
    beneficios: str,
    tokens: str,
    visuales: str,
    atributos_cliente: list[str]
) -> str:
    """
    Compara los atributos que el mercado valora vs los que el cliente ofrece.
    """
    atributos_joined = "\n".join([f"- {a}" for a in atributos_cliente])

    return _call(f"""
Based on the following Amazon review analysis (benefits, differentiator tokens, and visual cues), extract the product attributes that customers clearly value.

Then compare these attributes to the ones provided by the client.

List:
1. Attributes valued by the market.
2. Attributes the client provides that are also valued by the market.
3. Attributes valued by the market that are **missing** from the client.
4. Attributes the client provides but are **not** mentioned or valued by the market.

BENEFITS FROM REVIEWS:
{beneficios}

DIFFERENTIATION TOKENS:
{tokens}

VISUAL SUGGESTIONS:
{visuales}

CLIENT ATTRIBUTES:
{atributos_joined}

Be clear and organized. Respond in English.
""", temp=0.3)


def prompt_atributos_valorados(texto: str) -> str:
    return _call(f"""From the following Amazon product reviews, extract a short list of PRODUCT ATTRIBUTES that customers clearly care about or mention frequently.

Only include physical or functional product attributes (e.g., color, size, material, weight, accessories, durability, etc.).

**Format the output strictly as:**
- one attribute per line
- each line starts with a hyphen and a space (e.g., "- color")
- no empty lines, no bullet symbols, no formatting

REVIEWS:
{texto}
""", temp=0.3)
