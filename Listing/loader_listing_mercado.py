import pandas as pd
import streamlit as st
import re


# ============================================================
#  Helpers
# ============================================================

def cargar_lemas_clusters() -> pd.DataFrame:
    """
    Devuelve la tabla de lemas/cluster desde sesión si existe.
    """
    df = st.session_state.get("df_lemas_cluster", None)
    if isinstance(df, pd.DataFrame) and not df.empty:
        return df
    return pd.DataFrame()


# ============================================================
#  Constructor de la tabla final
# ============================================================

def construir_inputs_listing(resultados: dict, df_edit: pd.DataFrame) -> pd.DataFrame:
    """
    Arma la tabla final (una sola) con:
      - Nombre sugerido
      - Descripción breve
      - Beneficios (1/fila)
      - Buyer persona
      - Pros / Cons
      - Emociones
      - Léxico editorial
      - Visual
      - Contraste (Atributo/Variación) con Etiqueta = valor de "Atributo Cliente"
      - Tokens semánticos (si hay clusters)
    """
    data = []

    # ------------------------------
    # Reviews básicos
    # ------------------------------
    if nombre := resultados.get("nombre_producto"):
        data.append({
            "Tipo": "Nombre sugerido",
            "Contenido": nombre.strip(),
            "Etiqueta": "",
            "Fuente": "Reviews"
        })

    if descripcion := resultados.get("descripcion"):
        data.append({
            "Tipo": "Descripción breve",
            "Contenido": descripcion.strip(),
            "Etiqueta": "",
            "Fuente": "Reviews"
        })

    for linea in str(resultados.get("beneficios", "")).split("\n"):
        linea = linea.strip("-• ").strip()
        if linea:
            data.append({
                "Tipo": "Beneficio",
                "Contenido": linea,
                "Etiqueta": "Positivo",
                "Fuente": "Reviews"
            })

    if persona := resultados.get("buyer_persona"):
        data.append({
            "Tipo": "Buyer persona",
            "Contenido": persona.strip(),
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

    for linea in str(resultados.get("emociones", "")).split("\n"):
        linea = linea.strip("-• ").strip()
        if linea:
            data.append({
                "Tipo": "Emoción",
                "Contenido": linea,
                "Etiqueta": "",
                "Fuente": "Reviews"
            })

    if lexico := resultados.get("lexico_editorial"):
        data.append({
            "Tipo": "Léxico editorial",
            "Contenido": lexico.strip(),
            "Etiqueta": "",
            "Fuente": "Reviews"
        })

    if visual := resultados.get("visuales"):
        data.append({
            "Tipo": "Visual",
            "Contenido": visual.strip(),
            "Etiqueta": "",
            "Fuente": "IA"
        })

    # ------------------------------
    # CONTRASTE (df_edit) — Etiqueta = valor de "Atributo Cliente"
    # ------------------------------
    if df_edit is not None and isinstance(df_edit, pd.DataFrame) and not df_edit.empty:
        # Detectar columnas Valor 1..4 de forma robusta (Valor/Value con o sin guión/bajo/espacio)
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
            # Etiqueta = valor en "Atributo Cliente" (si existe). Fallback: Atributo IA, luego literal.
            etiqueta_cliente = str(row.get("Atributo Cliente", "")).strip()
            if not etiqueta_cliente:
                etiqueta_cliente = str(
                    row.get("Atributo IA", "")).strip() or "Atributo Cliente"

            # Extraer valores no vacíos de Valor 1..4
            values = []
            for c in val_cols:
                v = str(row.get(c, "")).strip()
                if v and v.lower() not in ("nan", "none", "—", "-", "n/a", "na", ""):
                    values.append(v)

            # Determinar tipo (preferir columna 'Tipo' si viene)
            if has_tipo:
                t_raw = str(row.get("Tipo", "")).strip().lower()
                if "variac" in t_raw:    # 'variación' / 'variacion'
                    tipo = "Variación"
                elif "atribut" in t_raw:
                    tipo = "Atributo"
                else:
                    tipo = "Atributo" if len(values) == 1 else "Variación"
            else:
                tipo = "Atributo" if len(values) == 1 else "Variación"

            # Sin valores: si hay Atributo IA, al menos registrar como Atributo
            if not values:
                atributo_ia = str(row.get("Atributo IA", "")).strip()
                if atributo_ia:
                    data.append({
                        "Tipo": "Atributo",
                        "Contenido": atributo_ia,
                        "Etiqueta": etiqueta_cliente,
                        "Fuente": "Contraste"
                    })
                continue

            # Con valores:
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

    # Salida
    df = pd.DataFrame(data)
    return df.dropna(hoy="all") if hasattr(pd.DataFrame, "dropna") else df.dropna(how="all")


# ============================================================
#  Carga desde sesión (compat)
# ============================================================

def cargar_inputs_para_listing() -> pd.DataFrame:
    """
    Retorna la tabla final construida si existe en sesión.
    """
    df = st.session_state.get("inputs_para_listing", None)
    if isinstance(df, pd.DataFrame) and not df.empty:
        return df
    return pd.DataFrame()
