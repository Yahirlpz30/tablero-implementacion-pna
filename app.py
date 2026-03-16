import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="Tablero PNA", layout="wide")

# =========================================================
# FUNCION CARGAR EXCEL
# =========================================================

def load_excel(path):
    try:
        return pd.read_excel(path)
    except:
        st.error(f"No se pudo cargar {path}")
        return pd.DataFrame()

# =========================================================
# CARGAR ARCHIVOS
# =========================================================

users = load_excel("www/user-pass.xlsx")
user_act = load_excel("www/user-act.xlsx")
pi_actores = load_excel("www/pi-actores.xlsx")
alineacion = load_excel("www/alineacion_pi.xlsx")

# =========================================================
# LOGIN
# =========================================================

if "logged" not in st.session_state:
    st.session_state.logged = False

if not st.session_state.logged:

    st.title("Sistema Estatal Anticorrupción")
    st.subheader("Login")

    user = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Entrar"):

        check = users[
            (users["user"] == user) &
            (users["password"] == password)
        ]

        if len(check) > 0:

            st.session_state.logged = True
            st.session_state.user = user
            st.rerun()

        else:
            st.error("Usuario o contraseña incorrectos")

    st.stop()

# =========================================================
# DETECTAR ACTOR
# =========================================================

actor_usuario = user_act.loc[
    user_act["user"] == st.session_state.user,
    "act"
].values[0]

# =========================================================
# LINEAS PERMITIDAS PARA ACTOR
# =========================================================

lineas_actor = pi_actores.loc[
    pi_actores["Actor"].str.contains(actor_usuario),
    "Línea de acción"
].unique()

alineacion_actor = alineacion[
    alineacion["Línea de acción"].isin(lineas_actor)
]

# =========================================================
# HEADER
# =========================================================

col1,col2 = st.columns([6,2])

with col1:
    st.title("Reporte de Acciones 2025")

with col2:
    if st.button("Cerrar sesión"):
        st.session_state.logged = False
        st.rerun()

st.divider()

# =========================================================
# SELECTORES
# =========================================================

estrategias = alineacion_actor["Estrategia"].unique()

estrategia = st.selectbox(
    "Estrategia",
    estrategias
)

lineas = alineacion_actor.loc[
    alineacion_actor["Estrategia"] == estrategia,
    "Línea de acción"
].unique()

linea = st.selectbox(
    "Línea de acción",
    lineas
)

# =========================================================
# SESSION DATA
# =========================================================

if "tabla" not in st.session_state:
    st.session_state.tabla = []

# =========================================================
# BOTONES
# =========================================================

col1,col2,col3 = st.columns(3)

with col1:
    if st.button("➕ Agregar Acción"):

        nueva = {
            "Actor": actor_usuario,
            "Estrategia": estrategia,
            "Linea": linea,
            "Accion":"",
            "Inicio":"",
            "Fin":"",
            "Tipo":"",
            "Tematica":""
        }

        st.session_state.tabla.append(nueva)

with col2:
    if st.button("Guardar Borrador"):

        df = pd.DataFrame(st.session_state.tabla)

        nombre = f"borrador_{actor_usuario}.xlsx"

        df.to_excel(nombre,index=False)

        st.success("Borrador guardado")

with col3:
    if st.button("Enviar"):
        st.success("Acciones enviadas")

st.divider()

# =========================================================
# TABLA
# =========================================================

if len(st.session_state.tabla) > 0:

    for i,row in enumerate(st.session_state.tabla):

        cols = st.columns([1,2,3,2,2,2,2,1])

        with cols[0]:
            st.write(row["Estrategia"])

        with cols[1]:
            st.write(row["Linea"])

        with cols[2]:
            st.session_state.tabla[i]["Accion"] = st.text_input(
                "Acción",
                row["Accion"],
                key=f"accion_{i}"
            )

        with cols[3]:
            st.session_state.tabla[i]["Inicio"] = st.text_input(
                "Inicio",
                row["Inicio"],
                placeholder="dd/mm/aaaa",
                key=f"inicio_{i}"
            )

        with cols[4]:
            st.session_state.tabla[i]["Fin"] = st.text_input(
                "Fin",
                row["Fin"],
                placeholder="dd/mm/aaaa",
                key=f"fin_{i}"
            )

        with cols[5]:
            st.session_state.tabla[i]["Tipo"] = st.selectbox(
                "Tipo de Acción",
                ["","Capacitación","Diagnóstico","Sistema","Norma","Convenio"],
                key=f"tipo_{i}"
            )

        with cols[6]:
            st.session_state.tabla[i]["Tematica"] = st.text_input(
                "Temática",
                row["Tematica"],
                key=f"tema_{i}"
            )

        with cols[7]:
            if st.button("🗑",key=f"del{i}"):

                st.session_state.tabla.pop(i)
                st.rerun()

        st.divider()
