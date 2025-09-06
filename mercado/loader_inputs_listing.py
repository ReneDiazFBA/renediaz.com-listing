# mercado/loader_inputs_listing.py — v3.10
# Base: v3.9-fix (traer Marca de CustData!E12 con ExcelFile/dict/DF)
# Cambios:
# - Tipos: Beneficio valorado, Ventaja, SEO semántico
# - Emoción: etiqueta Positive/Negative (headers y [+]/[-])
# - Fuentes: solo Mercado / Keywords
# - Atributo/Variación -> Fuente: Mercado

import streamlit as st
import pandas as pd
import re
import unicodedata
from typing import Dict, List, Optional, Any

VERSION_TAG = "loader_inputs_listing v3.10"

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


def _split_pros_cons(text: str):
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


def _split_tokens_pos_neg(text: str):
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
# Marca: CustData!E12  (FIX: soporta ExcelFile / dict / DataFrame)
# ----------------------------


def _get_brand_e12() -> str:
    """
    Lee exactamente CustData!E12 (fila 11, col 4 0-based) desde:
    - st.session_state["excel_data"] como pd.ExcelFile (parse)
    - o como dict {sheet_name: DataFrame}
    - o como DataFrame ya correspondiente a CustData
    Devuelve el valor tal cual (string).
    """
    excel = st.session_state.get("excel_data")

    # Caso 1: ExcelFile -> parse hoja CustData (header=None para no depender de encabezados)
    if isinstance(excel, pd.ExcelFile):
        df = excel.parse("CustData", header=None)
        return str(df.iloc[11, 4])

    # Caso 2: dict de hojas -> DataFrame
    if isinstance(excel, dict):
        for k in ("CustData", "custdata", "Custdata"):
            if k in excel and isinstance(excel[k], pd.DataFrame):
                df = excel[k]
                return str(df.iloc[11, 4])
        return ""

    # Caso 3: ya es un DataFrame (se asume que es la hoja CustData)
    if isinstance(excel, pd.DataFrame):
        return str(excel.iloc[11, 4])

    # Formato inesperado
    return ""

# ----------------------------
# Tokens semánticos: SOLO desde sesión
# ----------------------------


