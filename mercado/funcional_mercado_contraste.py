# mercado/funcional_mercado_contraste.py

import pandas as pd
import streamlit as st


def obtener_atributos_cliente(excel_data: pd.ExcelFile) -> pd.DataFrame:
    """
    Lee la hoja 'CustData' para obtener los atributos relevantes del cliente,
    incluyendo valores y variaciones si corresponde.
    """
    try:
        df = excel_data.parse("CustData", header=None)
    except Exception as e:
        st.error(f"Error al leer hoja 'CustData': {e}")
        return pd.DataFrame()

    try:
        df = df.iloc[12:, :]  # Fila 13 (índice 12) en adelante
        df.columns = ["Atributo", "Relevante", "Variacion"] + \
            [f"Valor_{i}" for i in range(1, df.shape[1] - 3 + 1)]
        df = df[df["Relevante"].str.upper() == "SI"]

        resultados = []
        for _, row in df.iterrows():
            atributo = str(row["Atributo"]).strip()
            es_variacion = str(row["Variacion"]).strip().upper() == "SI"

            valores = []
            # Tomar el valor base
            base = row.get("Valor_1", None)
            if pd.notna(base) and str(base).strip():
                valores.append(str(base).strip())

            # Si es variación, tomar también columnas adicionales
            if es_variacion:
                for i in range(2, df.shape[1] - 3 + 1):
                    val = row.get(f"Valor_{i}", None)
                    if pd.notna(val) and str(val).strip():
                        valores.append(str(val).strip())

            resultados.append({
                "atributo": atributo,
                "es_variacion": es_variacion,
                "valores": valores
            })

        return pd.DataFrame(resultados)

    except Exception as e:
        st.error(f"Error al procesar atributos del cliente: {e}")
        return pd.DataFrame()
