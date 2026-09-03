# ============================================================
# SIPREM-BOVINO
# DASHBOARD
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from utils.database import get_connection


# ============================================================
# CONFIGURACIÓN
# ============================================================

st.set_page_config(
    page_title="SIPREM-BOVINO | Dashboard",
    page_icon="🐄",
    layout="wide"
)


# ============================================================
# TÍTULO
# ============================================================

st.title("🐄 SIPREM-BOVINO")
st.subheader("Dashboard de predicción de riesgo de mortalidad")

st.caption(
    "Monitoreo de predicciones generadas mediante Random Forest "
    "para un horizonte de 4 semanas."
)


# ============================================================
# CARGA DE DATOS
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

        df = pd.read_sql(
            query,
            conn
        )

    finally:

        conn.close()

    return df


# ============================================================
# CARGAR
# ============================================================

try:

    df = cargar_predicciones()

except Exception as e:

    st.error(
        "❌ No fue posible conectar con Supabase."
    )

    st.exception(e)

    st.stop()


if df.empty:

    st.warning(
        "⚠️ No existen predicciones registradas "
        "en gold_ml.predicciones."
    )

    st.stop()


# ============================================================
# PREPARACIÓN DE DATOS
# ============================================================

df = df.copy()


# Fecha
df["fecha"] = pd.to_datetime(
    df["fecha"],
    errors="coerce"
)


# Normalizar booleano de riesgo
if df["riesgo_alto_predicho"].dtype != bool:

    df["riesgo_alto_predicho"] = (
        df["riesgo_alto_predicho"]
        .astype(str)
        .str.lower()
        .map({
            "true": True,
            "false": False,
            "1": True,
            "0": False
        })
    )


# Nivel de riesgo
df["nivel_riesgo"] = np.where(
    df["riesgo_alto_predicho"],
    "ALTO",
    "BAJO"
)


# Porcentaje
df["probabilidad_pct"] = (
    df["probabilidad_riesgo_predicha"] * 100
)


# Semana / periodo
df["semana"] = df["fecha"].dt.isocalendar().week.astype("Int64")


# ============================================================
# BARRA LATERAL - FILTROS
# ============================================================

st.sidebar.header("🔎 Filtros")


# ------------------------------------------------------------
# MODELO
# ------------------------------------------------------------

modelos = sorted(
    df["modelo_utilizado"]
    .dropna()
    .unique()
    .tolist()
)

modelos_seleccionados = st.sidebar.multiselect(
    "Modelo",
    modelos,
    default=modelos
)


# ------------------------------------------------------------
# LOTES
# ------------------------------------------------------------

lotes = sorted(
    df["id_lote"]
    .dropna()
    .unique()
    .tolist()
)

lotes_seleccionados = st.sidebar.multiselect(
    "Lotes",
    lotes,
    default=lotes
)


# ------------------------------------------------------------
# RIESGO
# ------------------------------------------------------------

niveles = st.sidebar.multiselect(
    "Nivel de riesgo",
    ["ALTO", "BAJO"],
    default=["ALTO", "BAJO"]
)


# ------------------------------------------------------------
# FECHA
# ------------------------------------------------------------

fecha_min = df["fecha"].min().date()
fecha_max = df["fecha"].max().date()


rango_fecha = st.sidebar.date_input(
    "Rango de fechas",
    value=(fecha_min, fecha_max),
    min_value=fecha_min,
    max_value=fecha_max
)


# ============================================================
# APLICAR FILTROS
# ============================================================

df_filtrado = df.copy()


if modelos_seleccionados:

    df_filtrado = df_filtrado[
        df_filtrado["modelo_utilizado"]
        .isin(modelos_seleccionados)
    ]


if lotes_seleccionados:

    df_filtrado = df_filtrado[
        df_filtrado["id_lote"]
        .isin(lotes_seleccionados)
    ]


if niveles:

    df_filtrado = df_filtrado[
        df_filtrado["nivel_riesgo"]
        .isin(niveles)
    ]


if len(rango_fecha) == 2:

    fecha_inicio = pd.Timestamp(
        rango_fecha[0]
    )

    fecha_fin = (
        pd.Timestamp(rango_fecha[1])
        + pd.Timedelta(days=1)
    )

    df_filtrado = df_filtrado[
        (df_filtrado["fecha"] >= fecha_inicio)
        &
        (df_filtrado["fecha"] < fecha_fin)
    ]


# ============================================================
# VALIDAR RESULTADO DEL FILTRO
# ============================================================

if df_filtrado.empty:

    st.warning(
        "⚠️ No existen registros con los filtros seleccionados."
    )

    st.stop()


