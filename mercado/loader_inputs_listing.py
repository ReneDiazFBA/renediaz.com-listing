# mercado/loader_inputs_listing.py

import streamlit as st
import pandas as pd
import re

from listing.loader_listing_mercado import cargar_lemas_clusters


# ---------- Helpers de acceso a Excel / marca ----------
def _get_excelfile_from_anywhere(excel_data_param):
    """
    Devuelve un pd.ExcelFile si existe en 'excel_data_param' o en st.session_state["excel_data"].
    Si no existe, retorna None sin romper flujo.
    """
    if excel_data_param is not None:
        return excel_data_param
    try:
        x = st.session_state.get("excel_data")
        return x if x is not None else None
    except Exception:
        return None


def _safe_get_brand_from_custdata(excel_data_param=None) -> str:
    """
    Lee la marca desde CustData!E12 (fila 12 base 1 => index 11, col E => index 4).
    Devuelve "" si no existe o hay error.
    """
    try:
        excel = _get_excelfile_from_anywhere(excel_data_param)
        if excel is None:
            return ""
        if not hasattr(excel, "parse"):
            return ""
        df = excel.parse("CustData", header=None)
        val = str(df.iloc[11, 4]).strip()
        if not val or val.lower() == "nan":
            return ""
        return val
    except Exception:
        return ""


# ---------- Robustez para clustering ya existente ----------
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


# ---------- Construcción principal ----------
def construir_inputs_listing(resultados: dict, df_edit: pd.DataFrame, excel_data: pd.ExcelFile = None) -> pd.DataFrame:
    """
    Construye la tabla final de inputs para el listing.
    - Quita 'Nombre sugerido' (si existía en resultados) y agrega fila de 'marca' desde CustData!E12.
    - Integra atributos/variaciones (df_edit).
    - Agrega tokens semánticos (clusters) y además seeds 'Core' (lemmas).
    """
    data = []

    # 1) MARCA (reemplaza 'Nombre sugerido')
    marca = _safe_get_brand_from_custdata(excel_data)
    if marca:
        data.append({
            "Tipo": "marca",
            "Contenido": marca,
            "Etiqueta": "",
            "Fuente": "Formulario"
        })

    # 2) Descripción breve (se mantiene)
    if descripcion := resultados.get("descripcion"):
        data.append({
            "Tipo": "Descripción breve",
            "Contenido": str(descripcion).strip(),
            "Etiqueta": "",
            "Fuente": "Reviews"
        })

    # 3) Beneficios
    for linea in str(resultados.get("beneficios", "")).split("\n"):
        linea = linea.strip("-• ").strip()
        if linea:
            data.append({
                "Tipo": "Beneficio",
                "Contenido": linea,
                "Etiqueta": "Positivo",
                "Fuente": "Reviews"
            })

    # 4) Buyer persona
    if persona := resultados.get("buyer_persona"):
        data.append({
            "Tipo": "Buyer persona",
            "Contenido": str(persona).strip(),
            "Etiqueta": "",
            "Fuente": "Reviews"
        })

    # 5) Pros / Cons → Beneficio / Obstáculo
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

    # 6) Emociones
    for linea in str(resultados.get("emociones", "")).split("\n"):
        linea = linea.strip("-• ").strip()
        if linea:
            data.append({
                "Tipo": "Emoción",
                "Contenido": linea,
                "Etiqueta": "",
                "Fuente": "Reviews"
            })

    # 7) Léxico editorial
    if lexico := resultados.get("lexico_editorial"):
        data.append({
            "Tipo": "Léxico editorial",
            "Contenido": str(lexico).strip(),
            "Etiqueta": "",
            "Fuente": "Reviews"
        })

    # 8) Visuales (brief)
    if visual := resultados.get("visuales"):
        data.append({
            "Tipo": "Visual",
            "Contenido": str(visual).strip(),
            "Etiqueta": "",
            "Fuente": "IA"
        })

    # 9) Atributos/Variaciones desde Contraste (df_edit)
    # Regla:
    # - Si SOLO hay Valor 1 (y está lleno):    Tipo=Atributo, Contenido=Valor 1, Etiqueta="Atributo Cliente", Fuente="Contraste"
    # - Si hay 2+ valores (entre Valor 1..4):  Tipo=Variación para CADA valor (incluye Valor 1), Etiqueta="Atributo Cliente", Fuente="Contraste"
    # - Si Valor 1 está vacío: se ignora el atributo por completo.
    if df_edit is not None and not df_edit.empty:
        for _, row in df_edit.iterrows():
            # Tomar valores no vacíos entre Valor 1..4
            vals = []
            for k in ("Valor 1", "Valor 2", "Valor 3", "Valor 4"):
                if k in row and pd.notna(row[k]):
                    sval = str(row[k]).strip()
                    if sval:
                        vals.append((k, sval))

            # Si Valor 1 está vacío o no existe, ignorar este atributo
            v1 = next((v for (k, v) in vals if k == "Valor 1"), "")
            if not v1:
                continue

            if len(vals) == 1:
                # SOLO Valor 1 → Atributo
                data.append({
                    "Tipo": "Atributo",
                    "Contenido": v1,
                    "Etiqueta": "Atributo Cliente",
                    "Fuente": "Contraste"
                })
            else:
                # 2 o más valores → TODAS como Variación (incluye Valor 1)
                for _, sval in vals:
                    data.append({
                        "Tipo": "Variación",
                        "Contenido": sval,
                        "Etiqueta": "Atributo Cliente",
                        "Fuente": "Contraste"
                    })

    # Construcción inicial del DF
    df = pd.DataFrame(data)
    df = agregar_semantico_a_inputs(df)  # tokens semánticos (clusters)
    df = agregar_core_seeds(df)          # seeds 'Core' (lemmas)
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


