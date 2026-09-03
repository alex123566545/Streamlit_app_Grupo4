# ============================================================
# SIPREM-BOVINO
# DASHBOARD DE RIESGO DE MORTALIDAD
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
    page_title="SIPREM-BOVINO | Riesgo",
    page_icon="🐄",
    layout="wide"
)


# ============================================================
# TÍTULO
# ============================================================

st.title("🐄 SIPREM-BOVINO")

st.subheader(
    "Análisis comparativo del riesgo de mortalidad"
)

st.caption(
    "Comparación entre predicciones de riesgo ALTO y BAJO "
    "generadas por el modelo Random Forest."
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
            ORDER BY fecha
        """

        df = pd.read_sql(
            query,
            conn
        )

    finally:

        conn.close()

    return df


# ============================================================
# CONEXIÓN
# ============================================================

try:

    df = cargar_predicciones()

except Exception as e:

    st.error(
        "❌ Error al cargar las predicciones."
    )

    st.exception(e)

    st.stop()


# ============================================================
# VALIDACIÓN
# ============================================================

if df.empty:

    st.warning(
        "No existen predicciones registradas."
    )

    st.stop()


# ============================================================
# PREPARACIÓN
# ============================================================

df = df.copy()


df["fecha"] = pd.to_datetime(
    df["fecha"],
    errors="coerce"
)


df[
    "probabilidad_riesgo_predicha"
] = pd.to_numeric(
    df[
        "probabilidad_riesgo_predicha"
    ],
    errors="coerce"
)


# ------------------------------------------------------------
# NORMALIZAR BOOLEANOS
# ------------------------------------------------------------

def normalizar_bool(valor):

    if pd.isna(valor):

        return False

    if isinstance(valor, bool):

        return valor

    if isinstance(
        valor,
        (
            int,
            float,
            np.integer,
            np.floating
        )
    ):

        return bool(valor)

    valor = str(valor).strip().lower()

    return valor in [
        "true",
        "1",
        "si",
        "sí",
        "alto"
    ]


df[
    "riesgo_alto_predicho"
] = df[
    "riesgo_alto_predicho"
].apply(
    normalizar_bool
)


# ------------------------------------------------------------
# NIVEL
# ------------------------------------------------------------

df["nivel_riesgo"] = np.where(
    df["riesgo_alto_predicho"],
    "ALTO",
    "BAJO"
)


# ------------------------------------------------------------
# PROBABILIDAD %
# ------------------------------------------------------------

df["probabilidad_pct"] = (
    df[
        "probabilidad_riesgo_predicha"
    ] * 100
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header(
    "🔎 Filtros"
)


# ============================================================
# FILTRO DE LOTES
# ============================================================

lotes = sorted(
    df[
        "id_lote"
    ]
    .dropna()
    .astype(str)
    .unique()
)


lotes_seleccionados = st.sidebar.multiselect(
    "Lotes",
    lotes,
    default=lotes
)


# ============================================================
# FILTRO DE RIESGO
# ============================================================

niveles_seleccionados = st.sidebar.multiselect(
    "Nivel de riesgo",
    ["ALTO", "BAJO"],
    default=["ALTO", "BAJO"]
)


# ============================================================
# FILTRO DE MODELO
# ============================================================

if "modelo_utilizado" in df.columns:

    modelos = sorted(
        df[
            "modelo_utilizado"
        ]
        .dropna()
        .astype(str)
        .unique()
    )

else:

    modelos = []


if modelos:

    modelos_seleccionados = st.sidebar.multiselect(
        "Modelo",
        modelos,
        default=modelos
    )

else:

    modelos_seleccionados = []


# ============================================================
# FILTRO DE FECHA
# ============================================================

fechas = df[
    "fecha"
].dropna()


if not fechas.empty:

    fecha_min = fechas.min().date()

    fecha_max = fechas.max().date()

    rango_fecha = st.sidebar.date_input(
        "Rango de fechas",
        value=(
            fecha_min,
            fecha_max
        ),
        min_value=fecha_min,
        max_value=fecha_max
    )

else:

    rango_fecha = None


# ============================================================
# APLICAR FILTROS
# ============================================================

df_filtrado = df.copy()


if lotes_seleccionados:

    df_filtrado = df_filtrado[
        df_filtrado[
            "id_lote"
        ].astype(str).isin(
            lotes_seleccionados
        )
    ]


if niveles_seleccionados:

    df_filtrado = df_filtrado[
        df_filtrado[
            "nivel_riesgo"
        ].isin(
            niveles_seleccionados
        )
    ]


if modelos_seleccionados:

    df_filtrado = df_filtrado[
        df_filtrado[
            "modelo_utilizado"
        ].isin(
            modelos_seleccionados
        )
    ]


if (
    rango_fecha is not None
    and len(rango_fecha) == 2
):

    fecha_inicio = pd.Timestamp(
        rango_fecha[0]
    )

    fecha_fin = (
        pd.Timestamp(
            rango_fecha[1]
        )
        + pd.Timedelta(days=1)
    )

    df_filtrado = df_filtrado[
        (
            df_filtrado["fecha"]
            >= fecha_inicio
        )
        &
        (
            df_filtrado["fecha"]
            < fecha_fin
        )
    ]


# ============================================================
# VALIDACIÓN
# ============================================================

if df_filtrado.empty:

    st.warning(
        "No existen registros para los filtros seleccionados."
    )

    st.stop()


# ============================================================
# UMBRAL
# ============================================================

if "umbral_utilizado" in df_filtrado.columns:

    umbrales = pd.to_numeric(
        df_filtrado[
            "umbral_utilizado"
        ],
        errors="coerce"
    ).dropna()

    if not umbrales.empty:

        umbral = float(
            umbrales.iloc[0]
        )

    else:

        umbral = 0.55

else:

    umbral = 0.55


# ============================================================
# INDICADORES
# ============================================================

total = len(
    df_filtrado
)


alto = int(
    df_filtrado[
        "riesgo_alto_predicho"
    ].sum()
)


bajo = (
    total - alto
)


porcentaje_alto = (
    alto / total * 100
)


porcentaje_bajo = (
    bajo / total * 100
)


promedio_alto = (
    df_filtrado[
        df_filtrado[
            "nivel_riesgo"
        ] == "ALTO"
    ][
        "probabilidad_riesgo_predicha"
    ].mean()
)


promedio_bajo = (
    df_filtrado[
        df_filtrado[
            "nivel_riesgo"
        ] == "BAJO"
    ][
        "probabilidad_riesgo_predicha"
    ].mean()
)


# ============================================================
# KPI
# ============================================================

st.header(
    "📊 Resumen general"
)


c1, c2, c3, c4, c5, c6 = st.columns(6)


with c1:

    st.metric(
        "Total",
        f"{total:,}"
    )


with c2:

    st.metric(
        "ALTO",
        f"{alto:,}"
    )


with c3:

    st.metric(
        "% ALTO",
        f"{porcentaje_alto:.1f}%"
    )


with c4:

    st.metric(
        "BAJO",
        f"{bajo:,}"
    )


with c5:

    st.metric(
        "% BAJO",
        f"{porcentaje_bajo:.1f}%"
    )


with c6:

    st.metric(
        "Umbral",
        f"{umbral:.2f}"
    )


st.divider()


# ============================================================
# 1. ALTO VS BAJO
# ============================================================

st.header(
    "1️⃣ Comparación ALTO vs BAJO"
)


datos = pd.DataFrame({
    "Nivel": [
        "ALTO",
        "BAJO"
    ],

    "Cantidad": [
        alto,
        bajo
    ]
})


fig = px.bar(
    datos,
    x="Nivel",
    y="Cantidad",
    color="Nivel",
    text="Cantidad",
    title="Cantidad de predicciones ALTO y BAJO"
)


fig.update_layout(
    xaxis_title="Nivel de riesgo",
    yaxis_title="Número de predicciones"
)


st.plotly_chart(
    fig,
    use_container_width=True
)


# ============================================================
# 2. PROPORCIÓN
# ============================================================

st.header(
    "2️⃣ Proporción ALTO vs BAJO"
)


fig = px.pie(
    datos,
    names="Nivel",
    values="Cantidad",
    hole=0.55,
    title="Distribución proporcional de las predicciones"
)


st.plotly_chart(
    fig,
    use_container_width=True
)


# ============================================================
# 3. DISTRIBUCIÓN DE PROBABILIDADES
# ============================================================

st.header(
    "3️⃣ Distribución de probabilidades ALTO y BAJO"
)


fig = px.histogram(
    df_filtrado,
    x="probabilidad_pct",
    color="nivel_riesgo",
    nbins=20,
    barmode="overlay",
    opacity=0.7,
    title=(
        "Distribución de probabilidades "
        "según clasificación"
    )
)


fig.add_vline(
    x=umbral * 100,
    line_dash="dash",
    annotation_text=(
        f"Umbral {umbral:.2f}"
    )
)


fig.update_layout(
    xaxis_title="Probabilidad (%)",
    yaxis_title="Cantidad"
)


st.plotly_chart(
    fig,
    use_container_width=True
)


# ============================================================
# 4. BOX PLOT
# ============================================================

st.header(
    "4️⃣ Distribución estadística ALTO vs BAJO"
)


fig = px.box(
    df_filtrado,
    x="nivel_riesgo",
    y="probabilidad_pct",
    color="nivel_riesgo",
    points="all",
    category_orders={
        "nivel_riesgo": [
            "BAJO",
            "ALTO"
        ]
    },
    title=(
        "Comparación de probabilidades "
        "entre ALTO y BAJO"
    )
)


fig.add_hline(
    y=umbral * 100,
    line_dash="dash",
    annotation_text="Umbral"
)


fig.update_layout(
    xaxis_title="Clasificación",
    yaxis_title="Probabilidad (%)"
)


st.plotly_chart(
    fig,
    use_container_width=True
)


# ============================================================
# 5. EVOLUCIÓN TEMPORAL ALTO VS BAJO
# ============================================================

st.header(
    "5️⃣ Evolución temporal ALTO vs BAJO"
)


evolucion = (
    df_filtrado
    .groupby(
        [
            "fecha",
            "nivel_riesgo"
        ]
    )
    .agg(
        probabilidad_promedio=(
            "probabilidad_riesgo_predicha",
            "mean"
        ),

        cantidad=(
            "id_lote",
            "count"
        )
    )
    .reset_index()
)


evolucion[
    "probabilidad_pct"
] = (
    evolucion[
        "probabilidad_promedio"
    ] * 100
)


fig = px.line(
    evolucion,
    x="fecha",
    y="probabilidad_pct",
    color="nivel_riesgo",
    markers=True,
    title=(
        "Evolución de la probabilidad promedio "
        "para ALTO y BAJO"
    )
)


fig.add_hline(
    y=umbral * 100,
    line_dash="dash",
    annotation_text="Umbral"
)


fig.update_layout(
    xaxis_title="Fecha",
    yaxis_title="Probabilidad promedio (%)"
)


st.plotly_chart(
    fig,
    use_container_width=True
)


# ============================================================
# 6. CANTIDAD ALTO VS BAJO POR FECHA
# ============================================================

st.header(
    "6️⃣ Cantidad de predicciones ALTO y BAJO por fecha"
)


fig = px.bar(
    evolucion,
    x="fecha",
    y="cantidad",
    color="nivel_riesgo",
    barmode="group",
    text="cantidad",
    title=(
        "Comparación temporal de predicciones "
        "ALTO y BAJO"
    )
)


fig.update_layout(
    xaxis_title="Fecha",
    yaxis_title="Cantidad"
)


st.plotly_chart(
    fig,
    use_container_width=True
)


# ============================================================
# 7. PORCENTAJE ALTO VS BAJO POR FECHA
# ============================================================

st.header(
    "7️⃣ Proporción ALTO vs BAJO por fecha"
)


proporcion = (
    df_filtrado
    .groupby(
        [
            "fecha",
            "nivel_riesgo"
        ]
    )
    .size()
    .reset_index(
        name="cantidad"
    )
)


totales_fecha = (
    proporcion
    .groupby("fecha")[
        "cantidad"
    ]
    .transform("sum")
)


proporcion[
    "porcentaje"
] = (
    proporcion[
        "cantidad"
    ]
    /
    totales_fecha
    * 100
)


fig = px.area(
    proporcion,
    x="fecha",
    y="porcentaje",
    color="nivel_riesgo",
    groupnorm="fraction",
    title=(
        "Proporción de ALTO y BAJO "
        "a lo largo del tiempo"
    )
)


fig.update_layout(
    xaxis_title="Fecha",
    yaxis_title="Porcentaje (%)"
)


st.plotly_chart(
    fig,
    use_container_width=True
)


# ============================================================
# 8. RIESGO POR LOTE ALTO VS BAJO
# ============================================================

st.header(
    "8️⃣ Distribución ALTO vs BAJO por lote"
)


lote_riesgo = (
    df_filtrado
    .groupby(
        [
            "id_lote",
            "nivel_riesgo"
        ]
    )
    .size()
    .reset_index(
        name="cantidad"
    )
)


fig = px.bar(
    lote_riesgo,
    x="id_lote",
    y="cantidad",
    color="nivel_riesgo",
    barmode="group",
    title=(
        "Comparación de predicciones ALTO y BAJO "
        "por lote"
    )
)


fig.update_layout(
    xaxis_title="Lote",
    yaxis_title="Cantidad"
)


st.plotly_chart(
    fig,
    use_container_width=True
)


# ============================================================
# 9. PORCENTAJE POR LOTE
# ============================================================

st.header(
    "9️⃣ Porcentaje ALTO y BAJO dentro de cada lote"
)


porcentaje_lote = (
    df_filtrado
    .groupby(
        [
            "id_lote",
            "nivel_riesgo"
        ]
    )
    .size()
    .reset_index(
        name="cantidad"
    )
)


totales_lote = (
    porcentaje_lote
    .groupby("id_lote")[
        "cantidad"
    ]
    .transform("sum")
)


porcentaje_lote[
    "porcentaje"
] = (
    porcentaje_lote[
        "cantidad"
    ]
    /
    totales_lote
    * 100
)


fig = px.bar(
    porcentaje_lote,
    x="id_lote",
    y="porcentaje",
    color="nivel_riesgo",
    barmode="stack",
    text="porcentaje",
    title=(
        "Composición porcentual ALTO / BAJO "
        "por lote"
    )
)


fig.update_layout(
    xaxis_title="Lote",
    yaxis_title="Porcentaje (%)"
)


st.plotly_chart(
    fig,
    use_container_width=True
)


# ============================================================
# 10. MAPA DE CALOR
# ============================================================

st.header(
    "🔟 Mapa de riesgo por lote y fecha"
)


heatmap = (
    df_filtrado
    .groupby(
        [
            "id_lote",
            "fecha"
        ]
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


pivot = heatmap.pivot(
    index="id_lote",
    columns="fecha",
    values="probabilidad_pct"
)


fig = go.Figure(
    data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns,
        y=pivot.index,
        colorbar=dict(
            title="Probabilidad (%)"
        ),
        hovertemplate=(
            "Lote: %{y}<br>"
            "Fecha: %{x}<br>"
            "Probabilidad: %{z:.1f}%"
            "<extra></extra>"
        )
    )
)


fig.update_layout(
    title=(
        "Probabilidad estimada de riesgo "
        "por lote y fecha"
    ),
    xaxis_title="Fecha",
    yaxis_title="Lote"
)


st.plotly_chart(
    fig,
    use_container_width=True
)


# ============================================================
# 11. PROBABILIDAD PROMEDIO ALTO VS BAJO
# ============================================================

st.header(
    "1️⃣1️⃣ Probabilidad promedio por clasificación"
)


promedios = pd.DataFrame({
    "Nivel": [
        "BAJO",
        "ALTO"
    ],

    "Probabilidad": [
        promedio_bajo * 100
        if not pd.isna(promedio_bajo)
        else 0,

        promedio_alto * 100
        if not pd.isna(promedio_alto)
        else 0
    ]
})


fig = px.bar(
    promedios,
    x="Nivel",
    y="Probabilidad",
    color="Nivel",
    text="Probabilidad",
    title=(
        "Probabilidad promedio estimada "
        "según clasificación"
    )
)


fig.update_traces(
    texttemplate="%{text:.1f}%"
)


fig.add_hline(
    y=umbral * 100,
    line_dash="dash",
    annotation_text="Umbral"
)


fig.update_layout(
    xaxis_title="Nivel",
    yaxis_title="Probabilidad promedio (%)"
)


st.plotly_chart(
    fig,
    use_container_width=True
)


# ============================================================
# 12. PREDICCIONES CERCANAS AL UMBRAL
# ============================================================

st.header(
    "1️⃣2️⃣ Predicciones cercanas al umbral"
)


df_filtrado[
    "distancia_umbral"
] = abs(
    df_filtrado[
        "probabilidad_riesgo_predicha"
    ]
    -
    umbral
)


cercanas = (
    df_filtrado
    .sort_values(
        "distancia_umbral"
    )
    .head(30)
    .copy()
)


cercanas[
    "distancia_pct"
] = (
    cercanas[
        "distancia_umbral"
    ] * 100
)


fig = px.scatter(
    cercanas,
    x="probabilidad_pct",
    y="id_lote",
    color="nivel_riesgo",
    size="distancia_pct",
    hover_data=[
        "fecha",
        "probabilidad_pct",
        "distancia_pct"
    ],
    title=(
        "Predicciones más cercanas "
        "al punto de decisión"
    )
)


fig.add_vline(
    x=umbral * 100,
    line_dash="dash",
    annotation_text="Umbral"
)


fig.update_layout(
    xaxis_title="Probabilidad (%)",
    yaxis_title="Lote"
)


st.plotly_chart(
    fig,
    use_container_width=True
)


# ============================================================
# 13. TABLA DE RESUMEN
# ============================================================

st.header(
    "1️⃣3️⃣ Resumen comparativo"
)


tabla = (
    df_filtrado
    .groupby("nivel_riesgo")
    .agg(
        predicciones=(
            "id_lote",
            "count"
        ),

        lotes=(
            "id_lote",
            "nunique"
        ),

        probabilidad_promedio=(
            "probabilidad_riesgo_predicha",
            "mean"
        ),

        probabilidad_minima=(
            "probabilidad_riesgo_predicha",
            "min"
        ),

        probabilidad_maxima=(
            "probabilidad_riesgo_predicha",
            "max"
        )
    )
    .reset_index()
)


tabla[
    "porcentaje_total"
] = (
    tabla[
        "predicciones"
    ]
    /
    total
    * 100
)


tabla[
    "probabilidad_promedio"
] *= 100


tabla[
    "probabilidad_minima"
] *= 100


tabla[
    "probabilidad_maxima"
] *= 100


tabla = tabla.rename(
    columns={
        "nivel_riesgo": "Nivel",
        "predicciones": "Predicciones",
        "lotes": "Lotes",
        "porcentaje_total": "% del total",
        "probabilidad_promedio": (
            "Probabilidad promedio (%)"
        ),
        "probabilidad_minima": (
            "Probabilidad mínima (%)"
        ),
        "probabilidad_maxima": (
            "Probabilidad máxima (%)"
        )
    }
)


st.dataframe(
    tabla,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# 14. REAL VS PREDICHO
# ============================================================

if (
    "verificado" in df_filtrado.columns
    and
    "target_riesgo_alto_4sem_real"
    in df_filtrado.columns
):

    df_real = df_filtrado.copy()


    df_real["verificado_bool"] = (
        df_real["verificado"]
        .apply(normalizar_bool)
    )


    df_real = df_real[
        df_real[
            "verificado_bool"
        ]
        &
        df_real[
            "target_riesgo_alto_4sem_real"
        ].notna()
    ].copy()


    if not df_real.empty:

        st.header(
            "1️⃣4️⃣ Riesgo real vs riesgo predicho"
        )


        df_real[
            "real_bool"
        ] = df_real[
            "target_riesgo_alto_4sem_real"
        ].apply(
            normalizar_bool
        )


        df_real[
            "real_nivel"
        ] = np.where(
            df_real[
                "real_bool"
            ],
            "ALTO",
            "BAJO"
        )


        comparacion = pd.crosstab(
            df_real[
                "real_nivel"
            ],
            df_real[
                "nivel_riesgo"
            ]
        )


        comparacion = comparacion.reindex(
            index=[
                "ALTO",
                "BAJO"
            ],
            columns=[
                "ALTO",
                "BAJO"
            ],
            fill_value=0
        )


        fig = go.Figure(
            data=go.Heatmap(
                z=comparacion.values,
                x=[
                    "Predicho ALTO",
                    "Predicho BAJO"
                ],
                y=[
                    "Real ALTO",
                    "Real BAJO"
                ],
                text=comparacion.values,
                texttemplate="%{text}",
                colorbar=dict(
                    title="Cantidad"
                )
            )
        )


        fig.update_layout(
            title=(
                "Matriz de comparación "
                "real vs predicha"
            ),
            xaxis_title="Predicción",
            yaxis_title="Resultado real"
        )


        st.plotly_chart(
            fig,
            use_container_width=True
        )


    else:

        st.info(
            "Todavía no existen suficientes "
            "predicciones verificadas para comparar "
            "mortalidad real y predicha."
        )


# ============================================================
# INFORMACIÓN FINAL
# ============================================================

st.divider()


st.caption(
    "El sistema clasifica como riesgo ALTO las observaciones "
    "cuya probabilidad estimada es mayor o igual al umbral "
    f"utilizado ({umbral:.2f}). Las categorías ALTO y BAJO "
    "representan predicciones del modelo; no deben interpretarse "
    "como mortalidad real hasta que exista un desenlace observado "
    "y registrado en target_riesgo_alto_4sem_real."
)