import streamlit as st
import dropbox

st.title("Prueba conexión Dropbox")

# leer token desde secrets
token = st.secrets["DROPBOX_TOKEN"]

# conectar con Dropbox
dbx = dropbox.Dropbox(token)

try:
    
    # listar archivos del root
    files = dbx.files_list_folder("").entries

    st.success("Conexión exitosa con Dropbox")

    st.write("Archivos encontrados:")

    for file in files:
        st.write(file.name)

except Exception as e:

    st.error("Error conectando con Dropbox")
    st.write(e)
