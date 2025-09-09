# listing/funcional_listing_copywrite.py
# v1.0 (contract-aligned) — Genera prompts por ETAPA (Title, Bullets, Description, Backend)
# y ejecuta 4 llamadas separadas al modelo. Cumple el Contrato:
# - Usa SOLO la tabla `inputs_para_listing` (inyectada desde app) -> no lee Excel crudo.
# - Se pega a PDFs (normativas + SOP) a través del dict `rules` (inyectado por la capa que parsea PDFs).
# - Devuelve JSON final ya sanitizado por `lafuncionqueejecuta_listing_sanitizer_en`.

from typing import Any, Dict, List, Optional
import os
import re
import json
import pandas as pd

from listing.prompts_listing_copywrite import (
    build_prompt_title,
    build_prompt_bullets,
    build_prompt_description,
    build_prompt_backend,
)
from listing.funcional_listing_sanitizer_en import lafuncionqueejecuta_listing_sanitizer_en

# -------------------------------------------------------------
# Helpers de extracción desde inputs_para_listing (DataFrame)
# -------------------------------------------------------------


def _take(df: pd.DataFrame, tipo: str) -> List[str]:
    if df is None or df.empty:
        return []
    if "Tipo" not in df.columns or "Contenido" not in df.columns:
        return []
    sub = df[df["Tipo"] == tipo]["Contenido"].dropna().astype(str).tolist()
    return [s.strip() for s in sub if str(s).strip()]


def _unique(seq: List[str]) -> List[str]:
    seen, out = set(), []
    for s in seq:
        k = re.sub(r"\s+", " ", str(s).strip().lower())
        if k and k not in seen:
            out.append(str(s).strip())
            seen.add(k)
    return out


def _collect_inputs(df: pd.DataFrame, cost_saver: bool = True) -> Dict[str, Any]:
    head_phrases = _unique(_take(df, "Keyword Frase"))
    core_tokens = _unique(_take(df, "Token Semántico"))
    attributes = _unique(_take(df, "Atributo"))
    variations = _unique(_take(df, "Variación"))
    benefits = _unique(_take(df, "Beneficio"))
    emotions = _unique(_take(df, "Emoción"))
    buyer_persona = " ".join(_take(df, "Buyer persona")[:1])
    lexico = " ".join(_take(df, "Léxico editorial")[:1])

    # Recortes para abaratar
    if cost_saver:
        head_phrases = head_phrases[:10]
        core_tokens = core_tokens[:40]
        attributes = attributes[:20]
        variations = variations[:20]
        benefits = benefits[:20]
        emotions = emotions[:10]

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

# -------------------------------------------------------------
# LLM call (economica) — 1 etapa = 1 llamada
# -------------------------------------------------------------


