import streamlit as st
import pandas as pd
import plotly.express as px

from utils.database import get_connection


st.set_page_config(
    page_title="Dashboard SIPREM-BOVINO",
    page_icon="🐄",
    layout="wide"
)


st.title("📊 Dashboard SIPREM-BOVINO")

st.caption(
    "Visualización de predicciones de riesgo de mortalidad bovina"
)


# ============================================================
# CARGAR DATOS
# ============================================================

@st.cache_data(ttl=60)
def cargar_predicciones():

    conn = get_connection()

    try:

        query = """
            SELECT *
            FROM gold_ml.predicciones
            ORDER BY fecha DESC
        """

        df = pd.read_sql(query, conn)

    finally:

        conn.close()

    return df


# ============================================================
# CARGA
# ============================================================

try:

    df = cargar_predicciones()

except Exception as e:

    st.error(
        f"No se pudo conectar con la base de datos:\n\n{e}"
    )

    st.stop()


if df.empty:

    st.warning(
        "No existen predicciones registradas."
    )

    st.stop()


# ============================================================
# CONVERSIÓN
# ============================================================

df["fecha"] = pd.to_datetime(
    df["fecha"],
    errors="coerce"
)


# ============================================================
# KPIs
# ============================================================

total_predicciones = len(df)

total_lotes = df["id_lote"].nunique()

riesgo_alto = int(
    df["riesgo_alto_predicho"].sum()
)

porcentaje_alto = (
    riesgo_alto / total_predicciones * 100
)


col1, col2, col3, col4 = st.columns(4)


col1.metric(
    "Predicciones",
    f"{total_predicciones:,}"
)

col2.metric(
    "Lotes",
    f"{total_lotes:,}"
)

col3.metric(
    "Riesgo alto",
    f"{riesgo_alto:,}"
)

col4.metric(
    "% riesgo alto",
    f"{porcentaje_alto:.1f}%"
)


st.divider()


# ============================================================
# DISTRIBUCIÓN DEL RIESGO
# ============================================================

st.subheader("🚨 Distribución de riesgo")


riesgo = (
    df["riesgo_alto_predicho"]
    .map({
        True: "ALTO",
        False: "BAJO"
    })
    .value_counts()
    .reset_index()
)


riesgo.columns = [
    "riesgo",
    "cantidad"
]


fig = px.bar(
    riesgo,
    x="riesgo",
    y="cantidad",
    text="cantidad",
    title="Predicciones por nivel de riesgo"
)

fig.update_layout(
    xaxis_title="Nivel de riesgo",
    yaxis_title="Cantidad",
    showlegend=False
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# ============================================================
# RIESGO POR LOTE
# ============================================================

st.subheader("🐄 Riesgo por lote")


riesgo_lote = (
    df.groupby("id_lote")
    .agg(
        predicciones=("id_lote", "count"),
        riesgo_alto=("riesgo_alto_predicho", "sum")
    )
    .reset_index()
)


riesgo_lote["porcentaje_alto"] = (
    riesgo_lote["riesgo_alto"]
    / riesgo_lote["predicciones"]
    * 100
)


fig_lotes = px.bar(
    riesgo_lote.sort_values(
        "porcentaje_alto",
        ascending=False
    ),
    x="id_lote",
    y="porcentaje_alto",
    title="% de predicciones de riesgo alto por lote",
    text_auto=".1f"
)


fig_lotes.update_layout(
    xaxis_title="Lote",
    yaxis_title="% riesgo alto"
)


st.plotly_chart(
    fig_lotes,
    use_container_width=True
)


# ============================================================
# EVOLUCIÓN TEMPORAL
# ============================================================

st.subheader("📈 Evolución temporal de la probabilidad")


evolucion = (
    df.groupby("fecha")[
        "probabilidad_riesgo_predicha"
    ]
    .mean()
    .reset_index()
)


fig_temporal = px.line(
    evolucion,
    x="fecha",
    y="probabilidad_riesgo_predicha",
    markers=True,
    title="Probabilidad promedio de riesgo"
)


fig_temporal.add_hline(
    y=0.55,
    line_dash="dash",
    annotation_text="Umbral 0.55"
)


fig_temporal.update_layout(
    xaxis_title="Fecha",
    yaxis_title="Probabilidad"
)


st.plotly_chart(
    fig_temporal,
    use_container_width=True
)