# ---------- Semántico: clustering base ----------
def agregar_semantico_a_inputs(df: pd.DataFrame) -> pd.DataFrame:
    df_sem = cargar_lemas_clusters()
    if df_sem.empty:
        df_sem = _cargar_lemas_clusters_robusto()
        if df_sem.empty:
            return df

    # Normalización defensiva
    df_sem = df_sem.copy()
    if "token_lema" not in df_sem.columns:
        posibles = [c for c in df_sem.columns if c.lower() in (
            "token", "lemma", "lema", "token_lema")]
        if posibles:
            df_sem["token_lema"] = df_sem[posibles[0]].astype(str)
        else:
            df_sem["token_lema"] = df_sem.iloc[:, 0].astype(str)

    if "cluster" not in df_sem.columns:
        if "Cluster" in df_sem.columns:
            df_sem["cluster"] = df_sem["Cluster"]
        else:
            df_sem["cluster"] = "?"

    bloque = pd.DataFrame({
        "Tipo": "Token Semántico",
        "Contenido": df_sem["token_lema"].astype(str),
        "Etiqueta": "Cluster " + df_sem["cluster"].astype(str),
        "Fuente": "Clustering"
    }).drop_duplicates()

    return pd.concat([df, bloque], ignore_index=True)


# ---------- Seeds desde lemmas 'Core' ----------
def agregar_core_seeds(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega filas 'seed' a partir de lemmas cuyo tier sea Core (robusto a distintos nombres de columna).
    - Tipo = 'seed'
    - Contenido = token_lema
    - Etiqueta = 'lemma'
    - Fuente = 'core'
    """
    df_sem = _cargar_lemas_clusters_robusto()
    if df_sem.empty:
        # intenta también desde el loader principal
        df_sem = cargar_lemas_clusters()
        if df_sem.empty:
            return df

    df_sem = df_sem.copy()

    # Columnas canónicas
    token_col = "token_lema"
    if token_col not in df_sem.columns:
        posibles = [c for c in df_sem.columns if c.lower() in (
            "token", "lemma", "lema", "token_lema")]
        token_col = posibles[0] if posibles else df_sem.columns[0]

    # Detectar 'Core' en alguna columna de tier
    core_mask = pd.Series([False] * len(df_sem))
    for col in df_sem.columns:
        if re.search(r"tier|origen|categoria|group|nivel", col, flags=re.I):
            core_mask = core_mask | df_sem[col].astype(
                str).str.contains(r"\bcore\b", case=False, regex=True)

    # Si no encontramos explícitamente, intenta por etiqueta/cluster que contenga 'core'
    if not core_mask.any():
        for col in df_sem.columns:
            core_mask = core_mask | df_sem[col].astype(
                str).str.contains(r"\bcore\b", case=False, regex=True)

    seeds = df_sem.loc[core_mask, token_col].dropna().astype(
        str).unique().tolist()
    if not seeds:
        return df

    bloque = pd.DataFrame({
        "Tipo": "seed",
        "Contenido": seeds,
        "Etiqueta": "lemma",
        "Fuente": "core"
    })

    # Evitar duplicados exactos (por si ya existían)
    df_out = pd.concat([df, bloque], ignore_index=True)
    df_out.drop_duplicates(
        subset=["Tipo", "Contenido", "Etiqueta", "Fuente"], inplace=True)
    return df_out
