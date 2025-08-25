# keywords/loader_deduplicado.py
from keywords.funcional_keywords_deduplicado import construir_tabla_maestra_raw

# Solo se usa como puente de carga, sin lógica adicional


def get_maestra_raw(excel_data):
    return construir_tabla_maestra_raw(excel_data)
