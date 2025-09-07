# listing/funcional_listing_copywrite.py
# Build inputs from the unified table, call AI once, validate compliance.

import os
import json
import re
from typing import Dict, List, Any

import pandas as pd

from listing.prompts_listing_copywrite import PROMPT_MASTER_JSON

# ─────────────────────────────
# Utilities
# ─────────────────────────────


def _no_space_bytes_len(s: str) -> int:
    return len((s or "").replace(" ", "").encode("utf-8"))


def _clean_list(xs: List[Any]) -> List[str]:
    out = []
    for x in xs or []:
        if x is None:
            continue
        s = str(x).strip()
        if s:
            out.append(s)
    return out


def _unique_keep_order(xs: List[str]) -> List[str]:
    seen = set()
    out = []
    for x in xs:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def _lower_ascii(s: str) -> str:
    try:
        return s.lower()
    except Exception:
        return s

# ─────────────────────────────
# 1) Build inputs from unified DF (Tipo, Contenido, Etiqueta, Fuente)
# ─────────────────────────────


def build_inputs_from_df(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Extracts the minimal, table-driven projections we need for copywriting.
    - brand: first row Tipo="Marca"
    - core_tokens: Tipo="SEO semántico" & Etiqueta contains "Core"
    - attributes: Tipo="Atributo" → use Contenido (value only)
    - variations: Tipo="Variación" → Contenido
    - benefits: Tipo in {"Beneficio", "Beneficio valorado", "Ventaja"}
    - emotions: Tipo="Emoción" → Contenido
    - buyer_persona: Tipo="Buyer persona" (first)
    - lexico: Tipo="Léxico editorial" (first, raw string)
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        return {
            "brand": "",
            "core_tokens": [],
            "attributes": [],
            "variations": [],
            "benefits": [],
            "emotions": [],
            "buyer_persona": "",
            "lexico": "",
        }

    def tipo_is(df, name: str) -> pd.Series:
        return df["Tipo"].astype(str).str.strip().str.lower().eq(name.lower())

    brand = ""
    _brand_rows = df[tipo_is(df, "marca")
                     ] if "Tipo" in df.columns else pd.DataFrame()
    if not _brand_rows.empty:
        brand = str(_brand_rows.iloc[0]["Contenido"]).strip()

    core_tokens = []
    if {"Tipo", "Etiqueta", "Contenido"}.issubset(df.columns):
        core_mask = (df["Tipo"].astype(str).str.lower().str.strip() == "seo semántico") | \
                    (df["Tipo"].astype(str).str.lower(
                    ).str.strip() == "seo semantico")
        core_mask = core_mask & df["Etiqueta"].astype(
            str).str.contains(r"\bcore\b", case=False, na=False)
        core_tokens = _clean_list(
            df.loc[core_mask, "Contenido"].astype(str).tolist())

    attributes = []
    if "Tipo" in df.columns and "Contenido" in df.columns:
        attr_mask = df["Tipo"].astype(
            str).str.lower().str.strip().eq("atributo")
        attributes = _clean_list(
            df.loc[attr_mask, "Contenido"].astype(str).tolist())

    variations = []
    if "Tipo" in df.columns and "Contenido" in df.columns:
        var_mask = df["Tipo"].astype(str).str.lower().str.strip().eq("variación") | \
            df["Tipo"].astype(str).str.lower().str.strip().eq("variacion")
        variations = _clean_list(
            df.loc[var_mask, "Contenido"].astype(str).tolist())

    benefits = []
    if "Tipo" in df.columns and "Contenido" in df.columns:
        ben_mask = df["Tipo"].astype(str).str.lower().str.strip().isin(
            ["beneficio", "beneficio valorado", "ventaja"]
        )
        benefits = _clean_list(
            df.loc[ben_mask, "Contenido"].astype(str).tolist())

    emotions = []
    if "Tipo" in df.columns and "Contenido" in df.columns:
        emo_mask = df["Tipo"].astype(str).str.lower().str.strip().eq("emoción") | \
            df["Tipo"].astype(str).str.lower().str.strip().eq("emocion")
        emotions = _clean_list(
            df.loc[emo_mask, "Contenido"].astype(str).tolist())

    buyer_persona = ""
    bp_rows = df[df["Tipo"].astype(str).str.lower().str.strip().eq(
        "buyer persona")] if "Tipo" in df.columns else pd.DataFrame()
    if not bp_rows.empty:
        buyer_persona = str(bp_rows.iloc[0]["Contenido"]).strip()

    lexico = ""
    lex_rows = df[df["Tipo"].astype(str).str.lower().str.strip().eq(
        "léxico editorial")] if "Tipo" in df.columns else pd.DataFrame()
    if lex_rows.empty and "Tipo" in df.columns:
        lex_rows = df[df["Tipo"].astype(
            str).str.lower().str.strip().eq("lexico editorial")]
    if not lex_rows.empty:
        lexico = str(lex_rows.iloc[0]["Contenido"]).strip()

    # Deduplicate while keeping order
    core_tokens = _unique_keep_order(core_tokens)
    attributes = _unique_keep_order(attributes)
    variations = _unique_keep_order(variations)
    benefits = _unique_keep_order(benefits)
    emotions = _unique_keep_order(emotions)

    return {
        "brand": brand,
        "core_tokens": core_tokens,
        "attributes": attributes,
        "variations": variations,
        "benefits": benefits,
        "emotions": emotions,
        "buyer_persona": buyer_persona,
        "lexico": lexico,
    }

# ─────────────────────────────
# 2) Call AI once (gpt-4o-mini). Return JSON.
# ─────────────────────────────


def generate_listing_json(inputs: Dict[str, Any], model: str = "gpt-4o-mini") -> Dict[str, Any]:
    """
    Single-shot generation: titles (per variation, desktop/mobile), 5 bullets, description, backend.
    Requires OPENAI_API_KEY in environment/st.secrets. No fallback text here by design.
    """
    prompt = PROMPT_MASTER_JSON(
        brand=inputs.get("brand", ""),
        core_tokens=inputs.get("core_tokens", []),
        attributes=inputs.get("attributes", []),
        variations=inputs.get("variations", []),
        benefits=inputs.get("benefits", []),
        emotions=inputs.get("emotions", []),
        buyer_persona=inputs.get("buyer_persona", ""),
        lexico=inputs.get("lexico", ""),
    )

    # Import lazily so environments without openai don't fail on import.
    try:
        from openai import OpenAI
    except Exception as e:
        raise RuntimeError(
            "OpenAI SDK not available. Install 'openai' >= 1.0.0") from e

    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        # Streamlit secrets (optional)
        try:
            import streamlit as st
            api_key = st.secrets.get("OPENAI_API_KEY", "")
        except Exception:
            pass
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not found.")

    client = OpenAI(api_key=api_key)

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a precise Amazon listing copywriter. Always return strict JSON."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )

    text = resp.choices[0].message.content
    try:
        data = json.loads(text)
    except Exception as e:
        raise RuntimeError(
            f"Model did not return valid JSON. Raw: {text[:400]}") from e

    # Minimal shape guard
    for k in ("titles", "bullets", "description", "search_terms"):
        if k not in data:
            raise RuntimeError(f"Missing '{k}' in model output.")
    return data

# ─────────────────────────────
# 3) Compliance checks (hard constraints)
# ─────────────────────────────


def compliance_report(draft: Dict[str, Any]) -> Dict[str, Any]:
    """
    Returns pass/fail + notes for: titles length, bullets count/length/format, description length, backend bytes/format.
    """
    report = {"ok": True, "issues": []}

    # Titles
    titles = draft.get("titles", [])
    if not isinstance(titles, list) or not titles:
        report["ok"] = False
        report["issues"].append("No titles array returned.")
    else:
        for i, t in enumerate(titles, 1):
            desktop = (t or {}).get("desktop", "")
            mobile = (t or {}).get("mobile", "")
            if not (150 <= len(desktop) <= 180):
                report["ok"] = False
                report["issues"].append(
                    f"Title #{i} desktop length={len(desktop)} (must be 150–180).")
            if not (75 <= len(mobile) <= 80):
                report["ok"] = False
                report["issues"].append(
                    f"Title #{i} mobile length={len(mobile)} (must be 75–80).")

    # Bullets
    bullets = draft.get("bullets", [])
    if len(bullets) != 5:
        report["ok"] = False
        report["issues"].append(f"Bullets count={len(bullets)} (must be 5).")
    for j, b in enumerate(bullets, 1):
        L = len(b or "")
        if not (130 <= L <= 180):
            report["ok"] = False
            report["issues"].append(
                f"Bullet {j} length={L} (must be 130–180).")
        if not re.match(r"^[A-Z0-9][A-Z0-9\s&\-\/]+:\s", b or ""):
            report["ok"] = False
            report["issues"].append(
                f"Bullet {j} must start with ALL-CAPS HEADER followed by ': '.")

    # Description
    desc = draft.get("description", "")
    if not (1500 <= len(desc) <= 1800):
        report["ok"] = False
        report["issues"].append(
            f"Description length={len(desc)} (must be 1500–1800).")
    if "<br><br>" not in (desc or ""):
        report["issues"].append(
            "Description should use <br><br> between paragraphs (advisory).")

    # Backend
    backend = draft.get("search_terms", "") or ""
    bytes_no_space = _no_space_bytes_len(backend)
    if not (243 <= bytes_no_space <= 249):
        report["ok"] = False
        report["issues"].append(
            f"Search terms bytes(no spaces)={bytes_no_space} (must be 243–249).")
    if backend.strip() != backend.strip().lower():
        report["issues"].append("Search terms should be lowercase.")
    if re.search(r"[,;:\-_/\\.]", backend):
        report["issues"].append(
            "Search terms should not contain punctuation; use spaces only.")

    return report
