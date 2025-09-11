# listing/funcional_listing_copywrite.py
# Orquestador IA por ETAPA (title / bullets / description / backend)
# - Usa EXCLUSIVAMENTE la tabla inputs_para_listing (Tipo, Etiqueta, Contenido).
# - Para TÍTULOS llama al prompt estricto definido en prompts_listing_copywrite.py (SOP RD + Brief General).
# - Bullets/Description/Backend quedan cableados a sus placeholders (no invento reglas).
# - Mantiene alias lafuncionqueejecuta_listing_copywrite para compatibilidad.

import os
import re
import json
import pandas as pd
from typing import Optional

# Prompts por etapa (títulos estrictos + placeholders para las otras)
from listing.prompts_listing_copywrite import (
    prompt_titles_json,
    prompt_bullets_json,
    prompt_description_json,
    prompt_backend_json,
)

# -------------------------- JSON robusto --------------------------


def _extract_first_json(txt: str) -> str:
    if not txt:
        return ""
    s = txt.strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", s, re.IGNORECASE)
    if m:
        s = m.group(1).strip()
    try:
        json.loads(s)
        return s
    except Exception:
        pass
    start = s.find("{")
    if start == -1:
        return ""
    depth = 0
    for i in range(start, len(s)):
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
            if depth == 0:
                candidate = s[start:i+1]
                try:
                    json.loads(candidate)
                    return candidate
                except Exception:
                    break
    return ""


def _parse_json(txt: str) -> dict:
    cand = _extract_first_json(txt)
    if not cand:
        raise ValueError("La IA no devolvió JSON parseable.")
    return json.loads(cand)


# -------------------------- OpenAI --------------------------
try:
    from openai import OpenAI
    _openai_client = OpenAI()
except Exception:
    _openai_client = None

_MODEL_DEFAULT = os.getenv("LISTING_COPY_MODEL", "gpt-4o-mini")
_TEMPERATURE = float(os.getenv("LISTING_COPY_TEMPERATURE", "0.2"))
_MAXTOK = int(os.getenv("LISTING_COPY_MAXTOK", "1800"))


def _require_openai():
    if _openai_client is None:
        raise RuntimeError(
            "OpenAI SDK no disponible. Instala `openai>=1.0.0` y exporta OPENAI_API_KEY.")
    return _openai_client


def _chat_json(user_prompt: str) -> dict:
    client = _require_openai()
    resp = client.chat.completions.create(
        model=_MODEL_DEFAULT,
        temperature=_TEMPERATURE,
        max_tokens=_MAXTOK,
        messages=[
            {"role": "system", "content": "Return ONLY raw JSON. No prose, no markdown, no code fences."},
            {"role": "user",   "content": user_prompt},
        ],
    )
    content = (resp.choices[0].message.content or "").strip()
    return _parse_json(content)


# -------------------------- Helpers de datos --------------------------
REQ_COLS = ["Tipo", "Etiqueta", "Contenido"]


def _to_records(df: pd.DataFrame, budgeted: bool = True):
    miss = [c for c in REQ_COLS if c not in df.columns]
    if miss:
        raise ValueError(f"Faltan columnas en inputs_df: {miss}")
    df2 = df[REQ_COLS].copy()
    # cost_saver: recorta de forma simple por tipo si hay demasiadas filas
    if budgeted and len(df2) > 800:
        df2 = df2.groupby("Tipo", group_keys=False).head(
            200).reset_index(drop=True)
    for c in REQ_COLS:
        df2[c] = df2[c].astype(str)
    return df2.to_dict(orient="records")


