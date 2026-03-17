import streamlit as st
import pandas as pd
import datetime
import os
import io
import dropbox

st.set_page_config(layout="wide")

# =========================
# CONFIG DROPBOX
# =========================
DROPBOX_TOKEN = st.secrets.get("DROPBOX_TOKEN", "")
DROPBOX_FILE = "/tablero_prueba/base.xlsx"
DROPBOX_LOCK = "/tablero_prueba/base.lock"

def get_dbx():
    if not DROPBOX_TOKEN:
        return None
    return dropbox.Dropbox(DROPBOX_TOKEN)

def dbx_exists(dbx, path):
    try:
        dbx.files_get_metadata(path)
        return True
    except:
        return False

def acquire_lock(dbx):
    if dbx_exists(dbx, DROPBOX_LOCK):
        meta = dbx.files_get_metadata(DROPBOX_LOCK)
        server_time = meta.server_modified.replace(tzinfo=None)
        if (datetime.datetime.utcnow() - server_time).total_seconds() < 300:
            return False
        dbx.files_delete_v2(DROPBOX_LOCK)
    dbx.files_upload(b"lock", DROPBOX_LOCK, mode=dropbox.files.WriteMode.overwrite)
    return True

def release_lock(dbx):
    if dbx_exists(dbx, DROPBOX_LOCK):
        dbx.files_delete_v2(DROPBOX_LOCK)

def read_base(dbx):
    if not dbx or not dbx_exists(dbx, DROPBOX_FILE):
        return pd.DataFrame(columns=[
            "Estrategia","Línea de acción","Acción","Inicio","Fin","Tipo de Acción","Temática","Actor","Usuario","Año"
        ])
    _, res = dbx.files_download(DROPBOX_FILE)
    return pd.read_excel(io.BytesIO(res.content))

def write_base(dbx, df):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False)
    buffer.seek(0)
    dbx.files_upload(buffer.read(), DROPBOX_FILE, mode=dropbox.files.WriteMode.overwrite)

# =========================
# SESSION STATE SEGURO
# =========================
if "login" not in st.session_state:
    st.session_state.login = False

if "usuario" not in st.session_state:
    st.session_state.usuario = ""

if "rol" not in st.session_state:
    st.session_state.rol = ""

# =========================
# LOGO Y HEADER
# =========================
logo = "www/logo_tablero.png"

col1,col2,col3 = st.columns([1,6,2])

with col1:
    if os.path.exists(logo):
        st.image(logo,width=140)

with col2:
    st.markdown("## SISTEMA ESTATAL ANTICORRUPCIÓN")

with col3:
    if st.session_state.login:
        st.write(f"Usuario: {st.session_state.usuario}")
        if st.button("Cerrar sesión"):
            st.session_state.login=False
            st.session_state.usuario=""
            st.session_state.rol=""
            st.rerun()

# =========================
# LOGIN
# =========================
users = pd.read_excel("www/user-pass.xlsx")

if not st.session_state.login:

    st.markdown("### Iniciar sesión")

    usuario = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Entrar"):

        user = users[
            (users["user"] == usuario) &
            (users["password"] == password)
        ]

        if len(user) > 0:

            st.session_state.login = True
            st.session_state.usuario = usuario
            st.session_state.rol = user.iloc[0]["permissions"]

            st.rerun()

        else:
            st.error("Usuario o contraseña incorrectos")

    st.stop()

# =========================
# CARGA EXCEL
# =========================
alineacion = pd.read_excel("www/alineacion_pi.xlsx")

# =========================
# CREA COLUMNA NÚMERICA PARA ORDENAR 
# =========================
alineacion["orden"] = alineacion["Estrategia"].apply(safe_num)
    lambda x: float(x.split()[0]) if isinstance(x, str) else 999
)

# Ordenar TODO el dataframe
alineacion = alineacion.sort_values("orden")
)
# =========================
# ORDENA DATAFRAME
# =========================
alineacion = alineacion.sort_values("orden")

actores = pd.read_excel("www/pi-actores.xlsx")

usuario = st.session_state.usuario
rol = st.session_state.rol

tipos_accion = pd.read_excel("www/tipo_accion.xlsx")
tipos_accion.columns = tipos_accion.columns.str.strip()

lista_tipo_accion = tipos_accion.iloc[:,0].dropna().unique().tolist()

tematicas = pd.read_excel("www/tematicas.xlsx")
tematicas.columns = tematicas.columns.str.strip()

lista_tematicas = tematicas.iloc[:,0].dropna().unique().tolist()

actor = usuario[:-1] if rol != "admin" else None

# =========================
# FILTRAR POR ACTOR
# =========================
if rol == "admin":
    alineacion_filtrada = alineacion
