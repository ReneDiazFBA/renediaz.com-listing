# mercado/loader_inputs_listing.py  — v3.3
# Etiqueta = valor real de "Atributo Cliente"
import streamlit as st
import pandas as pd
import re
import unicodedata
from typing import Dict, List, Optional, Tuple, Any

# ------------------------------------------------------------
# Helpers de normalización y detección de columnas
# ------------------------------------------------------------


def _norm(s: Any) -> str:
    """Normaliza unicode, quita tildes, colapsa espacios y pasa a lower."""
    if s is None:
        return ""
    s = str(s)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"\s+", " ", s.replace("\u00A0", " ")).strip().lower()
    return s


def _find_col(df: pd.DataFrame, targets: List[str]) -> Optional[str]:
    """Devuelve el nombre REAL de la columna cuyo normalizado coincida con algún target."""
    tset = {_norm(t) for t in targets}
    for c in df.columns:
        if _norm(c) in tset:
            return c
    return None

# ------------------------------------------------------------
# Lectura robusta de Marca (CustData!B12) con fallback
# ------------------------------------------------------------


def _safe_get_custdata_brand(excel_data: Any) -> str:
    """
    Intenta leer la Marca desde la hoja 'CustData' celda B12.
    Fallbacks:
      - Busca fila con primera columna 'Marca' y devuelve la siguiente celda.
      - Busca una columna llamada 'Marca' y toma primera fila no vacía.
    """
    try:
        # Caso típico: excel_data es dict {sheet_name: DataFrame}
        if isinstance(excel_data, dict) and "CustData" in excel_data:
            df = excel_data["CustData"]
            if isinstance(df, pd.DataFrame) and not df.empty:
                # Intento directo B12 (iloc 11, 1)
                try:
                    val = df.iloc[11, 1]
                    s = str(val).strip()
                    if s and _norm(s) not in ("nan", "none", ""):
                        return s
                except Exception:
                    pass

                # Fallback 1: buscar fila con 'Marca' en primera col
                try:
                    first_col = df.columns[0]
                    mask = df[first_col].astype(
                        str).str.strip().str.lower() == "marca"
                    if mask.any():
                        row_idx = mask.idxmax()
                        # toma valor en la segunda columna si existe
                        if df.shape[1] > 1:
                            s = str(df.iloc[row_idx, 1]).strip()
                            if s and _norm(s) not in ("nan", "none", ""):
                                return s
                except Exception:
                    pass

                # Fallback 2: buscar una columna llamada 'Marca'
                try:
                    marca_col = _find_col(df, ["marca"])
                    if marca_col:
                        series = df[marca_col].astype(str)
                        for v in series:
                            s = str(v).strip()
                            if s and _norm(s) not in ("nan", "none", ""):
                                return s
                except Exception:
                    pass
    except Exception:
        pass
    return ""

# ------------------------------------------------------------
# Clusters (igual que antes)
# ------------------------------------------------------------


def cargar_lemas_clusters() -> pd.DataFrame:
    df = st.session_state.get("df_lemas_cluster", None)
    if isinstance(df, pd.DataFrame) and not df.empty:
        return df
    return pd.DataFrame()

# ------------------------------------------------------------
# Parsers de listas por líneas
# ------------------------------------------------------------


def _iter_lines(text: Any) -> List[str]:
    out = []
    for linea in str(text or "").split("\n"):
        l = linea.strip().strip("-• ").strip()
        if l:
            out.append(l)
    return out


def _split_pros_cons(text: str) -> Tuple[List[str], List[str]]:
    """Acepta formatos tipo bloque 'PROS:' ... 'CONS:' y bullets sueltos."""
    pros, cons = [], []
    raw = str(text or "")
    up = raw.upper()
    if "PROS:" in up or "CONS:" in up:
        # Partición tolerante
        # Buscamos el segmento después de PROS: y después de CONS:
        # Estructura típica: "PROS:\n- ...\nCONS:\n- ..."
        pros_part = re.split(r"CONS\s*:", raw, flags=re.I)[0]
        pros_part = re.split(r"PROS\s*:", pros_part, flags=re.I)[-1]
        cons_part = ""
        cons_split = re.split(r"CONS\s*:", raw, flags=re.I)
        if len(cons_split) > 1:
            cons_part = cons_split[1]
        pros = _iter_lines(pros_part)
        cons = _iter_lines(cons_part)
    else:
        # Sin etiquetas, no inferimos; dejamos vacío
        pass
    return pros, cons

# ------------------------------------------------------------
# Tokens positivos/negativos desde texto libre (opcional)
# ------------------------------------------------------------


