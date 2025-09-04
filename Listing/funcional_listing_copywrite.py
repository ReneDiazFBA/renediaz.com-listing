# listing/funcional_listing_copywrite.py
# Main entry: lafuncionqueejecuta_listing_copywrite(inputs_df, use_ai=True) -> dict
# Sin Streamlit. Python 3.9 compatible.

from typing import Any, Dict, List, Optional, Tuple, Union
import os
import re
import json
import hashlib
import pandas as pd

from listing.prompts_listing_copywrite import prompt_master_json
from listing.funcional_listing_sanitizer_en import lafuncionqueejecuta_listing_sanitizer_en

# ----------------- config helpers -----------------


def _flag_true(val: Union[str, bool, None]) -> bool:
    if isinstance(val, bool):
        return val
    return str(val or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _maybe_set_openai_key():
    if not os.environ.get("OPENAI_API_KEY"):
        return  # si no hay clave, simplemente no se usa IA


def _hash_inputs(*parts) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(str(p).encode("utf-8", errors="ignore"))
    return h.hexdigest()

# ----------------- read helpers -----------------


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
    core_tokens = _unique([t for t in _take(df, "Token Semántico")][:20])
    attributes = _unique(_take(df, "Atributo"))
    variations = _unique(_take(df, "Variación"))
    benefits = _unique(_take(df, "Beneficio"))
    emotions = _unique(_take(df, "Emoción"))
    buyer_persona = " ".join(_take(df, "Buyer persona")[:1])
    lexico = " ".join(_take(df, "Léxico editorial")[:1])

    def trunc_list(xs: List[str], n: int, each_chars: int) -> List[str]:
        out = []
        for x in xs[:n]:
            out.append(x[:each_chars])
        return out

    if cost_saver:
        head_phrases = trunc_list(head_phrases, 6, 60)
        core_tokens = trunc_list(core_tokens, 20, 32)
        attributes = trunc_list(attributes, 8, 40)
        variations = trunc_list(variations, 12, 40)
        benefits = trunc_list(benefits, 10, 120)
        emotions = trunc_list(emotions, 6, 24)
        buyer_persona = buyer_persona[:200]
        lexico = lexico[:200]

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
    _maybe_set_openai_key()
    if not os.environ.get("OPENAI_API_KEY"):
        return ""  # sin API key => no IA

    cache_key = _hash_inputs(
        "copywriter", model, max_tokens, temperature, system_prompt, user_prompt)
    # cache mínimo en archivo tmp opcional (omitir para simplicidad) -> devolvemos directo

    try:
        from openai import OpenAI
        client = OpenAI()
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception:
        return ""

# ----------------- deterministic fallback -----------------


def _limit_bytes(text: str, max_bytes: int) -> str:
    b = (text or "").encode("utf-8")
    if len(b) <= max_bytes:
        return text or ""
    cut = b[:max_bytes]
    while cut and (cut[-1] & 0xC0) == 0x80:
        cut = cut[:-1]
    return cut.decode("utf-8", errors="ignore")


def _build_title_fallback(head_phrases: List[str], attributes: List[str], benefits: List[str]) -> str:
    blocks = []
    if head_phrases:
        blocks.append(head_phrases[0])
    if attributes:
        blocks.append(", ".join(attributes[:2]))
    if len(head_phrases) > 1:
        blocks.append(head_phrases[1])
    if benefits:
        blocks.append(benefits[0][:60])
    raw = " | ".join(blocks)
    raw = re.sub(r"\s+", " ", raw).strip()
    return _limit_bytes(raw, 200)


def _build_bullets_fallback(attributes: List[str], benefits: List[str], emotions: List[str]) -> List[str]:
    out = []
    if attributes:
        out.append(f"{attributes[0]}.")
    for b in benefits[:2]:
        bb = f"{b.rstrip('.')}. "
        out.append(bb.strip())
    if emotions:
        out.append(f"Inspired by {emotions[0].lower()} for better focus.")
    while len(out) < 5:
        out.append("Thoughtful design focused on real-world use.")
    # **< 150 characters**
    return [re.sub(r"\s+", " ", b).strip()[:150].rstrip() + ("" if re.search(r"[.!?]$", b) else ".") for b in out[:5]]


def _build_description_fallback(breves: List[str], benefits: List[str], buyer: str, lexico: str) -> str:
    parts = []
    if breves:
        parts.append(breves[0])
    if benefits:
        parts.append("Key benefits: " +
                     "; ".join([b.rstrip('.') for b in benefits[:5]]) + ".")
    if buyer:
        parts.append(f"Ideal for: {buyer}.")
    if lexico:
        parts.append(f"Style: {lexico}")
    raw = " ".join(parts)
    raw = re.sub(r"\s+", " ", raw).strip()
    return _limit_bytes(raw, 2000)


def _build_backend_fallback(head_phrases: List[str], core_tokens: List[str], title: str, bullets: List[str], description: str) -> str:
    used = set(re.findall(r"[a-z0-9]+", (title + " " +
               " ".join(bullets) + " " + description).lower()))
    words = []
    for p in head_phrases + core_tokens:
        for w in re.findall(r"[a-z0-9]+", p.lower()):
            if w not in used and w not in words:
                words.append(w)
    return _limit_bytes(" ".join(words), 249)

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
    Construye listing EN (title, bullets, description, backend) desde inputs_df (Tipo/Contenido).
    - Si hay OPENAI_API_KEY y use_ai=True -> usa IA barata (gpt-4o-mini por defecto).
    - Si falla o no hay clave -> fallback determinístico.
    - Aplica sanitizer EN (bullets < 150 chars, backend <= 249 bytes).

    Retorna: {"title": str, "bullets": List[str], "description": str, "search_terms": str}
    """
    payload = _collect_inputs(inputs_df, cost_saver=cost_saver)

    # --- IA (opcional) ---
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
            "OPENAI_MAX_TOKENS_COPY", "700"))
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

    # --- Fallback determinístico si falta algo ---
    if not title or not bullets or not description or not backend:
        breves = _take(inputs_df, "Descripción breve")
        title = _build_title_fallback(
            payload["head_phrases"] or payload["core_tokens"], payload["attributes"], payload["benefits"])
        bullets = _build_bullets_fallback(
            payload["attributes"], payload["benefits"], payload["emotions"])
        description = _build_description_fallback(
            breves, payload["benefits"], payload["buyer_persona"], payload["lexico"])
        backend = _build_backend_fallback(
            payload["head_phrases"], payload["core_tokens"], title, bullets, description)

    # --- Sanitizer Amazon EN ---
    draft = {
        "title": title,
        "bullets": bullets,
        "description": description,
        "search_terms": backend,
    }
    return lafuncionqueejecuta_listing_sanitizer_en(draft)
