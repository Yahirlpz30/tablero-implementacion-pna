import streamlit as st
import pandas as pd
import datetime
import dropbox
import io

st.set_page_config(layout="wide")

# -------------------------------
# LOGO
# -------------------------------

st.image("www/logo_tablero.png", width=200)

# -------------------------------
# CARGA DE ARCHIVOS
# -------------------------------

alineacion = pd.read_excel("www/alineacion_pi.xlsx")
tipo_accion = pd.read_excel("www/tipo_accion.xlsx")
tematicas = pd.read_excel("www/tematicas.xlsx")
usuarios = pd.read_excel("www/usuarios.xlsx")

# -------------------------------
# LOGIN
# -------------------------------

if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:

    st.title("SISTEMA ESTATAL ANTICORRUPCIÓN")

    usuario = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Entrar"):

        user = usuarios[
            (usuarios["usuario"] == usuario) &
            (usuarios["password"] == password)
        ]

        if len(user) > 0:

            st.session_state.login = True
            st.session_state.user = usuario

            st.rerun()

        else:
            st.error("Usuario o contraseña incorrectos")

    st.stop()

# -------------------------------
# USUARIO LOGUEADO
# -------------------------------

usuario_actual = st.session_state.user

info_usuario = usuarios[
    usuarios["usuario"] == usuario_actual
].iloc[0]

rol = info_usuario["rol"]

# -------------------------------
# FILTRAR ESTRATEGIAS
# -------------------------------

if rol == "admin":

    estrategias_disponibles = alineacion["Estrategia"].unique()

else:

    estrategias_permitidas = str(
        info_usuario["estrategias"]
    ).split(",")

    estrategias_disponibles = alineacion[
        alineacion["Estrategia"].str.startswith(
            tuple(estrategias_permitidas)
        )
    ]["Estrategia"].unique()

# -------------------------------
# HEADER
# -------------------------------

col1, col2 = st.columns([8,2])

with col1:
    st.title("Reporte de Acciones 2025")
    st.caption("Programa de Implementación del PNA")

with col2:

    st.write(f"Usuario: {usuario_actual}")

    if st.button("Cerrar sesión"):
        st.session_state.login = False
        st.rerun()

# -------------------------------
# BOTONES
# -------------------------------

c1, c2, c3 = st.columns([2,2,2])

if "tabla" not in st.session_state:

    st.session_state.tabla = pd.DataFrame(columns=[
        "Estrategia",
        "Línea de Acción",
        "Acción",
        "Inicio",
        "Fin",
        "Tipo de Acción",
        "Temática"
    ])

with c1:

    if st.button("+ Agregar Acción"):

        nueva = {
            "Estrategia":"",
            "Línea de Acción":"",
            "Acción":"",
            "Inicio":"",
            "Fin":"",
            "Tipo de Acción":"",
            "Temática":""
        }

        st.session_state.tabla = pd.concat(
            [st.session_state.tabla, pd.DataFrame([nueva])],
            ignore_index=True
        )

with c2:

    guardar = st.button("Guardar Borrador")

with c3:

    enviar = st.button("Enviar")

# -------------------------------
# INFO
# -------------------------------

st.write(
f"Año: 2025 | Acciones: {len(st.session_state.tabla)}"
)

# -------------------------------
# TABLA
# -------------------------------

for i in range(len(st.session_state.tabla)):

    c1,c2,c3,c4,c5,c6,c7,c8 = st.columns([2,2,3,1,1,2,2,0.5])

    with c1:

        estrategia = st.selectbox(
            "Estrategia",
            estrategias_disponibles,
            key=f"est_{i}"
        )

    lineas = alineacion[
        alineacion["Estrategia"] == estrategia
    ]["Línea de acción"].unique()

    with c2:

        linea = st.selectbox(
            "Línea",
            lineas,
            key=f"lin_{i}"
        )

    acciones = alineacion[
        alineacion["Línea de acción"] == linea
    ]["Acción"].tolist()

    with c3:

        accion = st.selectbox(
            "Acción",
            acciones,
            key=f"acc_{i}"
        )

    with c4:

        inicio = st.date_input(
            "Inicio",
            key=f"ini_{i}"
        )

    with c5:

        fin = st.date_input(
            "Fin",
            key=f"fin_{i}"
        )

    with c6:

        tipo = st.selectbox(
            "Tipo",
            tipo_accion["tipo_accion"],
            key=f"tipo_{i}"
        )

    with c7:

        tema = st.selectbox(
            "Temática",
            tematicas["tematica"],
            key=f"tema_{i}"
        )

    with c8:

        if st.button("🗑", key=f"del_{i}"):

            st.session_state.tabla = st.session_state.tabla.drop(i)

            st.session_state.tabla.reset_index(
                drop=True,
                inplace=True
            )

            st.rerun()

# -------------------------------
# DROPBOX
# -------------------------------

DROPBOX_TOKEN = st.secrets["DROPBOX_TOKEN"]

dbx = dropbox.Dropbox(DROPBOX_TOKEN)

RUTA = "/tablero_prueba/base.xlsx"

# -------------------------------
# GUARDAR
# -------------------------------

def guardar_dropbox(df):

    buffer = io.BytesIO()

    df.to_excel(buffer, index=False)

    buffer.seek(0)

    dbx.files_upload(
        buffer.read(),
        RUTA,
        mode=dropbox.files.WriteMode.overwrite
    )

if guardar:

    guardar_dropbox(st.session_state.tabla)

    st.success("Guardado correctamente")

if enviar:

    guardar_dropbox(st.session_state.tabla)

    st.success("Información enviada")
