# listing/funcional_listing_copywrite.py
# Orquestador IA que GENERA el listing (Title, Bullets, Description, Backend) pegado a TUS reglas/SOPs.
# - Usa OpenAI (modelo por defecto: gpt-4o-mini; cambia con LISTING_COPY_MODEL).
# - Toma EXCLUSIVAMENTE rows de inputs_para_listing (Tipo, Etiqueta, Contenido).
# - Inyecta rules["title"|"bullets"|"description"|"backend"] completos en cada prompt.
# - Valida la salida y reintenta hasta 2 veces por etapa si no cumple (longitudes, formato, etc.).
# - Devuelve: {"title": str, "bullets": [str*5], "description": str, "search_terms": str}
# - Mantiene alias lafuncionqueejecuta_listing_copywrite para compatibilidad.

import os
import re
import json
import math
import pandas as pd

# -------------------------------------------------------------
# JSON robusto (maneja ```json ... ``` y texto extra)
# -------------------------------------------------------------


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
    cand = _extract_first_json(txt)
    if not cand:
        return fallback
    try:
        j = json.loads(cand)
        return j.get(field, fallback)
    except Exception:
        return fallback


# -------------------------------------------------------------
# OpenAI (SDK v1)
# -------------------------------------------------------------
try:
    from openai import OpenAI
    _openai_client = OpenAI()
except Exception:
    _openai_client = None  # se avisará en runtime

_MODEL_DEFAULT = os.getenv("LISTING_COPY_MODEL", "gpt-4o-mini")
_TEMPERATURE = float(os.getenv("LISTING_COPY_TEMPERATURE", "0.2"))
_MAXTOK = int(os.getenv("LISTING_COPY_MAXTOK", "1800"))


def _require_openai():
    if _openai_client is None:
        raise RuntimeError(
            "OpenAI SDK no disponible. Instala `pip install openai>=1.0.0` y exporta OPENAI_API_KEY."
        )
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
    cand = _extract_first_json(content)
    if not cand:
        raise ValueError("La IA no devolvió JSON parseable.")
    try:
        return json.loads(cand)
    except Exception as e:
        raise ValueError(f"JSON inválido: {e}")


# -------------------------------------------------------------
# Helpers de datos y conteo
# -------------------------------------------------------------
def _to_records(df: pd.DataFrame, budgeted: bool = True):
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
    for c in cols:
        df2[c] = df2[c].astype(str)
    return df2.to_dict(orient="records")


def _word_count_with_br(text: str) -> int:
    return len((text or "").replace("<br><br>", " ").split())


def _len_no_spaces_bytes(s: str) -> int:
    return len((s or "").replace(" ", "").encode("utf-8"))


def _has_banned_symbols(s: str) -> bool:
    # puedes extender
    return bool(re.search(r"[™®€…†‡º¢£¥©±~💥🔥✨🍀#@%=_/\\]", s or ""))


# -------------------------------------------------------------
# Validadores (pegados al contrato que definimos)
# -------------------------------------------------------------
def _validate_title(title: str) -> (bool, str):
    if not title or _has_banned_symbols(title):
        return False, "símbolos prohibidos o vacío"
    # Longitud típicamente 120–150 desktop; aquí validamos <=200 para no bloquear si tus reglas difieren.
    if len(title) > 200:
        return False, ">200 chars"
    return True, ""


def _validate_bullets(bullets: list) -> (bool, str):
    if not isinstance(bullets, list) or len(bullets) != 5:
        return False, "deben ser 5 bullets"
    for i, b in enumerate(bullets, 1):
        if not (150 <= len(b) <= 180):
            return False, f"bullet {i} fuera de rango 150–180"
        if b.endswith("."):
            return False, f"bullet {i} termina en punto"
    return True, ""


def _validate_description(desc: str) -> (bool, str):
    if not desc:
        return False, "vacío"
    paras = desc.count("<br><br>") + 1
    if paras not in (2, 3):
        return False, "debe tener 2–3 párrafos con <br><br>"
    wc = _word_count_with_br(desc)
    if not (150 <= wc <= 200):
        return False, f"{wc} palabras (debe 150–200)"
    if len(desc) > 2000:
        return False, ">2000 chars"
    return True, ""


def _validate_backend(line: str) -> (bool, str):
    if not line:
        return False, "vacío"
    if re.search(r"[^\sa-z0-9áéíóúüñ]", line):  # puntuación no permitida
        return False, "puntuación/símbolos no permitidos"
    length = _len_no_spaces_bytes(line)
    if not (220 <= length <= 249):
        return False, f"{length} bytes sin espacios (debe 220–249)"
    return True, ""


