# listing/funcional_listing_datos.py
# Extrae insumos desde la tabla unificada "inputs_para_listing"
# para que cualquier módulo (p.ej., copywriting) consuma datos
# sin volver a parsear el DataFrame.
#
# Espera un DataFrame con columnas: ["Tipo", "Contenido", "Etiqueta", "Fuente"]
# (salida del loader v3.10).

from __future__ import annotations
import unicodedata
import re
from typing import Dict, List, Tuple
import pandas as pd


# ─────────────────────────────────────────────────────────────
# Normalización suave (para comparar Tipo/Etiqueta sin dramas)
# ─────────────────────────────────────────────────────────────
def _norm(s: str) -> str:
    if s is None:
        return ""
    s = str(s)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s


def _ensure_df(df: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(df, pd.DataFrame) or df.empty:
        return pd.DataFrame(columns=["Tipo", "Contenido", "Etiqueta", "Fuente"])
    out = df.copy()
    for c in ("Tipo", "Contenido", "Etiqueta", "Fuente"):
        if c not in out.columns:
            out[c] = ""
        out[c] = out[c].astype(str)
    return out


def _sel(df: pd.DataFrame, tipo_targets: List[str]) -> pd.DataFrame:
    tt = {_norm(t) for t in tipo_targets}
    m = df["Tipo"].map(_norm).isin(tt)
    return df.loc[m].copy()


def _unique_nonempty(series: pd.Series, max_items: int | None = None) -> List[str]:
    vals = []
    seen = set()
    for x in series.astype(str):
        v = x.strip()
        if not v:
            continue
        if v not in seen:
            seen.add(v)
            vals.append(v)
        if max_items and len(vals) >= max_items:
            break
    return vals


# ─────────────────────────────────────────────────────────────
# Extractores atómicos
# ─────────────────────────────────────────────────────────────
def get_brand(df: pd.DataFrame) -> str:
    df = _ensure_df(df)
    rows = _sel(df, ["marca"])
    return rows["Contenido"].astype(str).str.strip().replace("nan", "", case=False).head(1).tolist()[0] if not rows.empty else ""


def get_description_short(df: pd.DataFrame) -> str:
    df = _ensure_df(df)
    rows = _sel(df, ["descripción breve", "descripcion breve"])
    return rows["Contenido"].astype(str).str.strip().head(1).tolist()[0] if not rows.empty else ""


def get_buyer_persona(df: pd.DataFrame) -> str:
    df = _ensure_df(df)
    rows = _sel(df, ["buyer persona"])
    return rows["Contenido"].astype(str).str.strip().head(1).tolist()[0] if not rows.empty else ""


def get_lexico(df: pd.DataFrame) -> str:
    df = _ensure_df(df)
    rows = _sel(df, ["léxico editorial", "lexico editorial"])
    return rows["Contenido"].astype(str).str.strip().head(1).tolist()[0] if not rows.empty else ""


def get_attributes(df: pd.DataFrame, top_k: int | None = None) -> List[str]:
    df = _ensure_df(df)
    rows = _sel(df, ["atributo"])
    return _unique_nonempty(rows["Contenido"], max_items=top_k)


def get_variations(df: pd.DataFrame, top_k: int | None = None) -> List[str]:
    df = _ensure_df(df)
    rows = _sel(df, ["variación", "variacion"])
    return _unique_nonempty(rows["Contenido"], max_items=top_k)


def get_core_tokens(df: pd.DataFrame, top_k: int | None = 25) -> List[str]:
    """
    SEO semántico (Core): Tipo = 'SEO semántico' y Etiqueta contiene 'core'
    (case-insensitive). También soporta legado: 'Token Semántico (Core)'.
    """
    df = _ensure_df(df)
    # Nuevo formato
    m_new = (_norm(df["Tipo"]) == "seo semantico") & (
        df["Etiqueta"].str.contains(r"\bcore\b", case=False, na=False))
    # Legado
    m_old = _norm(df["Tipo"]).eq("token semantico (core)")
    rows = df.loc[m_new | m_old]
    toks = _unique_nonempty(rows["Contenido"], max_items=top_k)
    return toks


def get_benefits(df: pd.DataFrame, top_k: int | None = None) -> List[str]:
    """
    Beneficios: 'Beneficio valorado' + 'Ventaja'
    """
    df = _ensure_df(df)
    rows = _sel(df, ["beneficio valorado", "ventaja"])
    return _unique_nonempty(rows["Contenido"], max_items=top_k)


def get_obstacles(df: pd.DataFrame, top_k: int | None = None) -> List[str]:
    df = _ensure_df(df)
    rows = _sel(df, ["obstáculo", "obstaculo"])
    return _unique_nonempty(rows["Contenido"], max_items=top_k)


def get_emotions(df: pd.DataFrame, top_k_each: int | None = None) -> Tuple[List[str], List[str]]:
    """
    Emociones separadas por etiqueta Positive/Negative.
    Acepta que vengan sin etiqueta (se ignoran en este extractor).
    """
    df = _ensure_df(df)
    rows = _sel(df, ["emoción", "emocion"])
    pos = rows.loc[rows["Etiqueta"].str.contains(
        r"positive", case=False, na=False), "Contenido"]
    neg = rows.loc[rows["Etiqueta"].str.contains(
        r"negative", case=False, na=False), "Contenido"]
    return _unique_nonempty(pos, max_items=top_k_each), _unique_nonempty(neg, max_items=top_k_each)


def get_head_phrases(df: pd.DataFrame, max_items: int = 8) -> List[str]:
    """
    Frases cabeza útiles para IA (mezcla corta de marca/beneficios/tokens).
    Compacto y sin duplicados.
    """
    brand = get_brand(df)
    cores = get_core_tokens(df, top_k=6)
    bens = get_benefits(df, top_k=6)
    out: List[str] = []
    if brand:
        out.append(brand)
    out.extend(cores)
    out.extend(bens)
    # Limpieza rápida
    out = [re.sub(r"\s+", " ", s).strip() for s in out if s and s.strip()]
    # Únicos y tope
    seen, final = set(), []
    for s in out:
        if s.lower() in seen:
            continue
        seen.add(s.lower())
        final.append(s)
        if len(final) >= max_items:
            break
    return final


# ─────────────────────────────────────────────────────────────
# Paquete único de insumos para Copywriting (una llamada)
# ─────────────────────────────────────────────────────────────
def get_insumos_copywrite(df: pd.DataFrame) -> Dict:
    df = _ensure_df(df)
    emotions_pos, emotions_neg = get_emotions(df, top_k_each=12)
    insumos = {
        "brand": get_brand(df),
        "description_short": get_description_short(df),
        "buyer_persona": get_buyer_persona(df),
        "lexico": get_lexico(df),
        "attributes": get_attributes(df, top_k=15),
        "variations": get_variations(df, top_k=15),
        "core_tokens": get_core_tokens(df, top_k=30),
        "benefits": get_benefits(df, top_k=20),
        "obstacles": get_obstacles(df, top_k=15),
        "emotions_pos": emotions_pos,
        "emotions_neg": emotions_neg,
        "emotions": emotions_pos + emotions_neg,  # conveniencia para prompts
        "head_phrases": get_head_phrases(df, max_items=10),
    }
    return insumos
