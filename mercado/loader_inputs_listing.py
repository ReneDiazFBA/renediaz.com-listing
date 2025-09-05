import streamlit as st
import pandas as pd
import re
from typing import Dict, List, Optional, Tuple

# ------------------------------------------------------------
# Helper: obtener Excel (el mismo que ya cargas en st.session_state["excel_data"])
# ------------------------------------------------------------


def _get_excel() -> Optional[object]:
    excel = st.session_state.get("excel_data")
    if excel is None or not hasattr(excel, "parse"):
        return None
    return excel


def _leer_celda(excel, sheet: str, row0: int, col0: int) -> str:
    try:
        df = excel.parse(sheet, header=None)
        val = str(df.iloc[row0, col0]).strip()
        return "" if val.lower() == "nan" else val
    except Exception:
        return ""

# ------------------------------------------------------------
# Lee MARCA exactamente de CustData!B12 (B=col 1; 12 => row index 11)
# ------------------------------------------------------------


def _leer_marca_custdata_b12() -> str:
    excel = _get_excel()
    if not excel:
        return ""
    return _leer_celda(excel, "CustData", 11, 1)

# ------------------------------------------------------------
# Trae “resultados_mercado” (si existe) y df_edit (Contraste) desde sesión
# ------------------------------------------------------------


def _get_resultados_mercado() -> Dict:
    r = st.session_state.get("resultados_mercado", {})
    return r if isinstance(r, dict) else {}


def _get_df_edit_contraste() -> pd.DataFrame:
    # prioriza la versión persistida con Tipo
    df = st.session_state.get("df_contraste_edit")
    if isinstance(df, pd.DataFrame) and not df.empty:
        return df
    for key in ("df_edit", "df_edit_atributos"):
        df = st.session_state.get(key)
        if isinstance(df, pd.DataFrame) and not df.empty:
            return df
    return pd.DataFrame()

# ------------------------------------------------------------
# Trae clusters/lemmas desde sesión con nombres conocidos
# ------------------------------------------------------------


def _get_df_sem() -> pd.DataFrame:
    for key in ("df_lemas_cluster", "listing_clusters"):
        df = st.session_state.get(key)
        if isinstance(df, pd.DataFrame) and not df.empty:
            return df.copy()
    return pd.DataFrame()

# ------------------------------------------------------------
# Utilidades varias
# ------------------------------------------------------------


def _split_lines(blob: str) -> List[str]:
    if not blob:
        return []
    out = []
    for line in str(blob).split("\n"):
        s = line.strip().lstrip("-• ").strip()
        if s:
            out.append(s)
    return out


def _split_pros_cons(blob: str) -> Tuple[List[str], List[str]]:
    if not blob:
        return ([], [])
    txt = str(blob)
    parts = re.split(r"(?i)CONS\s*:", txt, maxsplit=1)
    pros_part = re.sub(r"(?i)PROS\s*:", "", parts[0])
    cons_part = parts[1] if len(parts) > 1 else ""
    return _split_lines(pros_part), _split_lines(cons_part)


def _extraer_seeds_core(df_sem: pd.DataFrame) -> List[str]:
    if df_sem.empty:
        return []
    # token column robusta
    token_col = None
    for c in df_sem.columns:
        if c.lower() in ("token_lema", "token", "lemma", "lema"):
            token_col = c
            break
    if token_col is None:
        token_col = df_sem.columns[0]

    core_mask = pd.Series([False] * len(df_sem))
    for c in df_sem.columns:
        try:
            core_mask = core_mask | df_sem[c].astype(
                str).str.contains(r"\bcore\b", case=False, regex=True)
        except Exception:
            pass

    return (
        df_sem.loc[core_mask, token_col]
        .dropna().astype(str).str.strip().unique().tolist()
    )

# ============================================================
# ===========  CONSTRUCTOR UNIFICADO (UNA SOLA TABLA)  =======
# ============================================================


