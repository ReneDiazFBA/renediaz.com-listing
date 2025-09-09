# listing/prompts_listing_copywrite.py
# Prompts estrictos por etapa para la generación de listings de Amazon.
# Este módulo NO agrega reglas propias: solo expresa TUS SOPs.
# En caso de contradicción con guías generales de Amazon, TU SOP PREVALECE.

from typing import List

# ================================
# BRIEF GENERAL (PDF integrado)
# ================================
GENERAL_GUIDELINES_BRIEF = r"""
COPYWRITING GENERAL GUIDELINES FOR AMAZON PRODUCT LISTINGS — CONTRACT LAYER
(Purpose, Mandatory Elements, Compliance, Section Guidelines, Buyer’s Journey, Best Practices, Responsibilities)

PURPOSE
- Provide clear, concise, compliant instructions to maximize visibility, trust, and conversion while fully respecting Amazon’s listing policies.

MANDATORY ELEMENTS OF EVERY LISTING
- Product name / Title: brand, model, main attributes, variations (if applicable); clear and concise.
- Category / browse node: correctly assigned.
- Subscription details (if applicable): length, renewal terms, cost.
- Price & SKU / identifiers: accurate and truthful.
- Product images: follow Amazon standards (main image with white background, product only; no text/logos/watermarks).
- Bullet points (“About this item”): key features, benefits, differentiators.
- Description: expanded detail, narrative and persuasive.
- Search terms (backend): not visible to customers; improve discoverability.
- Brand name: must match registered brand or approved brand.

COMPLIANCE (STRICTLY ENFORCED — APPLY TO TITLE, BULLETS, DESCRIPTION, IMAGES)
- Do NOT include pornographic/obscene/offensive content.
- Do NOT include phone numbers, emails, or non-required URLs.
- Do NOT include testimonials, reviews, ratings, or requests for positive reviews.
- Do NOT include time-sensitive information (e.g., promo dates).
- Do NOT include promotional graphics, ads, watermarks on images.
- Avoid bad formatting or broken data (special characters, HTML errors).

SECTION WRITING GUIDELINES
- Title: quickly communicate brand, product type, and essential attributes; concise, keyword-rich; comply with Amazon character limits.
- Images: main image white background; secondary images show lifestyle, details, angles.
- Bullet Points: 5 bullets; each emphasizes a distinct value or solution (feature → benefit).
- Description: expand product story; persuasive yet factual; benefits and usage scenarios; use <br><br> for paragraphs if required by local SOP.
- A+ / Enhanced Content: visuals + copy to highlight differentiators (comparisons, storytelling).
- Search Terms (Backend): include synonyms, variations, tokens not present in title/bullets.

BUYER’S JOURNEY ALIGNMENT
- FIND: accurate category + search terms.
- CLICK: compelling title + main image.
- DECIDE: persuasive bullets + strong description (A+ content handled on page).

BEST PRACTICES FOR CONVERSION
- Clear, plain English.
- Focus on benefits + features (not specs alone).
- Use emotional triggers carefully (convenience, trust, security, joy).
- Clean formatting: short sentences, scannable lists, avoid walls of text.
- Consistent tone: professional, confident, factual.

RESPONSIBILITIES OF THE COPYWRITER
- Ensure accuracy, completeness, and Amazon-compliance.
- Cross-check restricted products guidelines and image standards.
- Never use manipulative or misleading claims.
- Provide content at least equal in quality to best competitor listings.
- Optimize for BOTH search visibility and conversion.

NOTE ON PRECEDENCE
- Where this brief and a local SOP conflict, the local SOP (ReneDiaz.com) PREVAILS for this system.
"""

