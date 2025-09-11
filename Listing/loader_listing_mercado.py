# mercado/loader_inputs_listing.py
import streamlit as st
import pandas as pd
import re
import unicodedata
from typing import Dict, List, Optional, Tuple


# ─────────────────────────────────────────────────────────
# Helpers generales
# ─────────────────────────────────────────────────────────
def cargar_lemas_clusters() -> pd.DataFrame:
    """
    Devuelve la tabla de lemas/cluster desde sesión si existe.
    """
    df = st.session_state.get("df_lemas_cluster", None)
    if isinstance(df, pd.DataFrame) and not df.empty:
        return df
    return pd.DataFrame()


def _norm_txt(s: str) -> str:
    """Normaliza texto: quita acentos/combining, baja a lower y colapsa espacios."""
    if not isinstance(s, str):
        s = "" if s is None else str(s)
    s = "".join(c for c in unicodedata.normalize(
        "NFKD", s) if not unicodedata.combining(c))
    s = re.sub(r"\s+", " ", s.strip().lower())
    return s


def _find_col_atributo_cliente(df: pd.DataFrame) -> Optional[str]:
    """
    Localiza la columna 'Atributo Cliente' de forma tolerante.
    Acepta variantes con/ sin acentos, espacios o guiones/underscores.
    """
    objetivos = {"atributo cliente", "atributo_cliente", "atributocliente"}
    for c in df.columns:
        n1 = _norm_txt(c)
        n2 = n1.replace("_", " ")
        n3 = n1.replace("_", "")
        if n1 in objetivos or n2 in objetivos or n3 in objetivos:
            return c
        # también acepta encabezados que empiecen por 'atributo cliente'
        if n2.startswith("atributo cliente"):
            return c
    return None


