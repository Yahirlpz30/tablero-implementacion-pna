# =========================================================
# IMPORTACIONES
# =========================================================

import streamlit as st
import pandas as pd
import bcrypt
import io
import time

from services.dropbox_service import download_file, upload_file
from services.lock_service import check_lock, create_lock, delete_lock


# =========================================================
# CONFIGURACIÓN
# =========================================================

st.set_page_config(
    page_title="Tablero Implementación PNA",
    layout="wide"
)

BASE_FILE = "/base.xlsx"


# =========================================================
# ESTILO MODERNO
# =========================================================

st.markdown("""
<style>

.main-card{
background:#f7f9fc;
padding:25px;
border-radius:10px;
margin-bottom:20px;
}

.header-title{
font-size:32px;
font-weight:700;
}

.sub-title{
color:#6c757d;
margin-bottom:20px;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# CARGAR USUARIOS
# =========================================================

users_df = pd.read_excel("www/user-pass.xlsx")


# =========================================================
# HASH TEMPORAL
# =========================================================

if "hashed_users" not in st.session_state:

    hashed_users = {}

    for _, row in users_df.iterrows():

        hashed = bcrypt.hashpw(str(row["password"]).encode(), bcrypt.gensalt())

        hashed_users[row["user"]] = {
            "hash": hashed,
            "permissions": row["permissions"]
        }

    st.session_state.hashed_users = hashed_users


# =========================================================
# LOGIN
# =========================================================

if "login" not in st.session_state:
    st.session_state.login = False


if not st.session_state.login:

    col1,col2,col3 = st.columns([1,2,1])

    with col2:

        st.image("www/logo_tablero.png", width=200)

        st.title("Sistema Estatal Anticorrupción")

        username = st.text_input("Usuario")

        password = st.text_input("Contraseña", type="password")

        if st.button("Ingresar"):

            if username in st.session_state.hashed_users:

                stored_hash = st.session_state.hashed_users[username]["hash"]

                if bcrypt.checkpw(password.encode(), stored_hash):

                    st.session_state.login = True
                    st.session_state.user = username
                    st.session_state.permission = st.session_state.hashed_users[username]["permissions"]

                    st.rerun()

                else:
                    st.error("Contraseña incorrecta")

            else:
                st.error("Usuario no encontrado")

    st.stop()


# =========================================================
# HEADER
# =========================================================

st.image("www/logo_tablero.png", width=150)

st.markdown('<div class="header-title">Reporte de Acciones 2025</div>', unsafe_allow_html=True)

st.markdown('<div class="sub-title">Programa de Implementación del PNA</div>', unsafe_allow_html=True)


# =========================================================
# ACTOR AUTOMÁTICO
# =========================================================

actores_df = pd.read_excel("www/user-act.xlsx")

actor_usuario = actores_df[actores_df["user"] == st.session_state.user]

if len(actor_usuario) > 0:
    actor = actor_usuario.iloc[0]["actor"]
else:
    actor = "Sin actor"


# =========================================================
# BLOQUEO MULTIUSUARIO
# =========================================================

if check_lock():
    st.warning("⚠ Otro usuario está editando el sistema")
else:
    create_lock(st.session_state.user)


# =========================================================
# CARGAR BASE DESDE DROPBOX
# =========================================================

def load_base():

    try:

        data = download_file(BASE_FILE)

        df = pd.read_excel(io.BytesIO(data))

        return df

    except:

        return pd.DataFrame()


df = load_base()


if "table_data" not in st.session_state:

    if not df.empty:
        st.session_state.table_data = df.to_dict("records")
    else:
        st.session_state.table_data = []


# =========================================================
# BOTONES
# =========================================================

c1,c2,c3 = st.columns(3)

with c1:
    add_action = st.button("+ Agregar Acción", use_container_width=True)

with c2:
    save_draft = st.button("Guardar Borrador", use_container_width=True)

with c3:
    send = st.button("Enviar", use_container_width=True)


# =========================================================
# ESTRATEGIAS
# =========================================================

alineacion = pd.read_excel("www/alineacion_pi.xlsx")

estrategias = alineacion["Estrategia"].unique()

estrategia = st.selectbox("Estrategia", estrategias)

lineas = alineacion[alineacion["Estrategia"] == estrategia]["Linea"].unique()

linea = st.selectbox("Línea de acción", lineas)


# =========================================================
# AGREGAR ACCIÓN
# =========================================================

if add_action:

    st.session_state.table_data.append({

        "Actor":actor,
        "Estrategia":estrategia,
        "Linea":linea,
        "Accion":"",
        "Inicio":"",
        "Fin":"",
        "Tipo":"",
        "Tematica":""

    })


# =========================================================
# TABLA EDITABLE
# =========================================================

df_table = pd.DataFrame(st.session_state.table_data)

edited = st.data_editor(
    df_table,
    use_container_width=True,
    num_rows="dynamic"
)

st.session_state.table_data = edited.to_dict("records")


# =========================================================
# GUARDAR
# =========================================================

def save_excel():

    df_save = pd.DataFrame(st.session_state.table_data)

    buffer = io.BytesIO()

    df_save.to_excel(buffer, index=False)

    buffer.seek(0)

    upload_file(BASE_FILE, buffer.read())


if save_draft:
    save_excel()
    st.success("Guardado correctamente")


if send:
    save_excel()
    st.success("Reporte enviado")


# =========================================================
# AUTOGUARDADO
# =========================================================

if "last_save" not in st.session_state:
    st.session_state.last_save = time.time()

if time.time() - st.session_state.last_save > 120:

    save_excel()

    st.session_state.last_save = time.time()

    st.success("Guardado automático realizado")
