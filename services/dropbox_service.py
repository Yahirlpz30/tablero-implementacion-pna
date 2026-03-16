import streamlit as st
import dropbox
import pandas as pd
from io import BytesIO


def connect_dropbox():

    token = st.secrets["DROPBOX_TOKEN"]

    dbx = dropbox.Dropbox(token)

    return dbx


def read_excel_dropbox(path):

    dbx = connect_dropbox()

    metadata, res = dbx.files_download(path)

    df = pd.read_excel(BytesIO(res.content))

    return df


def upload_excel_dropbox(df, path):

    dbx = connect_dropbox()

    buffer = BytesIO()

    df.to_excel(buffer, index=False)

    dbx.files_upload(
        buffer.getvalue(),
        path,
        mode=dropbox.files.WriteMode.overwrite
    )
