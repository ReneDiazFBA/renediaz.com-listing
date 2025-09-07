# listing/prompts_listing_copywrite.py
# Prompts EN – TÍTULOS únicamente (desktop + mobile por variación).
# Mantiene dos marcos globales: Amazon guidelines + Editorial brief.
# Genera SOLO JSON con: {"titles":[{"variation":"","desktop":"...","mobile":"..."}...]}

from typing import List

# ─────────────────────────────────────────────────────────────────────────────
# 1) AMAZON – MARCO GENERAL (siempre activo)
# ─────────────────────────────────────────────────────────────────────────────
AMAZON_GUIDELINES_BRIEF = """
AMAZON LISTING – GLOBAL POLICY (ALWAYS APPLY)
- No promotional language: no "free", "discount", "sale", "coupon", "shipping", "#1/best".
- No competitor mentions; avoid subjective claims ("top-rated", "must-have").
- No prohibited characters in titles: !, $, ?, _, {, }, ^, ¬, ¦.
  Allowed punctuation: hyphen (-), slash (/), comma (,), ampersand (&), period (.).
- Use digits for numbers ("2" not "two"); proper capitalization (no ALL CAPS).
- Concise, clear, non-redundant; do not stuff keywords; avoid repeating the same word >2 times in a title.
- Titles ≤200 chars (hard store limit, though we will target our custom caps below).
"""

# ─────────────────────────────────────────────────────────────────────────────
# 2) EDITORIAL – COMPORTAMIENTO VS TABLA
# ─────────────────────────────────────────────────────────────────────────────
EDITORIAL_BRIEF = """
EDITORIAL BRIEF – TABLE-DRIVEN BEHAVIOR
- Toda la copia deriva de una tabla con columnas: tipo, contenido, etiqueta.
- Recibirás proyecciones ya filtradas de esa tabla (no inventes datos).
- Buyer persona y léxico editorial orientan tono/claridad, pero NO se incluyen literalmente en el título salvo que aporten claridad del producto.
- Si hay "Marca", úsala; si no hay, NO inventes.
"""

# ─────────────────────────────────────────────────────────────────────────────
# 3) TÍTULO – CONTRATO (desktop + mobile por variación)
# ─────────────────────────────────────────────────────────────────────────────
TITLE_BRIEF = """
TITLE CONTRACT – DESKTOP & MOBILE (PER VARIATION)

Inputs (ya filtrados de la tabla):
- brand: string opcional (vacío si no hay marca).
- cores: lista de tokens CORE que definen QUÉ es el producto. (El nombre del producto se arma SOLO con cores.)
- atributos: lista de VALORES de atributos (no nombres). Priorizados por lo que dicen reviews.
- variaciones: lista de strings. Se genera un par de títulos por cada variación.
- context: descripción breve SOLO para entender el producto (no copiar literalmente).

Taxonomía y separadores:
- Forma: Brand + ProductName(from cores) - attr, attr - variation
  • Entre bloques (WHAT / ATTRS / VAR): " - "
  • Entre atributos: ", "
  • Entre Brand y WHAT: sin separador especial (espacio normal).
- No dupliques: si un valor aparece como variación, NO lo repitas como atributo.
- Usa tantos atributos como entren antes del límite.

Límites a cumplir:
- DesktopTitle: 150–180 chars (incluyendo espacios).
- MobileTitle: 75–80 chars (incluyendo espacios).
- Además, Amazon: título ≤200 chars, sin promos ni caracteres prohibidos, sin palabras repetidas >2 veces.

Capitalización y estilo:
- No ALL CAPS. Capitaliza inicial de cada palabra relevante (excepto artículos/preposiciones/conjunciones comunes).
- Usa dígitos (2, 3…), abreviaturas estándar de medida (cm, oz, in, kg) cuando aporte claridad.
"""

# ─────────────────────────────────────────────────────────────────────────────
# 4) PROMPT MASTER – SOLO TÍTULOS
# ─────────────────────────────────────────────────────────────────────────────
def prompt_title_json(
    head_phrases: List[str],
    core_tokens: List[str],
    attributes: List[str],
    variations: List[str],
    buyer_persona: str,
    lexico: str,
    brand: str = "",
    context_short: str = "",
) -> str:
    """
    Devuelve un prompt para generar EXCLUSIVAMENTE títulos:
      - Un par por variación: desktop (150–180) y mobile (75–80)
      - Si no hay variaciones, devolver un par con "variation": "".

    Notas:
    - ProductName se arma SOLO con core_tokens.
    - attributes = VALORES priorizados (no nombres).
    - variations = child options; no dupliques atributos que ya son variaciones.
    - head_phrases: semillas opcionales (si existen), p.ej. brand cues o hints útiles.
    """

    return f"""{AMAZON_GUIDELINES_BRIEF}

{EDITORIAL_BRIEF}

{TITLE_BRIEF}

ROLE:
You are an Amazon listing copywriter. Generate ONLY titles (desktop + mobile) per variation,
strictly following the contract and global policies. Do not output any other section.

RETURN STRICT JSON:
{{
  "titles": [
    {{"variation": "<variation or empty>", "desktop": "<150–180 chars>", "mobile": "<75–80 chars>"}}
  ]
}}

INPUTS:
Brand (empty if none): {brand}
Core tokens (WHAT – build ProductName ONLY from these): {core_tokens}
Attribute VALUES (prioritized by reviews; do not repeat values used as variations): {attributes}
Variations (one pair of titles per variation; if empty, return one pair with variation=""): {variations}
Head phrases (optional seeds): {head_phrases}
Buyer persona (context for clarity; do not copy literally): {buyer_persona}
Editorial lexicon (style/terms cues; do not force into title if unnatural): {lexico}
Short context (for understanding only; do not copy literally): {context_short}
"""
Í