# ============================================================
# INFORMACIÓN GENERAL
# ============================================================

total = len(df_filtrado)

total_lotes = df_filtrado[
    "id_lote"
].nunique()

riesgo_alto = int(
    df_filtrado["riesgo_alto_predicho"].sum()
)

riesgo_bajo = (
    total - riesgo_alto
)

porcentaje_alto = (
    riesgo_alto / total * 100
)

probabilidad_promedio = (
    df_filtrado[
        "probabilidad_riesgo_predicha"
    ].mean()
    * 100
)


# ============================================================
# KPI
# ============================================================

st.markdown("## 📊 Indicadores generales")


col1, col2, col3, col4, col5 = st.columns(5)


col1.metric(
    "Predicciones",
    f"{total:,}"
)


col2.metric(
    "Lotes",
    f"{total_lotes:,}"
)


col3.metric(
    "Riesgo ALTO",
    f"{riesgo_alto:,}"
)


col4.metric(
    "% Riesgo ALTO",
    f"{porcentaje_alto:.1f}%"
)


col5.metric(
    "Probabilidad promedio",
    f"{probabilidad_promedio:.1f}%"
)


st.divider()


# ============================================================
# 1. DISTRIBUCIÓN DEL RIESGO
# ============================================================

st.header("1️⃣ Distribución del riesgo")


col1, col2 = st.columns(2)


# ------------------------------------------------------------
# GRÁFICO DE BARRAS
# ------------------------------------------------------------

