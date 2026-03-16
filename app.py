import streamlit as st
import pandas as pd
import dropbox
import json
from datetime import datetime, timedelta

st.set_page_config(layout="wide")

# -----------------------------
# ESTILOS
# -----------------------------

st.markdown("""
<style>

.block-container{
padding-top:1rem;
}

.stButton>button{
border-radius:8px;
height:40px;
}

.sidebar .sidebar-content{
background-color:#2c2f33;
}

</style>
""",unsafe_allow_html=True)

# -----------------------------
# DROPBOX
# -----------------------------

DROPBOX_TOKEN = st.secrets["DROPBOX_TOKEN"]

dbx = dropbox.Dropbox(DROPBOX_TOKEN)

ARCHIVO = "/tablero_prueba/base.xlsx"
ARCHIVO_LOCK = "/tablero_prueba/lock_base.json"

# -----------------------------
# FUNCIONES DROPBOX
# -----------------------------

def descargar_excel():

    try:

        metadata,res = dbx.files_download(ARCHIVO)

        return pd.read_excel(res.content)

    except:

        return pd.DataFrame()

def subir_excel(df):

    dbx.files_upload(
        df.to_csv(index=False).encode(),
        ARCHIVO,
        mode=dropbox.files.WriteMode.overwrite
    )

# -----------------------------
# FUNCIONES LOCK
# -----------------------------

def leer_lock():

    try:

        metadata,res = dbx.files_download(ARCHIVO_LOCK)

        return json.loads(res.content)

    except:

        return None


def crear_lock(usuario):

    lock = leer_lock()

    if lock:

        tiempo_lock = datetime.fromisoformat(lock["time"])

        if datetime.now() - tiempo_lock < timedelta(minutes=2):

            return False

    data = {
        "usuario":usuario,
        "time":datetime.now().isoformat()
    }

    dbx.files_upload(
        json.dumps(data).encode(),
        ARCHIVO_LOCK,
        mode=dropbox.files.WriteMode.overwrite
    )

    return True


def liberar_lock():

    try:

        dbx.files_delete_v2(ARCHIVO_LOCK)

    except:

        pass

# -----------------------------
# LOGIN
# -----------------------------

usuarios = pd.read_excel("www/user-pass.xlsx")

if "login" not in st.session_state:
    st.session_state.login=False

if not st.session_state.login:

    st.image("www/logo_tablero.png",width=200)

    st.title("SISTEMA ESTATAL ANTICORRUPCIÓN")

    user = st.text_input("Usuario")
    password = st.text_input("Contraseña",type="password")

    if st.button("Entrar"):

        row = usuarios[
            (usuarios["user"]==user) &
            (usuarios["password"]==password)
        ]

        if len(row)>0:

            st.session_state.login=True
            st.session_state.usuario=user
            st.rerun()

        else:

            st.error("Usuario o contraseña incorrectos")

    st.stop()

# -----------------------------
# HEADER
# -----------------------------

col1,col2,col3 = st.columns([1,6,1])

with col1:
    st.image("www/logo_tablero.png",width=120)

with col3:

    if st.button("Cerrar sesión"):

        st.session_state.login=False
        st.rerun()

# -----------------------------
# SIDEBAR
# -----------------------------

st.sidebar.markdown("### 2025")

# -----------------------------
# TITULO
# -----------------------------

st.title("Reporte de Acciones 2025")
st.caption("Programa de Implementación del PNA")

# -----------------------------
# BOTONES
# -----------------------------

colA,colB,colC = st.columns([1,1,1])

with colA:
    agregar = st.button("+ Agregar Acción")

with colB:
    guardar = st.button("Guardar Borrador")

with colC:
    enviar = st.button("Enviar")

# -----------------------------
# CATALOGOS
# -----------------------------

alineacion = pd.read_excel("www/alineacion_pi.xlsx")
tipo_accion = pd.read_excel("www/tipo_accion.xlsx")
tematicas = pd.read_excel("www/tematicas.xlsx")

