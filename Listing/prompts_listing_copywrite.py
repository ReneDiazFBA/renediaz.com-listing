# listing/prompts_listing_copywrite.py
# Prompts EN for Title / Bullets / Description / Backend (ranges per RD spec).

from typing import List

# ============================================================
# AMAZON — GENERAL POLICY GUIDELINES (Contrato de cumplimiento)
# Sustituye al antiguo POLICY_BRIEF
# ============================================================

AMAZON_GUIDELINES_BRIEF = """
AMAZON LISTING – GENERAL POLICY GUIDELINES

Follow Amazon’s global rules for product detail pages. These rules apply to all products
(unless explicitly overridden by category-specific style guides).

TITLE
- Maximum 200 characters (spaces included).
- Order recommended: Brand + Line/Model + Product Type + 1–2 Key Attributes (material, color, size, pack).
- Use numerals ("2" not "two").
- No ALL CAPS, no promotional language ("free shipping", "best", "#1"), no competitor mentions.
- No special characters: !, $, ?, _, {, }, ^, ¬, ¦. Use only standard punctuation (- , / & .).
- No redundant words or unnecessary synonyms.
- Parent ASIN: generic title (no variation details). Child ASIN: include the variation (color/size).

BULLETS
- 5 bullets recommended, each concise (<200 characters is a safe target; hard max varies by category).
- Structure: Attribute + Benefit + Use case.
- Start with capital letter; avoid trailing punctuation.
- No subjective claims ("amazing", "perfect") and no promotions.
- Keep bullet structure consistent across variations.

DESCRIPTION
- 1,600–2,000 characters recommended.
- Plain text only; separate paragraphs with <br><br>.
- Expand bullets into narrative (benefits, objections handled, use-cases).
- No HTML tags (beyond <br><br> as separators), no emojis, no promotions.

SEARCH TERMS (Backend Keywords)
- Limit: 249 bytes max (measured without spaces).
- Do not repeat surface words from title, bullets, or description.
- Space-separated only (no commas or punctuation).
- Include synonyms, common misspellings, and relevant foreign terms.
- No brand names, ASINs, competitor references, or misleading terms.
- Choose singular OR plural, not both.

IMAGES
- Main image: pure white background (RGB 255), product ≥85% of frame.
- Professional photo only; no text, logos, watermarks, or misleading props.
- High resolution: ≥1600 px longest side (zoom enabled).
- Additional images: lifestyle, details, scale, and usage context.

VARIATIONS
- Allowed only when differences are a consistent attribute (size/color/pack).
- Parent: generic title/images. Child: variation-specific title/images.
- Do not group unrelated products.

GENERAL PROHIBITIONS
- No false or unverifiable claims.
- No reviews, quotes, or testimonials inside listing copy.
- No time-sensitive info (events, tour dates, etc.).
- No contact details, external URLs, or ordering info.
- One detail page = one unique product (no multi-product pages).
- Ensure valid category/browse node and product identifiers (UPC/EAN).

Non-compliance may result in listing suppression, automated corrections, or removal.
"""

# ============================================================
# EDITORIAL BRIEF (lo iremos afinando más adelante)
# ============================================================

