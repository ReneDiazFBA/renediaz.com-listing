# mercado/loader_inputs_listing.py — v3.6
# Cambios: Marca estricta en CustData!E12; Core tokens SOLO desde df_lemas_cluster en sesión; sin "Nombre sugerido"

import streamlit as st
import pandas as pd
import re
import unicodedata
from typing import Dict, List, Optional, Tuple, Any

VERSION_TAG = "loader_inputs_listing v3.6"

# ----------------------------
# Helpers
# ----------------------------


def _norm(s: Any) -> str:
    if s is None:
        return ""
    s = str(s)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"\s+", " ", s.replace("\u00A0", " ")).strip().lower()
    return s


def _find_col(df: pd.DataFrame, targets: List[str]) -> Optional[str]:
    tset = {_norm(t) for t in targets}
    for c in df.columns:
        if _norm(c) in tset:
            return c
    return None


def _iter_lines(text: Any) -> List[str]:
    out = []
    for linea in str(text or "").split("\n"):
        l = linea.strip().strip("-• ").strip()
        if l:
            out.append(l)
    return out


def _split_pros_cons(text: str) -> Tuple[List[str], List[str]]:
    pros, cons = [], []
    raw = str(text or "")
    up = raw.upper()
    if "PROS:" in up or "CONS:" in up:
        pros_part = re.split(r"CONS\s*:", raw, flags=re.I)[0]
        pros_part = re.split(r"PROS\s*:", pros_part, flags=re.I)[-1]
        cons_part = ""
        cons_split = re.split(r"CONS\s*:", raw, flags=re.I)
        if len(cons_split) > 1:
            cons_part = cons_split[1]
        pros = _iter_lines(pros_part)
        cons = _iter_lines(cons_part)
    return pros, cons


def _split_tokens_pos_neg(text: str) -> Tuple[List[str], List[str]]:
    pos, neg = [], []
    raw = str(text or "")

    if re.search(r"positive\s*:", raw, flags=re.I) or re.search(r"negative\s*:", raw, flags=re.I):
        pos_block = re.split(r"negative\s*:", raw, flags=re.I)[0]
        pos_block = re.split(r"positive\s*:", pos_block, flags=re.I)[-1]
        neg_block = ""
        neg_split = re.split(r"negative\s*:", raw, flags=re.I)
        if len(neg_split) > 1:
            neg_block = neg_split[1]
        pos = _iter_lines(pos_block)
        neg = _iter_lines(neg_block)
        return pos, neg

    for linea in raw.split("\n"):
        l = linea.strip()
        if re.match(r"^\s*\[\+\]\s*", l):
            pos.append(re.sub(r"^\s*\[\+\]\s*", "", l).strip())
        elif re.match(r"^\s*\[\-\]\s*", l):
            neg.append(re.sub(r"^\s*\[\-\]\s*", "", l).strip())

    return pos, neg

# ----------------------------
# Marca: SOLO CustData!E12
# ----------------------------


def _get_brand_e12(excel_data: Any) -> str:
    """
    Lee exclusivamente CustData!E12 (fila 11, col 4 en base 0).
    No hay escaneos ni fallbacks. Si no existe, retorna "".
    """
    try:
        if isinstance(excel_data, dict) and "CustData" in excel_data:
            df = excel_data["CustData"]
            if isinstance(df, pd.DataFrame) and df.shape[0] > 11 and df.shape[1] > 4:
                val = str(df.iloc[11, 4]).strip()  # E12
                if val and _norm(val) not in ("nan", "none", ""):
                    return val
    except Exception:
        pass
    return ""

# ----------------------------
# Lemas/Clusters: SOLO desde sesión
# ----------------------------


def cargar_lemas_clusters() -> pd.DataFrame:
    """
    Usa exclusivamente st.session_state['df_lemas_cluster'],
    que proviene del módulo 'Lematización de tokens priorizados'.
    """
    df = st.session_state.get("df_lemas_cluster", None)
    if isinstance(df, pd.DataFrame) and not df.empty:
        return df
    return pd.DataFrame()

# ----------------------------
# Constructor principal
# ----------------------------