# ================================
# TÍTULOS — SOP RD (ESTRICTO)
# ================================
TITLES_SOP_STRICT = r"""
SCOPE
- Titles must be generated ONLY from the structured table (rows with columns: Tipo, Etiqueta, Contenido).
- Use solely the table-derived projections you receive as inputs. If something is not present in those inputs, DO NOT include it.

SOP PRECEDENCE
- In any conflict between this SOP and Amazon general guidelines, THIS SOP PREVAILS.

OUTPUT SHAPE (JSON ONLY)
"title": {
  "parent": { "desktop": "...", "mobile": "..." },
  "<variation_slug_1>": { "desktop": "...", "mobile": "..." },
  "<variation_slug_2>": { "desktop": "...", "mobile": "..." }
  // One child key per value in rows where Tipo == "Variación".
  // The variation key is a slug: lowercase; strip punctuation; spaces→hyphens; collapse repeated hyphens.
}

DATA SOURCING (AUTHORIZED FIELDS ONLY — NO INVENTIONS)
- Brand:
  * ONLY if there is a row with Tipo == "Marca". Use Contenido EXACTLY (no edits). If no brand row exists, do NOT invent or add any brand (no "Generic").
- Product Name:
  * EXCLUSIVELY from rows where Tipo == "SEO semántico" AND Etiqueta == "Core".
  * You MAY insert minimal stopwords for readability, but semantic tokens MUST come from those Core rows.
- Attributes:
  * ONLY from rows where Tipo == "Atributo". Use the Contenido RAW, e.g., "5 Kg", not "Weight: 5 Kg".
  * NEVER use "use case" or any narrative text as attribute content.
  * Attribute PRIORITY (to decide WHICH attributes appear and their order):
      1) Beneficio valorado  → choose attributes that directly enable this benefit
      2) Ventaja             → next strongest differentiators
      3) Obstáculo           → attributes that resolve key objections
    IMPORTANT: The text of Beneficio/Ventaja/Obstáculo is NEVER copied into the title; it ONLY informs which attributes to surface (and in which order).
- Variation values (Child):
  * ONLY from rows where Tipo == "Variación". Use the Contenido EXACTLY (the value ONLY, no label like "Color:").

CANONICAL ORDER & IMMUTABLE BLOCKS
- Canonical order for BOTH Desktop and Mobile, for Parent and each Child:
  Brand + Product Name - Attributes (comma-separated, prioritized as above) - [Child ONLY] Variation
- Permitted separators: " - " (space-hyphen-space) and commas (",") between attributes.
- Do NOT add prefixes like "Brand:", "Attribute:", "Color:".
- IMMUTABLE: Brand, Product Name, and (for Child) Variation MUST NOT be altered, moved, or trimmed.
- ONLY attributes may be trimmed to meet character ranges.

VARIATION HANDLING
- Parent: MUST NOT contain any variation token (no color/size/flavor/etc. if they are variation dimensions).
- Child: append the variation VALUE at the END, after attributes, preceded by a comma and a space.
  Examples: ", Green" or ", 128 GB" or ", Large".
- If Flavor/Style/Color/Size/Pack/Model exist as ATTRIBUTES (not variations), they belong to the Attributes block.
- If Flavor/Style/Color/Size/Pack/Model exist as VARIATIONS, they must NOT appear in the Attributes block; they appear ONLY at the end as the Child variation value.
- If multiple variation dimensions exist, append ALL variation values at the end in this order: Color → Size/Pack → Model → Flavor/Style (values only, comma-separated).
- Child inherits Brand, Product Name and the SAME attributes as Parent (subject to trimming rules below); then appends the variation(s) at the end.

LENGTH & VERSIONS (STRICT; count VISIBLE Unicode characters including spaces)
- For EVERY Parent and for EACH Child, produce TWO versions:
  * Desktop: MIN 120 – MAX 150 characters.
  * Mobile : MIN  75 – MAX  90 characters.
- Build Desktop FIRST. Derive Mobile SOLELY by trimming attributes (in this order):
  1) least differentiating / repetitive attributes
  2) lower-impact attributes for conversion
- NEVER trim Brand, Product Name, or Variation.
- If the minimum cannot be met with authorized material, REJECT and output an empty string "" for that specific field.

STYLE & POLICY (APPLY ALL; SOP overrides Amazon where stricter)
- Global hard cap ≤ 200 characters (Amazon policy). SOP ranges above are REQUIRED.
- No promotional language (free, discount, sale, coupon, shipping), no competitor mentions, no "#1/best".
- No disallowed symbols (! $ ? _ { } ^ ¬ ¦), no emojis, no URLs/contact, no time/price/shipping info.
- No ALL CAPS for the whole line. Use Title Case (standard English); numerals for numbers; standard units/abbreviations; decimal/thousand separators consistent with the product niche.
- Avoid keyword stuffing. Do not repeat the same content word more than 2× (articles/prepositions/conjunctions exempt).
- Determinism & Traceability: same inputs → same outputs; every fragment must trace back to an authorized row (Marca / SEO Core / Atributo / Variación). No inventions.

REJECTION / EMPTY OUTPUT RULE
- When a desktop/mobile field cannot satisfy MIN length using ONLY authorized content, output "" for that field.
"""


