import streamlit as st
import pandas as pd

from listing.loader_listing_mercado import cargar_lemas_clusters


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

    # Atributos IA + Variaciones desde tabla editable
    if df_edit is not None and not df_edit.empty:
        for _, row in df_edit.iterrows():
            atributo = row.get("Atributo IA")
            if isinstance(atributo, str) and atributo.strip():
                atributo = atributo.strip()
                data.append({
                    "Tipo": "Atributo",
                    "Contenido": atributo,
                    "Etiqueta": "",
                    "Fuente": "IA"
                })
                for col in row.index:
                    if col.startswith("Valor") and pd.notna(row[col]):
                        variacion = str(row[col]).strip()
                        if variacion:
                            data.append({
                                "Tipo": "Variación",
                                "Contenido": variacion,
                                "Etiqueta": atributo,
                                "Fuente": "IA"
                            })

    df = pd.DataFrame(data)
    df = agregar_semantico_a_inputs(df)  # <- integración aquí
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


# >>> RD_FIX: helper robusto para tomar clusters desde session_state si el loader original no trae datos
def _cargar_lemas_clusters_robusto() -> pd.DataFrame:
    # Prioridad 1: alias expuesto por el bridge en Listing
    df = st.session_state.get("df_lemas_cluster")
    if isinstance(df, pd.DataFrame) and not df.empty:
        return df

    # Prioridad 2: artefacto nativo del módulo de Listing
    df = st.session_state.get("listing_clusters")
    if isinstance(df, pd.DataFrame) and not df.empty:
        return df

    return pd.DataFrame()
# <<< RD_FIX


def agregar_semantico_a_inputs(df: pd.DataFrame) -> pd.DataFrame:
    df_sem = cargar_lemas_clusters()
    if df_sem.empty:
        # >>> RD_FIX: fallback si el loader original no devolvió nada
        df_sem = _cargar_lemas_clusters_robusto()
        # <<< RD_FIX
        if df_sem.empty:
            return df

    # >>> RD_FIX: normalización defensiva
    if "token_lema" not in df_sem.columns:
        posibles = [c for c in df_sem.columns if c.lower() == "token"]
        df_sem = df_sem.copy()
        if posibles:
            df_sem["token_lema"] = df_sem[posibles[0]].astype(str)
        else:
            df_sem["token_lema"] = df_sem.iloc[:, 0].astype(str)

    if "cluster" not in df_sem.columns:
        df_sem = df_sem.copy()
        if "Cluster" in df_sem.columns:
            df_sem["cluster"] = df_sem["Cluster"]
        else:
            df_sem["cluster"] = "?"
    # <<< RD_FIX

    bloque = pd.DataFrame({
        "Tipo": "Token Semántico",
        "Contenido": df_sem["token_lema"].astype(str),
        "Etiqueta": "Cluster " + df_sem["cluster"].astype(str),
        "Fuente": "Clustering"
    }).drop_duplicates()

    return pd.concat([df, bloque], ignore_index=True)
