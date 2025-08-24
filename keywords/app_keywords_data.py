# reemplazo en keywords/app_keywords_data.py

from keywords.app_keywords_referencial import mostrar_tabla_referencial
from keywords.app_keywords_competidores import mostrar_tabla_competidores


def mostrar_keywords_data(excel_data: Optional[pd.ExcelFile] = None):
    st.markdown("### Keywords — Tablas de origen")

    secciones = {
        "referencial": ("Reverse ASIN Referencial", "CustKW"),
        "competidores": ("Reverse ASIN Competidores", "CompKW"),
        "mining": ("Mining de Keywords", "MiningKW")
    }

    qp = st.query_params
    active = qp.get("subview", ["referencial"])[0]

    from utils.nav_utils import render_subnav_cascaron as render_subnav
    render_subnav(active, secciones)
    st.divider()

    if active == "referencial":
        mostrar_tabla_referencial(excel_data, sheet_name="CustKW")
    elif active == "competidores":
        mostrar_tabla_competidores(excel_data, sheet_name="CompKW")
    else:
        st.info("Mining aún no implementado.")