# -------------------------------------------------------------
# Construcción de PROMPTS desde tus reglas (sin fallbacks genéricos)
# -------------------------------------------------------------
def _stage_prompt(stage: str, rules_stage: dict, rows: list) -> str:
    """
    Inserta Normativas + SOP completas para la etapa, más ESQUEMA estricto.
    """
    if stage == "title":
        schema = {
            "title": "string (<=200 chars; no promos; no banned chars; aplicar Parent/Child si corresponde)"
        }
        hard = (
            "Output ONLY raw JSON (no text, no markdown, no code fences). "
            "Use ONLY information present in Rows. "
            "Comply EXACTLY with ‘Rules’ below (non-negotiable)."
        )
    elif stage == "bullets":
        schema = {
            "bullets": [
                "b1", "b2", "b3", "b4", "b5"
            ]
        }
        hard = (
            "5 bullets; 150–180 chars cada uno; fragmentos; sin punto final; "
            "Bullet 1 trata variación según Parent/Child; "
            "Usa fascinación conforme a Manual; "
            "Output ONLY JSON."
        )
    elif stage == "description":
        schema = {
            "description": "2–3 paragraphs separated by <br><br>, 150–200 words total, <=2000 chars"
        }
        hard = "Narrativa según reglas; Output ONLY JSON."
    elif stage == "backend":
        schema = {
            "search_terms": "single line, lowercase, space-separated, no punctuation/stopwords/dupes; 220–240 chars (no spaces), <=249 hard; exclude title/bullets terms"
        }
        hard = "Solo desde Rows; Output ONLY JSON."
    else:
        raise ValueError(f"stage desconocido: {stage}")

    return (
        "You are a senior Amazon listing copy editor.\n"
        "Return ONLY raw JSON conforming to the schema; no prose, no markdown, no code fences.\n\n"
        f"Schema (JSON):\n{json.dumps(schema, ensure_ascii=False, indent=2)}\n\n"
        f"Rules (Normativas + SOP; non-negotiable; full detail):\n{json.dumps(rules_stage or {}, ensure_ascii=False)}\n\n"
        f"Rows (ONLY source of truth; Tipo/Etiqueta/Contenido):\n{json.dumps(rows, ensure_ascii=False)}\n\n"
        f"{hard}\n"
    ).strip()


def _retry_stage(system_prompt: str, user_prompt: str, validate_fn, field: str, max_tries=3):
    """
    Ejecuta IA, valida y reintenta (hasta 2 retries) explicándole el fallo al modelo.
    """
    last_err = ""
    for attempt in range(1, max_tries+1):
        j = _chat_json(system_prompt, user_prompt if attempt ==
                       1 else f"{user_prompt}\n\nNOTE: Previous output failed because: {last_err}. Fix and return JSON again.")
        val = _parse_json_field(json.dumps(j, ensure_ascii=False), field, None)
        ok, msg = validate_fn(
            val) if field != "bullets" else validate_fn(val or [])
        if ok:
            return val
        last_err = msg or "invalid"
    # si falla todo, devolvemos algo usable aunque sea vacío
    return val if val is not None else ("" if field != "bullets" else [])


# -------------------------------------------------------------
# EJECUCIÓN PÚBLICA (IA ON) — usa TUS REGLAS por etapa
# -------------------------------------------------------------
def run_listing_copywrite(inputs_df, use_ai=True, cost_saver=True, rules=None):
    """
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
        "Follow the schema exactly; use only provided Rows; obey Rules strictly."
    )

    # --- TITLE ---
    up_title = _stage_prompt("title", rules.get("title"), rows)
    title = _retry_stage(sys_prompt, up_title, _validate_title, "title")

    # --- BULLETS ---
    up_bul = _stage_prompt("bullets", rules.get("bullets"), rows)
    bullets = _retry_stage(sys_prompt, up_bul, _validate_bullets, "bullets")

    # --- DESCRIPTION ---
    up_desc = _stage_prompt("description", rules.get("description"), rows)
    description = _retry_stage(
        sys_prompt, up_desc, _validate_description, "description")

    # --- BACKEND ---
    up_back = _stage_prompt("backend", rules.get("backend"), rows)
    search_terms = _retry_stage(
        sys_prompt, up_back, _validate_backend, "search_terms")

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
