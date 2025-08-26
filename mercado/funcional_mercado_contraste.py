# mercado/funcional_mercado_contraste.py

import pandas as pd
import streamlit as st


def comparar_atributos_mercado_cliente(excel_data: pd.ExcelFile, atributos_mercado: list[str]) -> tuple[pd.DataFrame, dict]:
    """
    Compara los atributos detectados en los reviews con los que el cliente declara tener (CustData).
    Devuelve un DataFrame vertical y un resumen dict.
    """

    try:
        df = excel_data.parse("CustData", skiprows=12, header=None)
    except Exception as e:
        st.error(f"Error al leer atributos del cliente desde CustData: {e}")
        return pd.DataFrame(), {}

    df = df.dropna(how="all")
    st.write(f"Columnas detectadas: {df.shape[1]}")

    if df.shape[1] < 3:
        st.warning("No hay suficientes columnas en CustData.")
        return pd.DataFrame(), {}

    # Asignar nombres a las columnas
    col_total = df.shape[1]
    df.columns = ["Atributo", "Relevante", "Variacion"] + \
        [f"Valor_{i}" for i in range(1, col_total - 3 + 1)]

    # Filtrar atributos válidos
    df = df[df["Atributo"].notna()]
    df["Relevante"] = df["Relevante"].fillna(
        "").astype(str).str.strip().str.lower()
    df = df[df["Relevante"] == "si"]
    df["Atributo"] = df["Atributo"].astype(str).str.strip().str.lower()

    atributos_cliente = df["Atributo"].tolist()
    atributos_mercado = [a.strip().lower() for a in atributos_mercado]

    # Comparación
    en_mercado_no_cliente = [
        a for a in atributos_mercado if a not in atributos_cliente]
    en_cliente_no_mercado = [
        a for a in atributos_cliente if a not in atributos_mercado]
    presentes_en_ambos = [
        a for a in atributos_mercado if a in atributos_cliente]

    # DataFrame vertical para mostrar comparaciones
    df_comparado = pd.DataFrame({
        "Atributos del mercado": atributos_mercado,
        "Presente en cliente": ["✅" if a in atributos_cliente else "❌" for a in atributos_mercado]
    })

    resumen = {
        "Detectados en reviews (mercado)": atributos_mercado,
        "Indicados por el cliente": atributos_cliente,
        "Atributos valorados por el mercado pero no presentes en cliente": en_mercado_no_cliente,
        "Atributos declarados por cliente pero ignorados por el mercado": en_cliente_no_mercado,
        "Atributos presentes en ambos": presentes_en_ambos
    }

    return df_comparado, resumen
