# datos/app_datos_upload.py
import streamlit as st
import pandas as pd
import os
import shutil
import zipfile
import datetime

EXCEL_DIR = "data/raw"
EXCEL_NAME = "optimizacion_listing.xlsx"
EXCEL_PATH = os.path.join(EXCEL_DIR, EXCEL_NAME)


def mostrar_carga_excel():
    st.title("Carga de archivo Excel")

    # Crear carpeta si no existe
    os.makedirs(EXCEL_DIR, exist_ok=True)

    # Subida del archivo
    uploaded_file = st.file_uploader(
        "Selecciona el archivo Excel", type=["xlsx"])

    if uploaded_file:
        with open(EXCEL_PATH, "wb") as f:
            f.write(uploaded_file.read())
        st.success(f"Archivo guardado como: {EXCEL_PATH}")
        st.session_state.excel_data = pd.ExcelFile(EXCEL_PATH)

    # Verificar si ya existe uno cargado
    elif os.path.exists(EXCEL_PATH):
        st.info(f"Ya existe un archivo cargado: {EXCEL_PATH}")
        try:
            st.session_state.excel_data = pd.ExcelFile(EXCEL_PATH)
            st.success("Archivo cargado desde disco correctamente.")
        except Exception as e:
            st.error(f"Error al cargar archivo existente: {e}")
    else:
        st.warning("Aún no se ha subido ningún archivo.")

    # Backup del proyecto
    st.subheader("Backup del proyecto")
    if st.button("Crear backup .zip del proyecto actual"):
        fecha = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_filename = f"backup_renediaz_{fecha}.zip"
        backup_path = os.path.join("backups", backup_filename)
        os.makedirs("backups", exist_ok=True)

        with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk("."):
                for file in files:
                    if (
                        ".git" in root
                        or "__pycache__" in root
                        or file.endswith((".pyc", ".zip"))
                        or file.startswith(".")
                    ):
                        continue
                    filepath = os.path.join(root, file)
                    zipf.write(
                        filepath, arcname=os.path.relpath(filepath, "."))

        st.success(f"Backup creado: {backup_path}")
