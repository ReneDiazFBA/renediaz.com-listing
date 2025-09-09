# listing/funcional_listing_copywrite.py
# Orquestador IA en MODO CONTRATO ESTRICTO:
# - Usa OpenAI (modelo por defecto: gpt-4o-mini; cambia con LISTING_COPY_MODEL).
# - SOLO usa las ROWS (inputs_para_listing) y TUS RULES literales.
# - No agrega reglas propias, no rellena, no recorta, no corrige.
# - Devuelve:
#   {
#     "title":   { "parent":{"desktop","mobile"}, "<var>":{"desktop","mobile"}, ... },
#     "bullets": { "parent":[b1..b5], "<var>":[b1..b5], ... },
#     "description": str,
#     "search_terms": str
#   }
# - Mantiene alias lafuncionqueejecuta_listing_copywrite.

import os
import re
import json
import pandas as pd

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


def _parse_json_field(txt: str, field: str, fallback):
    candidate = _extract_first_json(txt)
    if not candidate:
        return fallback
    try:
        j = json.loads(candidate)
        val = j.get(field)
        return fallback if val is None else val
    except Exception:
        return fallback


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


def _chat_json(system_prompt: str, user_prompt: str) -> dict:
    client = _require_openai()
    resp = client.chat.completions.create(
        model=_MODEL_DEFAULT,
        temperature=_TEMPERATURE,
        max_tokens=_MAXTOK,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
    )
    content = (resp.choices[0].message.content or "").strip()
    candidate = _extract_first_json(content)
    if not candidate:
        raise ValueError("La IA no devolvió JSON parseable.")
    return json.loads(candidate)

# -------------------------- Helpers de datos --------------------------


def _to_records(df: pd.DataFrame, budgeted: bool = True):
    cols = ["Tipo", "Etiqueta", "Contenido"]
    miss = [c for c in cols if c not in df.columns]
    if miss:
        raise ValueError(f"Faltan columnas en inputs_df: {miss}")
    df2 = df[cols].copy()
    if budgeted and len(df2) > 400:
        df2 = df2.groupby("Tipo", group_keys=False).head(
            120).reset_index(drop=True)
    for c in cols:
        df2[c] = df2[c].astype(str)
    return df2.to_dict(orient="records")

# -------------------------- Variations --------------------------


