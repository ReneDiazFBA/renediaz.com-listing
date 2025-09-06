# mercado/loader_inputs_listing.py — v4.2
# Marca: CustData!E12 directo
# Tokens semánticos: desde st.session_state["df_lemas_cluster"]

import streamlit as st
import pandas as pd
import re
import unicodedata
from typing import Dict, List, Optional, Any

VERSION_TAG = "loader_inputs_listing v4.2"

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
    return [linea.strip().strip("-• ").strip()
            for linea in str(text or "").split("\n") if linea.strip()]

def _split_pros_cons(text: str):
    pros, cons = [], []
    raw = str(text or "")
    if "PROS:" in raw.upper() or "CONS:" in raw.upper():
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
    for linea in raw.split("\n"):
        l = linea.strip()
        if l.startswith("[+]"):
            pos.append(l.replace("[+]", "").strip())
        elif l.startswith("[-]"):
            neg.append(l.replace("[-]", "").strip())
    return pos, neg

# ----------------------------
# Marca: CustData!E12 directo
# ----------------------------
# ------- reemplaza TODO este bloque en tu loader -------

def _get_brand_e12_y_debug():
    """
    Devuelve (valor_E12, debug_str) SIN limpiar.
    Intenta SOLO CustData!E12 pero maneja formatos comunes de excel_data.
    """
    excel = st.session_state.get("excel_data")
    dbg_parts = [f"type(excel_data)={type(excel).__name__}"]

    # Caso 1: dict de hojas -> DataFrame
    if isinstance(excel, dict):
        dbg_parts.append(f"keys={list(excel.keys())[:6]}")
        # exacto y variantes típicas de capitalización
        for k in ("CustData", "custdata", "Custdata"):
            if k in excel and isinstance(excel[k], pd.DataFrame):
                df = excel[k]
                dbg_parts.append(f"sheet={k} shape={df.shape}")
                try:
                    val = df.iloc[11, 4]  # E12
                    return val, " | ".join(dbg_parts + [f"E12={repr(val)}"])
                except Exception as e:
                    return f"ERROR_E12({e.__class__.__name__})", " | ".join(dbg_parts + [f"E12_ERROR={e}"])

        return "ERROR_SHEET(CustData no está en dict)", " | ".join(dbg_parts)

    # Caso 2: ExcelFile -> parse
    if hasattr(excel, "parse"):
        try:
            df = excel.parse("CustData")
            dbg_parts.append(f"sheet=CustData(shape={df.shape})")
            val = df.iloc[11, 4]
            return val, " | ".join(dbg_parts + [f"E12={repr(val)}"])
        except Exception as e:
            return f"ERROR_PARSE({e.__class__.__name__})", " | ".join(dbg_parts + [f"PARSE_ERROR={e}"])

    # Caso 3: ya es un DataFrame (se asume que es CustData)
    if isinstance(excel, pd.DataFrame):
        try:
            dbg_parts.append(f"sheet=DataFrame(shape={excel.shape})")
            val = excel.iloc[11, 4]
            return val, " | ".join(dbg_parts + [f"E12={repr(val)}"])
        except Exception as e:
            return f"ERROR_DF({e.__class__.__name__})", " | ".join(dbg_parts + [f"E12_ERROR={e}"])

    return "ERROR_FMT(excel_data)", " | ".join(dbg_parts)

def construir_inputs_listing(resultados: dict,
                             df_edit: pd.DataFrame,
                             excel_data: object = None) -> pd.DataFrame:
    data: List[Dict[str, str]] = []

    # 1) SIEMPRE: trae Marca y un DEBUG visible para saber QUÉ se leyó
    marca_val, marca_dbg = _get_brand_e12_y_debug()
    data.append({"Tipo": "Marca", "Contenido": str(marca_val), "Etiqueta": "", "Fuente": "Mercado"})
    # (Déjalo mientras verificas; cuando veas la marca, puedes borrar esta línea DEBUG)
    data.append({"Tipo": "DEBUG", "Contenido": marca_dbg, "Etiqueta": "", "Fuente": "CustData!E12"})

    # ------- deja el resto de tu lógica (reviews/contraste/tokens) tal y como la tienes -------
    # ... (todo lo demás igual) ...

    df = pd.DataFrame(data, columns=["Tipo", "Contenido", "Etiqueta", "Fuente"])
    df.reset_index(drop=True, inplace=True)
    return df