def _collect(df_records):
    """
    PROYECCIÓN ESTRICTA A SOP (actualizada):
      - head_phrases: SOLO 'Marca' (tal cual tabla).
      - core_tokens : SOLO filas con Etiqueta == 'Core' (independiente del Tipo).
      - attributes  : SOLO Tipo == 'Atributo' → Contenido (RAW).
      - variations  : SOLO Tipo == 'Variación' → Contenido (RAW).
      - benefits    : SOLO Tipo == 'Beneficio' → Contenido (priorización; NO se copia al título).
      - emotions    : SOLO Tipo == 'Emoción' → Contenido (priorización; NO se copia al título).
      - buyer_persona: SOLO Tipo == 'Buyer persona' → concatenado.
      - lexico      : SOLO Tipo == 'Léxico editorial' → concatenado.
    NO se aceptan fuentes fuera de SOP.
    """
    head_phrases = []
    core_tokens = []
    attributes = []
    variations = []
    benefits = []
    emotions = []
    buyer_list = []
    lexico_list = []

    for r in df_records:
        tipo_raw = (r.get("Tipo") or "").strip()
        etiq_raw = (r.get("Etiqueta") or "").strip()
        cont = (r.get("Contenido") or "").strip()
        if not cont:
            continue

        # Marca
        if tipo_raw == "Marca":
            head_phrases.append(cont)

        # CORE (solo por Etiqueta == "Core", sin depender del Tipo)
        elif etiq_raw == "Core":
            core_tokens.append(cont)

        # Atributos / Variaciones
        elif tipo_raw == "Atributo":
            attributes.append(cont)
        elif tipo_raw == "Variación":
            variations.append(cont)

        # Info para priorización (no se copia al título)
        elif tipo_raw == "Beneficio":
            benefits.append(cont)
        elif tipo_raw == "Emoción":
            emotions.append(cont)

        # Metadatos editoriales
        elif tipo_raw == "Buyer persona":
            buyer_list.append(cont)
        elif tipo_raw == "Léxico editorial":
            lexico_list.append(cont)

    # dedupe conservando orden
    def _dedupe(seq):
        return list(dict.fromkeys(seq))

    buyer_persona = " | ".join(_dedupe(buyer_list)) if buyer_list else ""
    lexico = " | ".join(_dedupe(lexico_list)) if lexico_list else ""

    return {
        "head_phrases": _dedupe(head_phrases),
        "core_tokens":  _dedupe(core_tokens),
        "attributes":   _dedupe(attributes),
        "variations":   _dedupe(variations),
        "benefits":     _dedupe(benefits),
        "emotions":     _dedupe(emotions),
        "buyer_persona": buyer_persona,
        "lexico":        lexico,
    }

# -------------------------- Variations (slug) --------------------------


