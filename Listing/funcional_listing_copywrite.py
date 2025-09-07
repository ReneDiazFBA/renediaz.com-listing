# listing/funcional_listing_copywrite.py
# Extracts inputs from the consolidated table and calls OpenAI once to generate:
# Titles (desktop+mobile per variation), 5 bullets, description, backend (EN).
# Adds Quality & Compliance checks + optional auto-fixes.

import os
import re
import json
from typing import Dict, List, Tuple, Any
import pandas as pd

from listing.prompts_listing_copywrite import prompt_master_json_all

# ───────────── Projections from the unified table ─────────────


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

# ───────────── Utilities: compliance & auto-fix ─────────────


DISALLOWED_TITLE_CHARS = set("!$?_^¬¦{}")


def bytes_no_spaces(s: str) -> int:
    return len((s or "").replace(" ", "").encode("utf-8"))


def check_title_item(item: Dict[str, str]) -> List[str]:
    issues = []
    for k in ("variation", "desktop", "mobile"):
        if k not in item:
            issues.append(f"missing key '{k}'")
            return issues
    d, m = item["desktop"], item["mobile"]
    if len(d) < 150 or len(d) > 180:
        issues.append(f"desktop length {len(d)} outside 150–180")
    if len(m) < 75 or len(m) > 80:
        issues.append(f"mobile length {len(m)} outside 75–80")
    # disallowed chars
    if any(ch in DISALLOWED_TITLE_CHARS for ch in d):
        issues.append("desktop contains disallowed characters")
    if any(ch in DISALLOWED_TITLE_CHARS for ch in m):
        issues.append("mobile contains disallowed characters")
    # duplicate word > 2 times (rough check)

    def _dup_chk(txt: str) -> bool:
        words = re.findall(r"[A-Za-z0-9]+", txt.lower())
        counts = {}
        for w in words:
            counts[w] = counts.get(w, 0) + 1
            if counts[w] > 2:
                return True
        return False
    if _dup_chk(d):
        issues.append("desktop repeats a word more than twice")
    if _dup_chk(m):
        issues.append("mobile repeats a word more than twice")
    return issues


