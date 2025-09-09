
# listing/funcional_listing_copywrite.py (placeholder for robust parsing)
import json, re

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
        if val is None:
            return fallback
        return val
    except Exception:
        return fallback