def _cheap_llm_call(system_prompt: str, user_prompt: str, model: Optional[str], max_tokens: Optional[int], temperature: Optional[float]) -> str:
    """Envuelve una llamada simple a OpenAI ChatCompletions; devuelve texto o ''. No rompe si falta API."""
    mdl = model or os.environ.get("OPENAI_MODEL_COPY", "gpt-4o-mini")
    mtok = int(max_tokens or os.environ.get("OPENAI_MAX_TOKENS_COPY", "1400"))
    temp = float(temperature or os.environ.get(
        "OPENAI_TEMPERATURE_COPY", "0.3"))
    try:
        from openai import OpenAI
        client = OpenAI()
        resp = client.chat.completions.create(
            model=mdl,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temp,
            max_tokens=mtok,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception:
        return ""


def _parse_json_field(txt: str, field: str, fallback):
    try:
        j = json.loads(txt)
        val = j.get(field)
        if val is None:
            return fallback
        return val
    except Exception:
        return fallback

# -------------------------------------------------------------
# Builders determinísticos de respaldo (si use_ai=False o JSON falló)
# -------------------------------------------------------------


def _fallback_title(inputs: Dict[str, Any]) -> str:
    brand = next((t for t in inputs.get("core_tokens", [])
                 if len(t.split()) <= 2), "")
    base = next(iter(inputs.get("head_phrases", [])), "")
    attr = next(iter(inputs.get("attributes", [])), "")
    var = next(iter(inputs.get("variations", [])), "")
    # Ensamble simple y seguro; sanitizer recorta a rango final
    parts = [p for p in [brand, base, attr, var] if p]
    s = " | ".join(parts)
    return re.sub(r"\s+", " ", s).strip()[:200]


def _fallback_bullets(inputs: Dict[str, Any]) -> List[str]:
    attrs = inputs.get("attributes", [])[:5]
    bens = inputs.get("benefits", [])[:5]
    out = []
    for i in range(5):
        a = attrs[i] if i < len(attrs) else (attrs[0] if attrs else "Feature")
        b = bens[i] if i < len(bens) else (bens[0] if bens else "Benefit")
        out.append(f"{a}: {b}")
    return out


def _fallback_description(inputs: Dict[str, Any]) -> str:
    base = " ".join(inputs.get("head_phrases", [])[:5])
    persona = inputs.get("buyer_persona", "")
    bens = "; ".join(inputs.get("benefits", [])[:8])
    attrs = "; ".join(inputs.get("attributes", [])[:8])
    return f"{base}. For {persona}. Benefits: {bens}. Attributes: {attrs}."


def _fallback_backend(inputs: Dict[str, Any]) -> str:
    # Junta tokens y variaciones en una lista simple separada por espacios (sin comas)
    toks = inputs.get("core_tokens", [])[:40] + \
        inputs.get("variations", [])[:20]
    toks = [re.sub(r"[,;]+", " ", t).strip() for t in toks if t.strip()]
    joined = " ".join(_unique(toks))
    # backend son bytes sin espacios contados; aquí solo devolvemos texto base
    return joined

# -------------------------------------------------------------
# API principal
# -------------------------------------------------------------


def lafuncionqueejecuta_listing_copywrite(
    inputs_df: pd.DataFrame,
    use_ai: bool = True,
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    cost_saver: bool = True,
    rules: Optional[Dict[str, Any]] = None,  # <= reglas parseadas desde PDFs
) -> Dict[str, Any]:
    """
    Genera Title, 5 Bullets, Description y Backend en 4 llamadas separadas.
    Cumple el contrato: SOLO `inputs_para_listing` + `rules`.
    """
    # 1) Proyección desde la tabla
    inputs = _collect_inputs(inputs_df, cost_saver=cost_saver)

    # 2) Prompts por etapa
    rules = rules or {}
    sys_prompt = "You are a senior Amazon listing copy editor that outputs ONLY JSON as specified."

    title, bullets, description, backend = "", [], "", ""

    if use_ai:
        # ---- TITLE ----
        p_title = build_prompt_title(inputs, rules)
        t_resp = _cheap_llm_call(
            sys_prompt, p_title, model, max_tokens, temperature)
        title = _parse_json_field(t_resp, "title", _fallback_title(inputs))

        # ---- BULLETS ----
        p_bul = build_prompt_bullets(inputs, rules)
        b_resp = _cheap_llm_call(
            sys_prompt, p_bul, model, max_tokens, temperature)
        bullets = _parse_json_field(
            b_resp, "bullets", _fallback_bullets(inputs))
        if not isinstance(bullets, list):
            bullets = _fallback_bullets(inputs)

        # ---- DESCRIPTION ----
        p_desc = build_prompt_description(inputs, rules)
        d_resp = _cheap_llm_call(
            sys_prompt, p_desc, model, max_tokens, temperature)
        description = _parse_json_field(
            d_resp, "description", _fallback_description(inputs))

        # ---- BACKEND ----
        p_back = build_prompt_backend(inputs, rules)
        s_resp = _cheap_llm_call(
            sys_prompt, p_back, model, max_tokens, temperature)
        backend = _parse_json_field(
            s_resp, "search_terms", _fallback_backend(inputs))
    else:
        # Sin IA: usa fallbacks determinísticos
        title = _fallback_title(inputs)
        bullets = _fallback_bullets(inputs)
        description = _fallback_description(inputs)
        backend = _fallback_backend(inputs)

    # 3) Sanitizer EN (aplica hard limits de longitudes/normativas)
    draft = {
        "title": title or "",
        "bullets": bullets or [],
        "description": description or "",
        "search_terms": backend or "",
    }
    return lafuncionqueejecuta_listing_sanitizer_en(draft)
