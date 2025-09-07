# listing/funcional_listing_copywrite.py
# Single-button generation pipeline: extracts inputs from the consolidated table,
# builds the prompt, calls OpenAI (cheap model), validates, and returns a dict.

import json
import os
from typing import Dict, List, Any

import pandas as pd

from listing.prompts_listing_copywrite import PROMPT_MASTER_JSON

# ─────────────────────────────────────────────────────────────────────────────
# Helpers to extract inputs from the unified table (Tipo/Contenido/Etiqueta/Fuente)
# ─────────────────────────────────────────────────────────────────────────────


def _norm(s: Any) -> str:
    return str(s or "").strip()


def _first(series: pd.Series) -> str:
    try:
        val = series.dropna().astype(str)
        return val.iloc[0].strip() if not val.empty else ""
    except Exception:
        return ""


def _unique(series: pd.Series) -> List[str]:
    try:
        vals = series.dropna().astype(str).str.strip()
        vals = [v for v in vals if v]
        # preserve order while dedup
        seen = set()
        out = []
        for v in vals:
            if v not in seen:
                seen.add(v)
                out.append(v)
        return out
    except Exception:
        return []


def _col_exists(df: pd.DataFrame, name: str) -> bool:
    return any(str(c).strip().lower() == name.lower() for c in df.columns)


def _tipo_equals(df: pd.DataFrame, tipo: str) -> pd.DataFrame:
    if not _col_exists(df, "Tipo"):
        return df.iloc[0:0]
    return df[df["Tipo"].astype(str).str.lower() == tipo.lower()]


def _tipo_contains(df: pd.DataFrame, needle: str) -> pd.DataFrame:
    if not _col_exists(df, "Tipo"):
        return df.iloc[0:0]
    return df[df["Tipo"].astype(str).str.contains(needle, case=False, na=False)]


def _etiqueta_contains(df: pd.DataFrame, needle: str) -> pd.DataFrame:
    if not _col_exists(df, "Etiqueta"):
        return df.iloc[0:0]
    return df[df["Etiqueta"].astype(str).str.contains(needle, case=False, na=False)]


def _contenido_list(df: pd.DataFrame) -> List[str]:
    if not _col_exists(df, "Contenido"):
        return []
    return _unique(df["Contenido"])


def extract_inputs_from_table(inputs_df: pd.DataFrame) -> Dict[str, Any]:
    df = inputs_df.copy()

    # Brand
    brand = _first(_tipo_equals(df, "Marca")["Contenido"]) if not _tipo_equals(
        df, "Marca").empty else ""

    # Variations (values only)
    df_var = df[df["Tipo"].astype(str).str.contains(
        r"variaci", case=False, na=False)]
    variations = _contenido_list(df_var)

    # Attributes (values only)
    df_attr = _tipo_equals(df, "Atributo")
    attributes = _contenido_list(df_attr)

    # Core tokens (robust against v3.9/v3.10)
    # v3.10 → Tipo = "SEO semántico", Etiqueta includes "Core"
    # legacy → Tipo may be "Token Semántico (Core)" or similar
    core_tokens = []
    df_core_a = _tipo_equals(df, "SEO semántico")
    if not df_core_a.empty:
        core_tokens = _contenido_list(_etiqueta_contains(df_core_a, "core"))
    if not core_tokens:
        df_core_b = _tipo_contains(df, "token semántico")
        core_tokens = _contenido_list(_etiqueta_contains(df_core_b, "core"))

    # Benefits (support both "Beneficio valorado", "Ventaja", legacy "Beneficio")
    benefits = []
    for t in ["Beneficio valorado", "Ventaja", "Beneficio"]:
        benefits.extend(_contenido_list(_tipo_equals(df, t)))
    # dedup preserving order
    seen = set()
    benefits_dedup = []
    for b in benefits:
        if b not in seen:
            seen.add(b)
            benefits_dedup.append(b)
    benefits = benefits_dedup

    # Emotions
    emotions = _contenido_list(_tipo_equals(df, "Emoción"))

    # Buyer persona
    buyer_persona = _first(_tipo_equals(df, "Buyer persona")[
                           "Contenido"]) if not _tipo_equals(df, "Buyer persona").empty else ""

    # Editorial lexicon (concatenate if multiple rows)
    lexico_rows = _tipo_equals(df, "Léxico editorial")
    lexico = " ".join(_contenido_list(lexico_rows))

    # Head phrases = brand + a few core tokens (seed headline cues). Never invent.
    head_phrases = []
    if brand:
        head_phrases.append(brand)
    head_phrases.extend(core_tokens[:8])  # cap a few

    return dict(
        brand=brand,
        variations=variations,
        attributes=attributes,
        core_tokens=core_tokens,
        benefits=benefits,
        emotions=emotions,
        buyer_persona=buyer_persona,
        lexico=lexico,
        head_phrases=head_phrases,
    )

