# listing/funcional_listing_copywrite.py
# Orquestador IA que GENERA el listing (Title, Bullets, Description, Backend) pegado a TUS reglas/SOPs.
# - Usa OpenAI (modelo por defecto: gpt-4o-mini; cambia con LISTING_COPY_MODEL).
# - Toma EXCLUSIVAMENTE rows de inputs_para_listing (Tipo, Etiqueta, Contenido).
# - Inyecta rules["title"|"bullets"|"description"|"backend"] completos en cada prompt.
# - Schema dinámico por variaciones (detectadas desde rows Tipo="Variación").
# - Valida la salida y reintenta hasta 2 veces por etapa si no cumple (longitudes, formato, etc.).
# - Devuelve:
#   {
#     "title":   { "parent":{"desktop","mobile"}, "<var>":{"desktop","mobile"}, ... },
#     "bullets": { "parent":[b1..b5], "<var>":[b1..b5], ... },
#     "description": str,
#     "search_terms": str
#   }
# - Mantiene alias lafuncionqueejecuta_listing_copywrite para compatibilidad.

import os
import re
import json
import pandas as pd

# -------------------------------------------------------------
# JSON robusto (maneja ```json ... ``` y texto extra)
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
        return fallback if val is None else val
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
    candidate = _extract_first_json(content)
    if not candidate:
        raise ValueError("La IA no devolvió JSON parseable.")
    try:
        return json.loads(candidate)
    except Exception as e:
        raise ValueError(f"JSON inválido: {e}")


# -------------------------------------------------------------
# Helpers de datos / conteo / validación
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
    for c in cols:
        df2[c] = df2[c].astype(str)
    return df2.to_dict(orient="records")


def _word_count_with_br(text: str) -> int:
    return len((text or "").replace("<br><br>", " ").split())


def _len_no_spaces_bytes(s: str) -> int:
    return len((s or "").replace(" ", "").encode("utf-8"))


def _has_banned_symbols(s: str) -> bool:
    # amplía si tu contrato tiene más prohibidos
    return bool(re.search(r"[™®€…†‡º¢£¥©±~💥🔥✨🍀#@%=_/\\]", s or ""))


# -------------------------------------------------------------
# Validadores (pegados al contrato base)
# -------------------------------------------------------------
def _validate_title(title: str) -> (bool, str):
    if not title or _has_banned_symbols(title):
        return False, "símbolos prohibidos o vacío"
    if len(title) > 200:
        return False, ">200 chars"
    return True, ""


def _validate_bullets_list(bullets: list) -> (bool, str):
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
    # no puntuación; solo minúsculas, dígitos y espacios
    if re.search(r"[^\sa-z0-9áéíóúüñ]", line):
        return False, "puntuación/símbolos no permitidos"
    length = _len_no_spaces_bytes(line)
    if not (220 <= length <= 249):
        return False, f"{length} bytes sin espacios (debe 220–249)"
    # stopwords básicas ES/EN (se ampliará luego con tu fix)
    stop = set("a al ante bajo cabe con contra de del desde durante en entre hacia hasta mediante para por según sin sobre tras y e o u ni que como un una unos unas el la los las the a an and or for of with by to from".split())
    toks = line.split()
    if any(t in stop for t in toks):
        return False, "contiene stopwords (ES/EN)"
    return True, ""


# -------------------------------------------------------------
# Variations helpers (dinámico según inputs_para_listing)
# -------------------------------------------------------------
def _slugify_variation_value(s: str) -> str:
    # nombre de la clave en JSON (lowercase, alfanumérico con guiones)
    s = (s or "").strip().lower()
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s or "value"


def _get_variation_keys(rows: list) -> list:
    """
    Devuelve lista ordenada de keys para las variaciones, e.g. ["green","yellow","red"].
    Lee exclusivamente de rows con Tipo="Variación" → Contenido.
    """
    vals = []
    for r in rows:
        if str(r.get("Tipo", "")).strip().lower() == "variación":
            v = str(r.get("Contenido", "")).strip()
            if v:
                k = _slugify_variation_value(v)
                if k not in vals:
                    vals.append(k)
    return vals


