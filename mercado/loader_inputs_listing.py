# mercado/loader_inputs_listing.py  — v3.2 (Etiqueta = valor real de "Atributo Cliente")

import streamlit as st
import pandas as pd
import re
import unicodedata
from typing import Dict, List, Optional, Tuple

# ------------------------------------------------------------
# Helpers de normalización y detección de columnas
# ------------------------------------------------------------
def _norm(s: str) -> str:
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
# Clusters (igual que antes)
# ------------------------------------------------------------
def cargar_lemas_clusters() -> pd.DataFrame:
    df = st.session_state.get("df_lemas_cluster", None)
    if isinstance(df, pd.DataFrame) and not df.empty:
        return df
    return pd.DataFrame()

# ------------------------------------------------------------
# Constructor principal
# ------------------------------------------------------------
def construir_inputs_listing(resultados: dict,
                             df_edit: pd.DataFrame,
                             excel_data: object = None) -> pd.DataFrame:
    """
    Tabla final con:
      - Reviews (Descripción, Beneficios, Buyer, Pros/Cons, Emociones, Léxico, Visual)
      - Contraste: Etiqueta = **valor de 'Atributo Cliente'** (no placeholder)
                   Tipo = usa 'Tipo' si existe; si no, 1 valor => Atributo; 2+ => Variación
                   Contenido = cada Valor 1..4 no vacío
      - Tokens semánticos (si existen)
    """
    data: List[Dict] = []

    # ------------------------------
    # Reviews
    # ------------------------------
    if isinstance(resultados, dict):
        if (nombre := resultados.get("nombre_producto")):
            data.append({"Tipo": "Nombre sugerido", "Contenido": str(nombre).strip(), "Etiqueta": "", "Fuente": "Reviews"})

        if (descripcion := resultados.get("descripcion")):
            data.append({"Tipo": "Descripción breve", "Contenido": str(descripcion).strip(), "Etiqueta": "", "Fuente": "Reviews"})

        for linea in str(resultados.get("beneficios", "")).split("\n"):
            linea = linea.strip("-• ").strip()
            if linea:
                data.append({"Tipo": "Beneficio", "Contenido": linea, "Etiqueta": "Positivo", "Fuente": "Reviews"})

        if (persona := resultados.get("buyer_persona")):
            data.append({"Tipo": "Buyer persona", "Contenido": str(persona).strip(), "Etiqueta": "", "Fuente": "Reviews"})

        pros_cons_raw = str(resultados.get("pros_cons", ""))
        if "PROS:" in pros_cons_raw.upper():
            secciones = pros_cons_raw.split("CONS:")
            pros = secciones[0].replace("PROS:", "").split("\n")
            cons = secciones[1].split("\n") if len(secciones) > 1 else []
            for linea in pros:
                linea = linea.strip("-• ").strip()
                if linea:
                    data.append({"Tipo": "Beneficio", "Contenido": linea, "Etiqueta": "PRO", "Fuente": "Reviews"})
            for linea in cons:
                linea = linea.strip("-• ").strip()
                if linea:
                    data.append({"Tipo": "Obstáculo", "Contenido": linea, "Etiqueta": "CON", "Fuente": "Reviews"})

        for linea in str(resultados.get("emociones", "")).split("\n"):
            linea = linea.strip("-• ").strip()
            if linea:
                data.append({"Tipo": "Emoción", "Contenido": linea, "Etiqueta": "", "Fuente": "Reviews"})

        if (lexico := resultados.get("lexico_editorial")):
            data.append({"Tipo": "Léxico editorial", "Contenido": str(lexico).strip(), "Etiqueta": "", "Fuente": "Reviews"})

        if (visual := resultados.get("visuales")):
            data.append({"Tipo": "Visual", "Contenido": str(visual).strip(), "Etiqueta": "", "Fuente": "IA"})

    # ------------------------------
    # CONTRASTE (Etiqueta = valor real de 'Atributo Cliente')
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
        attr_col = _find_col(df_edit, ["atributo cliente", "atributo_cliente", "attribute client"])
        has_tipo = _find_col(df_edit, ["tipo"])  # devuelve nombre real si existe

        for _, row in df_edit.iterrows():
            # Etiqueta: el valor de la celda en la columna de Atributo Cliente
            etiqueta_cliente = ""
            if attr_col:
                etiqueta_cliente = str(row.get(attr_col, "")).strip()

            # Si no hay etiqueta, no generamos filas de contraste
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

            # Determinar Tipo
            if has_tipo:
                t_raw = str(row.get(has_tipo, "")).strip().lower()
                tipo = "Variación" if "variac" in t_raw else ("Atributo" if "atribut" in t_raw else ("Atributo" if len(values) == 1 else "Variación"))
            else:
                tipo = "Atributo" if len(values) == 1 else "Variación"

            # Emitir filas
            if tipo == "Atributo" and len(values) == 1:
                data.append({
                    "Tipo": "Atributo",
                    "Contenido": values[0],
                    "Etiqueta": etiqueta_cliente,   # ← valor real
                    "Fuente": "Contraste"
                })
            else:
                for v in values:
                    data.append({
                        "Tipo": "Variación",
                        "Contenido": v,
                        "Etiqueta": etiqueta_cliente,  # ← valor real
                        "Fuente": "Contraste"
                    })

    # ------------------------------
    # Tokens semánticos
    # ------------------------------
    df_semantic = cargar_lemas_clusters()
    if not df_semantic.empty:
        token_col = "token_lema" if "token_lema" in df_semantic.columns else df_semantic.columns[0]
        for _, r in df_semantic.iterrows():
            token = str(r.get(token_col, "")).strip()
            cluster = r.get("cluster", "")
            if token:
                data.append({
                    "Tipo": "Token Semántico",
                    "Contenido": token,
                    "Etiqueta": f"Cluster {cluster}",
                    "Fuente": "SemanticSEO"
                })

    df = pd.DataFrame(data)
    if not df.empty:
        df.dropna(how="all", inplace=True)
    return df

# ------------------------------------------------------------
# Compat: devolver lo que haya en sesión (si lo usas así)
# ------------------------------------------------------------
def cargar_inputs_para_listing() -> pd.DataFrame:
    df = st.session_state.get("inputs_para_listing", None)
    if isinstance(df, pd.DataFrame) and not df.empty:
        return df
    return pd.DataFrame()