def construir_inputs_listing(resultados: dict = None,
                             df_edit: pd.DataFrame = None,
                             excel_data: object = None) -> pd.DataFrame:
    """
    Construye UNA sola tabla final con todo lo que necesitas.
    - Marca (CustData!B12)
    - Reviews: Descripción breve, Beneficios (1/fila), Buyer persona,
               Pros (1/fila), Cons (1/fila),
               Emociones positivas/negativas (1/fila) o 'Emoción' fallback,
               Tokens diferenciadores (+)/(-) (1/fila) o genérico 'Token diferenciador'
    - Contraste Cliente: usa DIRECTO la columna 'Tipo' (Atributo/Variación) si viene en df_edit/df_contraste_edit,
                         desdoblando cada Valor 1..4 en filas (Contenido). Si no hay 'Tipo', decide por conteo.
    - Léxico editorial (texto)
    - Recomendaciones visuales (texto)
    - Semántico (Listing): Token semántico (cluster) y Seeds Core
    """
    filas = []

    # 1) Marca (B12)
    marca = _leer_marca_custdata_b12()
    if marca:
        filas.append({"Tipo": "Marca", "Contenido": marca,
                     "Etiqueta": "", "Fuente": "CustData"})

    # 2) Reviews (si existen)
    r = resultados if isinstance(
        resultados, dict) else _get_resultados_mercado()

    # Descripción breve
    if r.get("descripcion"):
        filas.append({"Tipo": "Descripción breve", "Contenido": str(
            r["descripcion"]).strip(), "Etiqueta": "", "Fuente": "Reviews"})

    # Beneficios (1/fila)
    for b in _split_lines(r.get("beneficios", "")):
        filas.append({"Tipo": "Beneficio", "Contenido": b,
                     "Etiqueta": "Valorado", "Fuente": "Reviews"})

    # Buyer persona
    if r.get("buyer_persona"):
        filas.append({"Tipo": "Buyer persona", "Contenido": str(
            r["buyer_persona"]).strip(), "Etiqueta": "", "Fuente": "Reviews"})

    # Pros / Cons (1/fila)
    pros, cons = _split_pros_cons(r.get("pros_cons", ""))
    for p in pros:
        filas.append({"Tipo": "Pro", "Contenido": p,
                     "Etiqueta": "PRO", "Fuente": "Reviews"})
    for c in cons:
        filas.append({"Tipo": "Con", "Contenido": c,
                     "Etiqueta": "CON", "Fuente": "Reviews"})

    # Emociones (+/-) o 'Emoción' fallback
    emos_pos = _split_lines(r.get("emociones_positivas", ""))
    emos_neg = _split_lines(r.get("emociones_negativas", ""))
    if emos_pos or emos_neg:
        for e in emos_pos:
            filas.append({"Tipo": "Emoción positiva", "Contenido": e,
                         "Etiqueta": "", "Fuente": "Reviews"})
        for e in emos_neg:
            filas.append({"Tipo": "Emoción negativa", "Contenido": e,
                         "Etiqueta": "", "Fuente": "Reviews"})
    else:
        for e in _split_lines(r.get("emociones", "")):
            filas.append({"Tipo": "Emoción", "Contenido": e,
                         "Etiqueta": "", "Fuente": "Reviews"})

    # Tokens diferenciadores (+/-) o genérico
    tok_pos = _split_lines(r.get("tokens_diferenciadores_positivos", ""))
    tok_neg = _split_lines(r.get("tokens_diferenciadores_negativos", ""))
    if tok_pos or tok_neg:
        for t in tok_pos:
            filas.append({"Tipo": "Token diferenciador (+)",
                         "Contenido": t, "Etiqueta": "", "Fuente": "Reviews"})
        for t in tok_neg:
            filas.append({"Tipo": "Token diferenciador (-)",
                         "Contenido": t, "Etiqueta": "", "Fuente": "Reviews"})
    else:
        for t in _split_lines(r.get("tokens_diferenciadores", "")):
            filas.append({"Tipo": "Token diferenciador",
                         "Contenido": t, "Etiqueta": "", "Fuente": "Reviews"})

    # 3) Contraste del cliente — usa 'Tipo' si viene; si no, decide por conteo
    dfe = df_edit if isinstance(
        df_edit, pd.DataFrame) else _get_df_edit_contraste()
    if isinstance(dfe, pd.DataFrame) and not dfe.empty:
        dfe_local = dfe.copy()

        # Detecta columnas Valor 1..4 de forma robusta
        val_cols = []
        for c in dfe_local.columns:
            if re.search(r"(?:^|[^A-Za-z])(valor|value)\s*_?\s*([1-4])(?:[^0-9]|$)", str(c), flags=re.I):
                val_cols.append(c)
        # Ordenar por índice numérico de valor si está presente

        def _orden_val(cname: str) -> int:
            m = re.findall(r"[1-4]", str(cname))
            return int(m[0]) if m else 9
        val_cols = sorted(val_cols, key=_orden_val)

        has_tipo = "Tipo" in dfe_local.columns

        for _, row in dfe_local.iterrows():
            # Extrae todos los valores no vacíos
            values = []
            for c in val_cols:
                v = str(row.get(c, "")).strip()
                if v and v.lower() not in ("nan", "none", "—", "-", "n/a", "na", ""):
                    values.append(v)
            if not values:
                continue

            if has_tipo:
                tipo = str(row.get("Tipo", "")).strip()
                tipo = "Variación" if tipo.lower() in ("variacion", "variación") else (
                    "Atributo" if tipo.lower() == "atributo" else "")
                if not tipo:
                    # fallback si el usuario borró Tipo
                    tipo = "Atributo" if len(values) == 1 else "Variación"
            else:
                # sin 'Tipo' en df_edit → decidir por conteo
                tipo = "Atributo" if len(values) == 1 else "Variación"

            for v in values:
                filas.append({
                    "Tipo": tipo,
                    "Contenido": v,
                    "Etiqueta": "Atributo Cliente",
                    "Fuente": "Contraste",
                })

    # 4) Léxico editorial
    if r.get("lexico_editorial"):
        filas.append({"Tipo": "Léxico editorial", "Contenido": str(
            r["lexico_editorial"]).strip(), "Etiqueta": "", "Fuente": "Reviews"})

    # 5) Recomendaciones visuales
    if r.get("visuales"):
        filas.append({"Tipo": "Recomendación visual", "Contenido": str(
            r["visuales"]).strip(), "Etiqueta": "", "Fuente": "Reviews"})

    # 6) Semántico (clusters + seeds core)
    df_sem = _get_df_sem()
    if not df_sem.empty:
        # token (robusto)
        token_col = None
        for c in df_sem.columns:
            if c.lower() in ("token_lema", "token", "lemma", "lema"):
                token_col = c
                break
        if token_col is None:
            token_col = df_sem.columns[0]
        # cluster (opcional)
        cluster_col = "cluster"
        if "cluster" not in df_sem.columns:
            cluster_col = None
            for c in df_sem.columns:
                if c.lower() == "cluster":
                    cluster_col = c
                    break

        # Tokens clusterizados (1/fila)
        for _, rsem in df_sem.iterrows():
            token_val = str(rsem.get(token_col, "")).strip()
            if not token_val:
                continue
            etiqueta = f"Cluster {rsem.get(cluster_col)}" if cluster_col else ""
            filas.append({
                "Tipo": "Token semántico",
                "Contenido": token_val,
                "Etiqueta": etiqueta,
                "Fuente": "Listing",
            })

        # Seeds core (1/fila)
        for s in _extraer_seeds_core(df_sem):
            filas.append({
                "Tipo": "Seed core",
                "Contenido": s,
                "Etiqueta": "lemma",
                "Fuente": "Listing",
            })

    # DataFrame final
    df = pd.DataFrame(filas)
    if not df.empty:
        df.drop_duplicates(subset=[
                           "Tipo", "Contenido", "Etiqueta", "Fuente"], inplace=True, ignore_index=True)
    return df

# ------------------------------------------------------------
# Compat: la vista Mercado → "Tabla final" puede llamar a esto
# ------------------------------------------------------------


def cargar_inputs_para_listing() -> pd.DataFrame:
    """
    Devuelve SIEMPRE la tabla unificada (no depende de que otra vista la haya guardado).
    """
    return construir_inputs_listing()
