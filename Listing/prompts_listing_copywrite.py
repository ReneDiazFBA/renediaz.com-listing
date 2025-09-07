# listing/prompts_listing_copywrite.py
# Prompts EN for Title / Bullets / Description / Backend (ranges per RD spec).

from typing import List

# -----------------------------
# Amazon General Guidelines (hard policies)
# -----------------------------
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
- For parent ASINs: keep generic (no variation details). For child ASINs: include color/size variation.

BULLETS
- 5 bullets recommended, each <200 characters (hard max ~500).
- Structure: Attribute + Benefit + Use case.
- Begin with capital letter, no ending punctuation.
- No subjective claims ("amazing", "perfect"), no promotions.
- Be consistent across variations.

DESCRIPTION
- 1,600–2,000 characters recommended.
- Plain text only; separate paragraphs with <br><br>.
- Expand bullets into narrative: story, benefits, objections addressed.
- No HTML, emojis, or promotional claims.

SEARCH TERMS (Backend Keywords)
- Limit: 249 bytes max (measured without spaces).
- Do not repeat words from title, bullets, or description.
- Space-separated only (no commas, no punctuation).
- Include synonyms, common misspellings, and foreign terms if relevant.
- No brand names, ASINs, competitor references, or misleading terms.
- Choose singular OR plural, not both.

IMAGES
- Main image: pure white background (RGB 255), product occupies ≥85% of frame.
- Professional photo only; no text, logos, watermarks, or props that mislead.
- High resolution: ≥1600 px longest side to enable zoom.
- Additional images: lifestyle, detail shots, scale, usage context.

VARIATIONS
- Allowed only when products differ by a consistent attribute (e.g., size, color, pack).
- Parent = generic title and images. Child ASINs = variation-specific title + images.
- Do not group unrelated products.

GENERAL PROHIBITIONS
- No false or unverifiable claims.
- No reviews, quotes, testimonials inside listing copy.
- No time-sensitive info (events, tours, dates).
- No contact details, external URLs, or ordering info.
- Each detail page = one unique product. No multi-product detail pages.
- Ensure category (browse node) and UPC/EAN are valid.

Non-compliance may result in listing suppression, automated corrections, or removal.
"""

# -----------------------------
# Editorial Brief (style, tone, emotions)
# -----------------------------
EDITORIAL_BRIEF = """
EDITORIAL BRIEF – GENERAL COPYWRITING PRINCIPLES

1. Avatar (Buyer Persona)
- Write for one clear person, not for a generic audience.
- Mirror the language, concerns, and expressions found in reviews and inputs.
- Identify frustrations, dreams, and objectives directly.

2. Emotion as the Driver
- Purchases are driven by emotions first, logic second.
- Anchor copy to 1 primary and 2–3 secondary emotions.
- Core emotions: Status & Recognition; Financial Security; Time & Efficiency;
  Relationship & Connection; Confidence & Competence; Growth & Achievement;
  Safety & Peace of Mind; Pleasure & Enjoyment.
- Common fears to neutralize: financial loss, wasted time, embarrassment,
  missing out (FOMO), overwhelm, making a wrong choice.

3. Message Structure
- Hook → Emotion → Benefit → Proof/Attribute → Trust.
- Crocodile Brain (clarity, no spam/confusion).
- Midbrain (emotion, sensory examples, relatable scenarios).
- Neocortex (logic: attributes, data, justification).

4. Editorial Style
- Conversational, direct, simple language.
- Use action verbs, short sentences, sensory details when useful.
- Avoid jargon, fluff, or subjective claims.
- No hype (“best”, “#1”, “top quality”). Stay precise and benefit-driven.

5. Amazon Context
- Lead with benefits, reinforce with attributes.
- Mix logic + emotion consistently.
- Acknowledge objections and pivot to resolution.
- Customer-centric voice: use “you/your” more than “we/our”.

Always integrate these editorial principles while respecting Amazon Guidelines.
"""

# -----------------------------
# Master Prompt
# -----------------------------


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
    One-shot master prompt. Embeds Amazon Guidelines + Editorial Brief,
    then adds table-derived inputs.
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
