# listing/funcional_listing_sanitizer_en.py
# Amazon EN sanitizer. Enforces RD ranges and cleans content.
# Python 3.9+

import re
from typing import List, Dict

PROMO_TERMS = [
    r"\bfree\b", r"\bdiscount\b", r"\bsale\b", r"\bdeal\b", r"\boffer\b", r"\bpromotion\b",
    r"\bshipping\b", r"\bfast shipping\b", r"\bfree shipping\b", r"\b2\s*x\s*1\b", r"\bcoupon\b",
    r"\bclearance\b", r"\blowest price\b", r"\bcheapest\b", r"\bbest price\b", r"\btop deal\b",
    r"\bguaranteed\b", r"\blifetime guarantee\b", r"\bmoney[-\s]?back\b", r"\bfda\b"
]
SUBJECTIVE_CLAIMS = [
    r"\b#?1\b", r"\bnumber\s*1\b", r"\bno\.\s*1\b", r"\bbest\b", r"\btop seller\b",
    r"\bworld[-\s]?class\b", r"\bunbeatable\b", r"\bperfect\b", r"\bflawless\b"
]
COMPETITOR_CUES = [
    r"\bvs\b", r"\bbetter than\b", r"\bcompetes with\b", r"\bcompetitor(s)?\b", r"\bbeats\b"
]
FORBIDDEN_SYMBOLS = ["™", "®", "&", "@"]


def _strip_html(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&[a-z]+;", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _remove_forbidden(text: str) -> str:
    if not text:
        return ""
    t = text
    for s in FORBIDDEN_SYMBOLS:
        t = t.replace(s, " ")
    for patt in PROMO_TERMS + SUBJECTIVE_CLAIMS + COMPETITOR_CUES:
        t = re.sub(patt, "", t, flags=re.IGNORECASE)
    t = re.sub(r"\s*[\|\•·\u2022]\s*", " ", t)
    t = re.sub(r"\s+", " ", t).strip(" -–•|,.;:")
    return t


def _sentence_case(s: str) -> str:
    if not s:
        return ""
    s = s.strip()
    if re.fullmatch(r"[A-Z0-9\W]+", s):
        s = s.title()
    return s[:1].upper() + s[1:]


def _no_space_bytes_len(s: str) -> int:
    return len((s or "").replace(" ", "").encode("utf-8"))


def sanitize_title_en(title: str) -> str:
    t = _strip_html(title)
    t = _remove_forbidden(t)
    t = _sentence_case(t)
    # RD range: 150–200 chars. Enforced max here (min is goal, not hard).
    if len(t) > 200:
        t = t[:200].rstrip()
    return t


def sanitize_bullets_en(bullets: List[str]) -> List[str]:
    out = []
    for b in (bullets or [])[:5]:
        bb = _strip_html(b)
        bb = _remove_forbidden(bb)
        bb = _sentence_case(bb)
        bb = re.sub(r"\s+", " ", bb).strip()
        # RD range: 180–240 chars (enforce max; min is guidance)
        if len(bb) > 240:
            bb = bb[:240].rstrip()
        if bb and not re.search(r"[.!?]$", bb):
            bb += "."
        if bb:
            out.append(bb)
    while len(out) < 5:
        out.append("Thoughtful design focused on real-world use.")
    return out[:5]


def sanitize_description_en(desc: str) -> str:
    d = _strip_html(desc)
    d = _remove_forbidden(d)
    # RD range: 1600–2000 chars (enforce max; min es objetivo)
    if len(d) > 2000:
        d = d[:2000].rstrip()
    return d


def _trim_backend_no_space_limit(s: str, max_bytes: int) -> str:
    tokens = [t for t in re.split(r"\s+", s.strip()) if t]
    acc = []
    for tok in tokens:
        trial = (" ".join(acc + [tok])).strip()
        if _no_space_bytes_len(trial) <= max_bytes:
            acc.append(tok)
        else:
            break
    return " ".join(acc).strip()


def sanitize_backend_keywords_en(backend: str, already_used_text: str = "") -> str:
    # Clean, dedupe words, enforce max 249 BYTES (spaces not counted)
    b = _strip_html(backend)
    b = _remove_forbidden(b)

    # remove words present in surface copy
    used = set(re.findall(r"[a-z0-9]+", already_used_text.lower()))
    words = re.findall(r"[a-z0-9]+", b.lower())
    words = [w for w in words if w not in used]
    clean = " ".join(dict.fromkeys(words))  # dedupe preserving order

    # enforce max bytes ignoring spaces
    clean = _trim_backend_no_space_limit(clean, 249)
    return clean


def lafuncionqueejecuta_listing_sanitizer_en(draft: Dict[str, object]) -> Dict[str, object]:
    title = sanitize_title_en(str(draft.get("title", "")))
    bullets = sanitize_bullets_en(list(draft.get("bullets", []) or []))
    description = sanitize_description_en(str(draft.get("description", "")))
    already = " ".join([title] + bullets + [description])
    search_terms = sanitize_backend_keywords_en(
        str(draft.get("search_terms", "")), already_used_text=already)
    return {
        "title": title,
        "bullets": bullets,
        "description": description,
        "search_terms": search_terms
    }
