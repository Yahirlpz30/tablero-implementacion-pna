import streamlit as st
import pandas as pd
import datetime
import io
import dropbox
from dropbox.files import WriteMode

# ---------------------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA
# ---------------------------------------------------------
st.set_page_config(page_title="Sistema Estatal Anticorrupción", layout="wide")

# ---------------------------------------------------------
# LOGO
# ---------------------------------------------------------
st.image("www/logo_tablero.png", width=220)

# ---------------------------------------------------------
# CARGA DE EXCELS DE CONFIGURACIÓN
# ---------------------------------------------------------
# Alineación PEA (para Estrategia -> Línea -> Acción)
alineacion = pd.read_excel("www/alineacion_pi.xlsx")
alineacion.columns = alineacion.columns.str.strip()

# Catálogos
tipo_accion_df = pd.read_excel("www/tipo_accion.xlsx")
tematicas_df = pd.read_excel("www/tematicas.xlsx")

# Usuarios: login y permisos separados
user_pass = pd.read_excel("www/user-pass.xlsx")  # columnas: usuario, password
user_act  = pd.read_excel("www/user-act.xlsx")   # columnas: usuario, rol, estrategias

# Normalizar columnas
for df in [user_pass, user_act]:
    df.columns = df.columns.str.strip()

# ---------------------------------------------------------
# ESTADO DE SESIÓN
# ---------------------------------------------------------
if "login" not in st.session_state:
    st.session_state.login = False

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

if "ultimo_guardado" not in st.session_state:
    st.session_state.ultimo_guardado = None

# ---------------------------------------------------------
# LOGIN
# ---------------------------------------------------------
if not st.session_state.login:

    st.title("SISTEMA ESTATAL ANTICORRUPCIÓN")

    usuario = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Entrar"):

        user = user_pass[
            (user_pass["usuario"] == usuario) &
            (user_pass["password"] == password)
        ]

        if len(user) > 0:
            st.session_state.login = True
            st.session_state.user = usuario
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos")

    st.stop()

# ---------------------------------------------------------
# USUARIO ACTUAL
# ---------------------------------------------------------
usuario_actual = st.session_state.user

info_usuario = user_act[user_act["usuario"] == usuario_actual].iloc[0]
rol = info_usuario["rol"]

# ---------------------------------------------------------
# FILTRAR ESTRATEGIAS SEGÚN USUARIO
# ---------------------------------------------------------
if rol == "admin":
    estrategias_disponibles = alineacion["Estrategia"].unique()

else:
    estrategias_permitidas = str(info_usuario["estrategias"]).split(",")

    estrategias_disponibles = alineacion[
        alineacion["Estrategia"].astype(str).str.startswith(tuple(estrategias_permitidas))
    ]["Estrategia"].unique()

# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------
col1, col2 = st.columns([8,2])

with col1:
    st.title("Reporte de Acciones 2025")
    st.caption("Programa de Implementación del PNA")

with col2:
    st.write(f"Usuario: {usuario_actual}")
    if st.button("Cerrar sesión"):
        st.session_state.login = False
        st.rerun()

# ---------------------------------------------------------
# BOTONES PRINCIPALES
# ---------------------------------------------------------
b1, b2, b3 = st.columns([2,2,2])

with b1:
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
        st.rerun()

with b2:
    guardar_borrador = st.button("Guardar Borrador")

with b3:
    enviar = st.button("Enviar")

# ---------------------------------------------------------
# INFO DE TABLA
# ---------------------------------------------------------
acciones = len(st.session_state.tabla)

if st.session_state.ultimo_guardado:
    diff = datetime.datetime.now() - st.session_state.ultimo_guardado
    minutos = int(diff.total_seconds() / 60)
    msg_guardado = f"Guardado hace {minutos} min"
else:
    msg_guardado = "Aún no se ha guardado"

st.write(f"Año: 2025 | Acciones: {acciones} | {msg_guardado}")

# ---------------------------------------------------------
# TABLA DINÁMICA
# ---------------------------------------------------------
for i in range(len(st.session_state.tabla)):

    c1,c2,c3,c4,c5,c6,c7,c8 = st.columns([2,2,3,1,1,2,2,0.5])

    # Estrategia
    with c1:
        estrategia = st.selectbox(
            "Estrategia",
            estrategias_disponibles,
            key=f"est_{i}"
        )

    # Línea filtrada por estrategia
    lineas = alineacion[
        alineacion["Estrategia"] == estrategia
    ]["Línea de acción"].unique()

    with c2:
        linea = st.selectbox(
            "Línea",
            lineas,
            key=f"lin_{i}"
        )

    # Acción filtrada por línea
    acciones_linea = alineacion[
        alineacion["Línea de acción"] == linea
    ]["Acción"].tolist()

    with c3:
        accion = st.selectbox(
            "Acción",
            acciones_linea,
            key=f"acc_{i}"
        )

    with c4:
        inicio = st.date_input("Inicio", key=f"ini_{i}")

    with c5:
        fin = st.date_input("Fin", key=f"fin_{i}")

    with c6:
        tipo = st.selectbox(
            "Tipo",
            tipo_accion_df.iloc[:,0],
            key=f"tipo_{i}"
        )

    with c7:
        tema = st.selectbox(
            "Temática",
            tematicas_df.iloc[:,0],
            key=f"tema_{i}"
        )

    # BOTÓN BORRAR
    with c8:
        if st.button("🗑", key=f"del_{i}"):
            st.session_state.tabla = st.session_state.tabla.drop(i)
            st.session_state.tabla.reset_index(drop=True, inplace=True)
            st.rerun()

# ---------------------------------------------------------
# CONEXIÓN DROPBOX
# ---------------------------------------------------------
DROPBOX_TOKEN = st.secrets["DROPBOX_TOKEN"]
dbx = dropbox.Dropbox(DROPBOX_TOKEN)

RUTA_EXCEL = "/tablero_prueba/base.xlsx"
LOCK_FILE = "/tablero_prueba/base.lock"

# ---------------------------------------------------------
# FUNCIONES DE LOCK
# ---------------------------------------------------------
def existe_lock():
    try:
        dbx.files_get_metadata(LOCK_FILE)
        return True
    except:
        return False

def crear_lock():
    dbx.files_upload(
        b"locked",
        LOCK_FILE,
        mode=WriteMode.overwrite
    )

def eliminar_lock():
    try:
        dbx.files_delete_v2(LOCK_FILE)
    except:
        pass

# ---------------------------------------------------------
# GUARDAR A DROPBOX
# ---------------------------------------------------------
def guardar_dropbox(df):

    if existe_lock():
        st.warning("Otro usuario está guardando. Intenta en unos segundos.")
        return

    crear_lock()

    buffer = io.BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)

    dbx.files_upload(
        buffer.read(),
        RUTA_EXCEL,
        mode=WriteMode.overwrite
    )

    eliminar_lock()

    st.session_state.ultimo_guardado = datetime.datetime.now()
    st.success("Archivo guardado correctamente")

# ---------------------------------------------------------
# ACCIONES BOTONES
# ---------------------------------------------------------
if guardar_borrador:
    guardar_dropbox(st.session_state.tabla)

if enviar:
    guardar_dropbox(st.session_state.tabla)
    st.success("Información enviada")
