# listing/funcional_listing_copywrite.py
# Orquestador IA para generar Title, Bullets, Description y Backend desde inputs_para_listing.
# - Usa OpenAI (modelo por defecto: gpt-4o-mini; cambia con env LISTING_COPY_MODEL).
# - SOLO acepta como fuente la tabla (rows = Tipo, Etiqueta, Contenido).
# - Devuelve JSON con: title, bullets[5], description, search_terms.
# - Parser a prueba de fences y texto extra.
# - Mantiene alias lafuncionqueejecuta_listing_copywrite para compatibilidad.

import os
import re
import json
import pandas as pd

# -------------------------------------------------------------
# Parser robusto de JSON (maneja ```json ... ``` y texto extra)
# -------------------------------------------------------------


def _extract_first_json(txt: str) -> str:
    if not txt:
        return ""
    s = txt.strip()
    # Quitar code fences si vienen
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", s, re.IGNORECASE)
    if m:
        s = m.group(1).strip()
    # Intento directo
    try:
        json.loads(s)
        return s
    except Exception:
        pass
    # Fallback: buscar primer bloque {...} balanceado
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
    """txt puede ser JSON o texto con JSON dentro; devuelve j[field] o fallback."""
    candidate = _extract_first_json(txt)
    if not candidate:
        return fallback
    try:
        j = json.loads(candidate)
        val = j.get(field)
        if val is None:
            return fallback
        return val
    except Exception:
        return fallback


# -------------------------------------------------------------
# OpenAI setup
# -------------------------------------------------------------
try:
    from openai import OpenAI
    _openai_client = OpenAI()
except Exception:
    _openai_client = None  # se avisa en runtime

_MODEL_DEFAULT = os.getenv("LISTING_COPY_MODEL", "gpt-4o-mini")
_TEMPERATURE = float(os.getenv("LISTING_COPY_TEMPERATURE", "0.2"))
_MAXTOK = int(os.getenv("LISTING_COPY_MAXTOK", "1800"))


def _require_openai():
    if _openai_client is None:
        raise RuntimeError(
            "OpenAI SDK no disponible. Instala `pip install openai>=1.0.0` y exporta OPENAI_API_KEY."
        )
    return _openai_client


# -------------------------------------------------------------
# Helpers de datos
# -------------------------------------------------------------
def _to_records(df: pd.DataFrame, budgeted: bool = True):
    """Convierte inputs_para_listing a lista de dicts (Tipo/Etiqueta/Contenido)."""
    cols = ["Tipo", "Etiqueta", "Contenido"]
    miss = [c for c in cols if c not in df.columns]
    if miss:
        raise ValueError(f"Faltan columnas en inputs_df: {miss}")
    df2 = df[cols].copy()

    # cost_saver: limitar filas manteniendo variedad por Tipo
    if budgeted and len(df2) > 400:
        df2 = (
            df2.groupby("Tipo", group_keys=False)
               .head(120)
               .reset_index(drop=True)
        )
    # normalizar a str
    for c in cols:
        df2[c] = df2[c].astype(str)
    return df2.to_dict(orient="records")


def _chat_json(system_prompt: str, user_prompt: str):
    """Llama al modelo y devuelve dict (JSON) ya parseado."""
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
    try:
        return json.loads(candidate)
    except Exception as e:
        raise ValueError(f"JSON inválido: {e}")


# -------------------------------------------------------------
# Prompt builders: usa los oficiales si existen; si no, backups
# -------------------------------------------------------------
def _get_prompt_builder(name: str):
    """Intenta importar builder desde listing/prompts_listing_copywrite.py."""
    try:
        from listing import prompts_listing_copywrite as P
        fn = getattr(P, name, None)
        if callable(fn):
            return fn
    except Exception:
        pass
    return None


def _bp_title(rules, rows, cost_saver):
    return f"""
You are an Amazon listing copy expert. Output ONLY raw JSON, no prose, no markdown, no code fences.
Schema:
{{
  "title": "string (<=200 chars; no promos; no banned chars; Title Case; parent/child compliant per rules)"
}}
Rules (title, truncated): {json.dumps(rules.get("title", {}), ensure_ascii=False)[:3000]}
Rows (ONLY source of truth): {json.dumps(rows, ensure_ascii=False)[:4000]}
Return the JSON only.
""".strip()


def _bp_bullets(rules, rows, cost_saver):
    return f"""
You are an Amazon listing copy expert. Output ONLY raw JSON, no prose, no markdown, no code fences.
Schema:
{{
  "bullets": ["b1","b2","b3","b4","b5"]  // 5 items; 150–180 chars each; sentence fragments; no final period; fascination style per rules
}}
Rules (bullets, truncated): {json.dumps(rules.get("bullets", {}), ensure_ascii=False)[:3000]}
Rows (ONLY source of truth): {json.dumps(rows, ensure_ascii=False)[:4000]}
Return the JSON only.
""".strip()


