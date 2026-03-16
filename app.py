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

BASE_FILE = "/base_pna.xlsx"


# =====================================================
# ESTILOS
# =====================================================

st.markdown("""
<style>

header {visibility: hidden;}

.stButton>button {
    background-color:#0b7c83;
    color:white;
    border-radius:6px;
    height:40px;
}

.logout button {
    background-color:#a11d3a;
}

</style>
""", unsafe_allow_html=True)


# =====================================================
# FUNCION BUSCAR COLUMNA
# =====================================================

def find_column(df, keys):

    for c in df.columns:

        name = c.lower()

        for k in keys:

            if k in name:

                return c

    return None


# =====================================================
# LOGIN
# =====================================================

users = pd.read_excel("www/user-pass.xlsx")

user_col = find_column(users, ["user"])
pass_col = find_column(users, ["pass"])


if "login" not in st.session_state:
    st.session_state.login = False


if "hash_users" not in st.session_state:

    hashes = {}

    for _,row in users.iterrows():

        hashes[row[user_col]] = bcrypt.hashpw(
            str(row[pass_col]).encode(),
            bcrypt.gensalt()
        )

    st.session_state.hash_users = hashes


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


# =====================================================
# HEADER
# =====================================================

col1,col2,col3 = st.columns([1,6,2])

with col1:
    st.image("www/logo_tablero.png", width=120)

with col2:
    st.markdown("### Sistema Estatal Anticorrupción")

with col3:

    st.write(f"Usuario: *{st.session_state.user}*")

    if st.button("Cerrar sesión"):

        for k in list(st.session_state.keys()):
            del st.session_state[k]

        st.rerun()


st.divider()


# =====================================================
# SIDEBAR
# =====================================================

with st.sidebar:

    st.markdown("### Año")

    year = st.selectbox("", ["2025"])


# =====================================================
# ACTOR
# =====================================================

actores = pd.read_excel("www/user-act.xlsx")

user_col_act = find_column(actores, ["user"])
actor_col = find_column(actores, ["act"])


actor = "Sin actor"

fila = actores[actores[user_col_act] == st.session_state.user]

if len(fila) > 0:

    actor = fila.iloc[0][actor_col]


# =====================================================
# BLOQUEO
# =====================================================

if check_lock():

    st.warning("⚠ Otro usuario está editando")

else:

    create_lock(st.session_state.user)


# =====================================================
# CARGAR BASE
# =====================================================

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


# =====================================================
# TITULO
# =====================================================

st.title("Reporte de Acciones 2025")
st.caption("Programa de Implementación del PNA")


# =====================================================
# BOTONES
# =====================================================

col1,col2,col3 = st.columns(3)

with col1:
    add = st.button("➕ Agregar Acción")

with col2:
    save = st.button("💾 Guardar Borrador")

with col3:
    send = st.button("📤 Enviar")


# =====================================================
# ALINEACION
# =====================================================

alineacion = pd.read_excel("www/alineacion_pi.xlsx")

estrategia_col = find_column(alineacion, ["estrategia"])
linea_col = find_column(alineacion, ["linea","línea"])


estrategia = st.selectbox(
    "Estrategia",
    alineacion[estrategia_col].unique()
)

lineas = alineacion.loc[
    alineacion[estrategia_col] == estrategia,
    linea_col
].unique()

linea = st.selectbox(
    "Línea de acción",
    lineas
)

acciones = alineacion.loc[
    alineacion[linea_col] == linea,
    linea_col
]

accion = st.selectbox(
    "Acción",
    acciones
)


# =====================================================
# AGREGAR FILA
# =====================================================

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


# =====================================================
# TABLA
# =====================================================

st.info(
    f"Año: {year} | Acciones: {len(st.session_state.data)}"
)

df_table = pd.DataFrame(st.session_state.data)

edited = st.data_editor(
    df_table,
    num_rows="dynamic",
    use_container_width=True,
    height=400
)

st.session_state.data = edited.to_dict("records")


# =====================================================
# GUARDAR
# =====================================================

def save_excel():

    df_save = pd.DataFrame(st.session_state.data)

    buffer = io.BytesIO()

    df_save.to_excel(buffer, index=False)

    buffer.seek(0)

    upload_file(BASE_FILE, buffer.read())


if save:

    save_excel()

    st.success("Guardado correctamente")


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

    st.success("✔ Guardado automáticamente")
