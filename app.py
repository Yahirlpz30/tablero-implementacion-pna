import streamlit as st
import pandas as pd
import bcrypt
import io
import time

from services.dropbox_service import download_file, upload_file
from services.lock_service import check_lock, create_lock


# ======================================================
# CONFIGURACIÓN
# ======================================================

st.set_page_config(
    page_title="Tablero Implementación PNA",
    layout="wide"
)

BASE_FILE = "/base_pna.xlsx"


# ======================================================
# FUNCION PARA DETECTAR COLUMNAS
# ======================================================

def find_column(df, keywords):

    for c in df.columns:

        name = c.lower()

        for k in keywords:

            if k in name:

                return c

    return None


# ======================================================
# LOGIN
# ======================================================

users = pd.read_excel("www/user-pass.xlsx")

user_col = find_column(users, ["user"])
pass_col = find_column(users, ["pass"])
perm_col = find_column(users, ["perm"])


if "login" not in st.session_state:
    st.session_state.login = False


if "hash_users" not in st.session_state:

    hashed = {}

    for _, row in users.iterrows():

        hashed[row[user_col]] = bcrypt.hashpw(
            str(row[pass_col]).encode(),
            bcrypt.gensalt()
        )

    st.session_state.hash_users = hashed


if not st.session_state.login:

    st.title("Sistema Estatal Anticorrupción")

    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):

        if username in st.session_state.hash_users:

            if bcrypt.checkpw(
                password.encode(),
                st.session_state.hash_users[username]
            ):

                st.session_state.login = True
                st.session_state.user = username

                st.rerun()

            else:

                st.error("Contraseña incorrecta")

        else:

            st.error("Usuario no encontrado")

    st.stop()


# ======================================================
# ACTOR AUTOMÁTICO
# ======================================================

actores = pd.read_excel("www/user-act.xlsx")

user_col_act = find_column(actores, ["user"])
actor_col = find_column(actores, ["act","actor"])


actor = "Sin actor"

fila = actores[actores[user_col_act] == st.session_state.user]

if len(fila) > 0:

    actor = fila.iloc[0][actor_col]


# ======================================================
# BLOQUEO MULTIUSUARIO
# ======================================================

if check_lock():

    st.warning("⚠ Otro usuario está editando")

else:

    create_lock(st.session_state.user)


# ======================================================
# CARGAR BASE
# ======================================================

def load_base():

    try:

        data = download_file(BASE_FILE)

        df = pd.read_excel(io.BytesIO(data))

        return df

    except:

        return pd.DataFrame()


df = load_base()

if "data" not in st.session_state:

    if not df.empty:

        st.session_state.data = df.to_dict("records")

    else:

        st.session_state.data = []


# ======================================================
# CARGAR ALINEACIÓN
# ======================================================

alineacion = pd.read_excel("www/alineacion_pi.xlsx")

estrategia_col = find_column(alineacion, ["estrategia"])
linea_col = find_column(alineacion, ["linea","línea"])
accion_col = find_column(alineacion, ["accion"])


# ======================================================
# INTERFAZ
# ======================================================

st.title("Reporte de Acciones 2025")
st.caption("Programa de Implementación del PNA")


col1,col2,col3 = st.columns(3)

with col1:

    estrategia = st.selectbox(
        "Estrategia",
        alineacion[estrategia_col].unique()
    )


lineas = alineacion.loc[
    alineacion[estrategia_col] == estrategia,
    linea_col
].unique()


with col2:

    linea = st.selectbox(
        "Línea de acción",
        lineas
    )


acciones = alineacion.loc[
    alineacion[linea_col] == linea,
    accion_col
]


with col3:

    accion = st.selectbox(
        "Acción",
        acciones
    )


# ======================================================
# BOTONES
# ======================================================

c1,c2,c3 = st.columns(3)

with c1:

    add = st.button("+ Agregar acción")


with c2:

    save = st.button("Guardar")


with c3:

    send = st.button("Enviar")


# ======================================================
# AGREGAR FILA
# ======================================================

if add:

    st.session_state.data.append({

        "Actor":actor,
        "Estrategia":estrategia,
        "Linea":linea,
        "Accion":accion,
        "Inicio":"",
        "Fin":"",
        "Tipo":"",
        "Tematica":""

    })


# ======================================================
# TABLA
# ======================================================

df_table = pd.DataFrame(st.session_state.data)

edited = st.data_editor(

    df_table,
    num_rows="dynamic",
    use_container_width=True

)

st.session_state.data = edited.to_dict("records")


# ======================================================
# GUARDAR
# ======================================================

def save_excel():

    df_save = pd.DataFrame(st.session_state.data)

    buffer = io.BytesIO()

    df_save.to_excel(buffer, index=False)

    buffer.seek(0)

    upload_file(BASE_FILE, buffer.read())


if save:

    save_excel()

    st.success("Guardado")


if send:

    save_excel()

    st.success("Reporte enviado")


# ======================================================
# AUTOGUARDADO
# ======================================================

if "last_save" not in st.session_state:

    st.session_state.last_save = time.time()


if time.time() - st.session_state.last_save > 120:

    save_excel()

    st.session_state.last_save = time.time()

    st.success("Guardado automático")