# ─────────────────────────────────────────────────────────────────────────────
# OpenAI call (cheap model) – robust to both old/new SDKs
# ─────────────────────────────────────────────────────────────────────────────


def _call_openai_json(prompt: str, model: str = "gpt-4o-mini") -> Dict[str, Any]:
    # Ensure API key
    api_key = os.getenv("OPENAI_API_KEY") or ""
    if not api_key:
        # Streamlit secrets (optional)
        try:
            import streamlit as st  # type: ignore
            api_key = st.secrets.get("OPENAI_API_KEY", "")  # type: ignore
            if api_key:
                os.environ["OPENAI_API_KEY"] = api_key
        except Exception:
            pass
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY not found. Set it in env or st.secrets.")

    # Try new SDK first
    try:
        from openai import OpenAI  # type: ignore
        client = OpenAI()
        resp = client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            temperature=0.4,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that only returns valid JSON."},
                {"role": "user", "content": prompt},
            ],
        )
        text = resp.choices[0].message.content or "{}"
        return json.loads(text)
    except Exception:
        # Fallback to legacy SDK signature
        try:
            import openai  # type: ignore
            openai.api_key = os.getenv("OPENAI_API_KEY")
            resp = openai.ChatCompletion.create(
                model=model,
                temperature=0.4,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that only returns valid JSON."},
                    {"role": "user", "content": prompt},
                ],
            )
            text = resp["choices"][0]["message"]["content"] or "{}"
            return json.loads(text)
        except Exception as e2:
            raise RuntimeError(f"OpenAI call failed: {e2}")

# ─────────────────────────────────────────────────────────────────────────────
# Compliance checks (lightweight)
# ─────────────────────────────────────────────────────────────────────────────


def _bytes_wo_spaces(s: str) -> int:
    return len((s or "").replace(" ", "").encode("utf-8"))


def compliance_report(draft: Dict[str, Any]) -> Dict[str, Any]:
    issues = []

    # Titles
    for t in draft.get("titles", []) or []:
        desk = t.get("desktop", "")
        mob = t.get("mobile", "")
        if not (150 <= len(desk) <= 180):
            issues.append(
                f"Desktop title len out of range ({len(desk)}): {desk[:60]}…")
        if not (75 <= len(mob) <= 80):
            issues.append(
                f"Mobile title len out of range ({len(mob)}): {mob[:60]}…")

    # Bullets
    bullets = draft.get("bullets", []) or []
    if len(bullets) != 5:
        issues.append(f"Bullets count must be 5 (got {len(bullets)}).")
    for i, b in enumerate(bullets, 1):
        if not (130 <= len(b) <= 180):
            issues.append(f"Bullet {i} len out of range ({len(b)}).")
        if ":" not in b.split(" ", 1)[0]:
            issues.append(
                f"Bullet {i} must start with ALL-CAPS HEADER and colon.")
        if b.endswith("."):
            issues.append(f"Bullet {i} should not end with a period.")

    # Description
    desc = draft.get("description", "") or ""
    if not (1500 <= len(desc) <= 1800):
        issues.append(f"Description len out of range ({len(desc)}).")
    if "<br><br>" not in desc:
        issues.append("Description must include <br><br> paragraph breaks.")

    # Backend
    backend = draft.get("search_terms", "") or ""
    byt = _bytes_wo_spaces(backend)
    if not (243 <= byt <= 249):
        issues.append(f"Backend bytes (no spaces) out of range: {byt}.")

    return {"ok": len(issues) == 0, "issues": issues}

# ─────────────────────────────────────────────────────────────────────────────
# Main entry for the app
# ─────────────────────────────────────────────────────────────────────────────


def lafuncionqueejecuta_listing_copywrite(
    inputs_df: pd.DataFrame,
    model: str = "gpt-4o-mini",
) -> Dict[str, Any]:
    """
    Extracts inputs → builds prompt → calls OpenAI → returns JSON dict.
    No local fallbacks to fake content (to avoid confusion/cost surprises).
    """
    if not isinstance(inputs_df, pd.DataFrame) or inputs_df.empty:
        raise ValueError("inputs_df is empty.")

    inp = extract_inputs_from_table(inputs_df)

    prompt = PROMPT_MASTER_JSON(
        head_phrases=inp.get("head_phrases", []),
        core_tokens=inp.get("core_tokens", []),
        attributes=inp.get("attributes", []),
        variations=inp.get("variations", []),
        benefits=inp.get("benefits", []),
        emotions=inp.get("emotions", []),
        buyer_persona=inp.get("buyer_persona", ""),
        lexico=inp.get("lexico", ""),
        brand=inp.get("brand", ""),
    )

    draft = _call_openai_json(prompt, model=model)

    # Optional: minimal structural validation (fail fast if schema is broken)
    for key in ("titles", "bullets", "description", "search_terms"):
        if key not in draft:
            raise RuntimeError(f"Model did not return required key: {key}")

    return draft
