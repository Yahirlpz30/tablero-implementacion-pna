import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

from services.dropbox_service import read_excel_dropbox, upload_excel_dropbox


# =====================================
# Configuración visual de la app
# =====================================

st.set_page_config(
    page_title="Tablero de Implementación",
    layout="wide",
    page_icon="www/favicon.png"
)

# Logo
st.image("www/logo_tablero.png", width=300)

st.title("Tablero de Implementación de la Política Nacional Anticorrupción")

st.markdown("---")


# =====================================
# Cargar datos desde Dropbox
# =====================================

@st.cache_data
def load_data():
    return read_excel_dropbox("/tablero_prueba/base.xlsx")

try:

    data = load_data()

except Exception as e:

    st.error("Error cargando datos desde Dropbox")
    st.stop()


# =====================================
# KPIs
# =====================================

total_acciones = len(data)

acciones_reportadas = (data["Acción reportada"] != "Por reportar").sum()

avance = round((acciones_reportadas / total_acciones) * 100, 2)

k1, k2, k3 = st.columns(3)

k1.metric("Total acciones", total_acciones)

k2.metric("Acciones reportadas", acciones_reportadas)

k3.metric("Avance (%)", avance)


st.markdown("---")


# =====================================
# Ranking de instituciones
# =====================================

ranking = (
    data.groupby("Actor")
    .apply(lambda x: (x["Acción reportada"] != "Por reportar").mean() * 100)
    .reset_index(name="avance")
)

fig = px.bar(
    ranking,
    x="Actor",
    y="avance",
    title="Ranking de avance por institución",
    color="avance",
    color_continuous_scale="Blues"
)

st.plotly_chart(fig, use_container_width=True)


st.markdown("---")


# =====================================
# Filtros
# =====================================

st.subheader("Captura de acciones")

col1, col2, col3 = st.columns(3)

actores = sorted(data["Actor"].unique())

actor = col1.selectbox(
    "Institución",
    actores
)

df_actor = data[data["Actor"] == actor]


estrategias = sorted(df_actor["No. Estrategia"].unique())

estrategia = col2.selectbox(
    "Estrategia",
    estrategias
)

df_estrategia = df_actor[
    df_actor["No. Estrategia"] == estrategia
]


lineas = sorted(df_estrategia["No. Línea de acción"].unique())

linea = col3.selectbox(
    "Línea de acción",
    lineas
)

df_linea = df_estrategia[
    df_estrategia["No. Línea de acción"] == linea
]


st.markdown("---")


# =====================================
# Tabla editable
# =====================================

st.subheader("Registro de acciones")

edited_df = st.data_editor(
    df_linea,
    num_rows="dynamic",
    use_container_width=True
)


# =====================================
# Guardar cambios
# =====================================

if st.button("Guardar cambios"):

    with st.spinner("Guardando información..."):

        try:

            restante = data[
                data["No. Línea de acción"] != linea
            ]

            nuevo_df = pd.concat(
                [restante, edited_df]
            )

            upload_excel_dropbox(
                nuevo_df,
                "/tablero_prueba/base.xlsx"
            )

            # snapshot histórico

            snapshot_name = (
                "/tablero_prueba/snaps/"
                + actor
                + "_"
                + datetime.now().strftime("%Y%m%d_%H%M")
                + ".xlsx"
            )

            upload_excel_dropbox(
                edited_df,
                snapshot_name
            )

            st.success("Información guardada correctamente")

            st.cache_data.clear()

        except Exception as e:

            st.error("Error al guardar los datos")

            st.write(e)
