import streamlit as st
import pandas as pd
import dropbox
import bcrypt
import plotly.express as px
from datetime import datetime
import io


# -----------------------------------
# CONFIG
# -----------------------------------

st.set_page_config(
    page_title="Tablero de Implementación PNA",
    layout="wide"
)

# -----------------------------------
# CARGAR USUARIOS
# -----------------------------------

users = pd.read_excel("www/user-pass.xlsx")
user_actor = pd.read_excel("www/user-act.xlsx")


# -----------------------------------
# SESSION STATE
# -----------------------------------

if "login" not in st.session_state:
    st.session_state["login"] = False

if "user" not in st.session_state:
    st.session_state["user"] = None


# -----------------------------------
# DROPBOX
# -----------------------------------

DROPBOX_TOKEN = st.secrets["DROPBOX_TOKEN"]
dbx = dropbox.Dropbox(DROPBOX_TOKEN)

BASE_PATH = "/tablero_prueba/base.xlsx"
LOCK_FILE = "/tablero_prueba/lock.txt"


# -----------------------------------
# FUNCIONES DROPBOX
# -----------------------------------

def read_dropbox_excel(path):

    metadata, res = dbx.files_download(path)

    return pd.read_excel(res.content)


def upload_dropbox_excel(df, path):

    buffer = io.BytesIO()

    df.to_excel(buffer, index=False)

    buffer.seek(0)

    dbx.files_upload(
        buffer.read(),
        path,
        mode=dropbox.files.WriteMode.overwrite
    )


# -----------------------------------
# SISTEMA LOCK
# -----------------------------------

def check_lock():

    try:
        dbx.files_get_metadata(LOCK_FILE)
        return True
    except:
        return False


def create_lock(user):

    dbx.files_upload(
        user.encode(),
        LOCK_FILE,
        mode=dropbox.files.WriteMode.overwrite
    )


def remove_lock():

    try:
        dbx.files_delete_v2(LOCK_FILE)
    except:
        pass
        
# -----------------------------------
# LOGIN
# -----------------------------------

if not st.session_state.login:

    col1, col2, col3 = st.columns([1,2,1])

    with col2:

        st.image("www/logo_tablero.png", width=250)

        st.markdown("## Sistema Estatal Anticorrupción")
        st.markdown("Tablero de Implementación del PNA")

        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")

        login_button = st.button("Ingresar", use_container_width=True)

        if login_button:

            user = users[users["user"] == username]

            if len(user) > 0:

                stored_password = user.iloc[0]["password"]

                if password == stored_password:

                    st.session_state["login"] = True
                    st.session_state["user"] = username
                
                    st.rerun()

                else:
                st.error("Contraseña incorrecta")

            else:
                st.error("Usuario no encontrado")

    st.stop()


# -----------------------------------
# ACTOR DEL USUARIO
# -----------------------------------

actor = user_actor[
    user_actor["user"] == st.session_state.user
]["act"].values[0]


# -----------------------------------
# HEADER
# -----------------------------------

col1,col2 = st.columns([1,4])

with col1:
    st.image("www/logo_tablero.png", width=180)

with col2:
    st.title("Reporte de Acciones 2025")
    st.caption("Programa de Implementación del PNA")

if st.button("Cerrar sesión"):

    remove_lock()

    st.session_state.login = False
    st.session_state.user = None

    st.rerun()

st.divider()


# -----------------------------------
# BLOQUEO SIMULTÁNEO
# -----------------------------------

if check_lock():

    st.error("⚠️ Otro usuario está editando el sistema en este momento.")
    st.stop()

create_lock(st.session_state.user)


# -----------------------------------
# CARGAR ESTRUCTURA
# -----------------------------------

alineacion = pd.read_excel("www/alineacion_pi.xlsx")
actores = pd.read_excel("www/pi-actores.xlsx")

estructura = actores.merge(
    alineacion,
    on="Línea de acción",
    how="left"
)

data = read_dropbox_excel(BASE_PATH)


# -----------------------------------
# KPIs
# -----------------------------------

total = len(data)

reportadas = (data["Acción reportada"] != "Por reportar").sum()

avance = round(reportadas/total*100,2)

k1,k2,k3 = st.columns(3)

k1.metric("Total acciones", total)
k2.metric("Acciones reportadas", reportadas)
k3.metric("Avance %", avance)

st.divider()


# -----------------------------------
# RANKING
# -----------------------------------

ranking = (
    data.groupby("Actor")
    .apply(lambda x: (x["Acción reportada"] != "Por reportar").mean()*100)
    .reset_index(name="avance")
)

fig = px.bar(
    ranking,
    x="Actor",
    y="avance",
    title="Ranking de avance por institución",
    color="avance",
    color_continuous_scale="Blues"
)

st.plotly_chart(fig, use_container_width=True)

st.divider()


# -----------------------------------
# FILTRAR ACTOR
# -----------------------------------

df_actor = estructura[
    estructura["Actor"] == actor
]

estrategias = sorted(df_actor["Estrategia"].unique())

estrategia = st.selectbox(
    "Estrategia",
    estrategias
)

df_est = df_actor[
    df_actor["Estrategia"] == estrategia
]

lineas = sorted(df_est["Línea de acción"].unique())

linea = st.selectbox(
    "Línea de acción",
    lineas
)

df_linea = data[
    (data["Actor"] == actor) &
    (data["Línea de acción"] == linea)
]

st.divider()


# -----------------------------------
# TABLA EDITABLE
# -----------------------------------

edited = st.data_editor(
    df_linea,
    num_rows="dynamic",
    use_container_width=True
)


# -----------------------------------
# BOTONES
# -----------------------------------

col1,col2 = st.columns(2)

with col1:

    if st.button("Guardar borrador"):

        restante = data[
            ~(
                (data["Actor"] == actor) &
                (data["Línea de acción"] == linea)
            )
        ]

        nuevo = pd.concat([restante, edited])

        upload_dropbox_excel(nuevo, BASE_PATH)

        remove_lock()

        st.success("Guardado correctamente")


with col2:

    if st.button("Enviar"):

        restante = data[
            ~(
                (data["Actor"] == actor) &
                (data["Línea de acción"] == linea)
            )
        ]

        nuevo = pd.concat([restante, edited])

        upload_dropbox_excel(nuevo, BASE_PATH)

        remove_lock()

        st.success("Acciones enviadas")
