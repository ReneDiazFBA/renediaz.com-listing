# mercado/funcional_mercado_contraste.py

import pandas as pd
import streamlit as st
import re


def _is_value_col(name: str) -> int:
    """
    Devuelve índice 1..4 si el nombre parece 'Valor 1/2/3/4' (con o sin espacio, en ES o EN).
    Match: 'Valor 1', 'Valor1', 'VALUE 2', 'value_3', etc.
    """
    if not isinstance(name, str):
        return 0
    m = re.search(
        r"(?:^|[^A-Za-z])(valor|value)\s*_?\s*([1-4])(?:[^0-9]|$)", name, flags=re.I)
    return int(m.group(2)) if m else 0


def _clean_cell(x) -> str:
    s = str(x).strip()
    if s.lower() in ("", "nan", "none", "—", "-", "n/a", "na"):
        return ""
    return s


def _recompute_tipo(df: pd.DataFrame) -> pd.DataFrame:
    """
    Recalcula la columna 'Tipo' en función de cuántos 'Valor 1..4' NO vacíos tenga cada fila:
      - 0 valores => Tipo = "" (vacío)
      - 1 valor   => 'Atributo'
      - 2+ valores=> 'Variación'
    Se ejecuta SIEMPRE que el usuario edite algo (automático).
    """
    if df is None or df.empty:
        return df

    # Detectar columnas de valores dinámicamente y en orden
    val_cols = []
    for c in df.columns:
        idx = _is_value_col(c)
        if idx:
            val_cols.append((idx, c))
    val_cols.sort(key=lambda t: t[0])
    only_cols = [c for _, c in val_cols]

    # Si no hay columnas de valores, no tocamos 'Tipo'
    if not only_cols:
        df["Tipo"] = df.get("Tipo", "")
        return df

    def _count_vals(row) -> int:
        cnt = 0
        for c in only_cols:
            if _clean_cell(row.get(c, "")):
                cnt += 1
        return cnt

    df = df.copy()
    counts = df.apply(_count_vals, axis=1)
    df["Tipo"] = counts.map(lambda k: "Atributo" if k ==
                            1 else ("Variación" if k >= 2 else ""))
    return df


def comparar_atributos_mercado_cliente(excel_data: pd.ExcelFile, atributos_ia: list[str]) -> pd.DataFrame:
    """
    Crea tabla editable para comparar atributos IA vs cliente.
    - Incluye SIEMPRE columna 'Tipo' (auto) que decide Atributo/Variación según Valor 1..4.
    - Persiste ediciones en st.session_state["df_contraste_edit"] y se reusa al volver a entrar.
    - NO requiere botones: recalcula 'Tipo' automáticamente tras cada edición.
    """
    # 1) Si ya existe una edición previa persistida, úsala como base
    persisted = st.session_state.get("df_contraste_edit")
    if isinstance(persisted, pd.DataFrame) and not persisted.empty:
        # Recalcular 'Tipo' por si el usuario tocó valores y vuelve a la vista
        df_persist = _recompute_tipo(persisted)
        st.session_state["df_contraste_edit"] = df_persist.copy()
        return df_persist

    # 2) Construir base desde Excel (solo primera vez o si no hay persistido)
    try:
        df = excel_data.parse("CustData", skiprows=12, header=None)
    except Exception as e:
        st.error(f"Error al leer atributos del cliente desde CustData: {e}")
        return pd.DataFrame()

    # Solo filas 13 a 24 (después del skip, índices 0..11)
    df = df.iloc[:12]
    df = df.dropna(how="all")

    if df.shape[1] < 4:
        st.warning("No hay suficientes columnas en CustData.")
        return pd.DataFrame()

    # Ajustar nombres: hay una columna vacía inicial que ignoramos
    col_total = df.shape[1]
    columnas = ["_IGN", "Atributo", "Relevante", "Variacion"] + \
        [f"Valor_{i}" for i in range(1, col_total - 4 + 1)]
    df.columns = columnas

    # Filtrar Relevante = "si"
    df = df[df["Relevante"].astype(str).str.lower() == "si"].copy()
    df["Atributo"] = df["Atributo"].astype(str).str.strip()

    # Extraer lista de valores del cliente y renombrar a 'Valor 1..'
    valores_cliente = df[[
        c for c in df.columns if c.startswith("Valor_")]].copy()
    valores_cliente.columns = [
        c.replace("Valor_", "Valor ") for c in valores_cliente.columns]

    # Igualar filas con atributos IA/Cliente (relleno con "")
    atributos_cliente = df["Atributo"].tolist()
    total_filas = max(len(atributos_ia), len(atributos_cliente))
    data = {
        "Atributo IA": (atributos_ia + [""] * (total_filas - len(atributos_ia))) if isinstance(atributos_ia, list) else atributos_cliente + [""] * (total_filas - len(atributos_cliente)),
        "Atributo Cliente": atributos_cliente + [""] * (total_filas - len(atributos_cliente)),
    }
    for col in valores_cliente.columns:
        col_vals = valores_cliente[col].tolist()
        data[col] = col_vals + [""] * (total_filas - len(col_vals))

    df_editable = pd.DataFrame(data)

    # 3) Calcular 'Tipo' inicial y PERSISTIR como base
    df_editable = _recompute_tipo(df_editable)
    st.session_state["df_contraste_edit"] = df_editable.copy()
    return df_editable