def _slugify_variation_value(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s or "value"


def _coerce_titles_shape(j_title: dict, variations_raw: list) -> dict:
    """
    Espera JSON con clave "title" y estructura:
      { "parent": {"desktop","mobile"}, "<var-slug>": {"desktop","mobile"}, ... }
    Si falta alguna clave, se rellena con "" (no se modifica contenido).
    """
    root = j_title.get("title") if isinstance(j_title, dict) else j_title
    out = {}
    if not isinstance(root, dict):
        return {"parent": {"desktop": "", "mobile": ""}}

    def _pair(d):
        if not isinstance(d, dict):
            d = {}
        return {
            "desktop": "" if d.get("desktop") is None else str(d.get("desktop")),
            "mobile":  "" if d.get("mobile") is None else str(d.get("mobile")),
        }

    out["parent"] = _pair(root.get("parent"))

    # garantizar todas las variaciones detectadas desde tabla estén presentes
    for raw in variations_raw:
        vk = _slugify_variation_value(raw)
        out[vk] = _pair(root.get(vk))

    return out


def _coerce_bullets_shape(j_bul: dict, variations_raw: list) -> dict:
    """
    Formato esperado:
      { "bullets": { "parent":[b1..b5], "<var>":[b1..b5], ... } }
    No copiamos ni recortamos; si faltan posiciones, se rellenan con "".
    """
    root = j_bul.get("bullets") if isinstance(j_bul, dict) else j_bul
    out = {}

    def _five(lst):
        lst = list(lst or [])
        if len(lst) < 5:
            lst += [""]*(5-len(lst))
        return ["" if x is None else str(x) for x in lst[:5]]

    if isinstance(root, dict):
        out["parent"] = _five(root.get("parent"))
        for raw in variations_raw:
            vk = _slugify_variation_value(raw)
            out[vk] = _five(root.get(vk))
    elif isinstance(root, list):
        out["parent"] = _five(root)
        for raw in variations_raw:
            vk = _slugify_variation_value(raw)
            out[vk] = _five([])
    else:
        out["parent"] = _five([])
        for raw in variations_raw:
            vk = _slugify_variation_value(raw)
            out[vk] = _five([])
    return out

# -------------------------- Ejecución por ETAPA --------------------------


def run_listing_stage(inputs_df: pd.DataFrame, stage: str, cost_saver: bool = True, rules: Optional[dict] = None):
    """
    Genera SOLO una etapa: 'title' | 'bullets' | 'description' | 'backend'
    No agrega reglas propias. Usa el prompt de esa etapa tal cual esté definido.
    """
    if not isinstance(inputs_df, pd.DataFrame) or inputs_df.empty:
        raise ValueError(
            "inputs_df vacío; construye inputs_para_listing primero.")

    rows = _to_records(inputs_df, budgeted=cost_saver)
    proj = _collect(rows)

    if stage == "title":
        up = prompt_titles_json(
            proj["head_phrases"], proj["core_tokens"], proj["attributes"], proj["variations"],
            proj["benefits"], proj["emotions"], proj["buyer_persona"], proj["lexico"]
        )
        j = _chat_json(up)
        titles = _coerce_titles_shape(j, proj["variations"])
        return {"title": titles}

    elif stage == "bullets":
        up = prompt_bullets_json(
            proj["head_phrases"], proj["core_tokens"], proj["attributes"], proj["variations"],
            proj["benefits"], proj["emotions"], proj["buyer_persona"], proj["lexico"]
        )
        j = _chat_json(up)
        bullets = _coerce_bullets_shape(j, proj["variations"])
        return {"bullets": bullets}

    elif stage == "description":
        up = prompt_description_json(
            proj["head_phrases"], proj["core_tokens"], proj["attributes"], proj["variations"],
            proj["benefits"], proj["emotions"], proj["buyer_persona"], proj["lexico"]
        )
        j = _chat_json(up)
        desc = j.get("description") if isinstance(j, dict) else ""
        if desc is None:
            desc = ""
        return {"description": str(desc)}

    elif stage == "backend":
        up = prompt_backend_json(
            proj["head_phrases"], proj["core_tokens"], proj["attributes"], proj["variations"],
            proj["benefits"], proj["emotions"], proj["buyer_persona"], proj["lexico"]
        )
        j = _chat_json(up)
        search = j.get("search_terms") if isinstance(j, dict) else ""
        if search is None:
            search = ""
        return {"search_terms": str(search)}

    else:
        raise ValueError(f"stage desconocido: {stage}")

# -------------------------- Batch opcional (compatibilidad) --------------------------


def run_listing_copywrite(inputs_df, use_ai=True, cost_saver=True, rules=None):
    """
    Compat: genera las 4 etapas en secuencia (solo si lo necesitas).
    """
    if not use_ai:
        raise ValueError("use_ai=False no soportado aquí. Activa 'Use AI'.")
    draft = {}
    for stg in ("title", "bullets", "description", "backend"):
        part = run_listing_stage(
            inputs_df, stg, cost_saver=cost_saver, rules=rules)
        draft.update(part)
    return draft

# Alias compat


def lafuncionqueejecuta_listing_copywrite(inputs_df, use_ai=True, cost_saver=True, rules=None):
    return run_listing_copywrite(inputs_df, use_ai=use_ai, cost_saver=cost_saver, rules=rules)
