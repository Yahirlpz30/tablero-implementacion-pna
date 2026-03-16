import dropbox
import streamlit as st


LOCK_FILE = "/lock.txt"


def get_client():
    return dropbox.Dropbox(st.secrets["DROPBOX_TOKEN"])


# ======================================
# VERIFICAR LOCK
# ======================================

def check_lock():

    dbx = get_client()

    try:
        dbx.files_get_metadata(LOCK_FILE)
        return True
    except:
        return False


# ======================================
# CREAR LOCK
# ======================================

def create_lock(user):

    dbx = get_client()

    try:
        dbx.files_upload(
            user.encode(),
            LOCK_FILE,
            mode=dropbox.files.WriteMode.overwrite
        )
    except:
        pass


# ======================================
# ELIMINAR LOCK
# ======================================

def delete_lock():

    dbx = get_client()

    try:
        dbx.files_delete_v2(LOCK_FILE)
    except:
        pass
