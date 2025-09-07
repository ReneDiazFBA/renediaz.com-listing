# listing/prompts_listing_copywrite.py
# Prompt maestro: Amazon Guidelines + Editorial Brief + Contratos por pieza (Title/Bullets/Description/Backend).
# Devuelve TODO en una sola respuesta JSON (titles por variación, bullets, descripción, backend).
# Exporta: PROMPT_MASTER_JSON

from typing import List, Optional

# ─────────────────────────────────────────────────────────────────────────────
# AMAZON – GLOBAL GUIDELINES (Hard Rules)
# ─────────────────────────────────────────────────────────────────────────────
AMAZON_GUIDELINES_BRIEF = r"""
AMAZON LISTING – GLOBAL GUIDELINES (HARD RULES)

LANGUAGE & STYLE
- Write in ENGLISH.
- Natural, clear, specific; no keyword stuffing; avoid repetition.
- Use numerals (2, 3…), standard ASCII letters/numbers. Avoid non-language ASCII (Æ, Œ, …).

PROHIBITED CONTENT
- No promotional claims (“free shipping”, “discount”, “#1/best”), no competitor mentions.
- No subjective or unverifiable superlatives (best, amazing, cheapest), no time-sensitive promises.
- No URLs, emails, phone numbers; no ASINs; no competitor brand names; only the product’s own brand where allowed.
- No profanity, offensive terms, or restricted claims.

PUNCTUATION & SYMBOLS
- Disallow: !, $, ?, _, {, }, ^, ¬, ¦.
- Use hyphens (-), commas (,), slashes (/), ampersands (&), periods (.) only when necessary and compliant.

FORMAT BASICS
- Include the minimum info needed to clearly describe the product.
- Title case for proper nouns; do NOT write full sentences in ALL CAPS.
- Avoid articles/stopwords in backend search terms (a, an, and, by, for, of, the, with…).
"""

# ─────────────────────────────────────────────────────────────────────────────
# EDITORIAL BRIEF – Table-Driven (acordado)
# ─────────────────────────────────────────────────────────────────────────────
EDITORIAL_BRIEF = r"""
EDITORIAL BRIEF – TABLE-DRIVEN

ORIGIN OF TRUTH
All inputs come from a structured table with (Tipo, Contenido, Etiqueta, Fuente).
You will receive already-projected lists/strings from that table. Do NOT invent data.

MAPPING
- brand (string): from Tipo="Marca" (if present).
- buyer_persona (string): from Tipo="Buyer persona".
- emotions (list): from Tipo="Emoción"; Etiqueta 'Positive' refuerza deseos; 'Negative'/'CON' = objeciones a abordar.
- benefits (list): advantages validated by market/client (Beneficio / Beneficio valorado / Ventaja).
- lexico (string): editorial lexicon/terms/tone to mirror exactly.
- attributes (list, values-only): product attributes as values (e.g., “green”, “steel”, “matte”); never include labels like “color:”.
- variations (list, values-only): size/pack/color etc. If a value exists as variation, do NOT duplicate as attribute.
- core_tokens (list): semantic core (lemmas) to signal the “what” and primary intent.

NARRATIVE & PERSUASION
- Benefit-led, objection-aware, persona-aligned.
- Use emotions as cues: negatives → pains/objections to resolve; positives → desired outcomes.
- Be specific and concrete; avoid vague claims; no promotional hype; compliance first.
"""

# ─────────────────────────────────────────────────────────────────────────────
# CONTRATOS por pieza
# ─────────────────────────────────────────────────────────────────────────────
TITLE_CONTRACT = r"""
TITLE CONTRACT
- Generate per-variation titles (one title set per variation): ONLY the variation value changes; the rest stays identical.
- Structure and separators:
  • Brand + ProductName(derived ONLY from core tokens; brief description is context only, not output) – Key Attributes (values only, comma-separated) – Variation (value only).
  • No attribute labels: never use “Color: Green” → “Green”.
  • Desktop: 150–180 characters (spaces included).
  • Mobile: 75–80 characters (spaces included).
  • Do not repeat the same word more than twice in the whole title.
  • If a value appears as variation, do NOT duplicate as attribute.
  • When trimming for mobile, NEVER truncate the ProductName; shorten the attributes first; variation only as last resort.
  • Allowed punctuation: hyphen (-) between blocks; commas to separate attributes. No exclamation marks or disallowed symbols.
"""

