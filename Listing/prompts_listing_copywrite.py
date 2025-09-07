# listing/prompts_listing_copywrite.py
# All-in-one prompts for Title(s) + Bullets + Description + Backend (EN).
# Amazon Guidelines brief + Editorial brief + section contracts.

from typing import List

AMAZON_GUIDELINES_BRIEF = """
AMAZON LISTING GUIDELINES — GLOBAL

General:
- Write in ENGLISH.
- Do not include promotional language (“free shipping”, “#1”, “best”), competitor mentions, links, emails, phone numbers.
- No emojis or decorative symbols. Disallowed in titles: !, $, ?, _, {, }, ^, ¬, ¦ (unless part of the registered brand name in Amazon's brand field).
- Use standard letters and numerals. No non-language ASCII like Æ, Œ, Ÿ, etc.
- Use numerals for numbers (2 not "two"). Space between digit and measurement (e.g., 60 ml).
- Avoid subjective, unverifiable performance or comparative claims. No awards unless substantiated elsewhere on the page.

Title (hard rules):
- ≤ 200 characters (including spaces) as global max.
- No promotional phrases. Do not repeat the same word more than twice (prepositions/articles/conjunctions are exceptions).
- Prefer concise, scannable structure. Title case (Capitalize Main Words), not ALL CAPS.
- Allowed punctuation: hyphens (-), slashes (/), commas (,), ampersands (&), periods (.).
- Put size/color/pack in child variations; parent titles should not duplicate variation values.

Bullets:
- 5 feature bullets recommended (we will generate exactly 5).
- Each bullet conveys UNIQUE info; remove redundancy. Sentence fragments, no terminal punctuation; use semicolons to separate phrases.
- No special symbols, links, contact details, guarantees, or prohibited green claims.
- Use clear, natural language; highlight concrete features → benefits → use cases.

Description:
- Plain text; paragraphs separated by <br><br>. No HTML beyond those breaks.
- Story + benefits + objection handling; consistent with bullets and title.

Backend Search Terms:
- Space-separated tokens (no commas/HTML).
- Do not repeat surface words already used in title/bullets/description.
- May include misspellings or other languages when relevant.
- Keep singular OR plural for a token family (not both).
"""

EDITORIAL_BRIEF = """
EDITORIAL BRIEF — INTEGRATED BEHAVIOR

Input data comes from a structured table with columns: Tipo, Contenido, Etiqueta.
You receive pre-extracted lists from that table; treat them as the ground truth.

Mapping principles:
- Buyer Persona: summarize who buys and why (tone + relevance).
- Emotions: reinforce positive desires; acknowledge negative pains and pivot to resolution.
- Benefits/Pros vs Obstacles/Cons: emphasize outcomes; address objections tactfully (1 slot).
- Lexicon: adopt the editorial terms and style cues verbatim when appropriate (no keyword stuffing).
- Brand: if provided, use it at the front of Titles. Do not invent a brand.

Copy logic:
- Amazon page = high intent; mix logic + emotion but stay specific and concrete.
- Structure tends to: problem/pain → consequences → product solution → relatable use cases.
- Subtle CTAs; never manipulative or non-compliant.
"""

TITLE_BRIEF = """
TITLE CONTRACT

We generate TWO title lengths per variation:
- Desktop: 150–180 characters (including spaces).
- Mobile: 75–80 characters (including spaces).

Construction (in order):
Brand + Product Name (built ONLY from core tokens; no invented terms) + Product Type
+ Key attribute values (values only, taken from prioritized attributes)
+ Variation (size/color/pack etc. — one title per variation with same base text)

Separators:
- Brand and Product Name/Product Type: space (no hyphen here)
- Between blocks (product type ↔ attributes ↔ variation): " - "
- Between multiple attributes: ", "

Strict rules:
- Do NOT duplicate a value as both attribute and variation; if a prioritized attribute is tagged as variation, place it ONLY as variation.
- Use as many attribute VALUES as fit within the target length; prioritize by review importance.
- Title case (Capitalize Main Words), avoid ALL CAPS.
- Respect Amazon disallowed characters and duplication limits.

Output for titles: JSON array "titles" of objects:
[
  {"variation": "<exact variation value>", "desktop": "<150–180 chars>", "mobile": "<75–80 chars>"},
  ...
]
"""

BULLETS_BRIEF = """
BULLETS CONTRACT

- Exactly 5 bullets.
- Each bullet 130–180 characters (including spaces).
- Format: ALL-CAPS HEADER followed by colon, then sentence fragment (no final period). Use semicolons to split phrases.
- Bullet anatomy: HEADER: Attribute value + resulting benefit + use case / scenario.
- Integrate clusterized SEO tokens naturally (no stuffing).
- Cover obstacles/cons by reframing in ONE bullet max.
- If a bullet depends on variation (e.g., pack size), generate per-variation text in "variation_bullets" with the same bullet order.

Output keys:
"bullets": [str, str, str, str, str]
"variation_bullets": { "<variation>": [str×5], ... }  # optional
"""

# >>> UPDATED: Description contract to 1500–1800 chars with multiple paragraphs
DESCRIPTION_BRIEF = """
DESCRIPTION CONTRACT

- Length: 1500–1800 characters (including spaces).
- Plain text only; separate paragraphs with <br><br>. Use MULTIPLE paragraphs (never a single block).
- Paragraphing guidance:
  * 1st: problem/pain + stakes (persona language)
  * 2nd: product solution + core features mapped to benefits
  * 3rd: use cases + proof-like specifics (materials, sizes, fit, care) in natural language
  * 4th (optional within limit): objection handling + reassurance (care, durability, compatibility, warranty info if applicable—no promos)
- Integrate core SEO tokens and prioritized attribute VALUES naturally; avoid keyword stuffing.
- Must be consistent with Titles and Bullets; no contradictions; no prohibited claims or competitor mentions.
"""

BACKEND_BRIEF = """
BACKEND SEARCH TERMS CONTRACT

- Space-separated tokens (no commas/HTML).
- 243–249 BYTES when removing spaces (count UTF-8 bytes of the string with spaces removed).
- Do NOT repeat any surface word used in Titles, Bullets, or Description.
- May include misspellings and language variants when relevant.
- Enforce singular OR plural per token family (not both).
- Prefer long-tail variations derived from core semantic tokens and attributes.
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
) -> str:
    return f"""{AMAZON_GUIDELINES_BRIEF}

{EDITORIAL_BRIEF}

{TITLE_BRIEF}

{BULLETS_BRIEF}

{DESCRIPTION_BRIEF}

{BACKEND_BRIEF}

You are an Amazon listing copywriter. Generate the FULL LISTING in ENGLISH.
Use ONLY the inputs below (they are projections from a structured table: Tipo/Contenido/Etiqueta):

Brand (from table, if present): {brand}
Core semantic tokens (lemmas; foundation for Product Name): {core_tokens}
Attribute VALUES (prioritized by reviews; no labels): {attributes}
Variations (size/color/pack etc. — one title per variation): {variations}
Benefits (market-validated): {benefits}
Obstacles/Cons (to tactfully address once): {obstacles}
Emotions (raw list): {emotions}
Buyer persona (avatar): {buyer_persona}
Editorial lexicon (exact terms/style to adopt): {lexico}

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
  "search_terms": "<243–249 bytes when removing spaces>"
}}

Strictly follow all contracts above.
"""
