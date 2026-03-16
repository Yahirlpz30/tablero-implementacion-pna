import streamlit as st
import pandas as pd
import dropbox
import hashlib
import plotly.express as px
from datetime import datetime

# -----------------------------------
# CONFIG
# -----------------------------------

st.set_page_config(
    page_title="Tablero de Implementación PNA",
    layout="wide"
)

# -----------------------------------
# DROPBOX
# -----------------------------------

DROPBOX_TOKEN = st.secrets["DROPBOX_TOKEN"]
dbx = dropbox.Dropbox(DROPBOX_TOKEN)

BASE_PATH = "/tablero_prueba/base.xlsx"

# -----------------------------------
# FUNCIONES DROPBOX
# -----------------------------------

def read_dropbox_excel(path):
    metadata, res = dbx.files_download(path)
    return pd.read_excel(res.content)

def upload_dropbox_excel(df, path):
    import io
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)

    dbx.files_upload(
        buffer.read(),
        path,
        mode=dropbox.files.WriteMode.overwrite
    )

# -----------------------------------
# LOGIN
# -----------------------------------

users = pd.read_excel("www/user-pass.xlsx")
user_actor = pd.read_excel("www/user-act.xlsx")

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()
    
st.image("www/logo_tablero.png", width=300)

st.title("Sistema Estatal Anticorrupción")

st.subheader("Tablero de Implementación del PNA")

st.write("")

username = st.text_input("Usuario")
password = st.text_input("Contraseña", type="password")

if "login" not in st.session_state:
    st.session_state.login = False

if st.sidebar.button("Ingresar"):

    user = users[users["user"] == username]

    if len(user) > 0:
        stored = user.iloc[0]["password"]

        if hash_password(password) == stored:
            st.session_state.login = True
            st.session_state.user = username

if not st.session_state.login:
    st.stop()

# -----------------------------------
# ACTOR
# -----------------------------------

actor = user_actor[
    user_actor["user"] == st.session_state.user
]["act"].values[0]

# -----------------------------------
# CARGAR DATOS
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
# HEADER
# -----------------------------------

col1, col2 = st.columns([1,4])

with col1:
    st.image("www/logo_tablero.png", width=200)

with col2:
    st.title("Reporte de Acciones 2025")
    st.caption("Programa de Implementación del PNA")

st.divider()

# -----------------------------------
# KPIs
# -----------------------------------

total_acciones = len(data)

reportadas = (data["Acción reportada"] != "Por reportar").sum()

avance = round(reportadas / total_acciones * 100,2)

k1,k2,k3 = st.columns(3)

k1.metric("Total acciones", total_acciones)
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
# TABLA
# -----------------------------------

edited = st.data_editor(
    df_linea,
    num_rows="dynamic",
    use_container_width=True
)

# -----------------------------------
# BOTONES
# -----------------------------------

c1,c2 = st.columns(2)

with c1:
    if st.button("Guardar borrador"):

        restante = data[
            ~(
                (data["Actor"] == actor) &
                (data["Línea de acción"] == linea)
            )
        ]

        nuevo = pd.concat([restante, edited])

        upload_dropbox_excel(nuevo, BASE_PATH)

        st.success("Guardado correctamente")

with c2:
    if st.button("Enviar"):

        restante = data[
            ~(
                (data["Actor"] == actor) &
                (data["Línea de acción"] == linea)
            )
        ]

        nuevo = pd.concat([restante, edited])

        upload_dropbox_excel(nuevo, BASE_PATH)

        st.success("Acciones enviadas")