# -------------------------------------------------------------
# Construcción de SCHEMA dinámico por etapa
# -------------------------------------------------------------
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


# -------------------------------------------------------------
# Construcción de PROMPTS (inyecta reglas completas por etapa)
# -------------------------------------------------------------
def _stage_prompt(stage: str, rules_stage: dict, rows: list, var_keys: list = None) -> str:
    """
    Inserta Normativas + SOP completas para la etapa, más ESQUEMA estricto.
    Para title/bullets, si hay variaciones, el schema se arma dinámicamente.
    """
    var_keys = var_keys or []

    if stage == "title":
        schema_dict = _build_title_schema_dict(var_keys)
        hard = (
            "Output ONLY raw JSON (no text, no markdown, no code fences). "
            "Use ONLY information present in Rows. "
            "Comply EXACTLY with ‘Rules’. "
            "For each variation key (generated from Rows with Tipo='Variación' → Contenido), "
            "produce desktop and mobile versions. No invented attributes or colors."
        )
    elif stage == "bullets":
        schema_dict = _build_bullets_schema_dict(var_keys)
        hard = (
            "Output ONLY raw JSON. "
            "Exactly 5 bullets per scope. 150–180 chars each; sentence fragments; no final period. "
            "Bullet 1 is variation-specific (Parent vs each variation). "
            "Bullets 2–5 MUST be identical across Parent and all variations. "
            "Use ONLY facts from Rows (Tipo=Atributo/Variación/etc.). No invented materials or accessories."
        )
    elif stage == "description":
        schema_dict = {
            "description": "2–3 paragraphs separated by <br><br>, 150–200 words total, <=2000 chars"}
        hard = (
            "Output ONLY raw JSON. Narrative coherence per Rules. "
            "Do NOT introduce attributes/colors not present in Rows (Tipo='Variación' or Tipo='Atributo')."
        )
    elif stage == "backend":
        schema_dict = {
            "search_terms": "single line, lowercase, space-separated, no punctuation/stopwords/dupes; 220–240 chars (no spaces), <=249 hard; exclude title/bullets terms"}
        hard = (
            "Output ONLY raw JSON. Source only from Rows (SEO clusters/attributes not used elsewhere). "
            "Apply stopword removal and normalization as per Rules."
        )
    else:
        raise ValueError(f"stage desconocido: {stage}")

    return (
        "You are a senior Amazon listing copy editor.\n"
        "Return ONLY raw JSON conforming to the schema; no prose, no markdown, no code fences.\n\n"
        f"Schema (JSON):\n{json.dumps(schema_dict, ensure_ascii=False, indent=2)}\n\n"
        f"Rules (Normativas + SOP; non-negotiable; full detail):\n{json.dumps(rules_stage or {}, ensure_ascii=False)}\n\n"
        f"Rows (ONLY source of truth; Tipo/Etiqueta/Contenido):\n{json.dumps(rows, ensure_ascii=False)}\n\n"
        f"{hard}\n"
    ).strip()


# -------------------------------------------------------------
# Normalización de salida (asegurar forma esperada)
# -------------------------------------------------------------
def _coerce_titles_shape(j_title: dict, var_keys: list) -> dict:
    """
    Asegura que title tenga:
    {
      "parent": {"desktop": str, "mobile": str},
      "<var>":  {"desktop": str, "mobile": str}, ...
    }
    """
    out = {}
    root = j_title.get("title") if isinstance(j_title, dict) else j_title
    if not isinstance(root, dict):
        return {"parent": {"desktop": "", "mobile": ""}}

    def _pair(d):
        desktop = (d or {}).get("desktop", "") if isinstance(d, dict) else ""
        mobile = (d or {}).get("mobile",  "") if isinstance(d, dict) else ""
        return {"desktop": str(desktop), "mobile": str(mobile)}

    out["parent"] = _pair(root.get("parent"))
    for vk in var_keys:
        out[vk] = _pair(root.get(vk))
    return out