def truncate_to_limit(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    cut = text[:max_len]
    # try to cut at a safe boundary
    for sep in [" - ", ", ", " "]:
        idx = cut.rfind(sep)
        if idx >= 50:  # avoid chopping too early
            return cut[:idx].rstrip()
    return cut.rstrip()


HEADER_COLON_RE = re.compile(r"^[A-Z0-9\s\-&]+:\s")


def check_bullets(bullets: List[str]) -> List[str]:
    issues = []
    if not isinstance(bullets, list) or len(bullets) != 5:
        return ["must return exactly 5 bullets"]
    seen = set()
    for i, b in enumerate(bullets, 1):
        L = len(b or "")
        if L < 130 or L > 180:
            issues.append(f"bullet {i} length {L} outside 130–180")
        if not HEADER_COLON_RE.match(b or ""):
            issues.append(
                f"bullet {i} must start with ALL-CAPS HEADER followed by colon")
        # uniqueness (rough)
        norm = re.sub(r"\W+", " ", (b or "").lower()).strip()
        if norm in seen:
            issues.append(f"bullet {i} duplicates another bullet")
        seen.add(norm)
    return issues


def collect_surface_words(payload: Dict[str, Any]) -> set:
    text = []
    for t in payload.get("titles", []):
        text += [t.get("desktop", ""), t.get("mobile", "")]
    text += payload.get("bullets", [])
    text.append(payload.get("description", ""))
    bag = set(w for w in re.findall(r"[a-z0-9]+", " ".join(text).lower()))
    return bag


def trim_backend(backend: str, min_bytes: int = 243, max_bytes: int = 249) -> str:
    tokens = [t for t in (backend or "").split() if t]
    # collapse duplicates, keep order
    seen = set()
    dedup = []
    for t in tokens:
        if t.lower() not in seen:
            seen.add(t.lower())
            dedup.append(t)
    out = " ".join(dedup)
    # trim from the end while > max
    while bytes_no_spaces(out) > max_bytes and dedup:
        dedup.pop()  # drop last
        out = " ".join(dedup)
    return out


def scrub_backend_surface_overlap(backend: str, surface_words: set) -> str:
    tokens = [t for t in (backend or "").split() if t]
    kept = [t for t in tokens if t.lower() not in surface_words]
    return " ".join(kept) if kept else backend


def check_backend(backend: str) -> List[str]:
    issues = []
    b = bytes_no_spaces(backend)
    if b < 243 or b > 249:
        issues.append(f"backend bytes {b} (spaces removed) outside 243–249")
    # commas or html
    if "," in (backend or "") or "<" in (backend or "") or ">" in (backend or ""):
        issues.append(
            "backend must be space-separated tokens (no commas/HTML)")
    return issues


def compliance_report(payload: Dict[str, Any]) -> Dict[str, Any]:
    rep = {"titles": [], "bullets": [], "backend": []}
    for item in payload.get("titles", []):
        rep["titles"].append({
            "variation": item.get("variation", ""),
            "issues": check_title_item(item)
        })
    rep["bullets"] = check_bullets(payload.get("bullets", []))
    rep["backend"] = check_backend(payload.get("search_terms", ""))
    return rep


def apply_auto_fixes(payload: Dict[str, Any],
                     fix_titles: bool = True,
                     fix_backend: bool = True) -> Dict[str, Any]:
    data = json.loads(json.dumps(payload))  # deep copy

    if fix_titles:
        new_titles = []
        for t in data.get("titles", []):
            d = t.get("desktop", "")
            m = t.get("mobile", "")
            # Only trim if too long; if too short, keep (manual pass preferred)
            if len(d) > 180:
                d = truncate_to_limit(d, 180)
            if len(m) > 80:
                m = truncate_to_limit(m, 80)
            new_titles.append({**t, "desktop": d, "mobile": m})
        data["titles"] = new_titles

    if fix_backend:
        backend = data.get("search_terms", "")
        # remove tokens present in surface copy
        surface = collect_surface_words(data)
        backend = scrub_backend_surface_overlap(backend, surface)
        # trim to byte window
        backend = trim_backend(backend, 243, 249)
        data["search_terms"] = backend

    return data

# ───────────── OpenAI one-shot ─────────────


def generar_listing_completo_desde_df(inputs_df: pd.DataFrame, model: str = "gpt-4o-mini") -> Dict:
    if not isinstance(inputs_df, pd.DataFrame) or inputs_df.empty:
        raise ValueError(
            "inputs_df is empty. Build 'inputs_para_listing' first.")
    for col in ("Tipo", "Contenido", "Etiqueta", "Fuente"):
        if col not in inputs_df.columns:
            raise ValueError(f"Missing required column in inputs_df: {col}")

    brand = _brand(inputs_df)
    core = _core_tokens(inputs_df)
    attrs = _attributes(inputs_df)
    vars_ = _variations(inputs_df)
    bens = _benefits(inputs_df)
    cons = _obstacles(inputs_df)
    emos = _emotions(inputs_df)
    lexico = _lexicon(inputs_df)
    persona_vals = _pick(inputs_df, "Buyer persona")
    persona = persona_vals[0] if persona_vals else ""

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
            max_tokens=2200,
        )
        content = resp.choices[0].message.content
        data = json.loads(content)

        # minimal schema checks
        for k in ("titles", "bullets", "description", "search_terms"):
            if k not in data:
                raise ValueError(f"Missing key in AI response: {k}")
        if not isinstance(data["bullets"], list) or len(data["bullets"]) != 5:
            raise ValueError("AI must return exactly 5 bullets.")

        # attach compliance snapshot
        data["_compliance"] = compliance_report(data)
        return data

    except Exception as e:
        raise RuntimeError(f"OpenAI call failed: {e}")
