mport streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="Tablero PNA", layout="wide")

# =====================================================
# FUNCION CARGAR EXCEL
# =====================================================

def load_excel(path):

    try:
        df = pd.read_excel(path)
        df.columns = df.columns.str.strip()
        return df

    except:
        st.error(f"No se pudo cargar {path}")
        return pd.DataFrame()


# =====================================================
# CARGAR ARCHIVOS
# =====================================================

users = load_excel("www/user-pass.xlsx")
user_act = load_excel("www/user-act.xlsx")
pi_actores = load_excel("www/pi-actores.xlsx")
alineacion = load_excel("www/alineacion_pi.xlsx")


# =====================================================
# LOGIN
# =====================================================

if "login" not in st.session_state:
    st.session_state.login = False


if not st.session_state.login:

    st.title("Sistema Estatal Anticorrupción")
    st.subheader("Ingreso al sistema")

    user = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Entrar"):

        check = users[
            (users["user"] == user) &
            (users["password"] == password)
        ]

        if len(check) > 0:

            st.session_state.login = True
            st.session_state.user = user
            st.rerun()

        else:

            st.error("Usuario o contraseña incorrectos")

    st.stop()


# =====================================================
# OBTENER ACTOR
# =====================================================

actor_usuario = user_act.loc[
    user_act["user"] == st.session_state.user,
    "act"
].values[0]


# =====================================================
# LINEAS PERMITIDAS
# =====================================================

lineas_actor = pi_actores.loc[
    pi_actores["Actor"].str.contains(actor_usuario),
    "Línea de acción"
].unique()


alineacion_actor = alineacion[
    alineacion["Línea de acción"].isin(lineas_actor)
]


# =====================================================
# HEADER
# =====================================================

col1,col2 = st.columns([6,1])

with col1:
    st.title("Reporte de Acciones 2025")

with col2:

    if st.button("Cerrar sesión"):
        st.session_state.login = False
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
    "Línea de acción"
].unique()


linea = st.selectbox(
    "Línea de acción",
    lineas
)


# =====================================================
# SESSION DATA
# =====================================================

if "tabla" not in st.session_state:

    st.session_state.tabla = pd.DataFrame(
        columns=[
            "Actor",
            "Estrategia",
            "Linea",
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
            "Actor":actor_usuario,
            "Estrategia":estrategia,
            "Linea":linea,
            "Accion":"",
            "Inicio":None,
            "Fin":None,
            "Tipo":"",
            "Tematica":""
        }

        st.session_state.tabla.loc[len(st.session_state.tabla)] = nueva


with col2:

    if st.button("Guardar Borrador"):

        nombre = f"borrador_{actor_usuario}.xlsx"

        st.session_state.tabla.to_excel(
            nombre,
            index=False
        )

        st.success("Borrador guardado")


with col3:

    if st.button("Enviar"):

        st.success("Acciones enviadas")


st.divider()


# =====================================================
# TABLA EDITABLE
# =====================================================

if len(st.session_state.tabla) > 0:

    edited = st.data_editor(

        st.session_state.tabla,

        use_container_width=True,

        column_config={

            "Inicio": st.column_config.DateColumn(
                "Inicio"
            ),

            "Fin": st.column_config.DateColumn(
                "Fin"
            ),

            "Tipo": st.column_config.SelectboxColumn(
                "Tipo de Acción",
                options=[
                    "Capacitación",
                    "Diagnóstico",
                    "Sistema",
                    "Norma",
                    "Convenio"
                ]
            )
        },

        num_rows="dynamic"
    )

    st.session_state.tabla = edited