def _coerce_bullets_shape(j_bul: dict, var_keys: list) -> dict:
    """
    Asegura que bullets tenga:
    {
      "parent": [b1,b2,b3,b4,b5],
      "<var>":  [b1,b2,b3,b4,b5], ...
    }
    y que bullets 2–5 se copien del parent (si el modelo no lo hizo).
    """
    root = j_bul.get("bullets") if isinstance(j_bul, dict) else j_bul
    out = {}
    if isinstance(root, dict) and isinstance(root.get("parent"), list):
        parent = [str(x) for x in (root.get("parent") or [])][:5]
        while len(parent) < 5:
            parent.append("")
        out["parent"] = parent
        for vk in var_keys:
            v_list = root.get(vk)
            if isinstance(v_list, list) and len(v_list) >= 1:
                # conservar b1 de la variación, forzar 2–5 desde parent
                b1 = str(v_list[0])
                v_norm = [b1] + parent[1:5]
            else:
                # si no vino, copiar completamente parent
                v_norm = parent[:]
            out[vk] = v_norm
    else:
        # fallback: si vino como lista plana
        base = [str(x) for x in (root if isinstance(root, list) else [])][:5]
        while len(base) < 5:
            base.append("")
        out["parent"] = base
        for vk in var_keys:
            out[vk] = base[:]
    return out


# -------------------------------------------------------------
# Reintento con validación (por etapa)
# -------------------------------------------------------------
def _retry_stage(system_prompt: str, user_prompt: str, field: str, validate_fn, max_tries=3):
    """
    Ejecuta IA, valida y reintenta (hasta 2 retries) explicándole el fallo al modelo.
    """
    last_err = ""
    val = None
    for attempt in range(1, max_tries+1):
        j = _chat_json(system_prompt, user_prompt if attempt ==
                       1 else f"{user_prompt}\n\nNOTE: Previous output failed because: {last_err}. Fix and return JSON again.")
        val = j if field is None else _parse_json_field(
            json.dumps(j, ensure_ascii=False), field, None)
        ok, msg = validate_fn(val) if validate_fn else (True, "")
        if ok:
            return val
        last_err = msg or "invalid"
    return val


