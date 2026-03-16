import streamlit as st
import pandas as pd
import bcrypt
import io
import time

from services.dropbox_service import download_file, upload_file
from services.lock_service import check_lock, create_lock


# =====================================================
# CONFIG
# =====================================================

st.set_page_config(
    page_title="Tablero Implementación PNA",
    layout="wide"
)

BASE_FILE = "/base.xlsx"


# =====================================================
# FUNCION BLINDADA PARA COLUMNAS
# =====================================================

def find_column(df, posibles):

    for c in df.columns:

        nombre = c.lower().strip()

        for p in posibles:

            if p in nombre:

                return c

    return None


# =====================================================
# CARGAR USUARIOS
# =====================================================

users_df = pd.read_excel("www/user-pass.xlsx")

user_col = find_column(users_df, ["user"])
pass_col = find_column(users_df, ["pass"])
perm_col = find_column(users_df, ["perm"])


# =====================================================
# HASH TEMPORAL
# =====================================================

if "hashed_users" not in st.session_state:

    hashed_users = {}

    for _, row in users_df.iterrows():

        hashed = bcrypt.hashpw(str(row[pass_col]).encode(), bcrypt.gensalt())

        hashed_users[row[user_col]] = {
            "hash": hashed,
            "perm": row[perm_col]
        }

    st.session_state.hashed_users = hashed_users


# =====================================================
# LOGIN
# =====================================================

if "login" not in st.session_state:
    st.session_state.login = False


if not st.session_state.login:

    col1,col2,col3 = st.columns([1,2,1])

    with col2:

        st.title("Sistema Estatal Anticorrupción")

        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")

        if st.button("Ingresar"):

            if username in st.session_state.hashed_users:

                stored_hash = st.session_state.hashed_users[username]["hash"]

                if bcrypt.checkpw(password.encode(), stored_hash):

                    st.session_state.login = True
                    st.session_state.user = username

                    st.rerun()

                else:
                    st.error("Contraseña incorrecta")

            else:
                st.error("Usuario no encontrado")

    st.stop()


# =====================================================
# DETECTAR ACTOR
# =====================================================

act_df = pd.read_excel("www/user-act.xlsx")

user_col_act = find_column(act_df, ["user"])
actor_col = find_column(act_df, ["act","actor","institucion"])


actor = "Sin actor"

if user_col_act and actor_col:

    fila = act_df[act_df[user_col_act] == st.session_state.user]

    if len(fila) > 0:

        actor = fila.iloc[0][actor_col]


# =====================================================
# BLOQUEO MULTIUSUARIO
# =====================================================

if check_lock():

    st.warning("⚠ Otro usuario está editando el sistema")

else:

    create_lock(st.session_state.user)


# =====================================================
# CARGAR BASE DESDE DROPBOX
# =====================================================

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


# =====================================================
# ESTRATEGIAS
# =====================================================

alineacion = pd.read_excel("www/alineacion_pi.xlsx")

estrategia_col = find_column(alineacion, ["estrategia"])
linea_col = find_column(alineacion, ["linea"])


estrategias = alineacion[estrategia_col].unique()

estrategia = st.selectbox("Estrategia", estrategias)


lineas = alineacion[alineacion[estrategia_col] == estrategia][linea_col].unique()

linea = st.selectbox("Linea de acción", lineas)


# =====================================================
# BOTONES
# =====================================================

c1,c2,c3 = st.columns(3)

with c1:
    add = st.button("+ Agregar acción")

with c2:
    save = st.button("Guardar")

with c3:
    send = st.button("Enviar")


# =====================================================
# AGREGAR FILA
# =====================================================

if add:

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


# =====================================================
# TABLA
# =====================================================

table_df = pd.DataFrame(st.session_state.table_data)

edited = st.data_editor(

    table_df,
    use_container_width=True,
    num_rows="dynamic"

)

st.session_state.table_data = edited.to_dict("records")


# =====================================================
# GUARDAR
# =====================================================

def save_excel():

    df_save = pd.DataFrame(st.session_state.table_data)

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


# =====================================================
# AUTOGUARDADO
# =====================================================

if "last_save" not in st.session_state:

    st.session_state.last_save = time.time()


if time.time() - st.session_state.last_save > 120:

    save_excel()

    st.session_state.last_save = time.time()

    st.success("Guardado automático")
