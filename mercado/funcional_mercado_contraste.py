# mercado/funcional_mercado_contraste.py

import pandas as pd
import streamlit as st


def comparar_atributos_mercado_cliente(excel_data: pd.ExcelFile, atributos_mercado: list[str]) -> pd.DataFrame:
    """
    Compara los atributos detectados en los reviews con los que el cliente dice tener (CustData).
    """

    try:
        df = excel_data.parse("CustData", skiprows=12, header=None)
    except Exception as e:
        st.error(f"Error al leer atributos del cliente desde CustData: {e}")
        return pd.DataFrame()

    # Ignorar filas completamente vacías
    df = df.dropna(how="all")

    # Validar que hay al menos 3 columnas
    if df.shape[1] < 3:
        st.warning("No hay suficientes columnas en CustData.")
        return pd.DataFrame()

    # Asignar nombres a las columnas disponibles
    col_total = df.shape[1]
    df.columns = ["Atributo", "Relevante", "Variacion"] + \
        [f"Valor_{i}" for i in range(1, col_total - 3 + 1)]

    # Limpiar filas sin atributo
    df = df[df["Atributo"].notna()]
    df = df[df["Relevante"].notna()]

    # Convertir a string por seguridad
    df["Atributo"] = df["Atributo"].astype(str)
    df["Relevante"] = df["Relevante"].astype(str)
    df["Variacion"] = df["Variacion"].astype(str)

    # Separar listas
    atributos_cliente = df["Atributo"].str.strip().str.lower().tolist()
    atributos_mercado = [a.strip().lower() for a in atributos_mercado]

    # Atributos mencionados en reviews pero no en cliente
    en_mercado_no_cliente = [
        a for a in atributos_mercado if a not in atributos_cliente]

    # Atributos declarados por cliente pero no mencionados en mercado
    en_cliente_no_mercado = [
        a for a in atributos_cliente if a not in atributos_mercado]

    # Resultado
    resultado = {
        "Atributos detectados en reviews (mercado)": atributos_mercado,
        "Atributos indicados por el cliente": atributos_cliente,
        "Atributos valorados por el mercado pero no presentes en cliente": en_mercado_no_cliente,
        "Atributos declarados por cliente pero ignorados por el mercado": en_cliente_no_mercado
    }

    return resultado