# ------- fin del bloque a reemplazar ------- 


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

    # --- Marca (siempre) ---
    marca = _get_brand_e12()
    data.append({"Tipo": "Marca", "Contenido": marca, "Etiqueta": "", "Fuente": "Mercado"})

    # --- Reviews ---
    if isinstance(resultados, dict):
        if (descripcion := resultados.get("descripcion")):
            data.append({"Tipo": "Descripción breve", "Contenido": str(descripcion).strip(),
                         "Etiqueta": "", "Fuente": "Reviews"})
        if (persona := resultados.get("buyer_persona")):
            data.append({"Tipo": "Buyer persona", "Contenido": str(persona).strip(),
                         "Etiqueta": "", "Fuente": "Reviews"})
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
        for e in _iter_lines(resultados.get("emociones", "")):
            etiqueta = "positive" if e.startswith("[+]") else "negative" if e.startswith("[-]") else ""
            e = e.replace("[+]", "").replace("[-]", "").strip()
            data.append({"Tipo": "Emoción", "Contenido": e, "Etiqueta": etiqueta, "Fuente": "Reviews"})
        if (lexico := resultados.get("lexico_editorial")):
            data.append({"Tipo": "Léxico editorial", "Contenido": str(lexico).strip(),
                         "Etiqueta": "", "Fuente": "Reviews"})
        if (visual := resultados.get("visuales")):
            data.append({"Tipo": "Visual", "Contenido": str(visual).strip(),
                         "Etiqueta": "", "Fuente": "IA"})
        tokens_raw = resultados.get("tokens", "")
        pos_toks, neg_toks = _split_tokens_pos_neg(tokens_raw)
        for t in pos_toks:
            data.append({"Tipo": "Token", "Contenido": t,
                         "Etiqueta": "Positive", "Fuente": "Reviews"})
        for t in neg_toks:
            data.append({"Tipo": "Token", "Contenido": t,
                         "Etiqueta": "Negative", "Fuente": "Reviews"})

    # --- Contraste ---
    if isinstance(df_edit, pd.DataFrame) and not df_edit.empty:
        val_cols = [c for c in df_edit.columns
                    if re.search(r"(valor|value)\s*[_\-]?[1-4]", str(c), flags=re.I)]
        val_cols = sorted(val_cols, key=lambda c: int(re.findall(r"[1-4]", str(c))[0]) if re.findall(r"[1-4]", str(c)) else 9)
        attr_col = _find_col(df_edit, ["atributo cliente", "atributo_cliente", "attribute client"])
        has_tipo = _find_col(df_edit, ["tipo"])
        for _, row in df_edit.iterrows():
            etiqueta_cliente = str(row.get(attr_col, "")).strip() if attr_col else ""
            if not etiqueta_cliente:
                continue
            values = [str(row.get(c, "")).strip() for c in val_cols if str(row.get(c, "")).strip()]
            if not values:
                continue
            if has_tipo:
                t_raw = str(row.get(has_tipo, "")).strip().lower()
                tipo = "Variación" if "variac" in t_raw else "Atributo" if "atribut" in t_raw else "Atributo" if len(values) == 1 else "Variación"
            else:
                tipo = "Atributo" if len(values) == 1 else "Variación"
            if tipo == "Atributo" and len(values) == 1:
                data.append({"Tipo": "Atributo", "Contenido": values[0],
                             "Etiqueta": etiqueta_cliente, "Fuente": "Contraste"})
            else:
                for v in values:
                    data.append({"Tipo": "Variación", "Contenido": v,
                                 "Etiqueta": etiqueta_cliente, "Fuente": "Contraste"})

    # --- Tokens semánticos ---
    df_semantic = cargar_lemas_clusters()
    if not df_semantic.empty:
        token_col = "token_lema" if "token_lema" in df_semantic.columns else df_semantic.columns[0]
        tier_col = "tier_origen" if "tier_origen" in df_semantic.columns else None
        cluster_col = "cluster" if "cluster" in df_semantic.columns else None
        df_tmp = df_semantic.copy()
        df_tmp[token_col] = df_tmp[token_col].astype(str).str.strip()
        df_tmp = df_tmp[df_tmp[token_col] != ""]
        core_df = df_tmp[df_tmp[tier_col].astype(str).str.contains(r"\bcore\b", case=False, na=False)] if tier_col else pd.DataFrame()
        if core_df.empty:
            core_df = df_tmp.drop_duplicates(subset=[token_col]).head(50)
        for t in core_df[token_col]:
            data.append({"Tipo": "Token Semántico (Core)", "Contenido": str(t).strip(),
                         "Etiqueta": "", "Fuente": "SemanticSEO"})
        if cluster_col:
            for _, r in df_tmp.iterrows():
                token = str(r.get(token_col, "")).strip()
                if token:
                    cl = r.get(cluster_col, "")
                    data.append({"Tipo": "Token Semántico (Cluster)", "Contenido": token,
                                 "Etiqueta": f"Cluster {cl}" if str(cl) else "", "Fuente": "SemanticSEO"})

    # --- Devolver siempre algo ---
    df = pd.DataFrame(data, columns=["Tipo", "Contenido", "Etiqueta", "Fuente"])
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