def _split_tokens_pos_neg(text: str) -> Tuple[List[str], List[str]]:
    """
    Soporta varios formatos:
      - Encabezados: 'Positive:' ... 'Negative:'
      - Prefijos en líneas: [+] xxx  |  [-] yyy
    Si no detecta nada, devuelve listas vacías y no se emiten filas de Tokens +/-.
    """
    pos, neg = [], []
    raw = str(text or "")

    # Caso encabezados
    if re.search(r"positive\s*:", raw, flags=re.I) or re.search(r"negative\s*:", raw, flags=re.I):
        # Capturar bloques
        pos_block = re.split(r"negative\s*:", raw, flags=re.I)[0]
        pos_block = re.split(r"positive\s*:", pos_block, flags=re.I)[-1]
        neg_block = ""
        neg_split = re.split(r"negative\s*:", raw, flags=re.I)
        if len(neg_split) > 1:
            neg_block = neg_split[1]
        pos = _iter_lines(pos_block)
        neg = _iter_lines(neg_block)
        return pos, neg

    # Caso prefijos por línea
    for linea in raw.split("\n"):
        l = linea.strip()
        if re.match(r"^\s*\[\+\]\s*", l):
            pos.append(re.sub(r"^\s*\[\+\]\s*", "", l).strip())
        elif re.match(r"^\s*\[\-\]\s*", l):
            neg.append(re.sub(r"^\s*\[\-\]\s*", "", l).strip())

    return pos, neg

# ------------------------------------------------------------
# Constructor principal
# ------------------------------------------------------------


