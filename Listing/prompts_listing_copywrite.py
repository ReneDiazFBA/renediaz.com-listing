# listing/prompts_listing_copywrite.py
# Prompts per stage for Amazon listings.
# No hidden fallbacks; no placeholders that pretend to work.
# In case of conflict, the local SOP (ReneDiaz.com) PREVAILS.

from typing import List

# ================================
# GENERAL GUIDELINES (integrated)
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
  * EXCLUSIVELY from rows where Etiqueta == "Core" (regardless of Tipo).
  * You MAY insert minimal stopwords for readability, but semantic tokens MUST come from those Core rows.
  * CONSTRUCTION RULES (compose a readable noun phrase ONLY with the provided Core tokens):
    - Build a grammatical phrase using ONLY the Core tokens + minimal function words (articles/prepositions/determiners) required for fluency in English.
    - DO NOT introduce any new content words (nouns/adjectives) not present in Core.
    - Normalize inflection (singular/plural) and order tokens in a natural English way.
    - Example: from Core tokens ["stove","gas","burners","5"] → "gas stove with 5 burners".
    - Keep marketplace conventions (e.g., unit placement, numeral formatting) but never add attributes not in Core.
    - If Core tokens are insufficient to form a readable phrase, output an empty string "" (reject) for that field.
  * CAPITALIZATION (STRICT for Product Name):
    - Apply Title Case to the Product Name.
    - Keep common stopwords in lowercase **unless** they are the first or last word, or follow a hyphen “-” or slash “/”.
    - Stopwords set (en): a, an, the, and, but, or, nor, for, so, yet, as, at, by, for, from, in, into, of, on, onto, over, to, up, with, via, per, vs
    - Examples: "Gas Stove with 5 Burners", "Privacy Dividers for Classrooms", "Rectangular / Foldable Labels"
    - Preserve brand casing exactly as provided in table; brand is not part of Product Name capitalization rules.
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
- Determinism & Traceability: same inputs → same outputs; every fragment must trace back to an authorized row (Marca / Core / Atributo / Variación). No inventions.

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
    Strict prompt for TITLES (SOP RD). Returns ONLY instructions to build the "title" key
    with parent/child and desktop/mobile. No fallbacks, no extra rules.
    """
    return f"""{GENERAL_GUIDELINES_BRIEF}

{TITLES_SOP_STRICT}

You are an Amazon listing copywriter executing a binding SOP. Use ONLY the inputs below (table projections). 
If something is not present here, do NOT include it.

AUTHORIZED INPUTS (table-derived projections):
- BRAND candidates (from Tipo="Marca"; may be empty): {head_phrases}
- SEO CORE tokens (Etiqueta="Core"): {core_tokens}
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


# ================================
# BULLETS — General Brief (Amazon + Editorial + Fascination)
# ================================
BULLETS_GENERAL_BRIEF = r"""
COPYWRITING GENERAL BULLETS GUIDELINES — CONTRACT LAYER
(Integrates Amazon section rules + Editorial Brief + Fascination styles)

AMAZON RULES
- 5 bullets in "About this item".
- Each one distinct, informative; no promotions, no competitors, no testimonials.
- Fragments; no period at end. Numbers: 1–9 spelled, 10+ as digits.
- Clean formatting; avoid HTML errors and symbol clutter.
- The local SOP (RD) prevails if stricter.

EDITORIAL RULES
- Tone: professional, clear, confident; adapted to buyer persona.
- Use the exact words from 'Léxico editorial' rows.
- Avoid exaggerated claims; favor precise, verifiable language.

FASCINATION STYLES
- Curiosity / Hidden Benefit
- Specificity / Proof
- Objection → Resolution
- Shortcut / Time-saver
- Use-case Spotlight
- Mini-mechanism
Each bullet MUST embody one fascination style (deterministic, based on attribute/variation + persona).
"""

