# listing/funcional_listing_copywrite.py
# IA-only: genera Title + Bullets + Description + Backend con gpt-4o-mini
# Requiere: OPENAI_API_KEY en st.secrets o variable de entorno

import os
import json
import re
import pandas as pd
import streamlit as st

from listing.funcional_listing_datos import get_insumos_copywrite
from listing.prompts_listing_copywrite import prompt_master_json

# --- util: limpia cercas de código y trailing ---


def _strip_code_fences(txt: str) -> str:
    if not isinstance(txt, str):
        return txt
    # quita ```json ... ``` o ``` ... ```
    txt = re.sub(r"^```(?:json)?\s*", "", txt.strip(), flags=re.I)
    txt = re.sub(r"\s*```$", "", txt, flags=re.I)
    return txt.strip()


def _safe_json_loads(s: str) -> dict:
    s = _strip_code_fences(s)
    try:
        return json.loads(s)
    except Exception:
        # intenta recortar basura antes/después del primer/último brace
        m = re.search(r"\{.*\}\s*$", s, flags=re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
        raise


def _get_api_key() -> str:
    # prioridad a st.secrets
    try:
        k = st.secrets.get("OPENAI_API_KEY", "")
        if k:
            return k
    except Exception:
        pass
    return os.environ.get("OPENAI_API_KEY", "")


def lafuncionqueejecuta_listing_copywrite(
    inputs_df: pd.DataFrame,
) -> dict:
    """
    IA-only. Construye insumos desde la tabla maestra y llama a gpt-4o-mini.
    Devuelve dict con keys: title, bullets[5], description, search_terms.
    """
    if not isinstance(inputs_df, pd.DataFrame) or inputs_df.empty:
        raise ValueError("inputs_df está vacío.")

    api_key = _get_api_key()
    if not api_key:
        raise RuntimeError("Falta OPENAI_API_KEY (st.secrets o env).")

    # 1) Compactar insumos desde la tabla
    ins = get_insumos_copywrite(inputs_df)

    # 2) Prompt maestro (JSON-only)
    prompt = prompt_master_json(
        head_phrases=ins.get("head_phrases", []),
        core_tokens=ins.get("core_tokens", []),
        attributes=ins.get("attributes", []),
        variations=ins.get("variations", []),
        benefits=ins.get("benefits", []),
        emotions=ins.get("emotions", []),
        buyer_persona=ins.get("buyer_persona", ""),
        lexico=ins.get("lexico", ""),
    )

    # 3) Llamada a OpenAI (chat.completions con gpt-4o-mini)
    #    Nota: mantenemos simple y robusto
    from openai import OpenAI
    client = OpenAI(api_key=api_key)

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.6,
        messages=[
            {"role": "system", "content": "You are a meticulous Amazon listing copywriter that ONLY returns valid JSON as instructed."},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
    )

    content = resp.choices[0].message.content if resp.choices else ""
    data = _safe_json_loads(content)

    # 4) Validación mínima (sin fallback creativo)
    #    Si faltan campos críticos, lanzamos error (preferible a inventar)
    for k in ("title", "bullets", "description", "search_terms"):
        if k not in data:
            raise ValueError(f"Respuesta IA incompleta: falta '{k}'.")

    # Normaliza tipos
    if not isinstance(data["bullets"], list):
        raise ValueError("El campo 'bullets' debe ser una lista de 5 strings.")

    return {
        "title": str(data["title"]),
        "bullets": [str(x) for x in data["bullets"]][:5],
        "description": str(data["description"]),
        "search_terms": str(data["search_terms"]),
    }
