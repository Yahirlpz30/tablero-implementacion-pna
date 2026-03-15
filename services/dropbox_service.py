import dropbox
import pandas as pd
from io import BytesIO
import streamlit as st

dbx = dropbox.Dropbox(st.secrets["DROPBOX_TOKEN"])

def read_excel_dropbox(path):

    metadata, res = dbx.files_download(path)

    return pd.read_excel(BytesIO(res.content))


def upload_excel_dropbox(df, path):

    buffer = BytesIO()

    df.to_excel(buffer, index=False)

    dbx.files_upload(
        buffer.getvalue(),
        path,
        mode=dropbox.files.WriteMode.overwrite
    )
