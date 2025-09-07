# listing/funcional_listing_copywrite.py
# Un solo flujo: lee la tabla final (st.session_state["inputs_para_listing"]), arma inputs, llama a IA con PROMPT_MASTER_JSON,
# hace validaciones y pequeñas correcciones (separadores, etiquetas, límites de longitud) y devuelve el dict final.

from listing.prompts_listing_copywrite import PROMPT_MASTER_JSON
import os
import re
import json
from typing import Dict, List, Tuple

import pandas as pd
import streamlit as st

# Cliente OpenAI compatible 0.x y 1.x


def _openai_chat(model: str, prompt: str) -> str:
    # Intenta OpenAI v1
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY",
                        st.secrets.get("OPENAI_API_KEY", "")))
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": "You are a precise, policy-compliant Amazon listing copywriter."},
                      {"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return resp.choices[0].message.content
    except Exception:
        pass
    # Fallback a v0.28
    import openai
    openai.api_key = os.getenv(
        "OPENAI_API_KEY", st.secrets.get("OPENAI_API_KEY", ""))
    resp = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "system", "content": "You are a precise, policy-compliant Amazon listing copywriter."},
                  {"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return resp["choices"][0]["message"]["content"]


# ─────────────────────────────────────────────────────────────────────────────
# Helpers para extraer / normalizar
# ─────────────────────────────────────────────────────────────────────────────
_ALLOWED_HYPHEN = "-"
_ALLOWED_COMMA = ","
_BLOCK_SEP = f" {_ALLOWED_HYPHEN} "


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def _val_only(x: str) -> str:
    """Elimina prefijos tipo 'color:', 'size:' si aparecieran."""
    s = _norm(x)
    s = re.sub(r"^\s*[A-Za-z]+\s*:\s*", "", s)
    s = re.sub(r"\b(color|size|talla|pack|cantidad)\b\s*:\s*",
               "", s, flags=re.I)
    return s.strip()


def _unique(seq: List[str]) -> List[str]:
    out, seen = [], set()
    for x in seq:
        k = x.lower().strip()
        if k and k not in seen:
            seen.add(k)
            out.append(x)
    return out


def _from_df(df: pd.DataFrame, tipo: str) -> List[str]:
    mask = df["Tipo"].astype(str).str.lower().eq(tipo.lower())
    return df.loc[mask, "Contenido"].astype(str).str.strip().tolist()


def _brand(df: pd.DataFrame) -> str:
    vals = _from_df(df, "Marca")
    return vals[0].strip() if vals else ""


def _brief_desc(df: pd.DataFrame) -> str:
    vals = _from_df(df, "Descripción breve")
    return vals[0].strip() if vals else ""


def _buyer_persona(df: pd.DataFrame) -> str:
    vals = _from_df(df, "Buyer persona")
    return vals[0].strip() if vals else ""


def _lexico(df: pd.DataFrame) -> str:
    vals = _from_df(df, "Léxico editorial")
    return vals[0].strip() if vals else ""


def _benefits(df: pd.DataFrame) -> List[str]:
    tipos = ["Beneficio", "Beneficio valorado", "Ventaja"]
    mask = df["Tipo"].astype(str).str.lower().isin([t.lower() for t in tipos])
    out = df.loc[mask, "Contenido"].astype(str).str.strip().tolist()
    return _unique([x for x in out if x])


def _emotions(df: pd.DataFrame) -> List[str]:
    mask = df["Tipo"].astype(str).str.lower().eq("emoción")
    out = df.loc[mask, "Contenido"].astype(str).str.strip().tolist()
    return _unique([x for x in out if x])


def _core_tokens(df: pd.DataFrame) -> List[str]:
    # Soporta "SEO semántico" (Etiqueta "Core") o "Token Semántico (Core)"
    mask1 = (df["Tipo"].astype(str).str.lower().eq("seo semántico")) & (
        df["Etiqueta"].astype(str).str.contains(
            r"\bcore\b", flags=re.I, regex=True)
    )
    mask2 = df["Tipo"].astype(str).str.lower().eq("token semántico (core)")
    out = pd.concat([df.loc[mask1, "Contenido"],
                    df.loc[mask2, "Contenido"]], ignore_index=True)
    vals = out.astype(str).str.strip().tolist()
    return _unique([x for x in vals if x])


def _variations(df: pd.DataFrame) -> List[str]:
    mask = df["Tipo"].astype(str).str.lower().eq("variación")
    vals = df.loc[mask, "Contenido"].astype(str).map(_val_only).tolist()
    return _unique([x for x in vals if x])


def _attributes(df: pd.DataFrame, variations: List[str]) -> List[str]:
    mask = df["Tipo"].astype(str).str.lower().eq("atributo")
    vals = df.loc[mask, "Contenido"].astype(str).map(_val_only).tolist()
    vals = [v for v in vals if v]
    # No duplicar valores que ya son variación
    var_l = {v.lower() for v in variations}
    vals = [v for v in vals if v.lower() not in var_l]
    return _unique(vals)

# Heurística simple: prioriza atributos mencionados dentro de beneficios


def _rank_attributes_by_benefits(attributes: List[str], benefits: List[str]) -> List[str]:
    scores = []
    benefit_blob = " ".join(benefits).lower()
    for a in attributes:
        cnt = benefit_blob.count(a.lower())
        scores.append((cnt, len(a), a))
    scores.sort(key=lambda t: (t[0], t[1]), reverse=True)
    return [a for _, __, a in scores]

# ─────────────────────────────────────────────────────────────────────────────
# Validadores / Correcciones
# ─────────────────────────────────────────────────────────────────────────────


def _clean_title_value_chunks(s: str) -> str:
    # quita etiquetas tipo "color:"; colapsa espacios; remueve símbolos prohibidos
    s = _val_only(s)
    s = re.sub(r"[!$?_\{\}\^¬¦]+", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _dedup_words_limit(title: str) -> str:
    # No permitir la misma palabra > 2 veces
    words = _norm(title).split()
    from collections import Counter
    c = Counter([w.lower() for w in words])
    banned = {w for w, n in c.items() if n > 2}
    if not banned:
        return title
    out_words = []
    counts = {}
    for w in words:
        wl = w.lower()
        if wl in banned:
            n = counts.get(wl, 0)
            if n >= 2:
                continue
            counts[wl] = n + 1
        out_words.append(w)
    return " ".join(out_words)


def _compose_title(brand: str, product_name: str, attrs: List[str], variation: str) -> str:
    brand = _clean_title_value_chunks(brand)
    product_name = _clean_title_value_chunks(product_name)
    attrs = [_clean_title_value_chunks(a) for a in attrs if a]
    variation = _clean_title_value_chunks(variation)

    # Ensamble con separadores pactados
    left = f"{brand} {product_name}".strip() if brand else product_name
    mid = (", ".join(attrs)).strip()
    if mid:
        full = f"{left}{_BLOCK_SEP}{mid}{_BLOCK_SEP}{variation}".strip()
    else:
        full = f"{left}{_BLOCK_SEP}{variation}".strip()

    full = _dedup_words_limit(full)
    full = re.sub(r"\s+,", ",", full)
    return full


def _fit_length_desktop(title: str) -> str:
    if len(title) <= 180:
        if len(title) < 150:
            # intentar añadir nada (no inventamos); lo dejamos y lo reportamos arriba en compliance
            return title
        return title
    # cortar desde el final, preferentemente después del último bloque
    while len(title) > 180:
        # intenta quitar el último atributo (si existen)
        parts = title.split(_BLOCK_SEP)
        if len(parts) >= 3 and "," in parts[1]:
            attrs = [a.strip() for a in parts[1].split(",")]
            if len(attrs) > 1:
                attrs = attrs[:-1]
                parts[1] = ", ".join(attrs)
                title = _BLOCK_SEP.join(parts).strip()
                continue
        # si no, recorta duro al último espacio
        title = title[:180].rstrip()
    return title


def _fit_length_mobile(title: str, product_name: str) -> str:
    # móvil 75–80; nunca recortar product_name
    if 75 <= len(title) <= 80:
        return title
    # intentamos encoger atributos
    parts = title.split(_BLOCK_SEP)
    if len(parts) >= 2:
        left = parts[0]  # brand + product_name
        mid = parts[1] if len(parts) == 3 else ""
        right = parts[2] if len(parts) == 3 else (
            parts[1] if len(parts) == 2 else "")
        # product_name protegido: si hace falta, reducimos attrs primero
        if mid:
            attrs = [a.strip() for a in mid.split(",")]
            while len(f"{left}{_BLOCK_SEP}{', '.join(attrs)}{_BLOCK_SEP}{right}") > 80 and len(attrs) > 0:
                attrs = attrs[:-1]
            candidate = f"{left}{_BLOCK_SEP}{', '.join(attrs)}{_BLOCK_SEP}{right}".strip(
            ) if attrs else f"{left}{_BLOCK_SEP}{right}".strip()
        else:
            candidate = title
        # ajuste final duro
        if len(candidate) > 80:
            candidate = candidate[:80].rstrip()
        # si quedó corto, no inventamos
        return candidate
    # fallback
    return title[:80].rstrip()


def _extract_product_name(core_tokens: List[str]) -> str:
    # nombre a partir de cores (orden natural, 2–5 tokens razonables)
    toks = [t for t in core_tokens if re.search(r"[A-Za-z0-9]", t or "")]
    if not toks:
        return "Product"
    # corta a 3–5 tokens
    return " ".join(toks[:5]).title()

# ─────────────────────────────────────────────────────────────────────────────
# API pública
# ─────────────────────────────────────────────────────────────────────────────


def compliance_report(result: Dict) -> Dict:
    """Pequeño chequeo de rangos y formato para mostrar en UI."""
    issues = []
    # Titles
    for t in result.get("titles", []):
        d, m = t.get("desktop", ""), t.get("mobile", "")
        if not (150 <= len(d) <= 180):
            issues.append(
                f'Desktop title len out of range ({len(d)}): {d[:60]}…')
        if not (75 <= len(m) <= 80):
            issues.append(
                f'Mobile title len out of range ({len(m)}): {m[:60]}…')
        if re.search(r"(color\s*:)", d, flags=re.I) or re.search(r"(color\s*:)", m, flags=re.I):
            issues.append("Title contains label like 'Color:'.")
    # Bullets
    bullets = result.get("bullets", []) or []
    if len(bullets) != 5:
        issues.append(f"Bullets count != 5 ({len(bullets)}).")
    for i, b in enumerate(bullets, 1):
        if not (130 <= len(b) <= 180):
            issues.append(f"Bullet {i} len out of range ({len(b)}).")
        if not re.match(r"^[A-Z0-9][A-Z0-9\s\-&/]+:\s", b):
            issues.append(
                f"Bullet {i} must start with ALL-CAPS HEADER and colon.")
    # Description
    desc = result.get("description", "")
    if not (1500 <= len(desc) <= 1800):
        issues.append(f"Description len out of range ({len(desc)}).")
    if "<br><br>" not in desc:
        issues.append(
            "Description must include paragraph breaks with <br><br>.")
    # Backend
    backend = result.get("search_terms", "")
    no_space_bytes = len(backend.replace(" ", "").encode("utf-8"))
    if not (243 <= no_space_bytes <= 249):
        issues.append(
            f"Backend bytes (no spaces) out of range: {no_space_bytes}.")
    if re.search(r"[A-Z]", backend):
        issues.append("Backend must be lowercase tokens.")
    if "," in backend or "." in backend or ";" in backend or ":" in backend:
        issues.append("Backend must not include punctuation.")
    return {"issues": issues}


def generate_listing_copy(inputs_df: pd.DataFrame, model: str = "gpt-4o-mini") -> Dict:
    if not isinstance(inputs_df, pd.DataFrame) or inputs_df.empty:
        raise ValueError("Empty inputs table.")

    # Asegura columnas
    for col in ("Tipo", "Contenido", "Etiqueta", "Fuente"):
        if col not in inputs_df.columns:
            inputs_df[col] = ""

    brand = _brand(inputs_df)
    brief = _brief_desc(inputs_df)
    buyer = _buyer_persona(inputs_df)
    lex = _lexico(inputs_df)
    variations = _variations(inputs_df)
    benefits = _benefits(inputs_df)
    emotions = _emotions(inputs_df)
    cores = _core_tokens(inputs_df)
    attrs_all = _attributes(inputs_df, variations)
    attrs_ranked = _rank_attributes_by_benefits(attrs_all, benefits)

    # Prompt maestro
    prompt = PROMPT_MASTER_JSON(
        brand=brand,
        brief_description=brief,
        core_tokens=cores,
        attributes=attrs_ranked,
        variations=variations,
        benefits=benefits,
        emotions=emotions,
        buyer_persona=buyer,
        lexico=lex,
    )

    raw = _openai_chat(model, prompt)
    try:
        data = json.loads(raw)
    except Exception:
        # intenta limpiar bloque triple backticks si viniera
        raw2 = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.S)
        data = json.loads(raw2)

    # ── Post-proceso títulos: construir nombre de producto a partir de cores y asegurar reglas
    product_name = _extract_product_name(cores)

    fixed_titles = []
    for v in variations if variations else [""]:
        v_clean = _clean_title_value_chunks(v)
        # Usa las 3–5 primeras attrs rankeadas (se podrán recortar por longitud)
        attrs_use = attrs_ranked[:5]
        desktop = _compose_title(brand, product_name, attrs_use, v_clean)
        desktop = _fit_length_desktop(desktop)
        # móvil a partir de desktop ajustando atributos
        mobile = _fit_length_mobile(desktop, product_name)
        fixed_titles.append({"variation": v_clean or "",
                            "desktop": desktop, "mobile": mobile})

    # Si IA también trajo titles, preferimos los fijos (reglas más duras)
    data["titles"] = fixed_titles

    # Asegura estructura mínima
    data.setdefault("bullets", [])
    data.setdefault("description", "")
    data.setdefault("search_terms", "")

    return data