with col1:

    resumen_riesgo = (
        df_filtrado[
            "nivel_riesgo"
        ]
        .value_counts()
        .reset_index()
    )

    resumen_riesgo.columns = [
        "nivel_riesgo",
        "cantidad"
    ]

    fig = px.bar(
        resumen_riesgo,
        x="nivel_riesgo",
        y="cantidad",
        text="cantidad",
        title="Cantidad de predicciones por nivel de riesgo"
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


# ------------------------------------------------------------
# DONA
# ------------------------------------------------------------

with col2:

    fig_pie = px.pie(
        resumen_riesgo,
        names="nivel_riesgo",
        values="cantidad",
        hole=0.5,
        title="Proporción de riesgo"
    )

    st.plotly_chart(
        fig_pie,
        use_container_width=True
    )


# ============================================================
# 2. DISTRIBUCIÓN DE PROBABILIDADES
# ============================================================

st.header("2️⃣ Distribución de probabilidades")


fig_hist = px.histogram(
    df_filtrado,
    x="probabilidad_pct",
    nbins=20,
    marginal="box",
    title="Distribución de la probabilidad de riesgo"
)


fig_hist.add_vline(
    x=df_filtrado[
        "umbral_utilizado"
    ].iloc[0] * 100,
    line_dash="dash",
    annotation_text="Umbral"
)


fig_hist.update_layout(
    xaxis_title="Probabilidad de riesgo (%)",
    yaxis_title="Número de predicciones"
)


st.plotly_chart(
    fig_hist,
    use_container_width=True
)


# ============================================================
# 3. RIESGO POR LOTE
# ============================================================

st.header("3️⃣ Análisis de riesgo por lote")


riesgo_lote = (
    df_filtrado
    .groupby("id_lote")
    .agg(
        predicciones=(
            "id_lote",
            "count"
        ),

        riesgo_alto=(
            "riesgo_alto_predicho",
            "sum"
        ),

        probabilidad_promedio=(
            "probabilidad_riesgo_predicha",
            "mean"
        )
    )
    .reset_index()
)


riesgo_lote["porcentaje_alto"] = (
    riesgo_lote["riesgo_alto"]
    /
    riesgo_lote["predicciones"]
    * 100
)


col1, col2 = st.columns(2)


# ------------------------------------------------------------
# % ALTO POR LOTE
# ------------------------------------------------------------

with col1:

    fig_lotes = px.bar(
        riesgo_lote.sort_values(
            "porcentaje_alto",
            ascending=False
        ),
        x="id_lote",
        y="porcentaje_alto",
        text="porcentaje_alto",
        title="% de predicciones de riesgo ALTO por lote"
    )

    fig_lotes.update_traces(
        texttemplate="%{text:.1f}%"
    )

    fig_lotes.update_layout(
        xaxis_title="Lote",
        yaxis_title="% Riesgo ALTO"
    )

    st.plotly_chart(
        fig_lotes,
        use_container_width=True
    )


# ------------------------------------------------------------
# PROBABILIDAD PROMEDIO POR LOTE
# ------------------------------------------------------------

with col2:

    riesgo_lote_plot = riesgo_lote.copy()

    riesgo_lote_plot[
        "probabilidad_promedio_pct"
    ] = (
        riesgo_lote_plot[
            "probabilidad_promedio"
        ] * 100
    )

    fig_prob_lote = px.bar(
        riesgo_lote_plot.sort_values(
            "probabilidad_promedio_pct",
            ascending=False
        ),
        x="id_lote",
        y="probabilidad_promedio_pct",
        text="probabilidad_promedio_pct",
        title="Probabilidad promedio por lote"
    )

    fig_prob_lote.update_traces(
        texttemplate="%{text:.1f}%"
    )

    fig_prob_lote.update_layout(
        xaxis_title="Lote",
        yaxis_title="Probabilidad promedio (%)"
    )

    st.plotly_chart(
        fig_prob_lote,
        use_container_width=True
    )


# ============================================================
# 4. EVOLUCIÓN TEMPORAL
# ============================================================

st.header("4️⃣ Evolución temporal")


evolucion = (
    df_filtrado
    .groupby("fecha")
    .agg(
        probabilidad_promedio=(
            "probabilidad_riesgo_predicha",
            "mean"
        ),

        porcentaje_riesgo_alto=(
            "riesgo_alto_predicho",
            "mean"
        )
    )
    .reset_index()
)


evolucion[
    "probabilidad_promedio_pct"
] = (
    evolucion[
        "probabilidad_promedio"
    ] * 100
)


evolucion[
    "porcentaje_riesgo_alto"
] = (
    evolucion[
        "porcentaje_riesgo_alto"
    ] * 100
)


# ------------------------------------------------------------
# PROBABILIDAD
# ------------------------------------------------------------

fig_temporal = px.line(
    evolucion,
    x="fecha",
    y="probabilidad_promedio_pct",
    markers=True,
    title="Evolución de la probabilidad promedio"
)


umbral = float(
    df_filtrado[
        "umbral_utilizado"
    ].iloc[0]
) * 100


fig_temporal.add_hline(
    y=umbral,
    line_dash="dash",
    annotation_text=f"Umbral {umbral:.1f}%"
)


fig_temporal.update_layout(
    xaxis_title="Fecha",
    yaxis_title="Probabilidad (%)"
)


st.plotly_chart(
    fig_temporal,
    use_container_width=True
)


# ------------------------------------------------------------
# % ALTO POR FECHA
# ------------------------------------------------------------

fig_temporal_riesgo = px.line(
    evolucion,
    x="fecha",
    y="porcentaje_riesgo_alto",
    markers=True,
    title="Porcentaje de predicciones de riesgo ALTO por fecha"
)


fig_temporal_riesgo.update_layout(
    xaxis_title="Fecha",
    yaxis_title="% Riesgo ALTO"
)


st.plotly_chart(
    fig_temporal_riesgo,
    use_container_width=True
)


# ============================================================
# 5. MAPA DE CALOR LOTE / FECHA
# ============================================================

st.header("5️⃣ Mapa de riesgo por lote y fecha")


heatmap = (
    df_filtrado
    .groupby(
        ["id_lote", "fecha"]
    )["probabilidad_riesgo_predicha"]
    .mean()
    .reset_index()
)


heatmap[
    "probabilidad_pct"
] = (
    heatmap[
        "probabilidad_riesgo_predicha"
    ] * 100
)


pivot_heatmap = heatmap.pivot(
    index="id_lote",
    columns="fecha",
    values="probabilidad_pct"
)


fig_heatmap = go.Figure(
    data=go.Heatmap(
        z=pivot_heatmap.values,
        x=pivot_heatmap.columns,
        y=pivot_heatmap.index,
        colorbar_title="Riesgo (%)"
    )
)


fig_heatmap.update_layout(
    title="Probabilidad de riesgo por lote y fecha",
    xaxis_title="Fecha",
    yaxis_title="Lote"
)


st.plotly_chart(
    fig_heatmap,
    use_container_width=True
)


# ============================================================
# 6. PROBABILIDAD SEGÚN NIVEL DE RIESGO
# ============================================================

st.header("6️⃣ Separación entre predicciones ALTO y BAJO")


fig_box = px.box(
    df_filtrado,
    x="nivel_riesgo",
    y="probabilidad_pct",
    points="outliers",
    title="Distribución de probabilidad según clasificación"
)


fig_box.add_hline(
    y=umbral,
    line_dash="dash",
    annotation_text="Umbral"
)


fig_box.update_layout(
    xaxis_title="Nivel de riesgo",
    yaxis_title="Probabilidad (%)"
)


st.plotly_chart(
    fig_box,
    use_container_width=True
)


# ============================================================
# 7. RELACIÓN SALUD VS RIESGO
# ============================================================

if "indice_salud_lote" in df_filtrado.columns:

    st.header("7️⃣ Índice de salud y riesgo")


    fig_salud = px.scatter(
        df_filtrado,
        x="indice_salud_lote",
        y="probabilidad_pct",
        color="nivel_riesgo",
        hover_data=[
            "id_lote",
            "fecha",
            "probabilidad_pct"
        ],
        title="Índice de salud del lote vs probabilidad de riesgo"
    )


    fig_salud.add_hline(
        y=umbral,
        line_dash="dash"
    )


    fig_salud.update_layout(
        xaxis_title="Índice de salud del lote",
        yaxis_title="Probabilidad de riesgo (%)"
    )


    st.plotly_chart(
        fig_salud,
        use_container_width=True
    )


# ============================================================
# 8. VARIABLES SANITARIAS
# ============================================================

st.header("8️⃣ Indicadores sanitarios")


columnas_sanitarias = [
    "casos_respiratorios",
    "casos_diarreicos",
    "cobertura_vacunacion_pct",
    "dias_desde_desparasitacion"
]


columnas_sanitarias = [
    col
    for col in columnas_sanitarias
    if col in df_filtrado.columns
]


for columna in columnas_sanitarias:

    datos = (
        df_filtrado
        .groupby("nivel_riesgo")[columna]
        .mean()
        .reset_index()
    )


    fig = px.bar(
        datos,
        x="nivel_riesgo",
        y=columna,
        text=columna,
        title=f"{columna.replace('_', ' ').title()} según nivel de riesgo"
    )


    fig.update_layout(
        xaxis_title="Nivel de riesgo",
        yaxis_title=columna.replace(
            "_",
            " "
        ).title()
    )


    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ============================================================
# 9. VARIABLES AMBIENTALES
# ============================================================

st.header("9️⃣ Indicadores ambientales")


columnas_ambientales = [
    "temperatura_media_c",
    "temperatura_min_c",
    "temperatura_max_c",
    "humedad_relativa_pct",
    "precipitacion_semanal_mm",
    "condicion_pastura_indice"
]


columnas_ambientales = [
    col
    for col in columnas_ambientales
    if col in df_filtrado.columns
]


for columna in columnas_ambientales:

    datos = (
        df_filtrado
        .groupby("nivel_riesgo")[columna]
        .mean()
        .reset_index()
    )


    fig = px.bar(
        datos,
        x="nivel_riesgo",
        y=columna,
        text=columna,
        title=f"{columna.replace('_', ' ').title()} según nivel de riesgo"
    )


    fig.update_layout(
        xaxis_title="Nivel de riesgo",
        yaxis_title=columna.replace(
            "_",
            " "
        ).title()
    )


    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ============================================================
# 10. COBERTURA DE VACUNACIÓN
# ============================================================

if "cobertura_vacunacion_pct" in df_filtrado.columns:

    st.header("🔟 Cobertura de vacunación")


    fig_vac = px.scatter(
        df_filtrado,
        x="cobertura_vacunacion_pct",
        y="probabilidad_pct",
        color="nivel_riesgo",
        hover_data=[
            "id_lote",
            "fecha"
        ],
        title="Cobertura de vacunación vs probabilidad de riesgo"
    )


    fig_vac.add_hline(
        y=umbral,
        line_dash="dash"
    )


    fig_vac.update_layout(
        xaxis_title="Cobertura de vacunación (%)",
        yaxis_title="Probabilidad de riesgo (%)"
    )


    st.plotly_chart(
        fig_vac,
        use_container_width=True
    )


# ============================================================
# 11. PRECIPITACIÓN VS RIESGO
# ============================================================

if "precipitacion_semanal_mm" in df_filtrado.columns:

    st.header("1️⃣1️⃣ Precipitación y riesgo")


    fig_prec = px.scatter(
        df_filtrado,
        x="precipitacion_semanal_mm",
        y="probabilidad_pct",
        color="nivel_riesgo",
        hover_data=[
            "id_lote",
            "fecha"
        ],
        title="Precipitación semanal vs probabilidad de riesgo"
    )


    fig_prec.add_hline(
        y=umbral,
        line_dash="dash"
    )


    fig_prec.update_layout(
        xaxis_title="Precipitación semanal (mm)",
        yaxis_title="Probabilidad de riesgo (%)"
    )


    st.plotly_chart(
        fig_prec,
        use_container_width=True
    )


# ============================================================
# 12. CONDICIÓN CORPORAL
# ============================================================

if "condicion_corporal_prom" in df_filtrado.columns:

    st.header("1️⃣2️⃣ Condición corporal")


    fig_cc = px.scatter(
        df_filtrado,
        x="condicion_corporal_prom",
        y="probabilidad_pct",
        color="nivel_riesgo",
        hover_data=[
            "id_lote",
            "fecha"
        ],
        title="Condición corporal vs probabilidad de riesgo"
    )


    fig_cc.add_hline(
        y=umbral,
        line_dash="dash"
    )


    fig_cc.update_layout(
        xaxis_title="Condición corporal promedio",
        yaxis_title="Probabilidad de riesgo (%)"
    )


    st.plotly_chart(
        fig_cc,
        use_container_width=True
    )


# ============================================================
# 13. ACTIVIDAD DEL SENSOR
# ============================================================

if "actividad_sensor_indice" in df_filtrado.columns:

    st.header("1️⃣3️⃣ Actividad de sensores")


    datos_sensor = (
        df_filtrado[
            df_filtrado[
                "actividad_sensor_indice"
            ].notna()
        ]
        .copy()
    )


    if not datos_sensor.empty:

        fig_sensor = px.scatter(
            datos_sensor,
            x="actividad_sensor_indice",
            y="probabilidad_pct",
            color="nivel_riesgo",
            hover_data=[
                "id_lote",
                "fecha"
            ],
            title="Actividad de sensores vs probabilidad de riesgo"
        )


        fig_sensor.add_hline(
            y=umbral,
            line_dash="dash"
        )


        fig_sensor.update_layout(
            xaxis_title="Índice de actividad",
            yaxis_title="Probabilidad de riesgo (%)"
        )


        st.plotly_chart(
            fig_sensor,
            use_container_width=True
        )

    else:

        st.info(
            "No existen registros de actividad de sensores "
            "disponibles para los filtros actuales."
        )


# ============================================================
# 14. TABLA RESUMEN POR LOTE
# ============================================================

st.header("1️⃣4️⃣ Resumen detallado por lote")


resumen_lotes = (
    df_filtrado
    .groupby("id_lote")
    .agg(
        predicciones=("id_lote", "count"),

        riesgo_alto=(
            "riesgo_alto_predicho",
            "sum"
        ),

        probabilidad_promedio=(
            "probabilidad_riesgo_predicha",
            "mean"
        ),

        salud_promedio=(
            "indice_salud_lote",
            "mean"
        )
    )
    .reset_index()
)


resumen_lotes["riesgo_alto_pct"] = (
    resumen_lotes["riesgo_alto"]
    /
    resumen_lotes["predicciones"]
    * 100
)


resumen_lotes[
    "probabilidad_promedio_pct"
] = (
    resumen_lotes[
        "probabilidad_promedio"
    ] * 100
)


resumen_lotes[
    "salud_promedio"
] = resumen_lotes[
    "salud_promedio"
].round(3)


st.dataframe(
    resumen_lotes.sort_values(
        "riesgo_alto_pct",
        ascending=False
    ),
    use_container_width=True,
    hide_index=True
)


# ============================================================
# 15. ÚLTIMAS PREDICCIONES
# ============================================================

st.header("1️⃣5️⃣ Predicciones más recientes")


columnas_mostrar = [
    "id_lote",
    "fecha",
    "probabilidad_pct",
    "nivel_riesgo",
    "umbral_utilizado",
    "modelo_utilizado"
]


columnas_mostrar = [
    col
    for col in columnas_mostrar
    if col in df_filtrado.columns
]


ultimas = (
    df_filtrado
    .sort_values(
        "fecha",
        ascending=False
    )
    .head(50)
)


st.dataframe(
    ultimas[
        columnas_mostrar
    ],
    use_container_width=True,
    hide_index=True
)


# ============================================================
# INFORMACIÓN DEL MODELO
# ============================================================

st.divider()

st.header("ℹ️ Información del modelo")


col1, col2, col3 = st.columns(3)


with col1:

    st.metric(
        "Modelo utilizado",
        str(
            df_filtrado[
                "modelo_utilizado"
            ].mode().iloc[0]
        )
    )


with col2:

    st.metric(
        "Umbral",
        f"{umbral:.2f}"
    )


with col3:

    st.metric(
        "Horizonte",
        "4 semanas"
    )


st.caption(
    "Las predicciones mostradas corresponden a los registros "
    "almacenados en gold_ml.predicciones. El nivel ALTO/BAJO "
    "se determina comparando la probabilidad estimada contra "
    "el umbral registrado para la predicción."
)