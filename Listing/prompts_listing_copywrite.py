# listing/prompts_listing_copywrite.py
# Prompts EN for Title / Bullets / Description / Backend.

from typing import List

POLICY_BRIEF = """Write in English. Follow Amazon style:
- No promotional language (free, discount, sale, coupon, shipping), no competitor mentions, no "#1/best".
- No special symbols (™, ®, &, @), no emojis, no HTML.
- Title ≤ ~200 bytes, bullets < 150 characters each, description ≤ ~2000 bytes, backend ≤ 249 bytes.
- Use clear benefits and concrete attributes. Avoid subjective claims.
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
You are an Amazon listing copywriter. Create a concise listing in ENGLISH from the inputs.

Return ONLY valid JSON with keys:
- "title": string (<= 200 bytes)
- "bullets": array of 5 short strings (< 150 characters each)
- "description": string (<= 2000 bytes)
- "search_terms": string (backend keywords, <= 249 bytes, space-separated, no commas)

Guidelines:
- Title: use 1–2 head phrases + 1–2 key attributes + 1 differentiator. Avoid redundancy.
- Bullets: attributes + benefits + usage/care tips. Each under 150 characters.
- Description: brief overview + 3–5 benefits fused + audience fit; plain text.
- Backend: relevant long-tail NOT already present in title/bullets/description.

INPUTS
Head phrases: {head_phrases}
Core semantic tokens: {core_tokens}
Attributes: {attributes}
Variations: {variations}
Top benefits: {benefits}
Emotions: {emotions}
Buyer persona: {buyer_persona}
Editorial lexicon: {lexico}
"""
