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

    # Ignorar filas vacías
    df = df.dropna(how="all")

    if df.shape[1] < 3:
        st.warning("No hay suficientes columnas en CustData.")
        return pd.DataFrame()

    col_total = df.shape[1]
    columnas = ["Atributo", "Relevante", "Variacion"] + \
        [f"Valor_{i}" for i in range(1, col_total - 3 + 1)]
    df.columns = columnas

    # Filtrar por Relevante = "si"
    df = df[df["Relevante"].astype(str).str.lower() == "si"]
    df["Atributo"] = df["Atributo"].astype(str).str.strip()

    # Construcción del DataFrame editable
    editable_rows = max(len(atributos_ia), len(df))

    data = {
        "Atributo IA": atributos_ia + [""] * (editable_rows - len(atributos_ia)),
        "Atributo Cliente": df["Atributo"].tolist() + [""] * (editable_rows - len(df)),
    }

    # Agregar columnas de valores del cliente (Valor_1, Valor_2, ...)
    for col in [c for c in df.columns if c.startswith("Valor_")]:
        data[col.replace("Valor_", "Valor ")] = df[col].tolist() + \
            [""] * (editable_rows - len(df))

    df_editable = pd.DataFrame(data)
    return df_editable