def construir_inputs_listing(resultados: dict,
                             df_edit: pd.DataFrame,
                             excel_data: object = None) -> pd.DataFrame:
    """
    Devuelve DataFrame con columnas: Tipo | Contenido | Etiqueta | Fuente
    Incluye:
      - Marca (CustData!E12)
      - Reviews (Descripción breve, Beneficios, Buyer, PROS, CONS, Emociones +/- , Léxico, Visuales)
      - Contraste (Etiqueta = valor real de 'Atributo Cliente'; Tipo Atributo/Variación)
      - Tokens (Positive/Negative si vienen en 'resultados')
      - Tokens semánticos (Core por tier_origen~'core'; Cluster si existe 'cluster') DESDE SESIÓN
    """
    try:
        st.session_state["loader_inputs_listing_version"] = VERSION_TAG
    except Exception:
        pass

    data: List[Dict[str, str]] = []

    # Marca (EXCLUSIVO CustData!E12)
    marca = _get_brand_e12(excel_data)
    if marca:
        data.append({"Tipo": "Marca", "Contenido": marca,
                    "Etiqueta": "", "Fuente": "Mercado"})

    # Reviews
    if isinstance(resultados, dict):
        if (descripcion := resultados.get("descripcion")):
            data.append({"Tipo": "Descripción breve", "Contenido": str(
                descripcion).strip(), "Etiqueta": "", "Fuente": "Reviews"})

        if (persona := resultados.get("buyer_persona")):
            data.append({"Tipo": "Buyer persona", "Contenido": str(
                persona).strip(), "Etiqueta": "", "Fuente": "Reviews"})

        for linea in _iter_lines(resultados.get("beneficios", "")):
            data.append({"Tipo": "Beneficio", "Contenido": linea,
                        "Etiqueta": "Positivo", "Fuente": "Reviews"})

        pros, cons = _split_pros_cons(str(resultados.get("pros_cons", "")))
        for linea in pros:
            data.append({"Tipo": "Beneficio", "Contenido": linea,
                        "Etiqueta": "PRO", "Fuente": "Reviews"})
        for linea in cons:
            data.append({"Tipo": "Obstáculo", "Contenido": linea,
                        "Etiqueta": "CON", "Fuente": "Reviews"})

        emos = _iter_lines(resultados.get("emociones", ""))
        for e in emos:
            etiqueta = ""
            if re.match(r"^\s*\[\+\]\s*", e):
                etiqueta = "positive"
                e = re.sub(r"^\s*\[\+\]\s*", "", e).strip()
            elif re.match(r"^\s*\[\-\]\s*", e):
                etiqueta = "negative"
                e = re.sub(r"^\s*\[\-\]\s*", "", e).strip()
            data.append({"Tipo": "Emoción", "Contenido": e,
                        "Etiqueta": etiqueta, "Fuente": "Reviews"})

        if (lexico := resultados.get("lexico_editorial")):
            data.append({"Tipo": "Léxico editorial", "Contenido": str(
                lexico).strip(), "Etiqueta": "", "Fuente": "Reviews"})

        if (visual := resultados.get("visuales")):
            data.append({"Tipo": "Visual", "Contenido": str(
                visual).strip(), "Etiqueta": "", "Fuente": "IA"})

        tokens_raw = resultados.get("tokens", "")
        pos_toks, neg_toks = _split_tokens_pos_neg(tokens_raw)
        for t in pos_toks:
            if t:
                data.append({"Tipo": "Token", "Contenido": t,
                            "Etiqueta": "Positive", "Fuente": "Reviews"})
        for t in neg_toks:
            if t:
                data.append({"Tipo": "Token", "Contenido": t,
                            "Etiqueta": "Negative", "Fuente": "Reviews"})

    # CONTRASTE (Etiqueta = valor real de 'Atributo Cliente')
    if isinstance(df_edit, pd.DataFrame) and not df_edit.empty:
        val_cols = []
        for c in df_edit.columns:
            if re.search(r"(?:^|[^A-Za-z])(valor|value)\s*[_\-]?\s*([1-4])(?:[^0-9]|$)", str(c), flags=re.I):
                val_cols.append(c)

        def _orden_val(cname: str) -> int:
            m = re.findall(r"[1-4]", str(cname))
            return int(m[0]) if m else 9

        val_cols = sorted(val_cols, key=_orden_val)
        attr_col = _find_col(
            df_edit, ["atributo cliente", "atributo_cliente", "attribute client"])
        has_tipo = _find_col(df_edit, ["tipo"])

        for _, row in df_edit.iterrows():
            etiqueta_cliente = str(row.get(attr_col, "")
                                   ).strip() if attr_col else ""
            if not etiqueta_cliente:
                continue

            values = []
            for c in val_cols:
                v = str(row.get(c, "")).strip()
                if v and _norm(v) not in ("nan", "none", "-", "—", "n/a", "na", ""):
                    values.append(v)
            if not values:
                continue

            if has_tipo:
                t_raw = str(row.get(has_tipo, "")).strip().lower()
                tipo = "Variación" if "variac" in t_raw else ("Atributo" if "atribut" in t_raw else (
                    "Atributo" if len(values) == 1 else "Variación"))
            else:
                tipo = "Atributo" if len(values) == 1 else "Variación"

            if tipo == "Atributo" and len(values) == 1:
                data.append(
                    {"Tipo": "Atributo", "Contenido": values[0], "Etiqueta": etiqueta_cliente, "Fuente": "Contraste"})
            else:
                for v in values:
                    data.append({"Tipo": "Variación", "Contenido": v,
                                "Etiqueta": etiqueta_cliente, "Fuente": "Contraste"})

    # Tokens semánticos (Core/Cluster) — SOLO desde sesión
    df_semantic = cargar_lemas_clusters()
    if isinstance(df_semantic, pd.DataFrame) and not df_semantic.empty:
        # columnas
        norm_cols = {c: _norm(c) for c in df_semantic.columns}

        def pick(names: List[str], contains: Optional[str] = None) -> Optional[str]:
            for wanted in names:
                for c, n in norm_cols.items():
                    if n == _norm(wanted):
                        return c
            if contains:
                for c, n in norm_cols.items():
                    if contains in n:
                        return c
            return None

        token_col = pick(["token_lema", "lema", "token", "lemma",
                         "token_normalizado", "keyword"]) or list(df_semantic.columns)[0]
        tier_col = pick(
            ["tier_origen", "tier", "tier origen"], contains="tier")
        cluster_col = pick(["cluster", "cluster_id"], contains="cluster")
        is_core_col = pick(["is_core"])
        freq_col = pick(["freq", "frecuencia"], contains="freq")
        score_col = pick(["score", "puntaje"], contains="score")

        df_tmp = df_semantic.copy()
        df_tmp[token_col] = df_tmp[token_col].astype(str).str.strip()
        df_tmp = df_tmp[df_tmp[token_col] != ""]

        # CORE: primero tier_origen ~ "core"
        core_df = pd.DataFrame()
        if tier_col:
            core_df = df_tmp[df_tmp[tier_col].astype(
                str).str.contains(r"\bcore\b", case=False, na=False)]
        if core_df.empty and is_core_col and (df_tmp[is_core_col] == True).any():
            core_df = df_tmp[df_tmp[is_core_col] == True]
        if core_df.empty and freq_col:
            core_df = df_tmp.sort_values(by=freq_col, ascending=False).head(50)
        if core_df.empty and score_col:
            core_df = df_tmp.sort_values(
                by=score_col, ascending=False).head(50)
        if core_df.empty:
            core_df = df_tmp.drop_duplicates(subset=[token_col]).head(50)

        seen = set()
        for t in core_df[token_col].astype(str):
            t = t.strip()
            if t and t not in seen:
                seen.add(t)
                data.append({"Tipo": "Token Semántico (Core)",
                            "Contenido": t, "Etiqueta": "", "Fuente": "SemanticSEO"})

        # CLUSTER (si existe columna)
        if cluster_col:
            for _, r in df_tmp.iterrows():
                token = str(r.get(token_col, "")).strip()
                if not token:
                    continue
                cl = r.get(cluster_col, "")
                data.append({"Tipo": "Token Semántico (Cluster)", "Contenido": token,
                            "Etiqueta": f"Cluster {cl}" if str(cl) != "" else "", "Fuente": "SemanticSEO"})

    # Post
    df = pd.DataFrame(
        data, columns=["Tipo", "Contenido", "Etiqueta", "Fuente"])
    if not df.empty:
        df.dropna(how="all", inplace=True)
        df = df[df["Contenido"].astype(str).str.strip() != ""]
        df.reset_index(drop=True, inplace=True)
    return df

# Compat


def cargar_inputs_para_listing() -> pd.DataFrame:
    df = st.session_state.get("inputs_para_listing", None)
    if isinstance(df, pd.DataFrame) and not df.empty:
        return df
    return pd.DataFrame()
