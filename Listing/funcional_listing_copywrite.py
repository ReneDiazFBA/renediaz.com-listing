# listing/funcional_listing_copywrite.py

import os
import re
import json
from typing import Dict, List, Any
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
    if any(ch in DISALLOWED_TITLE_CHARS for ch in d):
        issues.append("desktop contains disallowed characters")
    if any(ch in DISALLOWED_TITLE_CHARS for ch in m):
        issues.append("mobile contains disallowed characters")

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
    if "," in (backend or "") or "<" in (backend or "") or ">" in (backend or ""):
        issues.append(
            "backend must be space-separated tokens (no commas/HTML)")
    return issues


# >>> NEW: Description checker
BR_TAG = "<br><br>"
SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")


def _para_count(desc: str) -> int:
    return len([p for p in (desc or "").split(BR_TAG) if p.strip()])


def _ensure_multi_paragraph(desc: str) -> str:
    """If model returns a single block, split roughly every 3–5 sentences."""
    if BR_TAG in (desc or "") and _para_count(desc) >= 2:
        return desc
    sentences = SENT_SPLIT.split(desc or "")
    if len(sentences) <= 3:
        # try a middle split
        mid = max(1, len(sentences)//2)
        return BR_TAG.join([" ".join(sentences[:mid]).strip(), " ".join(sentences[mid:]).strip()])
    # group into ~4 paragraphs
    chunk = max(3, min(5, len(sentences)//4 or 3))
    paras = []
    for i in range(0, len(sentences), chunk):
        paras.append(" ".join(sentences[i:i+chunk]).strip())
    return BR_TAG.join([p for p in paras if p])


def _strip_forbidden_breaks(desc: str) -> str:
    # allow ONLY <br><br>
    t = re.sub(r"<br\s*/?>", "<br>", desc or "", flags=re.I)
    t = re.sub(r"(?:<br>){2,}", BR_TAG, t)
    t = re.sub(r"</?[^>]+>", "", t)            # remove other html tags
    t = t.replace("<br>", "")                  # collapse single <br>
    return t


def check_description(desc: str) -> List[str]:
    issues = []
    L = len(desc or "")
    if L < 1500 or L > 1800:
        issues.append(f"description length {L} outside 1500–1800")
    if BR_TAG not in (desc or "") or _para_count(desc) < 2:
        issues.append(
            "description must contain MULTIPLE paragraphs separated by <br><br>")
    # ensure only <br><br> is used
    if re.search(r"</?[a-zA-Z]+[^>]*>", (desc or "")) or "<br>" in (desc or ""):
        issues.append(
            "description must use only <br><br> (no other HTML or single <br>)")
    return issues


def compliance_report(payload: Dict[str, Any]) -> Dict[str, Any]:
    rep = {"titles": [], "bullets": [], "backend": [], "description": []}
    for item in payload.get("titles", []):
        rep["titles"].append({
            "variation": item.get("variation", ""),
            "issues": check_title_item(item)
        })
    rep["bullets"] = check_bullets(payload.get("bullets", []))
    rep["backend"] = check_backend(payload.get("search_terms", ""))
    rep["description"] = check_description(payload.get("description", ""))
    return rep


def truncate_to_limit(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    cut = text[:max_len]
    for sep in [" "+BR_TAG+" ", BR_TAG, " - ", ", ", " "]:
        idx = cut.rfind(sep)
        if idx >= 200:
            return cut[:idx].rstrip()
    return cut.rstrip()


def apply_auto_fixes(payload: Dict[str, Any],
                     fix_titles: bool = True,
                     fix_backend: bool = True,
                     fix_description: bool = True) -> Dict[str, Any]:
    data = json.loads(json.dumps(payload))  # deep copy

    # Titles
    if fix_titles:
        new_titles = []
        for t in data.get("titles", []):
            d = t.get("desktop", "")
            m = t.get("mobile", "")
            if len(d) > 180:
                d = truncate_to_limit(d, 180)
            if len(m) > 80:
                m = truncate_to_limit(m, 80)
            new_titles.append({**t, "desktop": d, "mobile": m})
        data["titles"] = new_titles

    # Backend
    if fix_backend:
        backend = data.get("search_terms", "")
        surface = collect_surface_words(data)
        backend = scrub_backend_surface_overlap(backend, surface)
        backend = trim_backend(backend, 243, 249)
        data["search_terms"] = backend

    # >>> Description
    if fix_description:
        desc = data.get("description", "") or ""
        # allow only <br><br>
        desc = _strip_forbidden_breaks(desc)
        # force multiple paragraphs
        desc = _ensure_multi_paragraph(desc)
        # trim upper bound
        if len(desc) > 1800:
            desc = truncate_to_limit(desc, 1800)
        data["description"] = desc

    # refresh compliance
    data["_compliance"] = compliance_report(data)
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

        # attach compliance snapshot (incluye description)
        data["_compliance"] = compliance_report(data)
        return data

    except Exception as e:
        raise RuntimeError(f"OpenAI call failed: {e}")
