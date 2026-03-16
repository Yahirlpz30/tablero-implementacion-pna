import streamlit as st
import pandas as pd
import plotly.express as px

from services.dropbox_service import read_excel_dropbox, upload_excel_dropbox

st.set_page_config(
    page_title="Tablero de Implementación",
    layout="wide"
)

st.title("Tablero de Implementación - Sistema Anticorrupción")

# =========================
# Cargar datos desde Dropbox
# =========================

@st.cache_data
def load_data():
    return read_excel_dropbox("/tablero_prueba/base.xlsx")

data = load_data()

# =========================
# KPIs principales
# =========================

total_acciones = len(data)

acciones_reportadas = (data["Acción reportada"] != "Por reportar").sum()

avance = round((acciones_reportadas / total_acciones) * 100,2)

col1, col2, col3 = st.columns(3)

col1.metric("Total acciones", total_acciones)
col2.metric("Acciones reportadas", acciones_reportadas)
col3.metric("Avance (%)", avance)

st.divider()

# =========================
# Ranking de instituciones
# =========================

ranking = (
    data.groupby("Actor")
    .apply(lambda x: (x["Acción reportada"] != "Por reportar").mean()*100)
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

st.divider()

# =========================
# Filtros
# =========================

st.subheader("Filtros")

actores = sorted(data["Actor"].unique())

actor_seleccionado = st.selectbox(
    "Seleccionar institución",
    actores
)

df_actor = data[data["Actor"] == actor_seleccionado]

# Estrategias

estrategias = sorted(df_actor["No. Estrategia"].unique())

estrategia_seleccionada = st.selectbox(
    "Seleccionar estrategia",
    estrategias
)

df_estrategia = df_actor[df_actor["No. Estrategia"] == estrategia_seleccionada]

# Líneas de acción

lineas = sorted(df_estrategia["No. Línea de acción"].unique())

linea_seleccionada = st.selectbox(
    "Seleccionar línea de acción",
    lineas
)

df_linea = df_estrategia[df_estrategia["No. Línea de acción"] == linea_seleccionada]

st.divider()

# =========================
# Tabla editable
# =========================

st.subheader("Captura de acciones")

edited_df = st.data_editor(
    df_linea,
    num_rows="dynamic",
    use_container_width=True
)

# =========================
# Guardar cambios
# =========================

if st.button("Guardar cambios"):

    try:

        # eliminar filas viejas de esa línea
        data_restante = data[
            data["No. Línea de acción"] != linea_seleccionada
        ]

        # combinar con datos editados
        nuevo_df = pd.concat([data_restante, edited_df])

        # guardar en Dropbox
        upload_excel_dropbox(
            nuevo_df,
            "/tablero_prueba/base.xlsx"
        )

        st.success("Datos guardados correctamente")

        st.cache_data.clear()

    except Exception as e:

        st.error("Error guardando datos")
        st.write(e)