def _bp_description(rules, rows, cost_saver):
    return f"""
You are an Amazon listing copy expert. Output ONLY raw JSON, no prose, no markdown, no code fences.
Schema:
{{
  "description": "2–3 paragraphs, separated by <br><br>, 150–200 words total, <=2000 chars; parent/child narrative coherence per rules"
}}
Rules (description, truncated): {json.dumps(rules.get("description", {}), ensure_ascii=False)[:3000]}
Rows (ONLY source of truth): {json.dumps(rows, ensure_ascii=False)[:4000]}
Return the JSON only.
""".strip()


def _bp_backend(rules, rows, cost_saver):
    return f"""
You are an Amazon listing copy expert. Output ONLY raw JSON, no prose, no markdown, no code fences.
Schema:
{{
  "search_terms": "single line, lowercase, space-separated, no punctuation/stopwords/dupes; 220–240 chars (no spaces), <=249 hard; exclude title/bullets terms"
}}
Rules (backend, truncated): {json.dumps(rules.get("backend", {}), ensure_ascii=False)[:3000]}
Rows (ONLY source of truth): {json.dumps(rows, ensure_ascii=False)[:4000]}
Return the JSON only.
""".strip()


def _build_prompts(rules, rows, cost_saver):
    """Elige builders del módulo prompts si existen; si no, usa fallback interno."""
    mapping = {
        "title":       (_get_prompt_builder("build_prompt_title"),       _bp_title),
        "bullets":     (_get_prompt_builder("build_prompt_bullets"),     _bp_bullets),
        "description": (_get_prompt_builder("build_prompt_description"), _bp_description),
        "backend":     (_get_prompt_builder("build_prompt_backend"),     _bp_backend),
    }
    prompts = {}
    for key, (ext, fallback) in mapping.items():
        if ext:
            prompts[key] = ext(rules=rules, rows=rows, cost_saver=cost_saver)
        else:
            prompts[key] = fallback(rules, rows, cost_saver)
    return prompts


# -------------------------------------------------------------
# Orquestador público (IA ON)
# -------------------------------------------------------------
def run_listing_copywrite(inputs_df, use_ai=True, cost_saver=True, rules=None):
    """
    Genera con IA un borrador de listing basado EXCLUSIVAMENTE en inputs_df:
      return: {"title": str, "bullets": [str*5], "description": str, "search_terms": str}
    """
    if not use_ai:
        raise ValueError(
            "use_ai=False no soportado aquí. Activa 'Use AI' en la UI.")

    if not isinstance(inputs_df, pd.DataFrame) or inputs_df.empty:
        raise ValueError(
            "inputs_df vacío; construye inputs_para_listing primero.")

    rows = _to_records(inputs_df, budgeted=cost_saver)
    rules = rules or {}

    sys_prompt = (
        "You are a senior Amazon listing copy editor. "
        "Output ONLY raw JSON (no prose, no markdown, no code fences). "
        "The JSON schema and keys must match exactly."
    )
    prompts = _build_prompts(rules, rows, cost_saver)

    # TITLE
    j_title = _chat_json(sys_prompt, prompts["title"])
    title = _parse_json_field(json.dumps(
        j_title, ensure_ascii=False), "title", "")

    # BULLETS
    j_bul = _chat_json(sys_prompt, prompts["bullets"])
    bullets = _parse_json_field(json.dumps(
        j_bul, ensure_ascii=False), "bullets", [])
    bullets = (bullets or [])[:5]

    # DESCRIPTION
    j_desc = _chat_json(sys_prompt, prompts["description"])
    description = _parse_json_field(json.dumps(
        j_desc, ensure_ascii=False), "description", "")

    # BACKEND (Search terms)
    j_back = _chat_json(sys_prompt, prompts["backend"])
    search_terms = _parse_json_field(json.dumps(
        j_back, ensure_ascii=False), "search_terms", "")

    return {
        "title": title or "",
        "bullets": bullets or [],
        "description": description or "",
        "search_terms": search_terms or "",
    }


# -------------------------------------------------------------
# Alias de compatibilidad (tu app aún importa este nombre)
# -------------------------------------------------------------
def lafuncionqueejecuta_listing_copywrite(inputs_df, use_ai=True, cost_saver=True, rules=None):
    return run_listing_copywrite(inputs_df, use_ai=use_ai, cost_saver=cost_saver, rules=rules)