# -------------------------------------------------------------
# EJECUCIÓN PÚBLICA (IA ON) — usa TUS REGLAS por etapa
# -------------------------------------------------------------
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
        raise ValueError(
            "use_ai=False no soportado aquí. Activa 'Use AI' en la UI.")
    if not isinstance(inputs_df, pd.DataFrame) or inputs_df.empty:
        raise ValueError(
            "inputs_df vacío; construye inputs_para_listing primero.")

    rows = _to_records(inputs_df, budgeted=cost_saver)
    rules = rules or {}

    # === variaciones dinámicas ===
    var_keys = _get_variation_keys(rows)  # e.g., ["green","yellow","red"]

    sys_prompt = (
        "You are a senior Amazon listing copy editor. "
        "Output ONLY raw JSON (no prose, no markdown, no code fences). "
        "Follow the schema exactly; use only provided Rows; obey Rules strictly."
    )

    # --- TITLE (dinámico por variación) ---
    up_title = _stage_prompt("title", rules.get(
        "title"), rows, var_keys=var_keys)
    j_title = _retry_stage(sys_prompt, up_title, field=None, validate_fn=lambda jt: (
        True, ""))  # validamos por string más abajo
    title_map = _coerce_titles_shape(j_title, var_keys)
    # validación simple por cada desktop/mobile
    for scope, pair in title_map.items():
        ok, msg = _validate_title(pair.get("desktop", ""))
        if not ok:
            # Reintento dirigido SOLO de title (si falla validación)
            up_title_fix = up_title + \
                f"\n\nNOTE: '{scope}.desktop' failed because: {msg}. Fix and return JSON again."
            j_t_fix = _chat_json(sys_prompt, up_title_fix)
            title_map = _coerce_titles_shape(j_t_fix, var_keys)
            break
    for scope, pair in title_map.items():
        if len(pair.get("desktop", "")) > 200:
            pair["desktop"] = pair["desktop"][:200].rstrip()
        if len(pair.get("mobile", "")) > 200:
            pair["mobile"] = pair["mobile"][:200].rstrip()

    # --- BULLETS (dinámico por variación; b1 cambia, b2–b5 igual al parent) ---
    up_bul = _stage_prompt("bullets", rules.get(
        "bullets"), rows, var_keys=var_keys)
    j_bul = _retry_stage(sys_prompt, up_bul, field=None, validate_fn=lambda jb: (
        True, ""))  # normalizamos y luego validamos
    bullets_map = _coerce_bullets_shape(j_bul, var_keys)

    # validación 150–180 y sin punto final (si falla, reintento 1 vez con nota)
    def _validate_scope_bul(scope_list):
        return _validate_bullets_list(scope_list)

    invalid_scopes = []
    for scope, items in bullets_map.items():
        ok, msg = _validate_scope_bul(items)
        if not ok:
            invalid_scopes.append((scope, msg))

    if invalid_scopes:
        # Pedimos corrección indicando el primero que falló (para reducir token)
        scope_name, why = invalid_scopes[0]
        up_bul_fix = up_bul + \
            f"\n\nNOTE: Bullets for scope '{scope_name}' failed because: {why}. Fix and return JSON again."
        j_bul_fix = _chat_json(sys_prompt, up_bul_fix)
        bullets_map = _coerce_bullets_shape(j_bul_fix, var_keys)

    # Ajuste final duro (no inventa contenido; sólo corta/padding fragment neutro)
    for scope, items in bullets_map.items():
        fixed = []
        for i, b in enumerate(items, 1):
            b = (b or "").rstrip(".")
            if len(b) < 150:
                pad = "; pensado para uso diario"
                while len(b) < 150 and len(b)+len(pad) <= 180:
                    b += pad
            if len(b) > 180:
                b = b[:180].rstrip()
            fixed.append(b)
        bullets_map[scope] = fixed

    # --- DESCRIPTION ---
    up_desc = _stage_prompt("description", rules.get("description"), rows)
    j_desc = _retry_stage(
        sys_prompt, up_desc, field="description", validate_fn=_validate_description)
    description = j_desc if isinstance(j_desc, str) else _parse_json_field(
        json.dumps(j_desc, ensure_ascii=False), "description", "")
    # recorte suave si aún excede
    ok_desc, msg_desc = _validate_description(description)
    if not ok_desc and description:
        words = description.replace("<br><br>", " ").split()
        if len(words) > 200:
            words = words[:200]
            mid = len(words)//2
            description = " ".join(words[:mid]) + \
                "<br><br>" + " ".join(words[mid:])
        if len(description) > 2000:
            description = description[:2000].rstrip()

    # --- BACKEND ---
    up_back = _stage_prompt("backend", rules.get("backend"), rows)
    j_back = _retry_stage(sys_prompt, up_back,
                          field="search_terms", validate_fn=_validate_backend)
    search_terms = j_back if isinstance(j_back, str) else _parse_json_field(
        json.dumps(j_back, ensure_ascii=False), "search_terms", "")

    return {
        "title": title_map,
        "bullets": bullets_map,
        "description": description or "",
        "search_terms": search_terms or "",
    }


# -------------------------------------------------------------
# Alias de compatibilidad (tu app aún importa este nombre)
# -------------------------------------------------------------
def lafuncionqueejecuta_listing_copywrite(inputs_df, use_ai=True, cost_saver=True, rules=None):
    return run_listing_copywrite(inputs_df, use_ai=use_ai, cost_saver=cost_saver, rules=rules)
