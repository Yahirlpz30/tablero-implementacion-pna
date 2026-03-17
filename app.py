import streamlit as st
import pandas as pd
import datetime
import os
import io
import dropbox
import re

st.set_page_config(layout="wide")

# =========================
# CSS PRO
# =========================
st.markdown("""
<style>

/* TABLA TIPO DASHBOARD */
.card-tabla {
    background: white;
    border-radius: 12px;
    border: 1px solid #e6e6e6;
    padding: 15px;
    margin-top: 10px;
}

/* HEADER */
.header-tabla {
    font-weight: 600;
    color: #555;
    border-bottom: 2px solid #e6e6e6;
    padding-bottom: 8px;
    margin-bottom: 10px;
}

/* FILAS */
.fila-tabla {
    border-bottom: 1px solid #eee;
    padding: 10px 0;
}

/* SOLUCIÓN DROPDOWN (CLAVE) */
div[data-baseweb="popover"] {
    z-index: 999999 !important;
}

/* ESPACIO ENTRE FILAS */
.bloque-fila {
    margin-bottom: 15px;
}

</style>
""", unsafe_allow_html=True)

# =========================
# SESSION STATE
# =========================
if "tabla" not in st.session_state:
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

if "login" not in st.session_state:
    st.session_state.login = False

# =========================
# DROPBOX
# =========================
DROPBOX_TOKEN = st.secrets.get("DROPBOX_TOKEN", "")
DROPBOX_FILE = "/tablero_prueba/base.xlsx"
DROPBOX_LOCK = "/tablero_prueba/base.lock"

def get_dbx():
    return dropbox.Dropbox(DROPBOX_TOKEN) if DROPBOX_TOKEN else None

def dbx_exists(dbx, path):
    try:
        dbx.files_get_metadata(path)
        return True
    except:
        return False

def acquire_lock(dbx):
    if dbx_exists(dbx, DROPBOX_LOCK):
        return False
    dbx.files_upload(b"lock", DROPBOX_LOCK, mode=dropbox.files.WriteMode.overwrite)
    return True

def release_lock(dbx):
    if dbx_exists(dbx, DROPBOX_LOCK):
        dbx.files_delete_v2(DROPBOX_LOCK)

def read_base(dbx):
    if not dbx or not dbx_exists(dbx, DROPBOX_FILE):
        return pd.DataFrame()
    _, res = dbx.files_download(DROPBOX_FILE)
    return pd.read_excel(io.BytesIO(res.content))

def write_base(dbx, df):
    buffer = io.BytesIO()

    df["Inicio"] = pd.to_datetime(df["Inicio"], errors="coerce")
    df["Fin"] = pd.to_datetime(df["Fin"], errors="coerce")

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)

        sheet = writer.sheets["Sheet1"]

        for col in ["Inicio", "Fin"]:
            col_idx = df.columns.get_loc(col) + 1
            for row in range(2, len(df) + 2):
                sheet.cell(row=row, column=col_idx).number_format = "YYYY-MM-DD"

    buffer.seek(0)
    dbx.files_upload(buffer.read(), DROPBOX_FILE, mode=dropbox.files.WriteMode.overwrite)

# =========================
# LOGIN
# =========================
users = pd.read_excel("www/user-pass.xlsx")

if not st.session_state.login:

    col_logo, col_title = st.columns([1,3])

with col_logo:
    if os.path.exists("www/logo_tablero.png"):
        st.image("www/logo_tablero.png", width=120)

with col_title:
    st.title("INICIAR SESIÓN")

    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")

    if st.button("Entrar"):
        user = users[(users["user"] == u) & (users["password"] == p)]
        if len(user):
            st.session_state.login = True
            st.session_state.usuario = u
            st.session_state.rol = user.iloc[0]["permissions"]
            st.rerun()
        else:
            st.error("Credenciales incorrectas")

    st.stop()

# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.markdown("# 2025")

# =========================
# DATA
# =========================
alineacion = pd.read_excel("www/alineacion_pi.xlsx")
alineacion["Estrategia"] = alineacion["Estrategia"].astype(str).str.strip()

def extraer(x):
    m = re.search(r"\d+\.\d+", str(x))
    return float(m.group()) if m else 999

alineacion["orden"] = alineacion["Estrategia"].apply(extraer)
alineacion = alineacion.sort_values("orden")

estrategias = alineacion["Estrategia"].dropna().unique().tolist()

