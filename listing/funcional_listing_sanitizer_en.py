# listing/funcional_listing_sanitizer_en.py
# Amazon EN sanitizer: limpia promos/claims, símbolos, competidores; controla bytes y longitudes.
# Compatible Python 3.9+

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


def _limit_bytes(text: str, max_bytes: int) -> str:
    b = (text or "").encode("utf-8")
    if len(b) <= max_bytes:
        return text or ""
    cut = b[:max_bytes]
    while cut and (cut[-1] & 0xC0) == 0x80:
        cut = cut[:-1]
    return cut.decode("utf-8", errors="ignore")


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


def _words_set(text: str):
    return set(re.findall(r"[a-z0-9]+", (text or "").lower()))


def sanitize_title_en(title: str) -> str:
    t = _strip_html(title)
    t = _remove_forbidden(t)
    t = _sentence_case(t)
    return _limit_bytes(t, 200)


def sanitize_bullets_en(bullets: List[str]) -> List[str]:
    out = []
    for b in (bullets or [])[:5]:
        bb = _strip_html(b)
        bb = _remove_forbidden(bb)
        bb = _sentence_case(bb)
        bb = re.sub(r"\s+", " ", bb).strip()
        # **Requisito**: < 150 chars
        bb = bb[:150].rstrip()
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
    d = _limit_bytes(d, 2000)
    return d


def sanitize_backend_keywords_en(backend: str, already_used_text: str = "") -> str:
    b = _strip_html(backend)
    b = _remove_forbidden(b)
    used = _words_set(already_used_text)
    words = re.findall(r"[a-z0-9]+", b.lower())
    words = [w for w in words if w not in used]
    clean = " ".join(dict.fromkeys(words))
    return _limit_bytes(clean, 249)


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