def _slugify_variation_value(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s or "value"


def _get_variations(rows: list):
    keys, vals = [], []
    for r in rows:
        if str(r.get("Tipo", "")).strip().lower() == "variación":
            raw = str(r.get("Contenido", "")).strip()
            if raw:
                key = _slugify_variation_value(raw)
                if key not in keys:
                    keys.append(key)
                    vals.append(raw)
    return keys, vals

# -------------------------- Schemas --------------------------


def _build_title_schema_dict(var_keys: list) -> dict:
    t = {"parent": {"desktop": "...", "mobile": "..."}}
    for vk in var_keys:
        t[vk] = {"desktop": "...", "mobile": "..."}
    return {"title": t}


def _build_bullets_schema_dict(var_keys: list) -> dict:
    base = ["b1", "b2", "b3", "b4", "b5"]
    b = {"parent": base}
    for vk in var_keys:
        b[vk] = base
    return {"bullets": b}

# -------------------------- Prompt (estricto: solo tus reglas + rows) --------------------------


def _stage_prompt(stage: str, rules_stage: dict, rows: list, var_keys: list = None, var_values: list = None) -> str:
    var_keys = var_keys or []
    # schema solo define la forma del JSON esperado; no añade reglas
    if stage == "title":
        schema_dict = _build_title_schema_dict(var_keys)
    elif stage == "bullets":
        schema_dict = _build_bullets_schema_dict(var_keys)
    elif stage == "description":
        schema_dict = {"description": "string"}
    elif stage == "backend":
        schema_dict = {"search_terms": "string"}
    else:
        raise ValueError(f"stage desconocido: {stage}")

    rules_text = json.dumps(rules_stage or {}, ensure_ascii=False)

    return (
        "You are an Amazon Listing Copywriter executing a binding contract of rules.\n"
        "CRITICAL:\n"
        "- Obey RULES exactly as written (verbatim). Do NOT summarize or reinterpret.\n"
        "- Use ONLY the information present in ROWS as factual source. If a detail is not in ROWS, do NOT include it.\n"
        "- Return ONLY raw JSON conforming to the SCHEMA. No prose, no markdown, no code fences.\n"
        "- If RULES specify formatting, casing, tokens or structure, follow them literally.\n"
        "- If any conflict arises, prefer RULES and omit anything not guaranteed by ROWS.\n\n"
        f"SCHEMA (JSON):\n{json.dumps(schema_dict, ensure_ascii=False, indent=2)}\n\n"
        f"RULES (verbatim):\n{rules_text}\n\n"
        f"ROWS (sole source of truth; Tipo/Etiqueta/Contenido):\n{json.dumps(rows, ensure_ascii=False)}\n"
    ).strip()

# -------------------------- Coerción de forma (sin modificar contenido) --------------------------


def _coerce_titles_shape(j_title: dict, var_keys: list) -> dict:
    root = j_title.get("title") if isinstance(j_title, dict) else j_title
    out = {}
    if not isinstance(root, dict):
        return {"parent": {"desktop": "", "mobile": ""}}

    def _pair(d):
        if not isinstance(d, dict):
            d = {}
        return {"desktop": "" if d.get("desktop") is None else str(d.get("desktop")),
                "mobile":  "" if d.get("mobile") is None else str(d.get("mobile"))}
    out["parent"] = _pair(root.get("parent"))
    for vk in var_keys:
        out[vk] = _pair(root.get(vk))
    return out


def _coerce_bullets_shape(j_bul: dict, var_keys: list) -> dict:
    root = j_bul.get("bullets") if isinstance(j_bul, dict) else j_bul
    out = {}

    def _five(lst):
        lst = list(lst or [])
        if len(lst) < 5:
            lst += [""]*(5-len(lst))
        return ["" if x is None else str(x) for x in lst[:5]]
    if isinstance(root, dict):
        out["parent"] = _five(root.get("parent"))
        for vk in var_keys:
            out[vk] = _five(root.get(vk))
    elif isinstance(root, list):
        out["parent"] = _five(root)
        for vk in var_keys:
            out[vk] = _five([])
    else:
        out["parent"] = _five([])
        for vk in var_keys:
            out[vk] = _five([])
    return out

# -------------------------- Orquestación (una sola pasada, sin “arreglos”) --------------------------


def run_listing_copywrite(inputs_df, use_ai=True, cost_saver=True, rules=None):
    """
    return:
    {
      "title":   { "parent":{"desktop","mobile"}, "<var>":{"desktop","mobile"}, ... },
      "bullets": { "parent":[b1..b5], "<var>":[b1..b5], ... },
      "description": str,
      "search_terms": str
    }
    """
    if not use_ai:
        raise ValueError("use_ai=False no soportado aquí. Activa 'Use AI'.")
    if not isinstance(inputs_df, pd.DataFrame) or inputs_df.empty:
        raise ValueError(
            "inputs_df vacío; construye inputs_para_listing primero.")

    rows = _to_records(inputs_df, budgeted=cost_saver)
    rules = rules or {}

    var_keys, var_values = _get_variations(rows)

    sys_prompt = (
        "Return ONLY raw JSON. No prose, no markdown, no code fences. "
        "Follow the provided SCHEMA exactly. Use only RULES and ROWS."
    )

    # TITLE
    up_title = _stage_prompt("title", rules.get(
        "title"), rows, var_keys=var_keys, var_values=var_values)
    j_title = _chat_json(sys_prompt, up_title)
    title_map = _coerce_titles_shape(j_title, var_keys)

    # BULLETS
    up_bul = _stage_prompt("bullets", rules.get(
        "bullets"), rows, var_keys=var_keys, var_values=var_values)
    j_bul = _chat_json(sys_prompt, up_bul)
    bullets_map = _coerce_bullets_shape(j_bul, var_keys)

    # DESCRIPTION
    up_desc = _stage_prompt("description", rules.get(
        "description"), rows, var_keys=var_keys, var_values=var_values)
    j_desc = _chat_json(sys_prompt, up_desc)
    description = j_desc.get("description") if isinstance(j_desc, dict) else _parse_json_field(
        json.dumps(j_desc, ensure_ascii=False), "description", "")
    description = "" if description is None else str(description)

    # BACKEND
    up_back = _stage_prompt("backend", rules.get(
        "backend"), rows, var_keys=var_keys, var_values=var_values)
    j_back = _chat_json(sys_prompt, up_back)
    search_terms = j_back.get("search_terms") if isinstance(j_back, dict) else _parse_json_field(
        json.dumps(j_back, ensure_ascii=False), "search_terms", "")
    search_terms = "" if search_terms is None else str(search_terms)

    return {
        "title": title_map,
        "bullets": bullets_map,
        "description": description,
        "search_terms": search_terms,
    }

# -------------------------- Alias compat --------------------------


def lafuncionqueejecuta_listing_copywrite(inputs_df, use_ai=True, cost_saver=True, rules=None):
    return run_listing_copywrite(inputs_df, use_ai=use_ai, cost_saver=cost_saver, rules=rules)
