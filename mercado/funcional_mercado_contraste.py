# mercado/funcional_mercado_contraste.py

import pandas as pd
import streamlit as st


def comparar_atributos_mercado_cliente(excel_data: pd.ExcelFile, atributos_mercado: list[str]) -> pd.DataFrame:
    """
    Compara los atributos detectados en los reviews con los que el cliente declara tener (CustData).
    Devuelve un DataFrame vertical para visualización.
    """

    try:
        df = excel_data.parse("CustData", skiprows=12, header=None)
    except Exception as e:
        st.error(f"Error al leer atributos del cliente desde CustData: {e}")
        return pd.DataFrame()

    # Ignorar filas completamente vacías
    df = df.dropna(how="all")

    # Validar que hay al menos 3 columnas
    st.markdown("### Vista previa de CustData (debug)")
    st.dataframe(df.head(5))
    st.write(f"Columnas detectadas: {df.shape[1]}")

    if df.shape[1] < 3:
        st.warning("No hay suficientes columnas en CustData.")
        return pd.DataFrame()

    # Asignar nombres a las columnas disponibles
    col_total = df.shape[1]
    df.columns = ["Atributo", "Relevante", "Variacion"] + \
        [f"Valor_{i}" for i in range(1, col_total - 3 + 1)]

    # Limpiar filas sin atributo o irrelevantes
    df = df[df["Atributo"].notna()]
    df = df[df["Relevante"].str.lower() == "si"]

    # Convertir a string por seguridad
    df["Atributo"] = df["Atributo"].astype(str).str.strip().str.lower()

    # Lista de atributos declarados por el cliente
    atributos_cliente = df["Atributo"].tolist()

    # Normalizar los atributos del mercado
    atributos_mercado = [a.strip().lower() for a in atributos_mercado]

    # Comparación
    en_mercado_no_cliente = [a for a in atributos_mercado if a not in atributos_cliente]
    en_cliente_no_mercado = [a for a in atributos_cliente if a not in atributos_mercado]
    presentes_en_ambos = [a for a in atributos_mercado if a in atributos_cliente]

    # Construir DataFrame de resumen
    data = {
        "Atributos del mercado": atributos_mercado,
        "Presente en cliente": ["✅" if a in atributos_cliente else "❌" for a in atributos_mercado]
    }
    df_comparado = pd.DataFrame(data)

    # Expandir resumen adicional (para vista por tipo)
    resumen = {
        "Detectados en reviews (mercado)": atributos_mercado,
        "Indicados por el cliente": atributos_cliente,
        "Valorados por mercado pero ausentes en cliente": en_mercado_no_cliente,
        "Declarados por cliente pero no valorados por mercado": en_cliente_no_mercado,
        "Atributos presentes en ambos": presentes_en_ambos
    }

    return df_comparado  # también puedes retornar resumen como segundo valor si luego lo necesitas