tipos_accion = pd.read_excel("www/tipo_accion.xlsx")
lista_tipo_accion = tipos_accion.iloc[:,0].dropna().tolist()

tematicas = pd.read_excel("www/tematicas.xlsx")
lista_tematicas = tematicas.iloc[:,0].dropna().tolist()

usuario = st.session_state.usuario
actor = usuario

# =========================
# HEADER
# =========================
col1, col2, col3 = st.columns([1,6,2])

with col1:
    if os.path.exists("www/logo_tablero.png"):
        st.image("www/logo_tablero.png", width=140)

with col2:
    st.markdown("## Sistema Estatal Anticorrupción")

with col3:
    st.write(f"Usuario: {st.session_state.usuario}")

# =========================
# BOTONES
# =========================
b1,b2,b3 = st.columns(3)

add = b1.button("➕ Agregar acción", use_container_width=True)
save = b2.button("💾 Guardar borrador", use_container_width=True)
send = b3.button("📤 Enviar", use_container_width=True)

if add:
    nueva = pd.DataFrame([{
        "Estrategia":"","Línea de acción":"","Acción":"",
        "Inicio":"","Fin":"","Tipo de Acción":"","Temática":"",
        "Actor":actor,"Usuario":usuario,"Año":2025
    }])
    st.session_state.tabla = pd.concat([st.session_state.tabla, nueva], ignore_index=True)
    st.rerun()

# =========================
# TABLA PRO
# =========================
st.markdown('<div class="card-tabla">', unsafe_allow_html=True)

st.markdown("### Acciones")

# HEADER
h1,h2,h3,h4,h5,h6,h7,h8 = st.columns([2,3,3,2,2,2,2,1])

h1.markdown('<div class="header-tabla">Estrategia</div>', unsafe_allow_html=True)
h2.markdown('<div class="header-tabla">Línea de acción</div>', unsafe_allow_html=True)
h3.markdown('<div class="header-tabla">Acción</div>', unsafe_allow_html=True)
h4.markdown('<div class="header-tabla">Inicio</div>', unsafe_allow_html=True)
h5.markdown('<div class="header-tabla">Fin</div>', unsafe_allow_html=True)
h6.markdown('<div class="header-tabla">Tipo de Acción</div>', unsafe_allow_html=True)
h7.markdown('<div class="header-tabla">Temática</div>', unsafe_allow_html=True)
h8.markdown("")

rows_delete = []

for i in range(len(st.session_state.tabla)):

    st.markdown('<div class="bloque-fila">', unsafe_allow_html=True)

    c1,c2,c3,c4,c5,c6,c7,c8 = st.columns([2,3,3,2,2,2,2,1])

    estrategia = c1.selectbox(
        "",
        [""] + estrategias,
        key=f"estr_{i}"
    )

    lineas = alineacion_filtrada[
        alineacion_filtrada["Estrategia"] == estrategia
    ]["Línea de acción"].unique() if estrategia else []

    linea = c2.selectbox(
        "",
        [""] + list(lineas),
        key=f"lin_{i}"
    )

    accion = c3.text_input("", key=f"acc_{i}")

    inicio = c4.date_input("", value=datetime.date.today(), key=f"ini_{i}")
    fin = c5.date_input("", value=datetime.date.today(), key=f"fin_{i}")

    tipo = c6.selectbox("", [""] + lista_tipo_accion, key=f"tipo_{i}")
    tem = c7.selectbox("", [""] + lista_tematicas, key=f"tem_{i}")

    delete = c8.button("🗑️", key=f"del_{i}")

    if delete:
        rows_delete.append(i)

    st.session_state.tabla.loc[i] = [
        estrategia, linea, accion, inicio, fin,
        tipo, tem, actor if actor else "", usuario, 2025
    ]

    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

if rows_delete:
    st.session_state.tabla.drop(rows_delete, inplace=True)
    st.session_state.tabla.reset_index(drop=True, inplace=True)
    st.rerun()

# =========================
# GUARDAR
# =========================
if save or send:
    dbx = get_dbx()
    if dbx:
        if acquire_lock(dbx):
            base = read_base(dbx)
            final = pd.concat([base, st.session_state.tabla], ignore_index=True)
            write_base(dbx, final)
            release_lock(dbx)
            st.success("Guardado correctamente")
        else:
            st.warning("Otro usuario está guardando")
