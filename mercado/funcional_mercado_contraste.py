# mercado/funcional_mercado_contraste.py

import pandas as pd
import streamlit as st


def comparar_atributos_mercado_cliente(excel_data: pd.ExcelFile, atributos_mercado: list[str]) -> pd.DataFrame:
    """
    Compara los atributos detectados en los reviews con los que el cliente declara tener (CustData).
    Devuelve un DataFrame editable con columnas IA, atributo cliente y valores.
    """

    try:
        df = excel_data.parse("CustData", skiprows=12, header=None)
    except Exception as e:
        st.error(f"Error al leer atributos del cliente desde CustData: {e}")
        return pd.DataFrame()

    df = df.dropna(how="all")

    if df.shape[1] < 3:
        st.warning("No hay suficientes columnas en CustData.")
        return pd.DataFrame()

    # Renombrar columnas según cantidad real
    col_total = df.shape[1]
    columnas = ["Atributo", "Relevante", "Variacion"] + [f"Valor_{i}" for i in range(1, col_total - 3 + 1)]
    df.columns = columnas

    # Filtrar solo atributos relevantes
    df = df[df["Atributo"].notna()]
    df = df[df["Relevante"].astype(str).str.lower() == "si"]
    df["Atributo"] = df["Atributo"].astype(str).str.strip()

    # Crear tabla editable
    valores_cols = [col for col in df.columns if col.startswith("Valor_")]
    df_editable = pd.DataFrame()
    df_editable["Atributo IA (mercado)"] = atributos_mercado + [""] * max(0, len(df) - len(atributos_mercado))
    df_editable["Atributo Cliente"] = df["Atributo"].tolist() + [""] * max(0, len(atributos_mercado) - len(df))
    
    for i, col in enumerate(valores_cols):
        df_editable[f"Valor {i+1}"] = df[col].tolist() + [""] * max(0, len(atributos_mercado) - len(df))

    return df_editable