def prompt_titles_json(
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
    Prompt ESTRICTO para TÍTULOS (SOP RD). Devuelve SOLO instrucciones para generar la clave "title"
    con parent/child y desktop/mobile, respetando TODAS las normas.
    """
    return f"""{GENERAL_GUIDELINES_BRIEF}

{TITLES_SOP_STRICT}

You are an Amazon listing copywriter executing a binding SOP. Use ONLY the inputs below (table projections). 
If something is not present here, do NOT include it.

AUTHORIZED INPUTS (table-derived projections):
- BRAND candidates (from Tipo="Marca"; may be empty): {head_phrases}
- SEO CORE tokens (Tipo="SEO semántico" & Etiqueta="Core"): {core_tokens}
- ATTRIBUTES (Tipo="Atributo" → Contenido RAW, exact): {attributes}
- VARIATIONS (Tipo="Variación" → Contenido RAW, exact): {variations}

PRIORITIZATION CONTEXT (ONLY to rank attributes; NEVER copy this text):
- beneficios: {benefits}
- emociones/persona (for prioritization signals only): {emotions}
- buyer_persona (overview only): {buyer_persona}
- editorial lexicon (style cues; NEVER invent semantics): {lexico}

INSTRUCTIONS:
- Follow TITLES_SOP_STRICT verbatim (SOP precedence over general guidelines).
- Build the JSON object "title" with:
  - "parent": {{"desktop": "...", "mobile": "..."}}
  - one key per variation, where the key is the slug of the variation value (lowercase; strip punctuation; spaces→hyphen; collapse hyphens)
    and the value is {{"desktop":"...", "mobile":"..."}}.
- Output ONLY the JSON for the "title" key; no other keys, no prose, no markdown, no fences.
"""


# ============================================================
# PLACEHOLDERS — BULLETS / DESCRIPTION / BACKEND (NO USAR)
# ============================================================
BULLETS_SOP_PLACEHOLDER = r"""
PLACEHOLDER — DO NOT USE.
This placeholder will be replaced with the strict SOP for bullets (headers in ALL CAPS + colon, 5 bullets, per-variation rules, etc.).
"""

DESCRIPTION_SOP_PLACEHOLDER = r"""
PLACEHOLDER — DO NOT USE.
This placeholder will be replaced with the strict SOP for description (2–3 paragraphs with <br><br>, avatar narrative, etc.).
"""

BACKEND_SOP_PLACEHOLDER = r"""
PLACEHOLDER — DO NOT USE.
This placeholder will be replaced with the strict SOP for backend search terms (byte count without spaces, dedupe vs surface copy, etc.).
"""


def prompt_bullets_json(
    head_phrases: List[str],
    core_tokens: List[str],
    attributes: List[str],
    variations: List[str],
    benefits: List[str],
    emotions: List[str],
    buyer_persona: str,
    lexico: str,
) -> str:
    return f"""{GENERAL_GUIDELINES_BRIEF}

{BULLETS_SOP_PLACEHOLDER}

(Inputs)
head_phrases: {head_phrases}
core_tokens:  {core_tokens}
attributes:   {attributes}
variations:   {variations}
benefits:     {benefits}
emotions:     {emotions}
buyer_persona:{buyer_persona}
lexico:       {lexico}
"""


def prompt_description_json(
    head_phrases: List[str],
    core_tokens: List[str],
    attributes: List[str],
    variations: List[str],
    benefits: List[str],
    emotions: List[str],
    buyer_persona: str,
    lexico: str,
) -> str:
    return f"""{GENERAL_GUIDELINES_BRIEF}

{DESCRIPTION_SOP_PLACEHOLDER}

(Inputs)
head_phrases: {head_phrases}
core_tokens:  {core_tokens}
attributes:   {attributes}
variations:   {variations}
benefits:     {benefits}
emotions:     {emotions}
buyer_persona:{buyer_persona}
lexico:       {lexico}
"""


def prompt_backend_json(
    head_phrases: List[str],
    core_tokens: List[str],
    attributes: List[str],
    variations: List[str],
    benefits: List[str],
    emotions: List[str],
    buyer_persona: str,
    lexico: str,
) -> str:
    return f"""{GENERAL_GUIDELINES_BRIEF}

{BACKEND_SOP_PLACEHOLDER}

(Inputs)
head_phrases: {head_phrases}
core_tokens:  {core_tokens}
attributes:   {attributes}
variations:   {variations}
benefits:     {benefits}
emotions:     {emotions}
buyer_persona:{buyer_persona}
lexico:       {lexico}
"""