def construir_inputs_listing(resultados: dict,
                             df_edit: pd.DataFrame,
                             excel_data: object = None) -> pd.DataFrame:
    """
    Tabla final con filas de 4 columnas: Tipo | Contenido | Etiqueta | Fuente

    Incluye:
      - Marca (CustData!B12) → Tipo='Marca', Fuente='Mercado'
      - Reviews (Nombre, Descripción breve, Beneficios, Buyer, PROS, CONS, Emociones [+/-], Léxico, Visuales)
      - Contraste (Etiqueta = valor real de 'Atributo Cliente'; Tipo Atributo/Variación según reglas)
      - Tokens (si se proveen positivos/negativos en resultados)
      - Tokens semánticos core y por cluster desde df_lemas_cluster
    """
    data: List[Dict[str, str]] = []

    # ------------------------------
    # Marca (de Mercado)
    # ------------------------------
    marca = _safe_get_custdata_brand(excel_data)
    if marca:
        data.append({"Tipo": "Marca", "Contenido": marca,
                    "Etiqueta": "", "Fuente": "Mercado"})

    # ------------------------------
    # Reviews (resultados)
    # ------------------------------
    if isinstance(resultados, dict):
        # Nombre sugerido (si lo usas)
        if (nombre := resultados.get("nombre_producto")):
            data.append({"Tipo": "Nombre sugerido", "Contenido": str(
                nombre).strip(), "Etiqueta": "", "Fuente": "Reviews"})

        # Descripción breve
        if (descripcion := resultados.get("descripcion")):
            data.append({"Tipo": "Descripción breve", "Contenido": str(
                descripcion).strip(), "Etiqueta": "", "Fuente": "Reviews"})

        # Buyer persona
        if (persona := resultados.get("buyer_persona")):
            data.append({"Tipo": "Buyer persona", "Contenido": str(
                persona).strip(), "Etiqueta": "", "Fuente": "Reviews"})

        # Beneficios (neutro/positivo)
        for linea in _iter_lines(resultados.get("beneficios", "")):
            data.append({"Tipo": "Beneficio", "Contenido": linea,
                        "Etiqueta": "Positivo", "Fuente": "Reviews"})

        # PROS / CONS
        pros_cons_raw = str(resultados.get("pros_cons", ""))
        pros, cons = _split_pros_cons(pros_cons_raw)
        for linea in pros:
            data.append({"Tipo": "Beneficio", "Contenido": linea,
                        "Etiqueta": "PRO", "Fuente": "Reviews"})
        for linea in cons:
            data.append({"Tipo": "Obstáculo", "Contenido": linea,
                        "Etiqueta": "CON", "Fuente": "Reviews"})

        # Emociones (si marcadas con [+]/[-] se etiqueta positive/negative)
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

        # Léxico editorial (completo)
        if (lexico := resultados.get("lexico_editorial")):
            data.append({"Tipo": "Léxico editorial", "Contenido": str(
                lexico).strip(), "Etiqueta": "", "Fuente": "Reviews"})

        # Recomendaciones visuales
        if (visual := resultados.get("visuales")):
            data.append({"Tipo": "Visual", "Contenido": str(
                visual).strip(), "Etiqueta": "", "Fuente": "IA"})

        # Tokens positivos / negativos (si vienen agregados en un bloque)
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

    # ------------------------------
    # CONTRASTE (Etiqueta = valor real de 'Atributo Cliente')
    # (NO se cambia el formato de Atributo/Variación)
    # ------------------------------
    if isinstance(df_edit, pd.DataFrame) and not df_edit.empty:

        # Detectar columnas Valor 1..4 (robusto)
        val_cols = []
        for c in df_edit.columns:
            if re.search(r"(?:^|[^A-Za-z])(valor|value)\s*[_\-]?\s*([1-4])(?:[^0-9]|$)", str(c), flags=re.I):
                val_cols.append(c)

        def _orden_val(cname: str) -> int:
            m = re.findall(r"[1-4]", str(cname))
            return int(m[0]) if m else 9
        val_cols = sorted(val_cols, key=_orden_val)

        # Encontrar el nombre REAL de la columna "Atributo Cliente"
        attr_col = _find_col(
            df_edit, ["atributo cliente", "atributo_cliente", "attribute client"])
        # devuelve nombre real si existe
        has_tipo = _find_col(df_edit, ["tipo"])

        for _, row in df_edit.iterrows():
            etiqueta_cliente = ""
            if attr_col:
                etiqueta_cliente = str(row.get(attr_col, "")).strip()
            if not etiqueta_cliente:
                continue

            # Recolectar valores 1..4
            values = []
            for c in val_cols:
                v = str(row.get(c, "")).strip()
                if v and _norm(v) not in ("nan", "none", "-", "—", "n/a", "na", ""):
                    values.append(v)
            if not values:
                continue

            # Determinar Tipo (respeta tu comportamiento)
            if has_tipo:
                t_raw = str(row.get(has_tipo, "")).strip().lower()
                tipo = "Variación" if "variac" in t_raw else ("Atributo" if "atribut" in t_raw else (
                    "Atributo" if len(values) == 1 else "Variación"))
            else:
                tipo = "Atributo" if len(values) == 1 else "Variación"

            # Emitir filas (SIN CAMBIOS en formato)
            if tipo == "Atributo" and len(values) == 1:
                data.append({
                    "Tipo": "Atributo",
                    "Contenido": values[0],
                    "Etiqueta": etiqueta_cliente,
                    "Fuente": "Contraste"
                })
            else:
                for v in values:
                    data.append({
                        "Tipo": "Variación",
                        "Contenido": v,
                        "Etiqueta": etiqueta_cliente,
                        "Fuente": "Contraste"
                    })

    # ------------------------------
    # Tokens semánticos (core y cluster)
    # ------------------------------
    df_semantic = cargar_lemas_clusters()
    if isinstance(df_semantic, pd.DataFrame) and not df_semantic.empty:
        # Detección de columnas
        token_col = "token_lema" if "token_lema" in df_semantic.columns else df_semantic.columns[
            0]
        cluster_col = "cluster" if "cluster" in df_semantic.columns else None
        is_core_col = "is_core" if "is_core" in df_semantic.columns else None
        freq_col = "freq" if "freq" in df_semantic.columns else None
        score_col = "score" if "score" in df_semantic.columns else None

        # CORE: preferimos is_core=True; si no existe, top por freq/score; si no, primeros N únicos
        core_tokens: List[str] = []
        try:
            df_tmp = df_semantic.copy()
            df_tmp[token_col] = df_tmp[token_col].astype(str).str.strip()
            df_tmp = df_tmp[df_tmp[token_col] != ""]
            if is_core_col:
                core_tokens = df_tmp.loc[df_tmp[is_core_col] ==
                                         True, token_col].dropna().astype(str).tolist()
            elif freq_col in df_tmp.columns:
                core_tokens = df_tmp.sort_values(by=freq_col, ascending=False)[
                    token_col].head(50).tolist()
            elif score_col in df_tmp.columns:
                core_tokens = df_tmp.sort_values(by=score_col, ascending=False)[
                    token_col].head(50).tolist()
            else:
                core_tokens = df_tmp[token_col].drop_duplicates().head(
                    50).tolist()
        except Exception:
            pass

        for t in core_tokens:
            if t:
                data.append({
                    "Tipo": "Token Semántico (Core)",
                    "Contenido": t,
                    "Etiqueta": "",
                    "Fuente": "SemanticSEO"
                })

        # CLUSTER: si existe columna cluster, emitimos token→cluster
        if cluster_col:
            for _, r in df_semantic.iterrows():
                token = str(r.get(token_col, "")).strip()
                if not token:
                    continue
                cluster = r.get(cluster_col, "")
                data.append({
                    "Tipo": "Token Semántico (Cluster)",
                    "Contenido": token,
                    "Etiqueta": f"Cluster {cluster}" if str(cluster) != "" else "",
                    "Fuente": "SemanticSEO"
                })

    # ------------------------------
    # Post
    # ------------------------------
    df = pd.DataFrame(
        data, columns=["Tipo", "Contenido", "Etiqueta", "Fuente"])
    if not df.empty:
        df.dropna(how="all", inplace=True)
        # Limpia filas que quedaron con contenido vacío
        df = df[df["Contenido"].astype(str).str.strip() != ""]
        df.reset_index(drop=True, inplace=True)
    return df

# ------------------------------------------------------------
# Compat: devolver lo que haya en sesión (si lo usas así)
# ------------------------------------------------------------


def cargar_inputs_para_listing() -> pd.DataFrame:
    df = st.session_state.get("inputs_para_listing", None)
    if isinstance(df, pd.DataFrame) and not df.empty:
        return df
    return pd.DataFrame()
