# ============================================================
# SIPREM-BOVINO
# DASHBOARD DE RIESGO DE MORTALIDAD
# ============================================================
#
# Este dashboard se enfoca exclusivamente en:
#
#   - Riesgo de mortalidad predicho
#   - Probabilidad estimada
#   - Clasificación ALTO / BAJO
#   - Evolución temporal
#   - Comportamiento por lote
#   - Comparación predicción vs desenlace real
#
# Fuente:
#   gold_ml.predicciones
#
# ============================================================


# ============================================================
# IMPORTACIONES
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from utils.database import get_connection


# ============================================================
# CONFIGURACIÓN DE STREAMLIT
# ============================================================

st.set_page_config(
    page_title="SIPREM-BOVINO | Riesgo de Mortalidad",
    page_icon="🐄",
    layout="wide"
)


# ============================================================
# TÍTULO
# ============================================================

st.title("🐄 SIPREM-BOVINO")

st.subheader(
    "Dashboard de riesgo de mortalidad bovina"
)

st.caption(
    "Visualización de predicciones generadas por el modelo "
    "Random Forest para un horizonte de 4 semanas."
)


# ============================================================
# FUNCIÓN PARA CARGAR LOS DATOS
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
# CARGAR DATOS
# ============================================================

try:

    df = cargar_predicciones()

except Exception as e:

    st.error(
        "❌ No fue posible conectarse con Supabase."
    )

    st.exception(e)

    st.stop()


# ============================================================
# VALIDAR DATASET
# ============================================================

if df.empty:

    st.warning(
        "⚠️ No existen predicciones registradas "
        "en gold_ml.predicciones."
    )

    st.stop()


# ============================================================
# COPIA DE SEGURIDAD
# ============================================================

df = df.copy()


# ============================================================
# PREPARACIÓN DE DATOS
# ============================================================

# ------------------------------------------------------------
# FECHA
# ------------------------------------------------------------

df["fecha"] = pd.to_datetime(
    df["fecha"],
    errors="coerce"
)


# ------------------------------------------------------------
# PROBABILIDAD
# ------------------------------------------------------------

df[
    "probabilidad_riesgo_predicha"
] = pd.to_numeric(
    df[
        "probabilidad_riesgo_predicha"
    ],
    errors="coerce"
)


# Eliminar probabilidades inválidas
df = df[
    df[
        "probabilidad_riesgo_predicha"
    ].notna()
].copy()


# ------------------------------------------------------------
# RIESGO PREDICHO
# ------------------------------------------------------------

def convertir_booleano(valor):

    if pd.isna(valor):
        return False

    if isinstance(valor, bool):
        return valor

    if isinstance(valor, (int, float, np.integer, np.floating)):
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
    convertir_booleano
)


# ------------------------------------------------------------
# NIVEL DE RIESGO
# ------------------------------------------------------------

df["nivel_riesgo"] = np.where(
    df["riesgo_alto_predicho"],
    "ALTO",
    "BAJO"
)


# ------------------------------------------------------------
# PORCENTAJE
# ------------------------------------------------------------