EDITORIAL_BRIEF = """
EDITORIAL BRIEF – INTEGRATED VERSION (BEHAVIORAL RULES)

All copy is derived from a structured table with columns: tipo, contenido, etiqueta.
Your inputs are pre-extracted lists from that table; treat them as faithful projections:

MAPPING (table → inputs you receive):
- Avatar (Buyer Persona): rows where tipo = "Buyer persona" → provided as buyer_persona (string).
- Emotions: rows where tipo = "Emoción" → provided as emotions (list). etiqueta='Positivo' reinforce desires; etiqueta='Negativo' or 'CON' address pain/objections.
  Map only relevant ones to the 8 core emotions: Status & Recognition; Financial Security; Time & Efficiency; Relationship & Connection;
  Confidence & Competence; Growth & Achievement; Safety & Peace of Mind; Pleasure & Enjoyment. Identify primary and secondary emotions.
- Story / Narrative: rows where tipo = "Obstáculo" and tipo = "Beneficio" → already summarized within benefits (list) and persona/lexicon.
  Use PRO to emphasize advantages/desirable outcomes; use CON to acknowledge pains and pivot to resolution.
- Placement: Amazon product page (high intent). Copy Triangle System:
  Where → Amazon; Why → purchase intent; What → conversion.
  Structure: start with problem/pain → agitate consequences → introduce the product as solution → relatable examples/use cases.
  Best practices: benefit-led headlines, address objections, mix logic + emotion. CTAs must be subtle and compliant (no explicit “Buy now”).
- Objective / Descripción breve: rows where tipo = "Descripción breve" → provided implicitly via benefits/persona/lexicon. Goal: conversion with specificity and personalization.
- Lexicon & Tone: rows where tipo = "Léxico editorial" → provided as lexico (string). Use those exact terms and style cues.
- Brand: if the table contains tipo = "marca", it may be present inside head_phrases or attributes/variations strings.
  If a brand-like value is present in your inputs, prepend it to the Title as Brand.
  If not present, do not invent a brand.

FORMATS TO PRODUCE:
- Title (150–200 chars): follow exactly → Brand (if available) + Product Name + Product Type + 1–2 Key Feature(s) + Use Case + Size/Quantity/Color.
  Keep it tight and non-redundant.
- Bullets (5 × 180–240 chars): each bullet MUST start with an ALL-CAPS HEADER followed by a colon, then the sentence.
  Pattern: HEADER: concise sentence that combines Attribute + Benefit + Use case. Use sensory/experiential language when appropriate.
- Description (1600–2000 chars): plain text; separate paragraphs with <br><br>. Blend story with benefits and objections for the avatar.
- Backend (243–249 bytes without spaces): space-separated tokens; no commas/HTML; do not repeat any surface words; may include typos/other languages; enforce singular OR plural (not both).
"""

# ============================================================
# Prompt maestro (genera Title + Bullets + Description + Backend en 1 paso)
# ============================================================


def prompt_master_json(
    head_phrases: List[str],
    core_tokens: List[str],
    attributes: List[str],
    variations: List[str],
    benefits: List[str],
    emotions: List[str],
    buyer_persona: str,
    lexico: str,
) -> str:
    """
    Master prompt que fija:
    - Cumplimiento de políticas de Amazon (AMAZON_GUIDELINES_BRIEF).
    - Marco editorial (EDITORIAL_BRIEF).
    - Generación en un solo paso: title, bullets, description y search_terms.
    """

    return f"""{AMAZON_GUIDELINES_BRIEF}

{EDITORIAL_BRIEF}

You are an Amazon listing copywriter. Build the ENGLISH listing using ONLY the inputs below
(which are projections of the table's 'tipo/contenido/etiqueta').

Return ONLY valid JSON with keys:
- "title": string (150–200 chars; Brand + Product Name + Product Type + 1–2 Key Features + Use Case + Size/Quantity/Color)
- "bullets": array of 5 strings (each 180–240 chars; **ALL-CAPS HEADER:** then a sentence that combines Attribute + Benefit + Use case; specific & action-oriented)
- "description": string (1600–2000 chars; paragraphs separated by <br><br>; story-led and avatar-personalized; benefit-driven; compliant with Amazon)
- "search_terms": string (backend keywords; 243–249 bytes when removing spaces; SPACE-separated; NO commas; NO HTML; NO duplication with surface copy; may include typos/other languages; singular OR plural only)

Inputs (table-derived projections):
Head phrases (may include Product Name / seed phrases / brand if present): {head_phrases}
Core semantic tokens (lemmas; can inform backend long-tail): {core_tokens}
Attributes (materials, features): {attributes}
Variations (size/quantity/color/measurements): {variations}
Top benefits (market-validated + client match): {benefits}
Emotions (raw list to map into core emotions): {emotions}
Buyer persona (avatar summary): {buyer_persona}
Editorial lexicon (exact style/terms to use): {lexico}
"""