estrategias = alineacion["Estrategia"].dropna().unique().tolist()
tipos = tipo_accion.iloc[:,0].dropna().tolist()
temas = tematicas.iloc[:,0].dropna().tolist()

# -----------------------------
# SESSION TABLA
# -----------------------------

if "tabla" not in st.session_state:

    st.session_state.tabla = pd.DataFrame(columns=[
        "Estrategia",
        "Linea",
        "Accion",
        "Inicio",
        "Fin",
        "Tipo",
        "Tematica"
    ])

# -----------------------------
# AGREGAR FILA
# -----------------------------

if agregar:

    nueva = pd.DataFrame([{
        "Estrategia":"",
        "Linea":"",
        "Accion":"",
        "Inicio":"",
        "Fin":"",
        "Tipo":"",
        "Tematica":""
    }])

    st.session_state.tabla = pd.concat(
        [st.session_state.tabla,nueva],
        ignore_index=True
    )

    st.rerun()

df = st.session_state.tabla

# -----------------------------
# INFO
# -----------------------------

st.write(f"Año: 2025 | Acciones: {len(df)}")

# -----------------------------
# CABECERA TABLA
# -----------------------------

h0,h1,h2,h3,h4,h5,h6,h7,h8 = st.columns([0.5,2,2,3,1.5,1.5,2,2,0.5])

h1.write("Estrategia")
h2.write("Línea de Acción")
h3.write("Acción")
h4.write("Inicio")
h5.write("Fin")
h6.write("Tipo de Acción")
h7.write("Temática")

# -----------------------------
# FILAS
# -----------------------------

for i in df.index:

    c0,c1,c2,c3,c4,c5,c6,c7,c8 = st.columns([0.5,2,2,3,1.5,1.5,2,2,0.5])

    with c1:

        estrategia = st.selectbox(
            "",
            estrategias,
            key=f"estrategia_{i}"
        )

        df.at[i,"Estrategia"]=estrategia

    lineas = alineacion[
        alineacion["Estrategia"]==estrategia
    ]["Línea de acción"].tolist()

    with c2:

        linea = st.selectbox(
            "",
            lineas,
            key=f"linea_{i}"
        )

        df.at[i,"Linea"]=linea

    acciones = alineacion[
        alineacion["Línea de acción"]==linea
    ]["Acción"].tolist()

    with c3:

        accion = st.selectbox(
            "",
            acciones,
            key=f"accion_{i}"
        )

        df.at[i,"Accion"]=accion

    with c4:

        inicio = st.date_input("",key=f"inicio_{i}")
        df.at[i,"Inicio"]=inicio

    with c5:

        fin = st.date_input("",key=f"fin_{i}")
        df.at[i,"Fin"]=fin

    with c6:

        tipo = st.selectbox("",tipos,key=f"tipo_{i}")
        df.at[i,"Tipo"]=tipo

    with c7:

        tematica = st.selectbox("",temas,key=f"tema_{i}")
        df.at[i,"Tematica"]=tematica

    with c8:

        if st.button("🗑",key=f"del_{i}"):

            st.session_state.tabla = st.session_state.tabla.drop(i).reset_index(drop=True)

            st.rerun()

# -----------------------------
# GUARDAR
# -----------------------------

if guardar:

    if crear_lock(st.session_state.usuario):

        subir_excel(st.session_state.tabla)

        liberar_lock()

        st.success(f"Guardado: {datetime.now().strftime('%H:%M')}")

    else:

        lock = leer_lock()

        if lock:

            st.error(f"Archivo en edición por {lock['usuario']}")

# -----------------------------
# ENVIAR
# -----------------------------

if enviar:

    if crear_lock(st.session_state.usuario):

        subir_excel(st.session_state.tabla)

        liberar_lock()

        st.success("Enviado correctamente")

    else:

        lock = leer_lock()

        if lock:

            st.error(f"Archivo en edición por {lock['usuario']}")
