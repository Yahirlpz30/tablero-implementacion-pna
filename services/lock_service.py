from services.dropbox_service import connect_dropbox
import dropbox

LOCK_FILE = "/tablero_prueba/lock.txt"


def check_lock():

    dbx = connect_dropbox()

    try:
        dbx.files_get_metadata(LOCK_FILE)
        return True
    except:
        return False


def create_lock():

    dbx = connect_dropbox()

    dbx.files_upload(
        b"locked",
        LOCK_FILE,
        mode=dropbox.files.WriteMode.overwrite
    )


def remove_lock():

    dbx = connect_dropbox()

    try:
        dbx.files_delete_v2(LOCK_FILE)
    except:
        pass
