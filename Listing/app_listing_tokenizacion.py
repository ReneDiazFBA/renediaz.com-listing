# listing/app_listing_tokenizacion.py

from listing.funcional_listing_tokenizacion import priorizar_tokens
import streamlit as st
from listing.funcional_listing_tokenizacion import tokenizar_keywords


def mostrar_listing_tokenizacion(excel_data=None):
    st.subheader("Tokenización de Keywords Estratégicas")

    df = tokenizar_keywords()

    if df.empty:
        st.warning("No se pudo cargar la tabla de keywords tokenizadas.")
        return

    st.caption("Vista previa de tokens generados por término:")
    st.dataframe(df[["Search Terms", "tokens"]], use_container_width=True)

# listing/app_listing_tokenizacion.py


def mostrar_listing_tokenizacion(excel_data=None):
    st.subheader("Tokenización priorizada de keywords estratégicas")

    df_tokens = priorizar_tokens()

    if df_tokens.empty:
        st.warning("No se pudo generar el listado de tokens priorizados.")
        return

    # Ordenar por prioridad jerárquica (tier_origen)
    orden_tiers = {
        "Core": 1,
        "Oportunidad crítica": 2,
        "Oportunidad directa": 3,
        "Especialización": 4
    }

    df_tokens["orden"] = df_tokens["tier_origen"].map(orden_tiers)
    df_tokens.sort_values(["orden", "token"], inplace=True)

    st.caption("Tokens únicos priorizados por tier estratégico. Si un token aparece más de una vez, se muestra su frecuencia.")
    st.dataframe(
        df_tokens[["token", "frecuencia", "tier_origen"]], use_container_width=True)
