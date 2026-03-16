import streamlit as st
import pandas as pd
import dropbox
import io
import datetime

st.set_page_config(layout="wide")

# -----------------------------
# CONFIG DROPBOX
# -----------------------------

DROPBOX_TOKEN = st.secrets["DROPBOX_TOKEN"]

dbx = dropbox.Dropbox(DROPBOX_TOKEN)

ARCHIVO_ACCIONES = "/acciones_2025.xlsx"
ARCHIVO_LOCK = "/lock_acciones.txt"


# -----------------------------
# FUNCIONES DROPBOX
# -----------------------------

def descargar_excel():

    try:
        metadata, res = dbx.files_download(ARCHIVO_ACCIONES)
        return pd.read_excel(io.BytesIO(res.content))

    except:
        return pd.DataFrame()


def subir_excel(df):

    buffer = io.BytesIO()
    df.to_excel(buffer, index=False)

    dbx.files_upload(
        buffer.getvalue(),
        ARCHIVO_ACCIONES,
        mode=dropbox.files.WriteMode.overwrite
    )


def crear_lock(usuario):

    try:
        dbx.files_upload(
            usuario.encode(),
            ARCHIVO_LOCK,
            mode=dropbox.files.WriteMode.add
        )
        return True
    except:
        return False


def liberar_lock():

    try:
        dbx.files_delete_v2(ARCHIVO_LOCK)
    except:
        pass


# -----------------------------
# CARGAR EXCELS
# -----------------------------

users = pd.read_excel("www/user-pass.xlsx")
alineacion = pd.read_excel("www/alineacion_pi.xlsx")

tipo_accion = pd.read_excel("www/tipo_accion.xlsx")
tematicas = pd.read_excel("www/tematicas.xlsx")


# -----------------------------
# LOGIN
# -----------------------------

if "login" not in st.session_state:
    st.session_state.login = False

if "usuario" not in st.session_state:
    st.session_state.usuario = None


def validar(usuario, password):

    row = users[
        (users["user"] == usuario)
        & (users["password"] == password)
    ]

    return len(row) > 0


if not st.session_state.login:

    col1,col2 = st.columns([1,6])

    with col1:
        st.image("www/logo_tablero.png",width=120)

    with col2:
        st.markdown("### SISTEMA ESTATAL ANTICORRUPCIÓN")

    usuario = st.text_input("Usuario")
    password = st.text_input("Contraseña",type="password")

    if st.button("Entrar"):

        if validar(usuario,password):

            st.session_state.login = True
            st.session_state.usuario = usuario
            st.rerun()

        else:

            st.error("Usuario o contraseña incorrectos")

    st.stop()


# -----------------------------
# HEADER
# -----------------------------

col1,col2,col3 = st.columns([1,6,2])

with col1:
    st.image("www/logo_tablero.png",width=120)

with col2:
    st.markdown("### SISTEMA ESTATAL ANTICORRUPCIÓN")

with col3:

    st.write("Usuario:",st.session_state.usuario)

    if st.button("Cerrar sesión"):

        liberar_lock()

        st.session_state.login = False
        st.rerun()


# -----------------------------
# SIDEBAR
# -----------------------------

st.sidebar.title("2025")


# -----------------------------
# TITULO
# -----------------------------

st.title("Reporte de Acciones 2025")
st.caption("Programa de Implementación del PNA")


# -----------------------------
# BOTONES
# -----------------------------

col1,col2,col3 = st.columns([2,2,2])

with col1:
    agregar = st.button("+ Agregar Acción")

with col2:
    guardar = st.button("Guardar Borrador")

with col3:
    enviar = st.button("Enviar")


# -----------------------------
# DATA
# -----------------------------

df = descargar_excel()

if df.empty:

    df = pd.DataFrame(columns=[
        "Estrategia",
        "Linea",
        "Accion",
        "Inicio",
        "Fin",
        "Tipo",
        "Tematica"
    ])


# -----------------------------
# AGREGAR ACCION
# -----------------------------

if agregar:

    df.loc[len(df)] = ["","","","","","",""]


# -----------------------------
# INFO
# -----------------------------

col1,col2,col3 = st.columns(3)

with col1:
    st.write("Año: 2025")

with col2:
    st.write("Acciones:",len(df))

with col3:
    if st.session_state.ultimo_guardado:

    diff = datetime.datetime.now() - st.session_state.ultimo_guardado
    minutos = int(diff.total_seconds() / 60)

    if minutos == 0:
        mensaje = "Guardado: hace unos segundos"
    elif minutos == 1:
        mensaje = "Guardado: hace 1 minuto"
    else:
        mensaje = f"Guardado: hace {minutos} minutos"

    st.write(mensaje)

else:
    st.write("Guardado: aún no se ha guardado")


# -----------------------------
# OPCIONES
# -----------------------------

estrategias = alineacion["Estrategia"].unique()

lineas = alineacion["Línea de acción"].unique()

tipo_lista = tipo_accion["tipo"].tolist()

tematica_lista = tematicas["tematica"].tolist()


# -----------------------------
# TABLA
# -----------------------------

for i in df.index:

    col1,col2,col3,col4,col5,col6,col7,col8 = st.columns(
        [2,2,3,2,2,2,2,1]
    )

    with col1:
        df.at[i,"Estrategia"] = st.selectbox(
            "Estrategia",
            estrategias,
            key=f"est{i}"
        )

    with col2:
        df.at[i,"Linea"] = st.selectbox(
            "Linea",
            lineas,
            key=f"lin{i}"
        )

    with col3:
        df.at[i,"Accion"] = st.text_input(
            "Accion",
            value=df.at[i,"Accion"],
            key=f"acc{i}"
        )

    with col4:
        df.at[i,"Inicio"] = st.date_input(
            "Inicio",
            key=f"ini{i}"
        )

    with col5:
        df.at[i,"Fin"] = st.date_input(
            "Fin",
            key=f"fin{i}"
        )

    with col6:
        df.at[i,"Tipo"] = st.selectbox(
            "Tipo",
            tipo_lista,
            key=f"tipo{i}"
        )

    with col7:
        df.at[i,"Tematica"] = st.selectbox(
            "Tematica",
            tematica_lista,
            key=f"tem{i}"
        )

    with col8:

        if st.button("🗑",key=f"del{i}"):

            df = df.drop(i)


# -----------------------------
# GUARDAR
# -----------------------------

if guardar:

    if crear_lock(st.session_state.usuario):

        subir_excel(df)

        liberar_lock()

        st.success("Guardado correctamente")

    else:

        st.error("Otro usuario está editando")


# -----------------------------
# ENVIAR
# -----------------------------

if enviar:

    if crear_lock(st.session_state.usuario):

        subir_excel(df)

        liberar_lock()

        st.success("Acciones enviadas")

    else:

        st.error("Otro usuario está editando")
