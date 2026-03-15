import dropbox
import streamlit as st

dbx = dropbox.Dropbox(st.secrets["DROPBOX_TOKEN"])

LOCK_PATH = "/tablero_prueba/save.lock"

def check_lock():

    try:
        dbx.files_get_metadata(LOCK_PATH)
        return True
    except:
        return False


def create_lock():

    dbx.files_upload(
        b"locked",
        LOCK_PATH,
        mode=dropbox.files.WriteMode.overwrite
    )


def remove_lock():

    try:
        dbx.files_delete_v2(LOCK_PATH)
    except:
        pass
