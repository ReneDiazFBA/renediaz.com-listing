# mercado/funcional_mercado_contraste.py

import pandas as pd
import streamlit as st


def comparar_atributos_mercado_cliente(excel_data: pd.ExcelFile, atributos_ia: list[str]) -> pd.DataFrame:
    """
    Crea tabla editable para comparar atributos IA vs cliente.
    Devuelve DataFrame editable con columnas: Atributo IA, Atributo Cliente, Valores del Cliente.
    """
    try:
        df = excel_data.parse("CustData", skiprows=12, header=None)
    except Exception as e:
        st.error(f"Error al leer atributos del cliente desde CustData: {e}")
        return pd.DataFrame()

    # Ignorar filas completamente vacías
    df = df.dropna(how="all")

    if df.shape[1] < 4:
        st.warning("No hay suficientes columnas en CustData.")
        return pd.DataFrame()

    # Ajustar nombres de columnas (hay una columna vacía al inicio que se ignora)
    col_total = df.shape[1]
    columnas = ["_IGN", "Atributo", "Relevante", "Variacion"] + \
        [f"Valor_{i}" for i in range(1, col_total - 4 + 1)]
    df.columns = columnas

    # Filtrar donde Relevante = "si"
    df = df[df["Relevante"].astype(str).str.lower() == "si"]
    df["Atributo"] = df["Atributo"].astype(str).str.strip()

    # Extraer los atributos y valores del cliente
    atributos_cliente = df["Atributo"].tolist()
    valores_cliente = df[[c for c in df.columns if c.startswith("Valor_")]].copy()
    valores_cliente.columns = [c.replace("Valor_", "Valor ") for c in valores_cliente.columns]

    # Igualar número de filas (máximo entre IA y cliente)
    total_filas = max(len(atributos_ia), len(atributos_cliente))

    data = {
        "Atributo IA": atributos_ia + [""] * (total_filas - len(atributos_ia)),
        "Atributo Cliente": atributos_cliente + [""] * (total_filas - len(atributos_cliente))
    }

    for col in valores_cliente.columns:
        data[col] = valores_cliente[col].tolist() + [""] * (total_filas - len(valores_cliente))

    df_editable = pd.DataFrame(data)
    return df_editable

