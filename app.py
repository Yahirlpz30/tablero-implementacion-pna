import streamlit as st
import pandas as pd
import datetime
import io
import dropbox
from dropbox.files import WriteMode

st.set_page_config(layout="wide")

# -------------------------------
# FUNCION LIMPIAR COLUMNAS
# -------------------------------

def limpiar_columnas(df):
    df.columns = df.columns.str.strip().str.lower()
    return df

# -------------------------------
# LOGO
# -------------------------------

st.image("www/logo_tablero.png", width=220)

# -------------------------------
# CARGAR EXCELS
# -------------------------------

alineacion = limpiar_columnas(pd.read_excel("www/alineacion_pi.xlsx"))
tipo_accion = limpiar_columnas(pd.read_excel("www/tipo_accion.xlsx"))
tematicas = limpiar_columnas(pd.read_excel("www/tematicas.xlsx"))
user_pass = limpiar_columnas(pd.read_excel("www/user-pass.xlsx"))
user_act = limpiar_columnas(pd.read_excel("www/user-act.xlsx"))

# -------------------------------
# SESSION STATE
# -------------------------------

if "login" not in st.session_state:
    st.session_state.login = False

if "tabla" not in st.session_state:
    st.session_state.tabla = []

if "ultimo_guardado" not in st.session_state:
    st.session_state.ultimo_guardado = None

# -------------------------------
# LOGIN
# -------------------------------

if not st.session_state.login:

    st.title("SISTEMA ESTATAL ANTICORRUPCIÓN")

    usuario = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Entrar"):

        user = user_pass[
            (user_pass["user"] == usuario) &
            (user_pass["password"] == password)
        ]

        if len(user) > 0:

            st.session_state.login = True
            st.session_state.user = usuario

            st.rerun()

        else:
            st.error("Usuario o contraseña incorrectos")

    st.stop()

# -------------------------------
# USUARIO ACTUAL
# -------------------------------

usuario_actual = st.session_state.user

info_usuario = user_act[
    user_act["user"] == usuario_actual
].iloc[0]

rol = info_usuario["rol"]

# -------------------------------
# FILTRAR ESTRATEGIAS
# -------------------------------

if rol == "admin":

    estrategias_disponibles = alineacion["estrategia"].unique()

else:

    estrategias_permitidas = str(info_usuario["estrategias"]).split(",")

    estrategias_disponibles = alineacion[
        alineacion["estrategia"].astype(str).str.startswith(tuple(estrategias_permitidas))
    ]["estrategia"].unique()

# -------------------------------
# HEADER
# -------------------------------

c1, c2 = st.columns([8,2])

with c1:
    st.title("Reporte de Acciones 2025")
    st.caption("Programa de Implementación del PNA")

with c2:
    st.write(usuario_actual)

    if st.button("Cerrar sesión"):
        st.session_state.login = False
        st.rerun()

# -------------------------------
# BOTONES
# -------------------------------

b1, b2, b3 = st.columns([2,2,2])

with b1:

    if st.button("+ Agregar Acción"):

        st.session_state.tabla.append({
            "estrategia":"",
            "linea":"",
            "accion":"",
            "inicio":"",
            "fin":"",
            "tipo":"",
            "tematica":""
        })

with b2:
    guardar = st.button("Guardar Borrador")

with b3:
    enviar = st.button("Enviar")

# -------------------------------
# INFO
# -------------------------------

acciones = len(st.session_state.tabla)

if st.session_state.ultimo_guardado:

    diff = datetime.datetime.now() - st.session_state.ultimo_guardado
    minutos = int(diff.total_seconds()/60)

    msg = f"Guardado hace {minutos} min"

else:

    msg = "Aún no se ha guardado"

st.write(f"Año: 2025 | Acciones: {acciones} | {msg}")

# -------------------------------
# TABLA
# -------------------------------

for i,row in enumerate(st.session_state.tabla):

    c1,c2,c3,c4,c5,c6,c7,c8 = st.columns([2,2,3,1,1,2,2,0.5])

    with c1:

        estrategia = st.selectbox(
            "Estrategia",
            estrategias_disponibles,
            key=f"est_{i}"
        )

    lineas = alineacion[
        alineacion["estrategia"] == estrategia
    ]["línea de acción"].unique()

    with c2:

        linea = st.selectbox(
            "Línea",
            lineas,
            key=f"lin_{i}"
        )

    acciones_lista = alineacion[
        alineacion["línea de acción"] == linea
    ]["acción"].tolist()

    with c3:

        accion = st.selectbox(
            "Acción",
            acciones_lista,
            key=f"acc_{i}"
        )

    with c4:
        inicio = st.date_input("Inicio", key=f"ini_{i}")

    with c5:
        fin = st.date_input("Fin", key=f"fin_{i}")

    with c6:
        tipo = st.selectbox(
            "Tipo",
            tipo_accion.iloc[:,0],
            key=f"tipo_{i}"
        )

    with c7:
        tema = st.selectbox(
            "Temática",
            tematicas.iloc[:,0],
            key=f"tema_{i}"
        )

    with c8:

        if st.button("🗑", key=f"del_{i}"):

            st.session_state.tabla.pop(i)
            st.rerun()

# -------------------------------
# DROPBOX
# -------------------------------

DROPBOX_TOKEN = st.secrets["DROPBOX_TOKEN"]

dbx = dropbox.Dropbox(DROPBOX_TOKEN)

ARCHIVO = "/tablero_prueba/base.xlsx"
LOCK = "/tablero_prueba/base.lock"

# -------------------------------
# LOCK
# -------------------------------

def existe_lock():

    try:
        dbx.files_get_metadata(LOCK)
        return True
    except:
        return False

def crear_lock():

    dbx.files_upload(
        b"lock",
        LOCK,
        mode=WriteMode.overwrite
    )

def eliminar_lock():

    try:
        dbx.files_delete_v2(LOCK)
    except:
        pass

# -------------------------------
# GUARDAR
# -------------------------------

def guardar_dropbox(data):

    if existe_lock():

        st.warning("Otro usuario está guardando")
        return

    crear_lock()

    df = pd.DataFrame(data)

    buffer = io.BytesIO()

    df.to_excel(buffer,index=False)

    buffer.seek(0)

    dbx.files_upload(
        buffer.read(),
        ARCHIVO,
        mode=WriteMode.overwrite
    )

    eliminar_lock()

    st.session_state.ultimo_guardado = datetime.datetime.now()

    st.success("Guardado correctamente")

# -------------------------------
# BOTONES
# -------------------------------

if guardar:

    guardar_dropbox(st.session_state.tabla)

if enviar:

    guardar_dropbox(st.session_state.tabla)
