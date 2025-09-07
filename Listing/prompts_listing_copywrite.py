# listing/prompts_listing_copywrite.py
# All-in-one prompts for Title(s) + Bullets + Description + Backend (EN).
from typing import List

AMAZON_GUIDELINES_BRIEF = """
AMAZON LISTING GUIDELINES — GLOBAL
General:
- Write in ENGLISH.
- No promos, no competitors, no links/contact, no emojis/decorative symbols.
- Title: ≤200 chars; no !, $, ?, _, {, }, ^, ¬, ¦ (except in brand field); avoid word repeated >2 times.
- Bullets: unique, clear; no prohibited claims/symbols.
- Description: plain text; paragraphs split with <br><br>; no other HTML.
- Backend search terms: space-separated tokens; no commas/HTML; avoid duplication with surface copy.
- Use numerals; standard letters; avoid subjective/comparative claims.
"""

EDITORIAL_BRIEF = """
EDITORIAL BRIEF — INTEGRATED BEHAVIOR
Use the structured table projections as ground truth (Tipo, Contenido, Etiqueta).
Keep copy specific, concrete, benefit-led, compliant. Subtle CTAs only.
Brand: if provided, prepend in titles; never invent a brand.
"""

TITLE_BRIEF = """
TITLE CONTRACT
Two lengths per variation: Desktop 150–180 chars; Mobile 75–80 chars.
Order: Brand + Product Name (from core tokens) + Product Type - attribute VALUES (prioritized) - variation.
No duplication between attributes and variation. Title Case; avoid ALL CAPS; allowed punctuation only.
Return: "titles": [{"variation":"...", "desktop":"...", "mobile":"..."}]
"""

BULLETS_BRIEF = """
BULLETS CONTRACT
Exactly 5 bullets, each 130–180 chars.
Format: ALL-CAPS HEADER: sentence fragment; use semicolons for phrases.
Each bullet unique; integrate clusterized SEO tokens naturally; max 1 bullet addresses an objection.
Optionally return per-variation bullets when content depends on variation.
"""

DESCRIPTION_BRIEF = """
DESCRIPTION CONTRACT
Length 1500–1800 chars. Multiple paragraphs separated with <br><br> only.
Para1: pain+stakes; Para2: solution+benefits; Para3: use cases+specifics; Para4 (opt): objections+reassurance.
Integrate core tokens and attribute VALUES naturally; no stuffing; no competitors or prohibited claims.
"""

# >>> BACKEND BRIEF — actualizado para “sobrantes”, español y 243–249 bytes
BACKEND_BRIEF = """
BACKEND SEARCH TERMS CONTRACT
Goal: produce the most relevant "generic keywords" up to 243–249 BYTES (counting bytes with SPACES REMOVED).
Hard rules:
- Output is ONE space-separated string in lowercase; no commas, no punctuation, no HTML.
- No brand names, no ASINs, no promos, no subjective claims, no offensive terms.
- Do NOT repeat any surface word (words already present in titles, bullets, description).
- Use either singular OR plural per token family (not both).
Coverage strategy (in priority order):
1) CORE semantic tokens not used on surface → include them (lowercase).
2) EXTRA tokens (non-core/cluster) not used on surface → include best-matching ones.
3) VARIATION terms (size/color/pack) ONLY if not used on surface and truly relevant for discovery.
4) Add meaningful synonyms/abbreviations/spelling variants (US/UK) when helpful (no “common misspellings”).
5) Add SPANISH equivalents of CORE tokens when they are natural translations (singular only), avoid diacritics if they inflate bytes.
Byte target:
- Aim for 247–249 bytes (spaces removed). If above 249, drop the least-important tail tokens; if below 243, append more relevant variants.
Return: field "search_terms": "<space separated tokens>"
"""


def prompt_master_json_all(
    brand: str,
    core_tokens: List[str],
    attributes: List[str],
    variations: List[str],
    benefits: List[str],
    obstacles: List[str],
    emotions: List[str],
    buyer_persona: str,
    lexico: str,
    extra_tokens: List[str],       # <<< NUEVO
    variation_terms: List[str],    # <<< NUEVO
) -> str:
    return f"""{AMAZON_GUIDELINES_BRIEF}

{EDITORIAL_BRIEF}

{TITLE_BRIEF}

{BULLETS_BRIEF}

{DESCRIPTION_BRIEF}

{BACKEND_BRIEF}

You are an Amazon listing copywriter. Generate the FULL LISTING in ENGLISH.
Use ONLY the inputs below (projections from the structured table: Tipo/Contenido/Etiqueta):

Brand: {brand}
Core semantic tokens (name/product foundation): {core_tokens}
Extra semantic tokens (non-core/cluster): {extra_tokens}
Attribute VALUES (no labels): {attributes}
Variations (size/color/pack): {variations}
Variation terms (normalized for backend): {variation_terms}
Benefits: {benefits}
Obstacles/Cons: {obstacles}
Emotions: {emotions}
Buyer persona: {buyer_persona}
Editorial lexicon: {lexico}

Return ONLY valid JSON with this exact schema:
{{
  "titles": [
    {{"variation":"<variation>", "desktop":"<150–180 chars>", "mobile":"<75–80 chars>"}}
  ],
  "bullets": ["<130–180>", "<130–180>", "<130–180>", "<130–180>", "<130–180>"],
  "variation_bullets": {{
    "<variation>": ["<130–180>", "<130–180>", "<130–180>", "<130–180>", "<130–180>"]
  }},
  "description": "<1500–1800 chars with <br><br> paragraph breaks (multiple paragraphs)>",
  "search_terms": "<space-separated; lowercase; 243–249 bytes when removing spaces; no surface duplicates>"
}}
Strictly follow all contracts above.
"""
