import dropbox
import streamlit as st


# ======================================================
# TOKEN
# ======================================================

DROPBOX_TOKEN = st.secrets["DROPBOX_TOKEN"]


# ======================================================
# CLIENTE
# ======================================================

def get_client():

    return dropbox.Dropbox(DROPBOX_TOKEN)


# ======================================================
# DESCARGAR ARCHIVO
# ======================================================

def download_file(path):

    dbx = get_client()

    metadata, res = dbx.files_download(path)

    return res.content


# ======================================================
# SUBIR ARCHIVO
# ======================================================

def upload_file(path, data):

    dbx = get_client()

    dbx.files_upload(
        data,
        path,
        mode=dropbox.files.WriteMode.overwrite
    )