else:
    lineas_actor = actores[
        actores["Actor"] == actor
    ]["Línea de acción"].unique()

    alineacion_filtrada = alineacion[
        alineacion["Línea de acción"].isin(lineas_actor)
    ]

estrategias = sorted(alineacion_filtrada["Estrategia"].unique())

# =========================
# TITULO
# =========================
st.markdown("# Reporte de Acciones 2025")
st.caption("Programa de Implementación del PNA")

# =========================
# BOTONES
# =========================
b1,b2,b3 = st.columns(3)

add = b1.button("+ Agregar Acción")
save = b2.button("Guardar Borrador")
send = b3.button("Enviar")

# =========================
# TABLA SESSION
# =========================
if "tabla" not in st.session_state or not isinstance(st.session_state.tabla, pd.DataFrame):

    st.session_state.tabla = pd.DataFrame({
        "Estrategia": [],
        "Línea de acción": [],
        "Acción": [],
        "Inicio": [],
        "Fin": [],
        "Tipo de Acción": [],
        "Temática": [],
        "Actor": [],
        "Usuario": [],
        "Año": []
    })

if add:

    nueva = pd.DataFrame([{
        "Estrategia":"",
        "Línea de acción":"",
        "Acción":"",
        "Inicio":"",
        "Fin":"",
        "Tipo de Acción":"",
        "Temática":"",
        "Actor":actor if actor else "",
        "Usuario":usuario,
        "Año":2025
    }])

    st.session_state.tabla = pd.concat(
        [st.session_state.tabla, nueva],
        ignore_index=True
    )

# =========================
# INFO TABLA
# =========================
acciones = len(st.session_state.tabla)

if "ultimo_guardado" not in st.session_state:
    msg_guardado = "aún no se ha guardado"
else:
    if "ultimo_guardado" not in st.session_state or st.session_state.ultimo_guardado is None:
        msg_guardado = "aún no se ha guardado"
    else:
        diff = datetime.datetime.now() - st.session_state.ultimo_guardado
        minutos = int(diff.total_seconds()/60)
        msg_guardado = f"hace {minutos} min" if minutos>0 else "hace unos segundos"

st.info(f"Año: 2025 | Acciones: {acciones} | Guardado: {msg_guardado}")

# =========================
# TABLA (SIEMPRE VISIBLE)
# =========================
st.markdown("### Acciones")

rows_delete = []

for i in range(len(st.session_state.tabla)):

    r = st.session_state.tabla.loc[i]

    c1,c2,c3,c4,c5,c6,c7,c8 = st.columns([2,3,3,2,2,2,2,1])

    estrategia = c1.selectbox(
        "Estrategia",
        [""] + estrategias,
        key=f"estr_{i}"
    )

    lineas = alineacion_filtrada[
        alineacion_filtrada["Estrategia"] == estrategia
    ]["Línea de acción"].unique() if estrategia else []

    linea = c2.selectbox(
        "Línea de acción",
        [""] + list(lineas),
        key=f"lin_{i}"
    )

    accion = c3.text_input("Acción",key=f"acc_{i}")
    inicio = c4.date_input("Inicio",value=datetime.date.today(),key=f"ini_{i}")
    fin = c5.date_input("Fin",value=datetime.date.today(),key=f"fin_{i}")
    tipo = c6.selectbox(
        "Tipo de Acción",
        [""] + list(lista_tipo_accion),
        key=f"tipo_{i}"
    )
    
    tem = c7.selectbox(
        "Temática",
        [""] + list(lista_tematicas),
        key=f"tem_{i}"
    )

    delete = c8.button("🗑️",key=f"del_{i}")

    if delete:
        rows_delete.append(i)

    st.session_state.tabla.loc[i] = [
        estrategia,linea,accion,inicio,fin,tipo,tem,actor if actor else "",usuario,2025
    ]

if rows_delete:
    st.session_state.tabla.drop(rows_delete,inplace=True)
    st.session_state.tabla.reset_index(drop=True,inplace=True)
    st.rerun()

# =========================
# GUARDAR DROPBOX
# =========================
if save or send:

    dbx = get_dbx()

    if not dbx:
        st.error("Dropbox no configurado")
    else:

        if not acquire_lock(dbx):
            st.warning("Otro usuario está guardando")
        else:

            try:

                base = read_base(dbx)

                nueva = pd.concat(
                    [base, st.session_state.tabla],
                    ignore_index=True
                )

                write_base(dbx, nueva)

                st.session_state.ultimo_guardado = datetime.datetime.now()

                st.success("Guardado correctamente")

            finally:
                release_lock(dbx)
