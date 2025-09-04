# listing/prompts_listing_copywrite.py
# Prompts EN for Title / Bullets / Description / Backend (ranges per RD spec).

from typing import List

POLICY_BRIEF = """Write in English. Follow Amazon style:
- No promotional language (free, discount, sale, coupon, shipping), no competitor mentions, no "#1/best".
- No special symbols (™, ®, &, @), no emojis, no HTML.
- Respect these HARD ranges:
  * Title: 150–200 characters.
  * Bullets: 180–240 characters each.
  * Description: 1600–2000 characters (plain text).
  * Backend: 243–249 BYTES, counting bytes with SPACES REMOVED (space is a separator only).
- Use clear benefits and concrete attributes. Avoid subjective claims.
- Do NOT include brand names or competitors.
- Backend must NOT repeat words already present in title/bullets/description.
- Backend may include common misspellings (typos) and terms in other languages when relevant.
- Use either plural OR singular forms (not both) for the same token family.
"""


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
    return f"""{POLICY_BRIEF}
You are an Amazon listing copywriter. Build a concise ENGLISH listing from the inputs.

Return ONLY valid JSON with keys:
- "title": string (150–200 chars)
- "bullets": array of 5 strings (each 180–240 chars; combine Attribute + Benefit + Use case; specific & action-oriented)
- "description": string (1600–2000 chars; overview + 3–5 fused benefits + audience fit; plain text)
- "search_terms": string (backend keywords; 243–249 bytes; SPACE-separated; NO commas; NO HTML; NO duplication with surface copy)

Inputs:
Head phrases: {head_phrases}
Core semantic tokens (lemmas): {core_tokens}
Attributes: {attributes}
Variations: {variations}
Top benefits: {benefits}
Emotions: {emotions}
Buyer persona: {buyer_persona}
Editorial lexicon: {lexico}
"""
