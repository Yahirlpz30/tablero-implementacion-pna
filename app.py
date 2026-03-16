import streamlit as st
import pandas as pd
import datetime
import os
import io
import dropbox

# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config(layout="wide")

DROPBOX_TOKEN = st.secrets.get("DROPBOX_TOKEN", "")
DROPBOX_FILE = "/tablero_prueba/base.xlsx"
DROPBOX_LOCK = "/tablero_prueba/base.lock"

# -----------------------------
# UTILIDADES DROPBOX
# -----------------------------
def get_dbx():
    if not DROPBOX_TOKEN:
        return None
    return dropbox.Dropbox(DROPBOX_TOKEN)

def dbx_file_exists(dbx, path):
    try:
        dbx.files_get_metadata(path)
        return True
    except:
        return False

def acquire_lock(dbx):
    # Si existe lock y es reciente (<5 min), bloquear
    if dbx_file_exists(dbx, DROPBOX_LOCK):
        meta = dbx.files_get_metadata(DROPBOX_LOCK)
        server_time = meta.server_modified
        if (datetime.datetime.utcnow() - server_time.replace(tzinfo=None)).total_seconds() < 300:
            return False
        # lock viejo → lo borramos
        dbx.files_delete_v2(DROPBOX_LOCK)
    dbx.files_upload(b"lock", DROPBOX_LOCK, mode=dropbox.files.WriteMode.overwrite)
    return True

def release_lock(dbx):
    if dbx_file_exists(dbx, DROPBOX_LOCK):
        dbx.files_delete_v2(DROPBOX_LOCK)

def read_base(dbx):
    if not dbx or not dbx_file_exists(dbx, DROPBOX_FILE):
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

# -----------------------------
# LOGO / HEADER
# -----------------------------
logo = "www/logo_tablero.png"
c1, c2, c3 = st.columns([1,6,2])
with c1:
    if os.path.exists(logo):
        st.image(logo, width=140)
with c2:
    st.markdown("## SISTEMA ESTATAL ANTICORRUPCIÓN")
with c3:
    if st.session_state.get("login", False):
        st.markdown(f"*Usuario:* {st.session_state.usuario}")
        if st.button("Cerrar sesión"):
            st.session_state.clear()
            st.rerun()

# -----------------------------
# LOGIN
# -----------------------------
users = pd.read_excel("www/user-pass.xlsx")  # columnas: user, password, permissions

if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.markdown("### Iniciar sesión")
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")

    if st.button("Entrar"):
        match = users[(users["user"] == u) & (users["password"] == p)]
        if len(match) > 0:
            st.session_state.login = True
            st.session_state.usuario = u
            st.session_state.rol = match.iloc[0]["permissions"]
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos")
    st.stop()

# -----------------------------
# CARGA DE CATÁLOGOS
# -----------------------------
alineacion = pd.read_excel("www/alineacion_pi.xlsx")   # Prioridad PEA, Estrategia, Línea de acción
actores = pd.read_excel("www/pi-actores.xlsx")         # Línea de acción, Actor

# actor desde usuario (ej. ASENL1 -> ASENL)
usuario = st.session_state.usuario
rol = st.session_state.rol
actor = usuario[:-1] if rol != "admin" else None

# -----------------------------
# FILTROS SEGÚN ACTOR
# -----------------------------
if rol == "admin":
    alineacion_filtrada = alineacion.copy()
else:
    lineas_actor = actores[actores["Actor"] == actor]["Línea de acción"].unique()
    alineacion_filtrada = alineacion[alineacion["Línea de acción"].isin(lineas_actor)]

estrategias = sorted(alineacion_filtrada["Estrategia"].dropna().unique())

# -----------------------------
# HEADER TABLERO
# -----------------------------
st.markdown("# Reporte de Acciones 2025")
st.caption("Programa de Implementación del PNA")

b1, b2, b3 = st.columns([1,1,1])
with b1:
    add = st.button("+ Agregar Acción")
with b2:
    save = st.button("Guardar Borrador")
with b3:
    send = st.button("Enviar")

# -----------------------------
# SESSION TABLA
# -----------------------------
if "tabla" not in st.session_state:
    st.session_state.tabla = pd.DataFrame(columns=[
        "Estrategia","Línea de acción","Acción","Inicio","Fin","Tipo de Acción","Temática","Actor","Usuario","Año"
    ])

if add:
    st.session_state.tabla.loc[len(st.session_state.tabla)] = ["","","","", "", "", "", actor if actor else "", usuario, 2025]

# -----------------------------
# RESUMEN
# -----------------------------
acciones = len(st.session_state.tabla)
if "ultimo_guardado" not in st.session_state:
    guardado_msg = "aún no se ha guardado"
else:
    diff = datetime.datetime.now() - st.session_state.ultimo_guardado
    mins = int(diff.total_seconds() // 60)
    guardado_msg = f"hace {mins} min" if mins > 0 else "hace unos segundos"

st.info(f"Año: 2025 | Acciones: {acciones} | Guardado: {guardado_msg}")

# -----------------------------
# TABLA EDITABLE
# -----------------------------
st.markdown("### Acciones")

rows_to_delete = []

for i in range(len(st.session_state.tabla)):
    r = st.session_state.tabla.loc[i]

    c1,c2,c3,c4,c5,c6,c7,c8 = st.columns([2,3,3,2,2,2,2,1])

    # Estrategia
    estrategia = c1.selectbox(
        "Estrategia",
        [""] + estrategias,
        index=0 if r["Estrategia"]=="" else ([""]+estrategias).index(r["Estrategia"]),
        key=f"estr_{i}"
    )

    # Líneas filtradas por estrategia
    lineas = alineacion_filtrada[alineacion_filtrada["Estrategia"]==estrategia]["Línea de acción"].unique() if estrategia else []
    linea = c2.selectbox(
        "Línea de acción",
        [""] + list(lineas),
        index=0 if r["Línea de acción"]=="" else ([""]+list(lineas)).index(r["Línea de acción"]) if r["Línea de acción"] in lineas else 0,
        key=f"lin_{i}"
    )

    accion = c3.text_input("Acción", r["Acción"], key=f"acc_{i}")
    inicio = c4.date_input("Inicio", value=datetime.date.today(), key=f"ini_{i}")
    fin = c5.date_input("Fin", value=datetime.date.today(), key=f"fin_{i}")
    tipo = c6.text_input("Tipo de Acción", r["Tipo de Acción"], key=f"tipo_{i}")
    tem = c7.text_input("Temática", r["Temática"], key=f"tem_{i}")

    delete = c8.button("🗑️", key=f"del_{i}")

    if delete:
        rows_to_delete.append(i)

    st.session_state.tabla.loc[i] = [
        estrategia, linea, accion, inicio, fin, tipo, tem, actor if actor else r["Actor"], usuario, 2025
    ]

# borrar filas
if rows_to_delete:
    st.session_state.tabla.drop(rows_to_delete, inplace=True)
    st.session_state.tabla.reset_index(drop=True, inplace=True)
    st.rerun()

# -----------------------------
# GUARDAR DROPBOX
# -----------------------------
if save or send:
    dbx = get_dbx()
    if not dbx:
        st.error("Dropbox no configurado en secrets")
    else:
        if not acquire_lock(dbx):
            st.warning("Otro usuario está guardando en este momento")
        else:
            try:
                base = read_base(dbx)
                nueva = pd.concat([base, st.session_state.tabla], ignore_index=True)
                write_base(dbx, nueva)
                st.session_state.ultimo_guardado = datetime.datetime.now()
                st.success("Guardado correctamente")
            finally:
                release_lock(dbx)
