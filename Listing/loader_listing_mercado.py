import pandas as pd
import streamlit as st
import re


# ============================================================
# Helpers
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
# Constructor de la tabla final
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
      - Contraste:
          * Etiqueta = valor de "Atributo Cliente" (estrictamente)
          * Tipo: usa columna "Tipo" si existe (Atributo/Variación); si no, 1 valor -> Atributo, 2+ -> Variación
          * Contenido = cada Valor 1..4 no vacío
          * Fuente = "Contraste"
      - Tokens semánticos (si hay clusters)
    """
    data = []

    # ------------------------------
    # Reviews básicos
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
    # CONTRASTE (df_edit) — Etiqueta = valor EXACTO de "Atributo Cliente"
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
            # Etiqueta = valor de "Atributo Cliente" (sin fallback)
            etiqueta_cliente = str(row.get("Atributo Cliente", "")).strip()
            if not etiqueta_cliente:
                # Si no hay Atributo Cliente, no generamos filas de contraste (evitamos literales)
                continue

            # Extraer valores no vacíos de Valor 1..4
            values = []
            for c in val_cols:
                v = str(row.get(c, "")).strip()
                if v and v.lower() not in ("nan", "none", "—", "-", "n/a", "na", ""):
                    values.append(v)

            if not values:
                # sin valores no generamos salida (regla estricta)
                continue

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

            # Emitir filas
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
    if not df.empty:
        df.dropna(how="all", inplace=True)
    return df


# ============================================================
# Carga desde sesión (compat)
# ============================================================

def cargar_inputs_para_listing() -> pd.DataFrame:
    """
    Retorna la tabla final construida si existe en sesión.
    """
    df = st.session_state.get("inputs_para_listing", None)
    if isinstance(df, pd.DataFrame) and not df.empty:
        return df
    return pd.DataFrame()