# ================================
# BULLETS — SOP RD (STRICT)
# ================================
SOP_BULLETS_STRICT = r"""
SOP RD — BULLETS (MANDATORY; overrides any conflicting guideline)

FORMAT
- IDEA in UPPERCASE (Etiqueta of Variación or Atributo).
- ":" separator.
- Development = Contenido + compatible semantic clusters; Core tokens ONLY if required for fluency (minimal).
- No final period. Length = 150–180 characters (visible Unicode).

COUNT & MAPPING
- Always 5 bullets per scope (Parent and each Child variation).
- Map variation dimensions by unique Etiqueta among Variación rows (first-appearance order):
  · Bullet #1 = 1st dimension (Parent IDEA = ETIQUETA; Child IDEA = VARIATION VALUE).
  · Bullet #2 = 2nd dimension, if exists (mismo criterio).
  · Bullet #3 = 3rd dimension, if exists.
- Remaining positions up to 5 → top-priority ATTRIBUTES (Beneficio > Ventaja > Obstáculo).
- Never duplicate the same attribute across different bullets.

SEMANTICS & SOURCING
- Maximize compatible CLUSTER tokens without harming readability.
- ALL content must come from table rows (Variación/Atributo/SEO semántico/Léxico). No inventions.
- Buyer persona and Emotions inform prioritization/style; their text is never copied verbatim.

STYLE & POLICY
- English. Only the IDEA is all-caps; development in normal case.
- No promotions, competitors, testimonials, or claims not supported by attributes.
- SOP prevails wherever conflicts arise.
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
    *,
    # NUEVO: pares etiqueta/contenido para cumplir SOP (IDEA=Etiqueta; desarrollo=Contenido)
    attributes_kv: List[dict],
    variations_kv: List[dict],
) -> str:
    """
    BULLETS prompt (SOP RD strict + general briefs).
    Devuelve SOLO JSON con:
    {
      "bullets": {
        "parent": ["b1..b5"],
        "<var-slug>": ["b1..b5"]
      }
    }
    """
    return f"""{BULLETS_GENERAL_BRIEF}

{SOP_BULLETS_STRICT}

You are an Amazon listing copywriter executing a binding SOP. Use ONLY the inputs below (table projections). 
If something is not present here, do NOT include it.

AUTHORIZED INPUTS (structured):
- BRAND (Marca; may be empty): {head_phrases}
- SEO semantic tokens (Core + clusters): {core_tokens}
- ATTRIBUTES (Atributo; label=Etiqueta, value=Contenido):
  · flat values: {attributes}
  · kv pairs   : {attributes_kv}
- VARIATIONS (Variación; dimension=Etiqueta, value=Contenido):
  · flat values: {variations}
  · kv pairs   : {variations_kv}
- Prioritization cues (never copied; ranking only): beneficios={benefits}, emociones={emotions}
- Buyer persona (overview): {buyer_persona}
- Editorial lexicon (actual words to use): {lexico}

MANDATORY INSTRUCTIONS:
- Generate exactly 5 bullets per scope (Parent and every variation child).
- Determine variation DIMENSIONS by unique Etiqueta among Variación (first-appearance order).
- Reserve b#1..b#K for K dimensions:
  · Parent: IDEA = ETIQUETA (uppercase). Development = clusters compatibles + minimal core if needed.
  · Child : IDEA = VARIATION VALUE (uppercase). Development idem.
- Fill remaining slots up to 5 with top-priority ATTRIBUTES:
  · IDEA = attribute ETIQUETA (uppercase).
  · Development = attribute Contenido + compatible clusters; minimal core only if improves readability.
- Each bullet must instantiate a Fascination style (deterministic to the attribute/variation + persona).
- Length 150–180 characters; no final period; English; high readability; no invented tokens.
- Return ONLY JSON with key "bullets". No prose, markdown, or fences.

OUTPUT SHAPE (JSON ONLY):
{{
  "bullets": {{
    "parent": ["b1","b2","b3","b4","b5"],
    "<variation_slug_1>": ["b1","b2","b3","b4","b5"],
    "<variation_slug_2>": ["b1","b2","b3","b4","b5"]
  }}
}}
- Variation keys use slug of the variation VALUE (lowercase; strip punctuation; spaces→hyphens; collapse hyphens).
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
    raise NotImplementedError(
        "Description SOP is not integrated yet. This function is intentionally not implemented to avoid hidden fallbacks.")


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
    raise NotImplementedError(
        "Backend SOP is not integrated yet. This function is intentionally not implemented to avoid hidden fallbacks.")