def cargar_lemas_clusters() -> pd.DataFrame:
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
    st.session_state["loader_inputs_listing_version"] = VERSION_TAG
    data: List[Dict[str, str]] = []

    # Marca (Mercado)
    marca = _get_brand_e12()
    if marca:
        data.append({"Tipo": "Marca", "Contenido": marca,
                    "Etiqueta": "", "Fuente": "Mercado"})

    # Reviews -> Mercado / Keywords según tipo
    if isinstance(resultados, dict):
        # Descripción breve / Buyer persona (Mercado)
        if (descripcion := resultados.get("descripcion")):
            data.append({"Tipo": "Descripción breve", "Contenido": str(descripcion).strip(),
                         "Etiqueta": "", "Fuente": "Mercado"})
        if (persona := resultados.get("buyer_persona")):
            data.append({"Tipo": "Buyer persona", "Contenido": str(persona).strip(),
                         "Etiqueta": "", "Fuente": "Mercado"})

        # Beneficios valorados (Mercado)
        for linea in _iter_lines(resultados.get("beneficios", "")):
            data.append({"Tipo": "Beneficio valorado", "Contenido": linea,
                         "Etiqueta": "Positivo", "Fuente": "Mercado"})

        # PROS / CONS (Mercado) -> Ventaja / Obstáculo
        pros, cons = _split_pros_cons(str(resultados.get("pros_cons", "")))
        for linea in pros:
            data.append({"Tipo": "Ventaja", "Contenido": linea,
                         "Etiqueta": "PRO", "Fuente": "Mercado"})
        for linea in cons:
            data.append({"Tipo": "Obstáculo", "Contenido": linea,
                         "Etiqueta": "CON", "Fuente": "Mercado"})

        # --- Emociones (Mercado) con etiqueta Positive/Negative, ignorando headers) ---
        emociones_texto = str(resultados.get("emociones", ""))
        current_label = ""  # "Positive" o "Negative"

        pat_pos = re.compile(
            r'^\s*POSITIVE\s+EMOTION(S)?\s*:?\s*$', flags=re.I)
        pat_neg = re.compile(
            r'^\s*NEGATIVE\s+EMOTION(S)?\s*:?\s*$', flags=re.I)

        for raw in emociones_texto.split("\n"):
            l = raw.strip().strip("-• ").strip()
            if not l:
                continue

            # Detecta headers "POSITIVE EMOTION(S)" / "NEGATIVE EMOTION(S)" y NO los agrega
            if pat_pos.match(l):
                current_label = "Positive"
                continue
            if pat_neg.match(l):
                current_label = "Negative"
                continue

            # También soporta formato con prefijos [+] / [-]
            if l.startswith("[+]"):
                current_label = "Positive"
                l = l[3:].strip()
            elif l.startswith("[-]"):
                current_label = "Negative"
                l = l[3:].strip()

            # Agrega la emoción con la etiqueta vigente
            data.append({
                "Tipo": "Emoción",
                "Contenido": l,
                "Etiqueta": current_label,
                "Fuente": "Mercado",
            })

        # Léxico editorial (Keywords)
        if (lexico := resultados.get("lexico_editorial")):
            data.append({"Tipo": "Léxico editorial", "Contenido": str(lexico).strip(),
                         "Etiqueta": "", "Fuente": "Keywords"})

        # Tokens diferenciadores (+/-) (Keywords)
        tokens_raw = resultados.get("tokens", "")
        pos_toks, neg_toks = _split_tokens_pos_neg(tokens_raw)
        for t in pos_toks:
            if t:
                data.append({"Tipo": "Token", "Contenido": t,
                             "Etiqueta": "Positive", "Fuente": "Keywords"})
        for t in neg_toks:
            if t:
                data.append({"Tipo": "Token", "Contenido": t,
                             "Etiqueta": "Negative", "Fuente": "Keywords"})

    # Contraste (Mercado)
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
                data.append({"Tipo": "Atributo", "Contenido": values[0],
                             "Etiqueta": etiqueta_cliente, "Fuente": "Mercado"})
            else:
                for v in values:
                    data.append({"Tipo": "Variación", "Contenido": v,
                                 "Etiqueta": etiqueta_cliente, "Fuente": "Mercado"})

    # SEO semántico (Keywords)
    df_semantic = cargar_lemas_clusters()
    if isinstance(df_semantic, pd.DataFrame) and not df_semantic.empty:
        token_col = "token_lema" if "token_lema" in df_semantic.columns else df_semantic.columns[
            0]
        tier_col = "tier_origen" if "tier_origen" in df_semantic.columns else None
        cluster_col = "cluster" if "cluster" in df_semantic.columns else None

        df_tmp = df_semantic.copy()
        df_tmp[token_col] = df_tmp[token_col].astype(str).str.strip()
        df_tmp = df_tmp[df_tmp[token_col] != ""]

        # Core
        core_df = pd.DataFrame()
        if tier_col:
            core_df = df_tmp[df_tmp[tier_col].astype(
                str).str.contains(r"\bcore\b", case=False, na=False)]
        if core_df.empty:
            core_df = df_tmp.drop_duplicates(subset=[token_col]).head(50)
        seen = set()
        for t in core_df[token_col].astype(str):
            tok = t.strip()
            if tok and tok not in seen:
                seen.add(tok)
                data.append({"Tipo": "SEO semántico", "Contenido": tok,
                             "Etiqueta": "Core", "Fuente": "Keywords"})

        # Cluster
        if cluster_col:
            for _, r in df_tmp.iterrows():
                tok = str(r.get(token_col, "")).strip()
                if not tok:
                    continue
                cl = r.get(cluster_col, "")
                etiqueta = f"Cluster {cl}" if str(cl) != "" else "Cluster"
                data.append({"Tipo": "SEO semántico", "Contenido": tok,
                             "Etiqueta": etiqueta, "Fuente": "Keywords"})

    df = pd.DataFrame(
        data, columns=["Tipo", "Contenido", "Etiqueta", "Fuente"])
    if not df.empty:
        df.dropna(how="all", inplace=True)
        df = df[df["Contenido"].astype(str).str.strip() != ""]
        df.reset_index(drop=True, inplace=True)
    return df

# ----------------------------
# Compat
# ----------------------------


def cargar_inputs_para_listing() -> pd.DataFrame:
    df = st.session_state.get("inputs_para_listing", None)
    if isinstance(df, pd.DataFrame) and not df.empty:
        return df
    return pd.DataFrame()
