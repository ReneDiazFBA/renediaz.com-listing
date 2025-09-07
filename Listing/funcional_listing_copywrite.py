# listing/funcional_listing_copywrite.py

import os
import re
import json
from typing import Dict, List, Any
import pandas as pd
from listing.prompts_listing_copywrite import prompt_master_json_all

# ---------- helpers para extraer proyecciones ----------


def _pick(df: pd.DataFrame, tipo_eq: str) -> List[str]:
    if df.empty:
        return []
    m = df["Tipo"].astype(str).str.strip(
    ).str.lower() == tipo_eq.strip().lower()
    return df.loc[m, "Contenido"].dropna().astype(str).str.strip().tolist()


def _brand(df: pd.DataFrame) -> str:
    vals = _pick(df, "Marca")
    return vals[0].strip() if vals else ""


def _attributes(df: pd.DataFrame) -> List[str]:
    return _pick(df, "Atributo")


def _variations(df: pd.DataFrame) -> List[str]:
    return _pick(df, "Variación")


def _benefits(df: pd.DataFrame) -> List[str]:
    out = set(_pick(df, "Beneficio"))
    out.update(_pick(df, "Beneficio valorado"))
    out.update(_pick(df, "Ventaja"))
    return [x for x in out if x]


def _obstacles(df: pd.DataFrame) -> List[str]:
    return _pick(df, "Obstáculo")


def _emotions(df: pd.DataFrame) -> List[str]:
    return _pick(df, "Emoción")


def _lexicon(df: pd.DataFrame) -> str:
    vals = _pick(df, "Léxico editorial")
    return vals[0] if vals else ""


def _core_tokens(df: pd.DataFrame) -> List[str]:
    if df.empty:
        return []
    m = df["Tipo"].astype(str).str.lower().str.contains("seo sem", na=False)
    sub = df.loc[m, ["Contenido", "Etiqueta"]].dropna(how="all")
    if sub.empty:
        return []
    core = sub[sub["Etiqueta"].astype(str).str.lower().eq("core")]
    if not core.empty:
        vals = core["Contenido"].dropna().astype(str).str.strip().tolist()
        return list(dict.fromkeys([v for v in vals if v]))
    vals = sub["Contenido"].dropna().astype(str).str.strip().tolist()
    return list(dict.fromkeys([v for v in vals if v]))[:50]


def _extra_semantic_tokens(df: pd.DataFrame) -> List[str]:
    """Tokens no-core (clusters u otros) para backend."""
    if df.empty:
        return []
    m = df["Tipo"].astype(str).str.lower().str.contains("seo sem", na=False)
    sub = df.loc[m, ["Contenido", "Etiqueta"]].dropna(how="all")
    if sub.empty:
        return []
    extra = sub[~sub["Etiqueta"].astype(str).str.lower().eq("core")]
    vals = extra["Contenido"].dropna().astype(str).str.strip().tolist()
    # únicos, sin vacíos
    return list(dict.fromkeys([v for v in vals if v]))[:100]


# ---------- compliance / fixes (resumen: ya lo tienes en tu versión previa) ----------
DISALLOWED_TITLE_CHARS = set("!$?_^¬¦{}")
BR_TAG = "<br><br>"
SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")


def bytes_no_spaces(s: str) -> int:
    return len((s or "").replace(" ", "").encode("utf-8"))


def collect_surface_words(payload: Dict[str, Any]) -> set:
    text = []
    for t in payload.get("titles", []):
        text += [t.get("desktop", ""), t.get("mobile", "")]
    text += payload.get("bullets", [])
    text.append(payload.get("description", ""))
    return set(w for w in re.findall(r"[a-z0-9]+", " ".join(text).lower()))


def trim_backend(backend: str, min_bytes: int = 243, max_bytes: int = 249) -> str:
    tokens = [t for t in (backend or "").split() if t]
    seen = set()
    dedup = []
    for t in tokens:
        key = t.lower()
        if key not in seen:
            seen.add(key)
            dedup.append(t)
    out = " ".join(dedup)
    while bytes_no_spaces(out) > max_bytes and dedup:
        dedup.pop()
        out = " ".join(dedup)
    # si quedó por debajo, lo dejamos (el prompt intenta 247–249)
    return out


def scrub_backend_surface_overlap(backend: str, surface_words: set) -> str:
    tokens = [t for t in (backend or "").split() if t]
    kept = [t for t in tokens if t.lower() not in surface_words]
    return " ".join(kept) if kept else backend


def normalize_backend_tokens(backend: str) -> str:
    """lowercase, sin puntuación, sin stopwords cortas, sin duplicados."""
    stop = {"a", "an", "and", "by", "for", "of", "the", "with"}
    toks = re.findall(r"[a-z0-9]+", (backend or "").lower())
    toks = [t for t in toks if t not in stop]
    seen = set()
    out = []
    for t in toks:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return " ".join(out)

# ---------- generación principal ----------


def generar_listing_completo_desde_df(inputs_df: pd.DataFrame, model: str = "gpt-4o-mini") -> Dict:
    if not isinstance(inputs_df, pd.DataFrame) or inputs_df.empty:
        raise ValueError(
            "inputs_df is empty. Build 'inputs_para_listing' first.")
    for col in ("Tipo", "Contenido", "Etiqueta", "Fuente"):
        if col not in inputs_df.columns:
            raise ValueError(f"Missing required column in inputs_df: {col}")

    brand = _brand(inputs_df)
    core = _core_tokens(inputs_df)
    extra = _extra_semantic_tokens(inputs_df)          # <<< NUEVO
    attrs = _attributes(inputs_df)
    vars_ = _variations(inputs_df)
    bens = _benefits(inputs_df)
    cons = _obstacles(inputs_df)
    emos = _emotions(inputs_df)
    lexico = _lexicon(inputs_df)
    persona_vals = _pick(inputs_df, "Buyer persona")
    persona = persona_vals[0] if persona_vals else ""

    # prompt actualizado con extra_tokens y variation_terms
    prompt = prompt_master_json_all(
        brand=brand,
        core_tokens=core,
        attributes=attrs,
        variations=vars_,
        benefits=bens,
        obstacles=cons,
        emotions=emos,
        buyer_persona=persona,
        lexico=lexico,
        extra_tokens=extra,
        variation_terms=vars_,     # pasa tal cual; el prompt decide incluirlos o no
    )

    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY not found. Set it before generating the listing.")

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=2300,
        )
        content = resp.choices[0].message.content
        data = json.loads(content)

        # schema mínimo
        for k in ("titles", "bullets", "description", "search_terms"):
            if k not in data:
                raise ValueError(f"Missing key in AI response: {k}")

        # post-proceso del backend: normalizar, quitar “surface”, forzar bytes
        surface = collect_surface_words(data)
        bk = data.get("search_terms", "")
        bk = normalize_backend_tokens(bk)
        bk = scrub_backend_surface_overlap(bk, surface)
        bk = trim_backend(bk, 243, 249)
        data["search_terms"] = bk

        return data

    except Exception as e:
        raise RuntimeError(f"OpenAI call failed: {e}")