df["probabilidad_pct"] = (
    df[
        "probabilidad_riesgo_predicha"
    ] * 100
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("🔎 Filtros")


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
        .tolist()
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
# FILTRO DE LOTE
# ============================================================

lotes = sorted(
    df[
        "id_lote"
    ]
    .dropna()
    .astype(str)
    .unique()
    .tolist()
)


lotes_seleccionados = st.sidebar.multiselect(
    "Lotes",
    lotes,
    default=lotes
)


# ============================================================
# FILTRO DE NIVEL DE RIESGO
# ============================================================

niveles_seleccionados = st.sidebar.multiselect(
    "Nivel de riesgo",
    ["ALTO", "BAJO"],
    default=["ALTO", "BAJO"]
)


# ============================================================
# FILTRO DE FECHA
# ============================================================

fecha_valida = df[
    "fecha"
].dropna()


if not fecha_valida.empty:

    fecha_min = fecha_valida.min().date()

    fecha_max = fecha_valida.max().date()

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


# ------------------------------------------------------------
# MODELO
# ------------------------------------------------------------

if modelos_seleccionados:

    df_filtrado = df_filtrado[
        df_filtrado[
            "modelo_utilizado"
        ].isin(
            modelos_seleccionados
        )
    ]


# ------------------------------------------------------------
# LOTE
# ------------------------------------------------------------

if lotes_seleccionados:

    df_filtrado = df_filtrado[
        df_filtrado[
            "id_lote"
        ].astype(str).isin(
            lotes_seleccionados
        )
    ]


# ------------------------------------------------------------
# NIVEL DE RIESGO
# ------------------------------------------------------------

if niveles_seleccionados:

    df_filtrado = df_filtrado[
        df_filtrado[
            "nivel_riesgo"
        ].isin(
            niveles_seleccionados
        )
    ]


# ------------------------------------------------------------
# FECHA
# ------------------------------------------------------------

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
# VALIDAR FILTROS
# ============================================================

if df_filtrado.empty:

    st.warning(
        "⚠️ No existen registros con los filtros seleccionados."
    )

    st.stop()


# ============================================================
# OBTENER UMBRAL
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
# INDICADORES GENERALES
# ============================================================

total_predicciones = len(
    df_filtrado
)


total_lotes = df_filtrado[
    "id_lote"
].nunique()


total_alto = int(
    df_filtrado[
        "riesgo_alto_predicho"
    ].sum()
)


total_bajo = (
    total_predicciones
    - total_alto
)


porcentaje_alto = (
    total_alto
    /
    total_predicciones
    * 100
)


probabilidad_promedio = (
    df_filtrado[
        "probabilidad_riesgo_predicha"
    ].mean()
    * 100
)


probabilidad_maxima = (
    df_filtrado[
        "probabilidad_riesgo_predicha"
    ].max()
    * 100
)


probabilidad_minima = (
    df_filtrado[
        "probabilidad_riesgo_predicha"
    ].min()
    * 100
)


# ============================================================
# SECCIÓN 1
# INDICADORES PRINCIPALES
# ============================================================

st.header(
    "📊 Indicadores generales de riesgo"
)


col1, col2, col3, col4, col5 = st.columns(5)


with col1:

    st.metric(
        "Predicciones",
        f"{total_predicciones:,}"
    )


with col2:

    st.metric(
        "Lotes",
        f"{total_lotes:,}"
    )


with col3:

    st.metric(
        "Riesgo ALTO",
        f"{total_alto:,}"
    )


with col4:

    st.metric(
        "% Riesgo ALTO",
        f"{porcentaje_alto:.1f}%"
    )


with col5:

    st.metric(
        "Probabilidad promedio",
        f"{probabilidad_promedio:.1f}%"
    )


st.divider()


# ============================================================
# SECCIÓN 2
# DISTRIBUCIÓN ALTO / BAJO
# ============================================================

st.header(
    "1️⃣ Distribución del riesgo de mortalidad"
)


col1, col2 = st.columns(2)


# ------------------------------------------------------------
# BARRAS
# ------------------------------------------------------------

with col1:

    datos_riesgo = pd.DataFrame({
        "nivel": [
            "ALTO",
            "BAJO"
        ],

        "cantidad": [
            total_alto,
            total_bajo
        ]
    })


    fig = px.bar(
        datos_riesgo,
        x="nivel",
        y="cantidad",
        text="cantidad",
        title="Cantidad de predicciones por nivel de riesgo"
    )


    fig.update_layout(
        xaxis_title="Nivel de riesgo",
        yaxis_title="Cantidad"
    )


    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ------------------------------------------------------------
# DONA
# ------------------------------------------------------------

with col2:

    fig = px.pie(
        datos_riesgo,
        names="nivel",
        values="cantidad",
        hole=0.55,
        title="Proporción de riesgo de mortalidad"
    )


    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ============================================================
# SECCIÓN 3
# DISTRIBUCIÓN DE PROBABILIDADES
# ============================================================

st.header(
    "2️⃣ Distribución de la probabilidad de mortalidad"
)


fig = px.histogram(
    df_filtrado,
    x="probabilidad_pct",
    nbins=20,
    marginal="box",
    title=(
        "Distribución de las probabilidades "
        "estimadas por el modelo"
    )
)


fig.add_vline(
    x=umbral * 100,
    line_dash="dash",
    annotation_text=(
        f"Umbral = {umbral:.2f}"
    )
)


fig.update_layout(
    xaxis_title="Probabilidad de riesgo (%)",
    yaxis_title="Número de predicciones"
)


st.plotly_chart(
    fig,
    use_container_width=True
)


# ============================================================
# SECCIÓN 4
# EVOLUCIÓN TEMPORAL
# ============================================================

st.header(
    "3️⃣ Evolución temporal del riesgo"
)


evolucion = (
    df_filtrado
    .groupby("fecha")
    .agg(
        probabilidad_promedio=(
            "probabilidad_riesgo_predicha",
            "mean"
        ),

        cantidad_alto=(
            "riesgo_alto_predicho",
            "sum"
        ),

        total=(
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


evolucion[
    "porcentaje_alto"
] = (
    evolucion[
        "cantidad_alto"
    ]
    /
    evolucion[
        "total"
    ]
    * 100
)


# ------------------------------------------------------------
# PROBABILIDAD PROMEDIO
# ------------------------------------------------------------

fig = px.line(
    evolucion,
    x="fecha",
    y="probabilidad_pct",
    markers=True,
    title=(
        "Evolución de la probabilidad "
        "promedio de riesgo"
    )
)


fig.add_hline(
    y=umbral * 100,
    line_dash="dash",
    annotation_text=(
        f"Umbral {umbral:.2f}"
    )
)


fig.update_layout(
    xaxis_title="Fecha",
    yaxis_title="Probabilidad promedio (%)"
)


st.plotly_chart(
    fig,
    use_container_width=True
)


# ------------------------------------------------------------
# ALERTAS ALTAS
# ------------------------------------------------------------

fig = px.bar(
    evolucion,
    x="fecha",
    y="cantidad_alto",
    text="cantidad_alto",
    title=(
        "Cantidad de predicciones clasificadas "
        "como riesgo ALTO por fecha"
    )
)


fig.update_layout(
    xaxis_title="Fecha",
    yaxis_title="Cantidad de alertas"
)


st.plotly_chart(
    fig,
    use_container_width=True
)


# ============================================================
# SECCIÓN 5
# PORCENTAJE ALTO POR FECHA
# ============================================================

st.header(
    "4️⃣ Porcentaje de riesgo ALTO a lo largo del tiempo"
)


fig = px.area(
    evolucion,
    x="fecha",
    y="porcentaje_alto",
    title=(
        "Proporción de predicciones de riesgo ALTO"
    )
)


fig.update_layout(
    xaxis_title="Fecha",
    yaxis_title="Riesgo ALTO (%)"
)


st.plotly_chart(
    fig,
    use_container_width=True
)


# ============================================================
# SECCIÓN 6
# RIESGO POR LOTE
# ============================================================

st.header(
    "5️⃣ Riesgo de mortalidad por lote"
)


riesgo_lote = (
    df_filtrado
    .groupby("id_lote")
    .agg(
        total_predicciones=(
            "id_lote",
            "count"
        ),

        alertas_alto=(
            "riesgo_alto_predicho",
            "sum"
        ),

        probabilidad_promedio=(
            "probabilidad_riesgo_predicha",
            "mean"
        ),

        probabilidad_maxima=(
            "probabilidad_riesgo_predicha",
            "max"
        )
    )
    .reset_index()
)


riesgo_lote[
    "porcentaje_alto"
] = (
    riesgo_lote[
        "alertas_alto"
    ]
    /
    riesgo_lote[
        "total_predicciones"
    ]
    * 100
)


riesgo_lote[
    "probabilidad_promedio_pct"
] = (
    riesgo_lote[
        "probabilidad_promedio"
    ] * 100
)


riesgo_lote[
    "probabilidad_maxima_pct"
] = (
    riesgo_lote[
        "probabilidad_maxima"
    ] * 100
)


# ------------------------------------------------------------
# GRÁFICO 1
# ------------------------------------------------------------

fig = px.bar(
    riesgo_lote.sort_values(
        "porcentaje_alto",
        ascending=False
    ),
    x="id_lote",
    y="porcentaje_alto",
    text="porcentaje_alto",
    title=(
        "Porcentaje de predicciones de "
        "riesgo ALTO por lote"
    )
)


fig.update_traces(
    texttemplate="%{text:.1f}%"
)


fig.update_layout(
    xaxis_title="Lote",
    yaxis_title="% Riesgo ALTO"
)


st.plotly_chart(
    fig,
    use_container_width=True
)


# ------------------------------------------------------------
# GRÁFICO 2
# ------------------------------------------------------------

fig = px.bar(
    riesgo_lote.sort_values(
        "probabilidad_promedio_pct",
        ascending=False
    ),
    x="id_lote",
    y="probabilidad_promedio_pct",
    text="probabilidad_promedio_pct",
    title=(
        "Probabilidad promedio de riesgo por lote"
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
    xaxis_title="Lote",
    yaxis_title="Probabilidad promedio (%)"
)


st.plotly_chart(
    fig,
    use_container_width=True
)


# ============================================================
# SECCIÓN 7
# TOP 10 LOTES
# ============================================================

st.header(
    "6️⃣ Ranking de lotes con mayor riesgo"
)


top_lotes = (
    riesgo_lote
    .sort_values(
        "probabilidad_promedio_pct",
        ascending=False
    )
    .head(10)
)


fig = px.bar(
    top_lotes.sort_values(
        "probabilidad_promedio_pct"
    ),
    x="probabilidad_promedio_pct",
    y="id_lote",
    orientation="h",
    text="probabilidad_promedio_pct",
    title=(
        "Top 10 lotes con mayor "
        "probabilidad promedio de riesgo"
    )
)


fig.update_traces(
    texttemplate="%{text:.1f}%"
)


fig.add_vline(
    x=umbral * 100,
    line_dash="dash",
    annotation_text="Umbral"
)


fig.update_layout(
    xaxis_title="Probabilidad promedio (%)",
    yaxis_title="Lote"
)


st.plotly_chart(
    fig,
    use_container_width=True
)


# ============================================================
# SECCIÓN 8
# MAPA DE CALOR
# ============================================================

st.header(
    "7️⃣ Mapa temporal del riesgo por lote"
)


heatmap = (
    df_filtrado
    .groupby(
        [
            "id_lote",
            "fecha"
        ]
    )[
        "probabilidad_riesgo_predicha"
    ]
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
            title="Riesgo (%)"
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
        "Probabilidad de riesgo de mortalidad "
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
# SECCIÓN 9
# BOXPLOT
# ============================================================

st.header(
    "8️⃣ Distribución de probabilidad según clasificación"
)


fig = px.box(
    df_filtrado,
    x="nivel_riesgo",
    y="probabilidad_pct",
    points="outliers",
    category_orders={
        "nivel_riesgo": [
            "BAJO",
            "ALTO"
        ]
    },
    title=(
        "Probabilidad estimada según "
        "la clasificación del modelo"
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
# SECCIÓN 10
# DISTANCIA AL UMBRAL
# ============================================================

st.header(
    "9️⃣ Predicciones cercanas al umbral"
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
    .head(20)
    .copy()
)


cercanas[
    "distancia_umbral_pct"
] = (
    cercanas[
        "distancia_umbral"
    ] * 100
)


fig = px.bar(
    cercanas.sort_values(
        "probabilidad_pct"
    ),
    x="probabilidad_pct",
    y="id_lote",
    color="nivel_riesgo",
    orientation="h",
    hover_data=[
        "fecha",
        "probabilidad_pct",
        "distancia_umbral_pct"
    ],
    title=(
        "Predicciones más cercanas al "
        "umbral de decisión"
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
# SECCIÓN 11
# MORTALIDAD REAL VS PREDICHA
# ============================================================

columnas_reales = [
    "verificado",
    "target_riesgo_alto_4sem_real"
]


existen_columnas_reales = all(
    col in df_filtrado.columns
    for col in columnas_reales
)


if existen_columnas_reales:

    df_verificado = df_filtrado[
        df_filtrado[
            "verificado"
        ].apply(convertir_booleano)
        &
        df_filtrado[
            "target_riesgo_alto_4sem_real"
        ].notna()
    ].copy()


    if not df_verificado.empty:

        st.header(
            "🔟 Mortalidad real vs riesgo predicho"
        )

        # ----------------------------------------------------
        # CONVERTIR TARGET REAL
        # ----------------------------------------------------

        df_verificado[
            "target_real"
        ] = df_verificado[
            "target_riesgo_alto_4sem_real"
        ].apply(
            convertir_booleano
        )


        df_verificado[
            "target_real_texto"
        ] = np.where(
            df_verificado[
                "target_real"
            ],
            "ALTO",
            "BAJO"
        )


        # ----------------------------------------------------
        # MATRIZ DE COMPARACIÓN
        # ----------------------------------------------------

        comparacion = pd.crosstab(
            df_verificado[
                "target_real_texto"
            ],
            df_verificado[
                "nivel_riesgo"
            ]
        )


        comparacion = comparacion.reindex(
            index=["ALTO", "BAJO"],
            columns=["ALTO", "BAJO"],
            fill_value=0
        )


        fig_confusion = go.Figure(
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


        fig_confusion.update_layout(
            title=(
                "Comparación entre mortalidad "
                "real y predicción"
            ),
            xaxis_title="Predicción del modelo",
            yaxis_title="Desenlace real"
        )


        st.plotly_chart(
            fig_confusion,
            use_container_width=True
        )


        # ----------------------------------------------------
        # CANTIDAD REAL VS PREDICHA
        # ----------------------------------------------------

        real_alto = int(
            df_verificado[
                "target_real"
            ].sum()
        )


        predicho_alto = int(
            df_verificado[
                "riesgo_alto_predicho"
            ].sum()
        )


        datos_comparacion = pd.DataFrame({
            "tipo": [
                "Mortalidad/riesgo real",
                "Riesgo predicho"
            ],

            "cantidad": [
                real_alto,
                predicho_alto
            ]
        })


        fig = px.bar(
            datos_comparacion,
            x="tipo",
            y="cantidad",
            text="cantidad",
            title=(
                "Riesgo real vs riesgo "
                "clasificado por el modelo"
            )
        )


        fig.update_layout(
            xaxis_title="Tipo",
            yaxis_title="Cantidad"
        )


        st.plotly_chart(
            fig,
            use_container_width=True
        )


        # ----------------------------------------------------
        # EVOLUCIÓN REAL VS PREDICHA
        # ----------------------------------------------------

        evolucion_real = (
            df_verificado
            .groupby("fecha")
            .agg(
                real=(
                    "target_real",
                    "mean"
                ),

                predicho=(
                    "riesgo_alto_predicho",
                    "mean"
                )
            )
            .reset_index()
        )


        evolucion_real[
            "real_pct"
        ] = (
            evolucion_real[
                "real"
            ] * 100
        )


        evolucion_real[
            "predicho_pct"
        ] = (
            evolucion_real[
                "predicho"
            ] * 100
        )


        fig = go.Figure()


        fig.add_trace(
            go.Scatter(
                x=evolucion_real[
                    "fecha"
                ],
                y=evolucion_real[
                    "real_pct"
                ],
                mode="lines+markers",
                name="Real"
            )
        )


        fig.add_trace(
            go.Scatter(
                x=evolucion_real[
                    "fecha"
                ],
                y=evolucion_real[
                    "predicho_pct"
                ],
                mode="lines+markers",
                name="Predicho"
            )
        )


        fig.update_layout(
            title=(
                "Evolución del riesgo real "
                "vs riesgo predicho"
            ),
            xaxis_title="Fecha",
            yaxis_title="Porcentaje (%)"
        )


        st.plotly_chart(
            fig,
            use_container_width=True
        )


    else:

        st.info(
            "ℹ️ Todavía no existen suficientes "
            "predicciones verificadas con desenlace "
            "real para mostrar la comparación."
        )


# ============================================================
# SECCIÓN 12
# TABLA DE LOTES
# ============================================================

st.header(
    "1️⃣1️⃣ Resumen de riesgo por lote"
)


tabla_lotes = riesgo_lote[
    [
        "id_lote",
        "total_predicciones",
        "alertas_alto",
        "porcentaje_alto",
        "probabilidad_promedio_pct",
        "probabilidad_maxima_pct"
    ]
].copy()


tabla_lotes = tabla_lotes.sort_values(
    "porcentaje_alto",
    ascending=False
)


tabla_lotes = tabla_lotes.rename(
    columns={
        "id_lote": "Lote",
        "total_predicciones": "Predicciones",
        "alertas_alto": "Alertas ALTO",
        "porcentaje_alto": "% ALTO",
        "probabilidad_promedio_pct": (
            "Probabilidad promedio (%)"
        ),
        "probabilidad_maxima_pct": (
            "Probabilidad máxima (%)"
        )
    }
)


st.dataframe(
    tabla_lotes,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# SECCIÓN 13
# PREDICCIONES MÁS CRÍTICAS
# ============================================================

st.header(
    "1️⃣2️⃣ Predicciones con mayor probabilidad de riesgo"
)


criticas = (
    df_filtrado
    .sort_values(
        "probabilidad_riesgo_predicha",
        ascending=False
    )
    .head(20)
    .copy()
)


columnas_criticas = [
    "id_lote",
    "fecha",
    "probabilidad_pct",
    "nivel_riesgo",
    "umbral_utilizado",
    "modelo_utilizado"
]


columnas_criticas = [
    col
    for col in columnas_criticas
    if col in criticas.columns
]


criticas_mostrar = criticas[
    columnas_criticas
].copy()


criticas_mostrar = criticas_mostrar.rename(
    columns={
        "id_lote": "Lote",
        "fecha": "Fecha",
        "probabilidad_pct": "Probabilidad (%)",
        "nivel_riesgo": "Riesgo",
        "umbral_utilizado": "Umbral",
        "modelo_utilizado": "Modelo"
    }
)


st.dataframe(
    criticas_mostrar,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# SECCIÓN 14
# INFORMACIÓN DEL MODELO
# ============================================================

st.divider()

st.header(
    "ℹ️ Información de la predicción"
)


col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "Horizonte",
        "4 semanas"
    )


with col2:

    st.metric(
        "Umbral",
        f"{umbral:.2f}"
    )


with col3:

    st.metric(
        "Probabilidad mínima",
        f"{probabilidad_minima:.1f}%"
    )


with col4:

    st.metric(
        "Probabilidad máxima",
        f"{probabilidad_maxima:.1f}%"
    )


st.caption(
    "La clasificación de riesgo ALTO se obtiene cuando "
    "la probabilidad estimada por el modelo supera o "
    "iguala el umbral utilizado en la predicción."
)


# ============================================================
# FIN
# ============================================================

st.success(
    "✅ Dashboard de riesgo de mortalidad cargado correctamente."
)