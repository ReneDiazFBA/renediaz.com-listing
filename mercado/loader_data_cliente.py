# mercado/loader_data_cliente.py

import pandas as pd
import streamlit as st


def cargar_data_cliente(excel_data: pd.ExcelFile) -> dict:
    """
    Carga y estructura la información del cliente desde la hoja 'DataCliente'.

    Returns:
        dict: {
            'asin_cliente': str,
            'asins_competidores': list[str],
            'atributos': list[dict],
            'preguntas_rufus': list[str]
        }
    """
    try:
        df = excel_data.parse("DataCliente", header=None)
    except Exception as e:
        st.error(f"Error al cargar hoja DataCliente: {e}")
        return {}

    # ASIN del cliente (fila 3, columna C)
    asin_cliente = str(df.iloc[2, 2]).strip()

    # ASINs competidores (fila 4, columna C), separados por coma
    asins_competidores = [
        x.strip() for x in str(df.iloc[3, 2]).split(",") if x.strip()
    ]

    # Atributos del producto: filas 12 a 24 (índices 11 a 23)
    atributos = []
    for i in range(11, 24):
        nombre = str(df.iloc[i, 1]).strip()
        relevante = str(df.iloc[i, 2]).strip().lower() == "sí"
        variacion = str(df.iloc[i, 3]).strip().lower() == "sí"

        if variacion:
            valores = [str(val).strip()
                       for val in df.iloc[i, 4:] if pd.notna(val)]
        else:
            valor = str(df.iloc[i, 4]).strip() if pd.notna(
                df.iloc[i, 4]) else ""
            valores = [valor] if valor else []

        if nombre:
            atributos.append({
                "nombre": nombre,
                "relevante": relevante,
                "variacion": variacion,
                "valores": valores
            })

    # Preguntas Rufus (fila 26 a 33, columna D → índice 3)
    preguntas_rufus = []
    for i in range(25, 33):
        val = df.iloc[i, 3]
        if pd.notna(val):
            preguntas_rufus.append(str(val).strip())

    return {
        "asin_cliente": asin_cliente,
        "asins_competidores": asins_competidores,
        "atributos": atributos,
        "preguntas_rufus": preguntas_rufus
    }
