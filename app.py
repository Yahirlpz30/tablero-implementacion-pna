import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

from services.dropbox_service import read_excel_dropbox, upload_excel_dropbox
from services.lock_service import check_lock, create_lock, remove_lock


st.set_page_config(
    page_title="Tablero de Implementación",
    layout="wide",
    page_icon="www/favicon.png"
)

st.image("www/logo_tablero.png", width=300)

# LOGIN

users = pd.read_excel("www/user-pass.xlsx")
user_act = pd.read_excel("www/user-act.xlsx")

if "logged" not in st.session_state:
    st.session_state.logged = False

if not st.session_state.logged:

    st.title("Inicio de sesión")

    user = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):

        check = users[
            (users["user"] == user) &
            (users["password"] == password)
        ]

        if len(check) > 0:

            st.session_state.logged = True
            st.session_state.user = user

            actor = user_act[user_act["user"] == user]["act"].values[0]

            st.session_state.actor = actor

            st.rerun()

        else:

            st.error("Usuario o contraseña incorrectos")

    st.stop()


@st.cache_data
def load_data():
    return read_excel_dropbox("/tablero_prueba/base.xlsx")

data = load_data()

actor_usuario = st.session_state.actor

st.title("Tablero de Implementación")

st.write("Institución:", actor_usuario)


# KPIs

total = len(data)

reportadas = (data["Acción reportada"] != "Por reportar").sum()

avance = round((reportadas / total) * 100, 2)

k1, k2, k3 = st.columns(3)

k1.metric("Total acciones", total)
k2.metric("Acciones reportadas", reportadas)
k3.metric("Avance %", avance)


# Ranking

ranking = (
    data.groupby("Actor")
    .apply(lambda x: (x["Acción reportada"] != "Por reportar").mean()*100)
    .reset_index(name="avance")
)

fig = px.bar(
    ranking,
    x="Actor",
    y="avance",
    title="Ranking de avance",
    color="avance"
)

st.plotly_chart(fig, use_container_width=True)


# FILTROS

df_actor = data[data["Actor"] == actor_usuario]

estrategias = sorted(df_actor["No. Estrategia"].unique())

estrategia = st.selectbox("Estrategia", estrategias)

df_estrategia = df_actor[
    df_actor["No. Estrategia"] == estrategia
]

lineas = sorted(df_estrategia["No. Línea de acción"].unique())

linea = st.selectbox("Línea de acción", lineas)

df_linea = df_estrategia[
    df_estrategia["No. Línea de acción"] == linea
]


# TABLA EDITABLE

edited = st.data_editor(
    df_linea,
    num_rows="dynamic",
    use_container_width=True
)


# GUARDAR

if st.button("Guardar cambios"):

    if check_lock():

        st.warning("Otro usuario está guardando datos. Intente nuevamente.")

        st.stop()

    create_lock()

    try:

        restante = data[
            data["No. Línea de acción"] != linea
        ]

        nuevo = pd.concat([restante, edited])

        upload_excel_dropbox(
            nuevo,
            "/tablero_prueba/base.xlsx"
        )

        snapshot = (
            "/tablero_prueba/snaps/"
            + actor_usuario
            + "_"
            + datetime.now().strftime("%Y%m%d_%H%M")
            + ".xlsx"
        )

        upload_excel_dropbox(
            edited,
            snapshot
        )

        st.success("Información guardada correctamente")

        st.cache_data.clear()

    except Exception as e:

        st.error("Error guardando información")
        st.write(e)

    finally:

        remove_lock()