BULLETS_CONTRACT = r"""
BULLETS CONTRACT (5 bullets)
- Each bullet: 130–180 characters.
- Start with ALL-CAPS HEADER then colon, e.g., PERFORMANCE: ... (no final period).
- Sentence fragment style; use semicolons to separate phrases when needed.
- Each bullet must introduce UNIQUE information (no duplication).
- Integrate SEO semantics (core/cluster) naturally (no stuffing); reflect lexico.
- Use at least two “fascination” styles tastefully (HOW-TO, SECRET, WHY, WHAT-NEVER, NUMBER, WARNING, DIRECT BENEFIT, SPECIFIC QUESTION, IF-THEN, QUICK & EASY, TRUTH, BETTER, SINGLE).
- If a concept is variation-specific, phrase bullets at parent-ASIN level (generic), unless explicitly instructed otherwise.
"""

DESCRIPTION_CONTRACT = r"""
DESCRIPTION CONTRACT
- 1500–1800 characters.
- Paragraphs separated ONLY by <br><br> (no other HTML).
- Structure:
  (1) Problem/pain (use Negative emotions/objections) →
  (2) Solution with concrete attributes → benefits →
  (3) Use cases/examples (persona-aligned) →
  (4) Subtle objection handling; lexico faithful.
- Natural inclusion of core/cluster tokens; no stuffing; maintain readability/compliance.
"""

BACKEND_CONTRACT = r"""
BACKEND SEARCH TERMS CONTRACT
- 243–249 bytes (spaces removed).
- Lowercase, space-separated tokens; no punctuation/commas.
- No brand names, ASINs, competitors, profanity, subjective or temporary terms.
- Remove stopwords; prefer core tokens + long-tail from attributes/variations/use cases.
- Include safe Spanish equivalents of CORE tokens (no diacritics) when relevant and non-redundant.
- Do not repeat any surface word present in titles/bullets/description.
- Enforce singular OR plural (not both) within the same family.
"""

# ─────────────────────────────────────────────────────────────────────────────
# PROMPT MAESTRO (una sola llamada IA → JSON)
# ─────────────────────────────────────────────────────────────────────────────


def PROMPT_MASTER_JSON(
    brand: str,
    brief_description: str,
    core_tokens: List[str],
    attributes: List[str],
    variations: List[str],
    benefits: List[str],
    emotions: List[str],
    buyer_persona: str,
    lexico: str,
) -> str:
    """
    Construye el prompt maestro para generar:
      - titles (por cada variation: desktop/mobile)
      - bullets (5)
      - description
      - search_terms (backend)
    """
    # Normaliza listas
    core_tokens = list(filter(None, core_tokens or []))
    attributes = list(filter(None, attributes or []))
    variations = list(filter(None, variations or []))
    benefits = list(filter(None, benefits or []))
    emotions = list(filter(None, emotions or []))

    return f"""
You are an Amazon listing copywriter. Return ONLY VALID JSON that contains:
- "titles": [{{"variation":"<value>", "desktop":"<150–180 chars>", "mobile":"<75–80 chars>"}} ... one per variation],
- "bullets": ["<5 bullets, each 130–180 chars, ALL-CAPS HEADER: fragment; no final period>"],
- "description": "<1500–1800 chars; paragraphs separated by <br><br>; no other HTML>",
- "search_terms": "<lowercase space-separated tokens; 243–249 BYTES when removing spaces; no duplicates with surface>".

GLOBAL GUIDELINES (MANDATORY):
{AMAZON_GUIDELINES_BRIEF}

EDITORIAL RULES (MANDATORY):
{EDITORIAL_BRIEF}

CONTRACTS (MANDATORY):
{TITLE_CONTRACT}
{BULLETS_CONTRACT}
{DESCRIPTION_CONTRACT}
{BACKEND_CONTRACT}

INPUTS (projected from the table; do NOT invent values):
- brand: {brand}
- brief_description (context only for understanding, not to be copied verbatim): {brief_description}
- core_tokens (use to craft ProductName and semantics): {core_tokens}
- attributes (values only, candidate key features; exclude anything that is also a variation value): {attributes}
- variations (values only; generate one title set per variation value): {variations}
- benefits (market-validated advantages/“pros”): {benefits}
- emotions (raw list; map to pains/desires sensibly): {emotions}
- buyer_persona: {buyer_persona}
- lexico (exact editorial cues/terms): {lexico}

SELF-CHECK BEFORE RESPONDING:
- Titles: correct separators; no labels; no repeated word >2x; desktop 150–180; mobile 75–80; only variation changes.
- Bullets: format + uniqueness + length range; contain useful SEO semantics naturally.
- Description: 1500–1800 chars; multiple paragraphs with <br><br>.
- Backend: 243–249 bytes (spaces removed); no surface duplicates; includes safe Spanish variants for core tokens; no stopwords/brands.

Respond ONLY with the JSON object described above.
"""