# ─────────────────────────────────────────────────────────
# Constructor de la tabla final
# ─────────────────────────────────────────────────────────
def construir_inputs_listing(resultados: dict,
                             df_edit: pd.DataFrame,
                             excel_data: object = None) -> pd.DataFrame:
    """
    Construye la tabla final con Reviews + Contraste + Semántico.
    En Contraste, la columna Etiqueta toma el VALOR REAL de 'Atributo Cliente'.
    Si la celda de 'Atributo Cliente' está vacía, NO se emite fila.
    """
    data = []

    # ------------------------------
    # Reviews
    # ------------------------------
    if isinstance(resultados, dict):
        if (nombre := resultados.get("nombre_producto")):
            data.append({
                "Tipo": "Nombre sugerido",
                "Contenido": str(nombre).strip(),
                "Etiqueta": "",
                "Fuente": "Reviews"
            })

        if (descripcion := resultados.get("descripcion")):
            data.append({
                "Tipo": "Descripción breve",
                "Contenido": str(descripcion).strip(),
                "Etiqueta": "",
                "Fuente": "Reviews"
            })

        beneficios = str(resultados.get("beneficios", "")).split("\n")
        for linea in beneficios:
            linea = linea.strip("-• ").strip()
            if linea:
                data.append({
                    "Tipo": "Beneficio",
                    "Contenido": linea,
                    "Etiqueta": "Positivo",
                    "Fuente": "Reviews"
                })

        if (persona := resultados.get("buyer_persona")):
            data.append({
                "Tipo": "Buyer persona",
                "Contenido": str(persona).strip(),
                "Etiqueta": "",
                "Fuente": "Reviews"
            })

        pros_cons_raw = str(resultados.get("pros_cons", ""))
        if "PROS:" in pros_cons_raw.upper():
            secciones = pros_cons_raw.split("CONS:")
            pros = secciones[0].replace("PROS:", "").split("\n")
            cons = secciones[1].split("\n") if len(secciones) > 1 else []
            for linea in pros:
                linea = linea.strip("-• ").strip()
                if linea:
                    data.append({
                        "Tipo": "Beneficio",
                        "Contenido": linea,
                        "Etiqueta": "PRO",
                        "Fuente": "Reviews"
                    })
            for linea in cons:
                linea = linea.strip("-• ").strip()
                if linea:
                    data.append({
                        "Tipo": "Obstáculo",
                        "Contenido": linea,
                        "Etiqueta": "CON",
                        "Fuente": "Reviews"
                    })

        emociones = str(resultados.get("emociones", "")).split("\n")
        for linea in emociones:
            linea = linea.strip("-• ").strip()
            if linea:
                data.append({
                    "Tipo": "Emoción",
                    "Contenido": linea,
                    "Etiqueta": "",
                    "Fuente": "Reviews"
                })

        if (lexico := resultados.get("lexico_editorial")):
            data.append({
                "Tipo": "Léxico editorial",
                "Contenido": str(lexico).strip(),
                "Etiqueta": "",
                "Fuente": "Reviews"
            })

        if (visual := resultados.get("visuales")):
            data.append({
                "Tipo": "Visual",
                "Contenido": str(visual).strip(),
                "Etiqueta": "",
                "Fuente": "IA"
            })

    # ------------------------------
    # CONTRASTE (Etiqueta = valor exacto de 'Atributo Cliente')
    # ------------------------------
    if df_edit is not None and isinstance(df_edit, pd.DataFrame) and not df_edit.empty:
        # localizar columna 'Atributo Cliente' robustamente
        col_attr_cliente = _find_col_atributo_cliente(df_edit)

        # detectar columnas Valor 1..4 de forma tolerante
        val_cols = []
        for c in df_edit.columns:
            if re.search(r"(?:^|[^A-Za-z])(valor|value)\s*[_\-]?\s*([1-4])(?:[^0-9]|$)", str(c), flags=re.I):
                val_cols.append(c)

        def _orden_val(cname: str) -> int:
            m = re.findall(r"[1-4]", str(cname))
            return int(m[0]) if m else 9

        val_cols = sorted(val_cols, key=_orden_val)
        has_tipo = "Tipo" in df_edit.columns

        for _, row in df_edit.iterrows():
            # si no encontramos la columna, no emitimos filas de contraste
            if not col_attr_cliente:
                continue

            etiqueta_cliente = str(row.get(col_attr_cliente, "")).strip()
            if not etiqueta_cliente:
                # sin etiqueta de cliente, no generamos filas
                continue

            # valores (Valor 1..4) no vacíos
            values = []
            for c in val_cols:
                v = str(row.get(c, "")).strip()
                if v and v.lower() not in ("nan", "none", "—", "-", "n/a", "na", ""):
                    values.append(v)

            if not values:
                continue

            # tipo (preferir columna 'Tipo' si existe)
            if has_tipo:
                t_raw = str(row.get("Tipo", "")).strip().lower()
                if "variac" in t_raw:   # variación/variacion
                    tipo = "Variación"
                elif "atribut" in t_raw:
                    tipo = "Atributo"
                else:
                    tipo = "Atributo" if len(values) == 1 else "Variación"
            else:
                tipo = "Atributo" if len(values) == 1 else "Variación"

            # emitir filas
            if tipo == "Atributo" and len(values) == 1:
                data.append({
                    "Tipo": "Atributo",
                    "Contenido": values[0],
                    "Etiqueta": etiqueta_cliente,   # ← valor REAL
                    "Fuente": "Contraste"
                })
            else:
                for v in values:
                    data.append({
                        "Tipo": "Variación",
                        "Contenido": v,
                        "Etiqueta": etiqueta_cliente,  # ← valor REAL
                        "Fuente": "Contraste"
                    })

    # ------------------------------
    # Tokens semánticos (clusters)
    # ------------------------------
    df_semantic = cargar_lemas_clusters()
    if not df_semantic.empty:
        token_col = "token_lema" if "token_lema" in df_semantic.columns else df_semantic.columns[
            0]
        for _, row in df_semantic.iterrows():
            token = str(row.get(token_col, "")).strip()
            cluster = row.get("cluster", "")
            if token:
                data.append({
                    "Tipo": "Token Semántico",
                    "Contenido": token,
                    "Etiqueta": f"Cluster {cluster}",
                    "Fuente": "SemanticSEO"
                })

    df = pd.DataFrame(data)
    if not df.empty:
        df.drop_duplicates(subset=[
                           "Tipo", "Contenido", "Etiqueta", "Fuente"], inplace=True, ignore_index=True)
        df.dropna(how="all", inplace=True)
    st.session_state["inputs_para_listing"] = df    
    return df


# ─────────────────────────────────────────────────────────
# Compat: carga desde sesión si ya existe
# ─────────────────────────────────────────────────────────
def cargar_inputs_para_listing() -> pd.DataFrame:
    df = st.session_state.get("inputs_para_listing", None)
    if isinstance(df, pd.DataFrame) and not df.empty:
        return df
    return pd.DataFrame()
