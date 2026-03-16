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
    layout="wide",
    page_icon="www/favicon.png"
)

BASE_FILE = "/base_pna.xlsx"


# =====================================================
# ESTILOS
# =====================================================

st.markdown("""
<style>
.stButton>button {
    background-color:#0b7c83;
    color:white;
    border-radius:6px;
    height:40px;
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
# CARGAR EXCEL
# =====================================================

def load_excel(path):

    try:
        return pd.read_excel(path)

    except:
        st.error(f"No se pudo cargar {path}")
        st.stop()


# =====================================================
# LOGIN
# =====================================================

users = load_excel("www/user-pass.xlsx")

user_col = find_column(users, ["user"])
pass_col = find_column(users, ["pass"])

if "login" not in st.session_state:
    st.session_state.login = False

if "hash_users" not in st.session_state:

    hashes = {}

    for _, row in users.iterrows():

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
    st.image("www/logo_tablero.png", width=110)

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
# ACTOR AUTOMATICO
# =====================================================

actores = load_excel("www/user-act.xlsx")

user_col_act = find_column(actores, ["user"])
actor_col = find_column(actores, ["act"])

fila = actores[actores[user_col_act] == st.session_state.user]

actor = "SIN_ACTOR"

if len(fila) > 0:
    actor = fila.iloc[0][actor_col]


# =====================================================
# BLOQUEO MULTIUSUARIO
# =====================================================

try:

    if check_lock():
        st.warning("⚠ Otro usuario está editando")

    else:
        create_lock(st.session_state.user)

except:
    pass


# =====================================================
# CARGAR BASE DROPBOX
# =====================================================

def load_base():

    try:

        data = download_file(BASE_FILE)

        return pd.read_excel(io.BytesIO(data))

    except:

        return pd.DataFrame()


df = load_base()

if "data" not in st.session_state:

    if not df.empty:
        st.session_state.data = df.to_dict("records")

    else:
        st.session_state.data = []


# =====================================================
# CARGAR CATALOGOS
# =====================================================

alineacion = load_excel("www/alineacion_pi.xlsx")

tipo_df = load_excel("www/tipo_accion.xlsx")

tipo_list = tipo_df.iloc[:,0].dropna().tolist()

estrategia_col = find_column(alineacion, ["estrategia"])
linea_col = find_column(alineacion, ["linea","línea"])


# =====================================================
# FILTRAR LINEAS POR ACTOR
# =====================================================

actores_lineas = load_excel("www/pi-actores.xlsx")

actor_col_actor = find_column(actores_lineas, ["actor"])
linea_col_actor = find_column(actores_lineas, ["linea","línea"])

lineas_actor = actores_lineas.loc[
    actores_lineas[actor_col_actor] == actor,
    linea_col_actor
].dropna().unique()


# =====================================================
# TITULO
# =====================================================

st.title("Reporte de Acciones 2025")
st.caption("Programa de Implementación del PNA")
st.caption(f"Institución: *{actor}*")


# =====================================================
# SELECTORES
# =====================================================

col1,col2,col3 = st.columns(3)

with col1:

    estrategias = alineacion[estrategia_col].dropna().unique()

    estrategia = st.selectbox("Estrategia", estrategias)


lineas = alineacion.loc[
    (alineacion[estrategia_col] == estrategia) &
    (alineacion[linea_col].isin(lineas_actor)),
    linea_col
].dropna().unique()


with col2:

    linea = st.selectbox("Línea de acción", lineas)


with col3:

    accion = st.text_input("Acción")


st.divider()


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
# AGREGAR FILA
# =====================================================

if add:

    st.session_state.data.append({

        "Actor": actor,
        "Estrategia": estrategia,
        "Linea": linea,
        "Accion": accion,
        "Inicio": "",
        "Fin": "",
        "Tipo": "",
        "Tematica": ""

    })


# =====================================================
# FILTRAR SOLO INSTITUCION
# =====================================================

df_all = pd.DataFrame(st.session_state.data)

if "Actor" not in df_all.columns:
    df_all["Actor"] = actor

df_table = df_all[df_all["Actor"] == actor].copy()


# =====================================================
# TABLA CON BOTON ELIMINAR
# =====================================================

df_table["Eliminar"] = False

edited = st.data_editor(

    df_table,

    num_rows="dynamic",

    use_container_width=True,

    height=420,

    column_config={

        "Eliminar": st.column_config.CheckboxColumn(
            "🗑",
            help="Eliminar fila"
        ),

        "Inicio": st.column_config.DateColumn(
            "Inicio",
            format="DD/MM/YYYY"
        ),

        "Fin": st.column_config.DateColumn(
            "Fin",
            format="DD/MM/YYYY"
        ),

        "Tipo": st.column_config.SelectboxColumn(
            "Tipo de Acción",
            options=tipo_list
        ),

        "Tematica": st.column_config.TextColumn("Temática")

    }

)

edited = edited[edited["Eliminar"] == False]

edited = edited.drop(columns=["Eliminar"])


# =====================================================
# PROTEGER DATOS DE OTROS ACTORES
# =====================================================

edited_records = edited.to_dict("records")

df_original = pd.DataFrame(st.session_state.data)

otros = df_original[df_original["Actor"] != actor]

nuevo = pd.DataFrame(edited_records)

nuevo["Actor"] = actor

final = pd.concat([otros, nuevo], ignore_index=True)

st.session_state.data = final.to_dict("records")


# =====================================================
# GUARDAR
# =====================================================

def save_excel():

    df_save = pd.DataFrame(st.session_state.data)

    buffer = io.BytesIO()

    df_save.to_excel(buffer, index=False)

    buffer.seek(0)

    try:
        upload_file(BASE_FILE, buffer.read())

    except:
        st.warning("No se pudo guardar en Dropbox")


if save:

    save_excel()
    st.success("Guardado correctamente")


if send:

    save_excel()
    st.success("Reporte enviado")


# =====================================================
# AUTOSAVE
# =====================================================

if "last_save" not in st.session_state:
    st.session_state.last_save = time.time()

if time.time() - st.session_state.last_save > 120:

    save_excel()

    st.session_state.last_save = time.time()

    st.success("✔ Guardado automáticamente")
