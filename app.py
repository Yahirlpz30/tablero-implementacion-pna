import streamlit as st
import pandas as pd
import bcrypt
import io

st.set_page_config(page_title="Sistema Estatal Anticorrupción", layout="wide")

# ---------------------------------------------------
# FUNCION LEER EXCEL
# ---------------------------------------------------

def cargar_excel(path):

    df = pd.read_excel(path)
    df.columns = df.columns.str.strip()

    return df


# ---------------------------------------------------
# CARGAR BASES
# ---------------------------------------------------

users = cargar_excel("www/user-pass.xlsx")
user_act = cargar_excel("www/user-act.xlsx")
pi_actores = cargar_excel("www/pi-actores.xlsx")
alineacion = cargar_excel("www/alineacion_pi.xlsx")
tipo_accion = cargar_excel("www/tipo_accion.xlsx")
tematicas = cargar_excel("www/tematicas.xlsx")


opciones_tipo = tipo_accion.iloc[:,0].dropna().tolist()
opciones_tematicas = tematicas.iloc[:,0].dropna().tolist()


# ---------------------------------------------------
# HASH TEMPORAL
# ---------------------------------------------------

if "hash_users" not in st.session_state:

    hashes = {}

    for _,row in users.iterrows():

        hashes[row["user"]] = bcrypt.hashpw(
            str(row["password"]).encode(),
            bcrypt.gensalt()
        )

    st.session_state.hash_users = hashes


# ---------------------------------------------------
# LOGIN
# ---------------------------------------------------

if "login" not in st.session_state:
    st.session_state.login = False


def validar(user,password):

    if user not in st.session_state.hash_users:
        return False

    hashed = st.session_state.hash_users[user]

    return bcrypt.checkpw(password.encode(),hashed)


if not st.session_state.login:

    st.title("Sistema Estatal Anticorrupción")

    usuario = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Entrar"):

        if validar(usuario,password):

            st.session_state.login = True
            st.session_state.usuario = usuario
            st.rerun()

        else:

            st.error("Usuario o contraseña incorrectos")

    st.stop()


# ---------------------------------------------------
# ACTOR DEL USUARIO
# ---------------------------------------------------

actor_usuario = user_act.loc[
    user_act["user"] == st.session_state.usuario,
    "act"
].values[0]


# ---------------------------------------------------
# LINEAS DEL ACTOR
# ---------------------------------------------------

lineas_actor = pi_actores.loc[
    pi_actores["Actor"] == actor_usuario,
    "Línea de acción"
].unique()


alineacion_actor = alineacion[
    alineacion["Línea de acción"].isin(lineas_actor)
]


# ---------------------------------------------------
# HEADER
# ---------------------------------------------------

col1,col2 = st.columns([8,1])

with col1:

    st.image("www/logo_tablero.png", width=120)
    st.title("Reporte de Acciones 2025")
    st.write("Programa de Implementación del PNA")


with col2:

    if st.button("Cerrar sesión"):

        st.session_state.clear()
        st.rerun()


st.divider()


# ---------------------------------------------------
# SELECTORES
# ---------------------------------------------------

estrategias = alineacion_actor["Estrategia"].unique()

estrategia = st.selectbox(
    "Estrategia",
    estrategias
)


lineas = alineacion_actor.loc[
    alineacion_actor["Estrategia"] == estrategia,
    "Línea de acción"
].unique()


linea = st.selectbox(
    "Línea de Acción",
    lineas
)


# ---------------------------------------------------
# TABLA EN MEMORIA
# ---------------------------------------------------

if "tabla" not in st.session_state:

    st.session_state.tabla = pd.DataFrame(
        columns=[
            "Estrategia",
            "Línea de Acción",
            "Acción",
            "Inicio",
            "Fin",
            "Tipo de Acción",
            "Temática"
        ]
    )


# ---------------------------------------------------
# BOTONES
# ---------------------------------------------------

col1,col2,col3 = st.columns(3)

with col1:

    if st.button("+ Agregar Acción"):

        nueva = {

            "Estrategia":estrategia,
            "Línea de Acción":linea,
            "Acción":"",
            "Inicio":None,
            "Fin":None,
            "Tipo de Acción":"",
            "Temática":""
        }

        st.session_state.tabla.loc[
            len(st.session_state.tabla)
        ] = nueva


with col2:

    st.button("Guardar Borrador")


with col3:

    st.button("Enviar")


# ---------------------------------------------------
# TABLA EDITABLE
# ---------------------------------------------------

if len(st.session_state.tabla) > 0:

    edited = st.data_editor(

        st.session_state.tabla,

        use_container_width=True,

        num_rows="dynamic",

        column_config={

            "Inicio": st.column_config.DateColumn(
                "Inicio"
            ),

            "Fin": st.column_config.DateColumn(
                "Fin"
            ),

            "Tipo de Acción": st.column_config.SelectboxColumn(
                "Tipo de Acción",
                options=opciones_tipo
            ),

            "Temática": st.column_config.SelectboxColumn(
                "Temática",
                options=opciones_tematicas
            )

        }
    )

    st.session_state.tabla = edited
