# listing/funcional_listing_copywrite.py
# Main entry: lafuncionqueejecuta_listing_copywrite(inputs_df, use_ai=True) -> dict
# Generates EN copy in RD ranges. Backend 243–249 BYTES without spaces, with typos/other languages, no duplication with surface copy.
# Python 3.9 compatible.

from __future__ import annotations
from listing.funcional_listing_datos import get_insumos_copywrite
from typing import Dict, List
from typing import Any, Dict, List, Optional, Tuple, Union
import os
import re
import json
import hashlib
import random
import pandas as pd

from listing.prompts_listing_copywrite import prompt_master_json
from listing.funcional_listing_sanitizer_en import lafuncionqueejecuta_listing_sanitizer_en

# ----------------- helpers -----------------


def _flag_true(val: Union[str, bool, None]) -> bool:
    if isinstance(val, bool):
        return val
    return str(val or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _hash_inputs(*parts) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(str(p).encode("utf-8", errors="ignore"))
    return h.hexdigest()


def _limit_chars(text: str, max_chars: int) -> str:
    t = (text or "").strip()
    return t[:max_chars].rstrip()


def _take(df: pd.DataFrame, tipo: str) -> List[str]:
    if df is None or df.empty:
        return []
    sub = df[df["Tipo"] == tipo]["Contenido"].dropna().astype(str).tolist()
    return [s.strip() for s in sub if s.strip()]


def _unique(seq: List[str]) -> List[str]:
    seen, out = set(), []
    for s in seq:
        key = re.sub(r"\s+", " ", s.strip().lower())
        if key and key not in seen:
            out.append(s.strip())
            seen.add(key)
    return out


def _collect_inputs(df: pd.DataFrame, cost_saver: bool = True) -> Dict[str, Any]:
    head_phrases = _unique(_take(df, "Keyword Frase"))
    core_tokens = _unique([t for t in _take(df, "Token Semántico")][:40])
    attributes = _unique(_take(df, "Atributo"))
    variations = _unique(_take(df, "Variación"))
    benefits = _unique(_take(df, "Beneficio"))
    emotions = _unique(_take(df, "Emoción"))
    buyer_persona = " ".join(_take(df, "Buyer persona")[:1])
    lexico = " ".join(_take(df, "Léxico editorial")[:1])

    def trunc(xs: List[str], n: int, each: int) -> List[str]:
        return [x[:each] for x in xs[:n]]

    if cost_saver:
        head_phrases = trunc(head_phrases, 8, 80)
        core_tokens = trunc(core_tokens, 30, 32)
        attributes = trunc(attributes, 10, 50)
        variations = trunc(variations, 16, 50)
        benefits = trunc(benefits, 14, 160)
        emotions = trunc(emotions, 8, 24)
        buyer_persona = buyer_persona[:240]
        lexico = lexico[:240]

    return {
        "head_phrases": head_phrases,
        "core_tokens": core_tokens,
        "attributes": attributes,
        "variations": variations,
        "benefits": benefits,
        "emotions": emotions,
        "buyer_persona": buyer_persona,
        "lexico": lexico,
    }

# ----------------- AI call (cheap) -----------------


def _cheap_llm_call(system_prompt: str, user_prompt: str, model: str, max_tokens: int, temperature: float) -> str:
    if not os.environ.get("OPENAI_API_KEY"):
        return ""
    try:
        from openai import OpenAI
        client = OpenAI()
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system_prompt},
                      {"role": "user", "content": user_prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception:
        return ""

# ----------------- deterministic fallback -----------------


def _build_title_fallback(head: List[str], attrs: List[str], bens: List[str], variations: List[str]) -> str:
    # Detect pack/measure hints
    pack_hint = ""
    for v in variations:
        if re.search(r"\b\d{1,4}\s*(?:pack|pcs|pieces|labels|count|ct)\b", v, flags=re.I):
            pack_hint = v
            break
        if re.search(r"\b\d{1,4}\s*(?:x|×)\s*\d{1,4}\s*(?:cm|mm|in)\b", v, flags=re.I):
            pack_hint = v
            break
    blocks = []
    if head:
        blocks.append(head[0])
    if attrs:
        blocks.append(", ".join(attrs[:2]))
    if pack_hint:
        blocks.append(pack_hint)
    if len(head) > 1:
        blocks.append(head[1])
    if bens:
        blocks.append(bens[0][:80])
    raw = " – ".join([b for b in blocks if b])
    raw = re.sub(r"\s+", " ", raw).strip()
    # Aim 150–200, enforce 200 max
    return _limit_chars(raw, 200)


def _build_bullets_fallback(attrs: List[str], bens: List[str], emos: List[str], variations: List[str]) -> List[str]:
    def pick(pats: List[str], pool: List[str]) -> str:
        for pat in pats:
            for x in pool:
                if re.search(pat, x, flags=re.I):
                    return x
        return ""
    material = pick([r"plastic|cardboard|paper|poly|vinyl"], attrs) or (
        attrs[0] if attrs else "Durable build")
    size = pick(
        [r"\b(cm|mm|in)\b|\bsize|dimension|width|height|length|desk"], variations + attrs)
    care = pick(
        [r"clean|wipe|wash|maintenance|reuse|reusable|durable"], bens + attrs)
    context = pick(
        [r"classroom|school|test|exam|assessment|office|home"], bens + variations + attrs)
    pack = pick([r"\b(pack|pcs|pieces|labels|count|ct)\b"], variations)
    b1 = bens[0] if bens else "Provides privacy for focused work"
    b2 = bens[1] if len(
        bens) > 1 else "Helps reduce distractions in busy settings"
    b3 = bens[2] if len(bens) > 2 else "Easy to deploy, store and reuse"
    bullets = []
    bullets.append(f"{material} — {b1}")
    bullets.append(
        f"Fit & size: {size} — ideal for desks and testing areas" if size else "Sized for classroom desks — visibility preserved while adding privacy")
    bullets.append(
        f"Low maintenance: {care.rstrip('.')} — easy to wipe and reuse" if care else "Easy-clean surface — reusable through daily classroom routines")
    bullets.append(
        f"Purpose-built for {context.lower()} — improves focus and organization" if context else "Purpose-built for classroom tests — promotes focus and order")
    bullets.append(
        f"Lightweight and stackable — convenient {pack} for quick distribution" if pack else "Lightweight, stackable design — quick to distribute and store")
    # Normalize to 180–240 (enforce 240 max)
    out = []
    for b in bullets[:5]:
        bb = re.sub(r"\s+", " ", b).strip()
        if len(bb) < 180:
            # pad with small rationale if too short (without breaking policy)
            bb = (
                bb + " Designed to support consistent classroom routines and reliable performance day after day.")[:240]
        elif len(bb) > 240:
            bb = bb[:240].rstrip()
        if not re.search(r"[.!?]$", bb):
            bb += "."
        out.append(bb)
    return out[:5]


def _expand_to_min_chars(text: str, min_chars: int, pools: List[List[str]]) -> str:
    t = text.strip()
    i = 0
    while len(t) < min_chars and i < 2000:
        for pool in pools:
            for item in pool:
                frag = re.sub(r"\s+", " ", item).strip().rstrip(".")
                if not frag:
                    continue
                candidate = (t + " " + frag + ".").strip()
                if len(candidate) > min_chars + 50:
                    t = candidate[:min_chars + 50].rstrip()
                    return t
                t = candidate
        i += 1
        if not pools:
            break
    return t


def _build_description_fallback(breves: List[str], bens: List[str], buyer: str, lexico: str, attrs: List[str], variations: List[str]) -> str:
    parts = []
    if breves:
        parts.append(breves[0])
    if bens:
        parts.append("Key benefits: " +
                     "; ".join([b.rstrip('.') for b in bens[:8]]) + ".")
    if buyer:
        parts.append(f"Ideal for: {buyer}.")
    if lexico:
        parts.append(f"Style: {lexico}")
    if attrs:
        parts.append("Notable attributes: " + ", ".join(attrs[:6]) + ".")
    if variations:
        parts.append("Options/measurements: " +
                     ", ".join(variations[:8]) + ".")
    raw = " ".join(parts)
    raw = re.sub(r"\s+", " ", raw).strip()
    # target 1600–2000
    raw = _expand_to_min_chars(raw, 1600, [bens, attrs, variations])
    return raw[:2000].rstrip()

# ----------------- backend builder (no spaces count) -----------------


def _no_space_bytes_len(s: str) -> int:
    return len((s or "").replace(" ", "").encode("utf-8"))


def _word_base(w: str) -> str:
    # crude singular/plural normalization
    w = w.lower()
    if re.match(r".*ies$", w):
        return re.sub(r"ies$", "y", w)
    if re.match(r".*ses$", w):
        return re.sub(r"es$", "", w)
    if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
        return w[:-1]
    return w


def _gen_typos(w: str) -> List[str]:
    # simple typos: drop a vowel; swap adjacent
    out = set()
    if len(w) >= 5:
        for i, ch in enumerate(w):
            if ch in "aeiou" and len(out) < 2:
                out.add(w[:i] + w[i+1:])
        for i in range(len(w)-1):
            if len(out) >= 3:
                break
            out.add(w[:i] + w[i+1] + w[i] + w[i+2:])
    return list(out)


def _phrase_words(p: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", p.lower())


def _pack_backend_terms(candidates: List[str], used_surface: str, min_bytes: int = 243, max_bytes: int = 249) -> str:
    # dedupe vs surface & among candidates; enforce singular/plural one only
    used_surface_words = set(_phrase_words(used_surface))
    seen_bases = set()
    acc_tokens: List[str] = []

    def can_add(token: str) -> bool:
        words = _phrase_words(token)
        if not words:
            return False
        # skip if all words already seen on surface
        if all(w in used_surface_words for w in words):
            return False
        # singular/plural control
        for w in words:
            base = _word_base(w)
            if base in seen_bases:
                return False
        return True

    def mark_added(token: str):
        for w in _phrase_words(token):
            seen_bases.add(_word_base(w))

    # Greedy pack to reach min_bytes..max_bytes counting without spaces
    for tok in candidates:
        if not can_add(tok):
            continue
        trial = (" ".join(acc_tokens + [tok])).strip()
        if _no_space_bytes_len(trial) <= max_bytes:
            acc_tokens.append(tok)
            mark_added(tok)
        # early finish if we are within range
        if _no_space_bytes_len(" ".join(acc_tokens)) >= min_bytes:
            break

    # if still below min, try to add single-words from phrases as fillers
    if _no_space_bytes_len(" ".join(acc_tokens)) < min_bytes:
        extra = []
        for tok in candidates:
            for w in _phrase_words(tok):
                if w not in used_surface_words and _word_base(w) not in seen_bases:
                    extra.append(w)
        for w in extra:
            trial = (" ".join(acc_tokens + [w])).strip()
            if _no_space_bytes_len(trial) <= max_bytes:
                acc_tokens.append(w)
                seen_bases.add(_word_base(w))
            if _no_space_bytes_len(" ".join(acc_tokens)) >= min_bytes:
                break

    return " ".join(acc_tokens).strip()


def _build_backend(
    head_phrases: List[str], core_tokens: List[str], attrs: List[str], variations: List[str],
    title: str, bullets: List[str], description: str
) -> str:
    surface = " ".join([title] + bullets + [description])

    # Start from long-tail phrases not in surface, then lemmas, then attributes/variations
    candidates: List[str] = []
    candidates.extend([p for p in head_phrases if p])
    candidates.extend([t for t in core_tokens if t])
    candidates.extend([a for a in attrs if a])
    candidates.extend([v for v in variations if v])

    # Add typos (only for single words; safe subset)
    typo_pool = []
    for p in candidates:
        words = _phrase_words(p)
        if len(words) == 1:
            w = words[0]
            typo_pool.extend(_gen_typos(w))
    candidates.extend(typo_pool)

    # Add “other languages” terms present in inputs (non-ascii / accent words will already be in candidates)
    # No extra generation here to avoid hallucinations.

    # Pack to 243–249 bytes (spaces NOT counted)
    backend = _pack_backend_terms(
        candidates, used_surface=surface, min_bytes=243, max_bytes=249)
    return backend

# ----------------- PUBLIC ENTRY -----------------


def lafuncionqueejecuta_listing_copywrite(
    inputs_df: pd.DataFrame,
    use_ai: bool = True,
    model: str = None,
    max_tokens: int = None,
    temperature: float = None,
    cost_saver: bool = True,
) -> Dict[str, Any]:
    """
    Builds EN listing in RD ranges:
      - Title: 150–200 chars
      - Bullets: 5 x (180–240 chars)
      - Description: 1600–2000 chars
      - Backend: 243–249 BYTES without counting spaces (no duplication with surface; may include typos/other languages; singular OR plural)
    """
    payload = _collect_inputs(inputs_df, cost_saver=cost_saver)

    # ---- IA (opcional; apunta a rangos) ----
    title, bullets, description, backend = "", [], "", ""
    if use_ai and os.environ.get("OPENAI_API_KEY"):
        system_prompt = "You are a precise Amazon listing copywriter. Always return valid JSON only."
        user_prompt = prompt_master_json(
            head_phrases=payload["head_phrases"],
            core_tokens=payload["core_tokens"],
            attributes=payload["attributes"],
            variations=payload["variations"],
            benefits=payload["benefits"],
            emotions=payload["emotions"],
            buyer_persona=payload["buyer_persona"],
            lexico=payload["lexico"],
        )
        mdl = model or os.environ.get("OPENAI_MODEL_COPY", "gpt-4o-mini")
        mtok = int(max_tokens or os.environ.get(
            "OPENAI_MAX_TOKENS_COPY", "1400"))
        temp = float(temperature or os.environ.get(
            "OPENAI_TEMPERATURE_COPY", "0.3"))
        text = _cheap_llm_call(system_prompt, user_prompt, mdl, mtok, temp)
        if text:
            try:
                j = json.loads(text)
                title = j.get("title", "") or ""
                bullets = j.get("bullets", []) or []
                description = j.get("description", "") or ""
                backend = j.get("search_terms", "") or ""
            except Exception:
                pass

    # ---- Fallback determinístico para asegurar rangos ----
    if not title:
        title = _build_title_fallback(
            payload["head_phrases"] or payload["core_tokens"],
            payload["attributes"],
            payload["benefits"],
            variations=payload["variations"],
        )
    if not bullets or any(len(b) < 180 for b in bullets):
        bullets = _build_bullets_fallback(
            payload["attributes"], payload["benefits"], payload["emotions"], variations=payload["variations"]
        )
    if not description or len(description) < 1600:
        breves = _take(inputs_df, "Descripción breve")
        description = _build_description_fallback(
            breves, payload["benefits"], payload["buyer_persona"], payload["lexico"],
            attrs=payload["attributes"], variations=payload["variations"]
        )
    if not backend:
        backend = _build_backend(
            payload["head_phrases"], payload["core_tokens"], payload["attributes"], payload["variations"],
            title, bullets, description
        )

    # ---- Sanitizer Amazon EN (limpia y aplica máximos) ----
    draft = {
        "title": title,
        "bullets": bullets,
        "description": description,
        "search_terms": backend,
    }
    return lafuncionqueejecuta_listing_sanitizer_en(draft)
# listing/funcional_listing_copywrite.py
# Orquesta la generación del copy: llama a funcional_listing_datos
# para extraer insumos desde inputs_para_listing y construye el prompt.
# Si hay OPENAI_API_KEY, usa IA; si no, usa un fallback local.


# ─────────────────────────────────────────────────────────────
# Fallback local (barato) por si no hay API: produce un JSON válido
# ─────────────────────────────────────────────────────────────
def _fallback_local_draft(ins: Dict) -> Dict:
    brand = (ins.get("brand") or "").strip()
    attrs = ins.get("attributes", [])[:3]
    vars_ = ins.get("variations", [])[:1]
    cores = ins.get("core_tokens", [])[:3]
    bens = ins.get("benefits", [])[:5]
    persona = ins.get("buyer_persona", "")
    desc = ins.get("description_short", "")

    # Title heurístico (≈150–180 chars cuando hay material)
    what = " ".join(cores) if cores else desc[:60]
    parts = []
    if brand:
        parts.append(brand)
    if what:
        parts.append(what)
    if attrs:
        parts.append(", ".join(attrs))
    if vars_:
        parts.append(vars_[0])
    title = " - ".join([parts[0], " - ".join(parts[1:])]
                       ) if len(parts) > 1 else (parts[0] if parts else "")

    # Bullets sencillos (5)
    def _cap(s: str) -> str:
        return s.upper().replace(":", "").strip()

    bullets: List[str] = []
    if bens:
        for b in bens[:5]:
            bullets.append(f"{_cap('benefit')}: {b}")
    while len(bullets) < 5:
        bullets.append(
            "FEATURE: Detail about a useful attribute and the benefit in a clear, compliant sentence.")

    # Description breve (no 1600–2000, solo para fallback)
    description = desc or "Concise product summary. Explain what it is, who it is for, and why it helps."

    # Backend básico (no garantizamos bytes sin espacios, solo placeholder)
    backend = " ".join(cores[:8] + attrs[:8])

    return {
        "title": title[:200],
        "bullets": bullets[:5],
        "description": description,
        "search_terms": backend,
    }


# ─────────────────────────────────────────────────────────────
# IA: genera borrador con modelo económico si hay API
# ─────────────────────────────────────────────────────────────
def _ai_generate_draft(ins: Dict, cost_saver: bool = True) -> Dict:
    # Preparar inputs para el prompt
    head_phrases = ins.get("head_phrases", [])
    core_tokens = ins.get("core_tokens", [])
    attributes = ins.get("attributes", [])
    variations = ins.get("variations", [])
    benefits = ins.get("benefits", [])
    emotions = ins.get("emotions", [])
    buyer_persona = ins.get("buyer_persona", "")
    lexico = ins.get("lexico", "")

    # Recortes para ahorrar costo
    if cost_saver:
        head_phrases = head_phrases[:8]
        core_tokens = core_tokens[:30]
        attributes = attributes[:12]
        variations = variations[:12]
        benefits = benefits[:12]
        emotions = emotions[:12]

    prompt = prompt_master_json(
        head_phrases=head_phrases,
        core_tokens=core_tokens,
        attributes=attributes,
        variations=variations,
        benefits=benefits,
        emotions=emotions,
        buyer_persona=buyer_persona,
        lexico=lexico,
    )

    # Si no hay API key, usar fallback
    api_key = os.getenv("OPENAI_API_KEY", "") or ""
    if not api_key:
        return _fallback_local_draft(ins)

    # Cliente OpenAI (v. nueva)
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            messages=[
                {"role": "system", "content": "You are an expert Amazon listing copywriter. Return ONLY valid JSON."},
                {"role": "user", "content": prompt},
            ],
        )
        txt = resp.choices[0].message.content.strip()
        # Intenta parsear JSON
        draft = json.loads(txt)
        # Validación mínima
        for k in ("title", "bullets", "description", "search_terms"):
            draft.setdefault(k, "" if k != "bullets" else [])
        return draft
    except Exception:
        # Ante cualquier error de red/formato, devolvemos fallback local
        return _fallback_local_draft(ins)


# ─────────────────────────────────────────────────────────────
# ENTRYPOINT público que usa la App
# ─────────────────────────────────────────────────────────────
def lafuncionqueejecuta_listing_copywrite(
    inputs_df: pd.DataFrame,
    use_ai: bool = True,
    cost_saver: bool = True,
) -> Dict:
    """
    - Lee insumos desde el DF maestro (inputs_para_listing) vía funcional_listing_datos.
    - Si use_ai y hay OPENAI_API_KEY → IA.
    - Si no → fallback local.
    """
    if not isinstance(inputs_df, pd.DataFrame) or inputs_df.empty:
        return {"title": "", "bullets": [], "description": "", "search_terms": ""}

    ins = get_insumos_copywrite(inputs_df)

    if use_ai:
        return _ai_generate_draft(ins, cost_saver=cost_saver)
    else:
        return _fallback_local_draft(ins)
