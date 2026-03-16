import streamlit as st
import pandas as pd
import bcrypt
import dropbox
import io

st.set_page_config(page_title="Tablero PNA", layout="wide")

# =====================================================
# FUNCION CARGAR EXCEL
# =====================================================

@st.cache_data
def load_excel(path):

    df = pd.read_excel(path)
    df.columns = df.columns.str.strip()

    return df


# =====================================================
# CARGAR ARCHIVOS
# =====================================================

users = load_excel("www/user-pass.xlsx")
user_act = load_excel("www/user-act.xlsx")
pi_actores = load_excel("www/pi-actores.xlsx")
alineacion = load_excel("www/alineacion_pi.xlsx")
tipo_accion = load_excel("www/tipo_accion.xlsx")
tem…
[1:10 AM, 3/16/2026] Yahir Lopez: import streamlit as st
import pandas as pd
import bcrypt
import dropbox
import io

st.set_page_config(page_title="Tablero PNA", layout="wide")

# =====================================================
# FUNCION CARGAR EXCEL
# =====================================================

@st.cache_data
def load_excel(path):

    df = pd.read_excel(path)
    df.columns = df.columns.str.strip()

    return df


# =====================================================
# CARGAR ARCHIVOS
# =====================================================

users = load_excel("www/user-pass.xlsx")
user_act = load_excel("www/user-act.xlsx")
pi_actores = load_excel("www/pi-actores.xlsx")
alineacion = load_excel("www/alineacion_pi.xlsx")
tipo_accion = load_excel("www/tipo_accion.xlsx")
tematicas = load_excel("www/tematicas.xlsx")


# =====================================================
# CATALOGOS
# =====================================================

opciones_tipo = tipo_accion.iloc[:,0].dropna().tolist()
opciones_tematicas = tematicas.iloc[:,0].dropna().tolist()


# =====================================================
# HASH DE CONTRASEÑAS EN MEMORIA
# =====================================================

if "hashed_users" not in st.session_state:

    hashed = {}

    for _,row in users.iterrows():

        hashed[row["user"]] = bcrypt.hashpw(
            str(row["password"]).encode(),
            bcrypt.gensalt()
        )

    st.session_state.hashed_users = hashed


# =====================================================
# LOGIN
# =====================================================

if "login" not in st.session_state:
    st.session_state.login = False


def check_password(user,password):

    if user not in st.session_state.hashed_users:
        return False

    hashed = st.session_state.hashed_users[user]

    return bcrypt.checkpw(password.encode(),hashed)


if not st.session_state.login:

    st.title("Sistema Estatal Anticorrupción")

    user = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Entrar"):

        if check_password(user,password):

            st.session_state.login = True
            st.session_state.user = user

            st.rerun()

        else:

            st.error("Usuario o contraseña incorrectos")

    st.stop()


# =====================================================
# ACTOR DEL USUARIO
# =====================================================

actor_usuario = user_act.loc[
    user_act["user"] == st.session_state.user,
    "act"
].values[0]


# =====================================================
# LINEAS PERMITIDAS
# =====================================================

lineas_actor = pi_actores.loc[
    pi_actores["Actor"] == actor_usuario,
    "Linea_codigo"
].unique()


alineacion_actor = alineacion[
    alineacion["Linea_codigo"].isin(lineas_actor)
]


# =====================================================
# HEADER
# =====================================================

col1,col2,col3 = st.columns([5,2,1])

with col1:
    st.title("Reporte de Acciones 2025")

with col2:
    st.write(f"Usuario: {st.session_state.user}")

with col3:

    if st.button("Cerrar sesión"):

        st.session_state.clear()
        st.rerun()


st.divider()


# =====================================================
# SELECTORES
# =====================================================

estrategias = alineacion_actor["Estrategia"].unique()

estrategia = st.selectbox(
    "Estrategia",
    estrategias
)


lineas = alineacion_actor.loc[
    alineacion_actor["Estrategia"] == estrategia,
    "Linea_codigo"
].unique()


linea = st.selectbox(
    "Línea de acción",
    lineas
)


linea_texto = alineacion_actor.loc[
    alineacion_actor["Linea_codigo"] == linea,
    "Linea_texto"
].values[0]


st.write(linea_texto)


# =====================================================
# TABLA EN MEMORIA
# =====================================================

if "tabla" not in st.session_state:

    st.session_state.tabla = pd.DataFrame(
        columns=[
            "Actor",
            "Estrategia",
            "Linea_codigo",
            "Linea_texto",
            "Accion",
            "Inicio",
            "Fin",
            "Tipo",
            "Tematica"
        ]
    )


# =====================================================
# BOTONES
# =====================================================

col1,col2,col3 = st.columns(3)

with col1:

    if st.button("➕ Agregar Acción"):

        nueva = {

            "Actor": actor_usuario,
            "Estrategia": estrategia,
            "Linea_codigo": linea,
            "Linea_texto": linea_texto,
            "Accion": "",
            "Inicio": None,
            "Fin": None,
            "Tipo": "",
            "Tematica": ""
        }

        st.session_state.tabla.loc[
            len(st.session_state.tabla)
        ] = nueva


with col2:

    if st.button("Guardar Borrador"):

        buffer = io.BytesIO()

        st.session_state.tabla.to_excel(
            buffer,
            index=False
        )

        st.download_button(
            "Descargar borrador",
            buffer.getvalue(),
            file_name="borrador.xlsx"
        )


with col3:

    if st.button("Enviar"):

        buffer = io.BytesIO()

        st.session_state.tabla.to_excel(
            buffer,
            index=False
        )

        dbx = dropbox.Dropbox(
            st.secrets["DROPBOX_TOKEN"]
        )

        dbx.files_upload(
            buffer.getvalue(),
            f"/envios/{actor_usuario}.xlsx",
            mode=dropbox.files.WriteMode.overwrite
        )

        st.success("Acciones enviadas")


st.divider()


# =====================================================
# TABLA EDITABLE
# =====================================================

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

            "Tipo": st.column_config.SelectboxColumn(
                "Tipo de Acción",
                options=opciones_tipo
            ),

            "Tematica": st.column_config.SelectboxColumn(
                "Temática",
                options=opciones_tematicas
            )

        }
    )

    st.session_state.tabla = edited
