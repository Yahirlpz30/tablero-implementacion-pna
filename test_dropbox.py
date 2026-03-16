import streamlit as st
import dropbox

st.title("Prueba conexión Dropbox")

token = st.secrets["DROPBOX_TOKEN"]
dbx = dropbox.Dropbox(token)

files = dbx.files_list_folder("").entries

st.write("Archivos encontrados en Dropbox:")

for file in files:
    st.write(file.name)
