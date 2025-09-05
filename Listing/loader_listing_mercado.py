import pandas as pd
import streamlit as st


def cargar_lemas_clusters() -> pd.DataFrame:
    df = st.session_state.get("df_lemas_cluster", None)
    if isinstance(df, pd.DataFrame) and not df.empty:
        return df
    return pd.DataFrame()


def construir_inputs_listing(resultados: dict, df_edit: pd.DataFrame) -> pd.DataFrame:
    data = []

    # Nombre del producto
    if nombre := resultados.get("nombre_producto"):
        data.append({
            "Tipo": "Nombre sugerido",
            "Contenido": nombre.strip(),
            "Etiqueta": "",
            "Fuente": "Reviews"
        })

    # Descripción
    if descripcion := resultados.get("descripcion"):
        data.append({
            "Tipo": "Descripción breve",
            "Contenido": descripcion.strip(),
            "Etiqueta": "",
            "Fuente": "Reviews"
        })

    # Beneficios
    for linea in resultados.get("beneficios", "").split("\n"):
        linea = linea.strip("-• ").strip()
        if linea:
            data.append({
                "Tipo": "Beneficio",
                "Contenido": linea,
                "Etiqueta": "Positivo",
                "Fuente": "Reviews"
            })

    # Buyer persona
    if persona := resultados.get("buyer_persona"):
        data.append({
            "Tipo": "Buyer persona",
            "Contenido": persona.strip(),
            "Etiqueta": "",
            "Fuente": "Reviews"
        })

    # Pros / Cons
    pros_cons_raw = resultados.get("pros_cons", "")
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

    # Emociones
    for linea in resultados.get("emociones", "").split("\n"):
        linea = linea.strip("-• ").strip()
        if linea:
            data.append({
                "Tipo": "Emoción",
                "Contenido": linea,
                "Etiqueta": "",
                "Fuente": "Reviews"
            })

    # Léxico editorial
    if lexico := resultados.get("lexico_editorial"):
        data.append({
            "Tipo": "Léxico editorial",
            "Contenido": lexico.strip(),
            "Etiqueta": "",
            "Fuente": "Reviews"
        })

    # Visuales
    if visual := resultados.get("visuales"):
        data.append({
            "Tipo": "Visual",
            "Contenido": visual.strip(),
            "Etiqueta": "",
            "Fuente": "IA"
        })

    # ------------------------------
    # CONTRASTE (df_edit):
    # - Etiqueta = valor de "Atributo Cliente" (si existe; fallback "Atributo Cliente")
    # - Atributo IA (si existe) → Tipo="Atributo" con Etiqueta del cliente
    # - Para cada "Valor*" no vacío → Tipo="Variación" con Etiqueta del cliente
    # - Fuente = "Contraste"
    # ------------------------------
    if df_edit is not None and isinstance(df_edit, pd.DataFrame) and not df_edit.empty:
        for _, row in df_edit.iterrows():
            etiqueta_cliente = str(
                row.get("Atributo Cliente", "")).strip() or "Atributo Cliente"

            # 1) Atributo IA (si existe y tiene texto)
            atributo_ia = row.get("Atributo IA")
            if isinstance(atributo_ia, str) and atributo_ia.strip():
                data.append({
                    "Tipo": "Atributo",
                    "Contenido": atributo_ia.strip(),
                    "Etiqueta": etiqueta_cliente,   # 👈 ahora etiqueta es el valor del cliente
                    "Fuente": "Contraste"
                })

            # 2) Variaciones desde columnas Valor*
            for col in row.index:
                if str(col).lower().startswith("valor") and pd.notna(row[col]):
                    variacion = str(row[col]).strip()
                    if variacion:
                        data.append({
                            "Tipo": "Variación",
                            "Contenido": variacion,
                            "Etiqueta": etiqueta_cliente,  # 👈 etiqueta del cliente
                            "Fuente": "Contraste"
                        })

    # Agregar lemas con clusters semánticos
    df_semantic = cargar_lemas_clusters()
    if not df_semantic.empty:
        for _, row in df_semantic.iterrows():
            token = str(row.get("token_lema", "")).strip()
            cluster = row.get("cluster", "")
            if token:
                data.append({
                    "Tipo": "Token Semántico",
                    "Contenido": token,
                    "Etiqueta": f"Cluster {cluster}",
                    "Fuente": "SemanticSEO"
                })

    df = pd.DataFrame(data)
    return df.dropna(how="all")


def cargar_inputs_para_listing() -> pd.DataFrame:
    """
    Retorna la tabla final construida si existe en sesión.
    """
    df = st.session_state.get("inputs_para_listing", None)
    if isinstance(df, pd.DataFrame) and not df.empty:
        return df
    else:
        return pd.DataFrame()
