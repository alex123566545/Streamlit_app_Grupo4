import streamlit as st
import pandas as pd
import numpy as np
from utils.database import get_connection


# ============================================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================

st.set_page_config(
    page_title="SIPREM-BOVINO | Evolución por lote",
    page_icon="🐄",
    layout="wide"
)


# ============================================================
# ESTILO VISUAL: SIPREM-BOVINO
# ============================================================

st.markdown(
    """
    <style>
        :root {
            --bg: #171411;
            --sidebar: #201A16;
            --card: #282019;
            --brown: #A8794E;
            --brown-light: #C49A70;
            --text: #FFFFFF;
            --muted: #D0C5BA;
            --border: #403329;
        }

        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"] {
            background-color: var(--bg) !important;
            color: var(--text) !important;
        }

        .block-container {
            max-width: 1500px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        header[data-testid="stHeader"] {
            background-color: var(--bg) !important;
            background-image: none !important;
            box-shadow: none !important;
        }

        section[data-testid="stSidebar"] {
            background-color: var(--sidebar) !important;
            border-right: 1px solid var(--border);
        }

        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a,
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a span {
            color: #FFFFFF !important;
        }

        h1, h2, h3, h4, h5, h6 {
            color: #FFFFFF !important;
            letter-spacing: -0.35px;
        }

        p, .stCaption, [data-testid="stCaptionContainer"] {
            color: var(--muted);
        }

        label,
        [data-testid="stCheckbox"] label,
        [data-testid="stRadio"] label {
            color: #FFFFFF !important;
        }

        /* Tarjetas de métricas */
        [data-testid="stMetric"] {
            background: var(--card) !important;
            border: 1px solid var(--border);
            border-radius: 13px;
            padding: 16px;
        }

        [data-testid="stMetricLabel"] {
            color: var(--muted) !important;
        }

        [data-testid="stMetricValue"] {
            color: var(--brown-light) !important;
        }

        [data-testid="stMetricDelta"] {
            color: var(--muted) !important;
        }

        /* Controles y selectores */
        .stSelectbox div[data-baseweb="select"] > div,
        .stMultiSelect div[data-baseweb="select"] > div,
        .stTextInput input,
        .stTextArea textarea,
        .stDateInput input,
        [data-baseweb="input"] > div {
            background-color: #000000 !important;
            color: #FFFFFF !important;
            border-color: var(--border) !important;
            border-radius: 8px;
        }

        .stTextInput input,
        .stTextArea textarea,
        .stDateInput input,
        [data-baseweb="input"] input {
            color: #FFFFFF !important;
            -webkit-text-fill-color: #FFFFFF !important;
            caret-color: #FFFFFF !important;
        }

        /* Opciones desplegables */
        [data-baseweb="select"] *,
        [data-baseweb="popover"] *,
        [role="listbox"] *,
        [role="option"] {
            color: #FFFFFF !important;
            -webkit-text-fill-color: #FFFFFF !important;
        }

        [data-baseweb="popover"],
        [data-baseweb="menu"],
        [role="listbox"],
        [role="option"] {
            background-color: #000000 !important;
        }

        [role="option"]:hover,
        [role="option"][aria-selected="true"],
        [role="option"][data-focused="true"] {
            background-color: var(--card) !important;
            color: #FFFFFF !important;
            -webkit-text-fill-color: #FFFFFF !important;
        }

        input::placeholder,
        textarea::placeholder {
            color: var(--muted) !important;
            -webkit-text-fill-color: var(--muted) !important;
            opacity: 1 !important;
        }

        /* Botones */
        .stButton > button,
        .stDownloadButton > button {
            background-color: var(--brown) !important;
            color: #FFFFFF !important;
            border: 1px solid var(--brown);
            border-radius: 9px;
            font-weight: 650;
            min-height: 42px;
            transition: all 0.2s ease;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover {
            background-color: var(--brown-light) !important;
            border-color: var(--brown-light) !important;
            color: #171411 !important;
        }

        .stButton > button:disabled,
        .stDownloadButton > button:disabled {
            background-color: #514438 !important;
            color: #BDB1A5 !important;
            border-color: #514438 !important;
        }

        /* Paneles y tablas */
        [data-testid="stDataFrame"],
        [data-testid="stTable"],
        [data-testid="stForm"],
        [data-testid="stExpander"] {
            border: 1px solid var(--border);
            border-radius: 10px;
        }

        [data-testid="stExpander"] {
            background-color: var(--card) !important;
        }

        [data-testid="stExpander"] summary {
            color: #FFFFFF !important;
        }

        hr {
            border-color: var(--border) !important;
        }

        [data-testid="stAlert"] {
            border-radius: 10px;
        }

        @media (max-width: 768px) {
            .block-container {
                padding: 1.2rem 1rem 2rem 1rem;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# ENCABEZADO
# ============================================================

st.title("🐄 Evolución histórica por lote")

st.caption(
    "Explore los cambios semanales de cada lote y contraste "
    "el riesgo histórico con las predicciones y los resultados verificados."
)


# ============================================================
# CONFIGURACIÓN DE VARIABLES
# ============================================================

VARIABLES = {
    "tamano_lote_cabezas": "Tamaño del lote (cabezas)",
    "cobertura_vacunacion_pct": "Cobertura de vacunación (%)",
    "dias_desde_desparasitacion": "Días desde desparasitación",
    "animales_nuevos_30d": "Animales nuevos (30 días)",
    "visitas_tecnicas_mes": "Visitas técnicas del mes",
    "casos_respiratorios": "Casos respiratorios",
    "casos_diarreicos": "Casos diarreicos",
    "temperatura_min_c": "Temperatura mínima (°C)",
    "temperatura_media_c": "Temperatura media (°C)",
    "temperatura_max_c": "Temperatura máxima (°C)",
    "humedad_relativa_pct": "Humedad relativa (%)",
    "precipitacion_semanal_mm": "Precipitación semanal (mm)",
    "condicion_pastura_indice": "Condición de pastura",
    "indice_ndvi_satelital": "Índice NDVI satelital",
    "consumo_ms_kg_animal_dia": "Consumo de materia seca (kg/animal/día)",
    "agua_l_animal_dia": "Consumo de agua (L/animal/día)",
    "actividad_sensor_indice": "Actividad del sensor",
    "condicion_corporal_prom": "Condición corporal promedio",
    "precio_leche_local_s_kg": "Precio local de leche (S/kg)",
    "altitud_msnm": "Altitud (msnm)",
    "distancia_centro_veterinario_km": "Distancia al centro veterinario (km)",
    "media_movil_3s_pastura": "Media móvil 3 semanas: pastura",
    "media_movil_3s_condicion_corporal": "Media móvil 3 semanas: condición corporal",
    "media_movil_3s_temperatura": "Media móvil 3 semanas: temperatura",
    "media_movil_4s_pastura": "Media móvil 4 semanas: pastura",
    "media_movil_4s_condicion_corporal": "Media móvil 4 semanas: condición corporal",
    "media_movil_4s_temperatura": "Media móvil 4 semanas: temperatura",
}


# ============================================================
# CARGA DE DATOS
# ============================================================

@st.cache_data(ttl=60)
def cargar_tablas():
    conn = get_connection()

    try:
        historico = pd.read_sql_query(
            """
            SELECT *
            FROM gold_ml.dataset_features
            ORDER BY id_lote, fecha;
            """,
            conn
        )

        predicciones = pd.read_sql_query(
            """
            SELECT *
            FROM gold_ml.predicciones
            ORDER BY id_lote, fecha;
            """,
            conn
        )

        return historico, predicciones

    finally:
        conn.close()


try:
    historico, predicciones = cargar_tablas()

except Exception as exc:
    st.error(
        "No se pudieron leer gold_ml.dataset_features y "
        "gold_ml.predicciones. Revise la conexión y los permisos."
    )
    st.exception(exc)
    st.stop()


# ============================================================
# VALIDACIÓN DE LAS TABLAS
# ============================================================

for df in (historico, predicciones):

    if not {"id_lote", "fecha"}.issubset(df.columns):
        st.error(
            "Ambas tablas deben contener las columnas id_lote y fecha."
        )
        st.stop()

    df["id_lote"] = df["id_lote"].astype(str)
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")

    df.dropna(subset=["fecha"], inplace=True)


if historico.empty and predicciones.empty:
    st.info("Todavía no hay registros para mostrar.")
    st.stop()


historico = historico.copy()
predicciones = predicciones.copy()

historico["_origen"] = "Histórico de entrenamiento"
predicciones["_origen"] = "Predicción operativa"

historico["_prioridad"] = 0
predicciones["_prioridad"] = 1


# ============================================================
# UNIFICAR HISTÓRICO Y PREDICCIONES
# ============================================================

datos = pd.concat(
    [historico, predicciones],
    ignore_index=True,
    sort=False
)

if "predicho_en" in datos.columns:

    datos["predicho_en"] = pd.to_datetime(
        datos["predicho_en"],
        errors="coerce"
    )

    datos = datos.sort_values(
        ["id_lote", "fecha", "_prioridad", "predicho_en"],
        na_position="first"
    )

else:

    datos = datos.sort_values(
        ["id_lote", "fecha", "_prioridad"]
    )


datos = (
    datos
    .drop_duplicates(["id_lote", "fecha"], keep="last")
    .sort_values(["id_lote", "fecha"])
    .copy()
)


lotes = sorted(
    datos["id_lote"].dropna().unique().tolist()
)

if not lotes:
    st.info("No se encontraron lotes válidos.")
    st.stop()


# ============================================================
# VISTA GENERAL: TODOS LOS LOTES
# ============================================================

st.divider()

st.header("📊 Evolución general de todos los lotes")

st.caption(
    "Compara los cambios semanales de los lotes durante un periodo "
    "determinado. Puedes visualizar todos los lotes o seleccionar "
    "únicamente aquellos que deseas analizar."
)


# ============================================================
# SELECTORES GENERALES DE LOTES Y FECHAS
# ============================================================

col_modo, col_lotes = st.columns([1, 2])

with col_modo:

    modo_lotes = st.selectbox(
        "¿Qué lotes deseas visualizar?",
        options=[
            "Todos los lotes",
            "Seleccionar lotes"
        ],
        index=0,
        key="modo_lotes_general"
    )


with col_lotes:

    if modo_lotes == "Todos los lotes":

        lotes_seleccionados = lotes

        st.multiselect(
            "Lotes incluidos",
            options=lotes,
            default=lotes,
            disabled=True,
            key="lotes_todos_general"
        )

    else:

        lotes_seleccionados = st.multiselect(
            "Selecciona los lotes que deseas comparar",
            options=lotes,
            default=lotes[:min(3, len(lotes))],
            key="lotes_seleccionados_general"
        )


# ============================================================
# FILTRAR POR FECHAS
# ============================================================

datos_fechas = datos[
    datos["id_lote"].isin(lotes_seleccionados)
].copy()


if not datos_fechas.empty:

    fecha_min_general = datos_fechas["fecha"].min().date()
    fecha_max_general = datos_fechas["fecha"].max().date()

    col_fecha_inicio, col_fecha_fin = st.columns(2)

    with col_fecha_inicio:

        fecha_inicio_general = st.date_input(
            "Fecha de inicio",
            value=fecha_min_general,
            min_value=fecha_min_general,
            max_value=fecha_max_general,
            key="fecha_inicio_general"
        )

    with col_fecha_fin:

        fecha_fin_general = st.date_input(
            "Fecha de fin",
            value=fecha_max_general,
            min_value=fecha_min_general,
            max_value=fecha_max_general,
            key="fecha_fin_general"
        )

    if fecha_inicio_general > fecha_fin_general:
        st.warning(
            "La fecha de inicio no puede ser posterior a la fecha de fin."
        )
        st.stop()

    df_todos = datos_fechas[
        (datos_fechas["fecha"].dt.date >= fecha_inicio_general)
        & (datos_fechas["fecha"].dt.date <= fecha_fin_general)
    ].copy()

else:

    df_todos = pd.DataFrame()

    st.info(
        "Selecciona al menos un lote para consultar su evolución."
    )


# ============================================================
# GRÁFICOS GENERALES
# ============================================================

if not df_todos.empty:

    st.caption(
        f"Lotes seleccionados: {df_todos['id_lote'].nunique()} | "
        f"Fechas disponibles: {df_todos['fecha'].nunique()} | "
        f"Registros: {len(df_todos)}"
    )

    # ========================================================
    # 1. RIESGO HISTÓRICO ENTRE LOTES
    # ========================================================

    st.subheader("1. Comparación del riesgo de mortalidad")

    st.write(
        "Se muestra únicamente el riesgo histórico de cada lote. "
        "El valor 0 indica un resultado negativo y 100 un resultado positivo."
    )

    columna_riesgo = "target_riesgo_alto_4sem"

    if columna_riesgo in df_todos.columns:

        grafico_riesgo = df_todos[
            ["fecha", "id_lote", columna_riesgo]
        ].copy()

        grafico_riesgo[columna_riesgo] = pd.to_numeric(
            grafico_riesgo[columna_riesgo],
            errors="coerce"
        )

        # Llevar las etiquetas 0/1 a una escala de 0/100.
        grafico_riesgo["valor"] = (
            grafico_riesgo[columna_riesgo] * 100
        )

        grafico_riesgo = grafico_riesgo.pivot_table(
            index="fecha",
            columns="id_lote",
            values="valor",
            aggfunc="last"
        ).sort_index()

        if not grafico_riesgo.dropna(how="all").empty:

            st.line_chart(
                grafico_riesgo,
                y_label="Riesgo histórico (0–100)",
                x_label="Fecha"
            )

            st.caption(
                "Cada línea representa un lote. "
                "0 = no hubo episodio de riesgo alto; "
                "100 = sí hubo un episodio de riesgo alto. "
                "Estos valores son etiquetas, no tasas de mortalidad."
            )

        else:

            st.info(
                "No hay etiquetas históricas disponibles para "
                "graficar en las fechas seleccionadas."
            )

    else:

        st.info(
            f"La columna '{columna_riesgo}' no existe "
            "en los datos disponibles."
        )


    # ========================================================
    # 2. EVOLUCIÓN DE VARIABLES ENTRE LOTES
    # ========================================================

    st.divider()

    st.subheader("2. Evolución de las variables por lote")

    st.caption(
        "Selecciona las variables que quieres comparar. "
        "Cada gráfico mostrará una línea por lote."
    )

    variables_generales = [
        c
        for c in VARIABLES
        if c in df_todos.columns
        and pd.to_numeric(
            df_todos[c],
            errors="coerce"
        ).notna().any()
    ]

    if variables_generales:

        variables_elegidas = st.multiselect(
            "Variables que deseas comparar",
            options=variables_generales,
            default=[
                c
                for c in [
                    "casos_respiratorios",
                    "casos_diarreicos",
                    "condicion_pastura_indice",
                    "temperatura_media_c"
                ]
                if c in variables_generales
            ][:1],
            format_func=lambda c: VARIABLES[c],
            key="variables_todos_lotes"
        )

        if variables_elegidas:

            for variable in variables_elegidas:

                st.markdown(f"**{VARIABLES[variable]}**")

                grafico_variable = df_todos[
                    ["fecha", "id_lote", variable]
                ].copy()

                grafico_variable[variable] = pd.to_numeric(
                    grafico_variable[variable],
                    errors="coerce"
                )

                grafico_variable = grafico_variable.pivot_table(
                    index="fecha",
                    columns="id_lote",
                    values=variable,
                    aggfunc="last"
                ).sort_index()

                if not grafico_variable.dropna(how="all").empty:

                    st.line_chart(
                        grafico_variable,
                        y_label=VARIABLES[variable],
                        x_label="Fecha"
                    )

                else:

                    st.info(
                        f"No hay valores disponibles para "
                        f"{VARIABLES[variable]} en este periodo."
                    )

        else:

            st.info("Selecciona al menos una variable.")

    else:

        st.info(
            "No se encontraron variables numéricas conocidas "
            "en los datos seleccionados."
        )


    # ========================================================
    # DESCARGAR DATOS GENERALES
    # ========================================================

    csv_general = (
        df_todos
        .drop(columns=["_prioridad"], errors="ignore")
        .to_csv(index=False)
        .encode("utf-8-sig")
    )

    st.download_button(
        "📥 Descargar datos de los lotes seleccionados (CSV)",
        data=csv_general,
        file_name="evolucion_todos_lotes.csv",
        mime="text/csv",
        key="descargar_evolucion_todos"
    )


else:

    st.info(
        "No hay registros para los lotes y el periodo seleccionados."
    )


# ============================================================
# ANÁLISIS INDIVIDUAL DE UN LOTE
# ============================================================

st.divider()

st.header("🔎 Análisis individual de un lote")

st.caption(
    "Selecciona un lote específico para estudiar sus predicciones, "
    "resultados verificados y variables históricas."
)


col1, col2 = st.columns([1, 2])

with col1:

    lote = st.selectbox(
        "Seleccione el lote",
        options=lotes,
        key="lote_individual"
    )


df_lote_completo = datos[
    datos["id_lote"] == lote
].copy()

fecha_min = df_lote_completo["fecha"].min().date()
fecha_max = df_lote_completo["fecha"].max().date()


with col2:

    rango = st.date_input(
        "Periodo del lote",
        value=(fecha_min, fecha_max),
        min_value=fecha_min,
        max_value=fecha_max,
        key="periodo_individual"
    )


df_lote = df_lote_completo.copy()

if isinstance(rango, (tuple, list)) and len(rango) == 2:

    inicio, fin = rango

    df_lote = df_lote[
        (df_lote["fecha"].dt.date >= inicio)
        & (df_lote["fecha"].dt.date <= fin)
    ]


df_lote = df_lote.sort_values("fecha")


if df_lote.empty:

    st.warning("No hay datos para el periodo seleccionado.")
    st.stop()


# ============================================================
# MÉTRICAS DEL LOTE INDIVIDUAL
# ============================================================

n_fechas = df_lote["fecha"].nunique()

n_pred = int(
    (df_lote["_origen"] == "Predicción operativa").sum()
)

if "verificado" in df_lote.columns:

    verificado = df_lote["verificado"]

    if verificado.dtype == object:
        verificado = (
            verificado.astype(str)
            .str.strip()
            .str.lower()
            .isin(["true", "1", "t", "sí", "si"])
        )
    else:
        verificado = verificado.fillna(False).astype(bool)

    n_verif = int(verificado.sum())

else:

    n_verif = 0


m1, m2, m3 = st.columns(3)

m1.metric("Fechas observadas", n_fechas)
m2.metric("Predicciones registradas", n_pred)
m3.metric("Predicciones verificadas", n_verif)


# ============================================================
# 1. RIESGO DE MORTALIDAD DEL LOTE INDIVIDUAL
# ============================================================

st.divider()

st.subheader("1. Evolución del riesgo de mortalidad")

st.caption(
    "El modelo estima si ocurrirá al menos un episodio de riesgo alto "
    "en las cuatro semanas posteriores a cada fecha. Estas etiquetas "
    "no representan por sí mismas el número de animales fallecidos."
)


riesgo = pd.DataFrame({
    "fecha": df_lote["fecha"]
}).set_index("fecha")


if "target_riesgo_alto_4sem" in df_lote.columns:

    riesgo["Target histórico (0/100)"] = (
        pd.to_numeric(
            df_lote["target_riesgo_alto_4sem"],
            errors="coerce"
        ).to_numpy() * 100
    )


if "probabilidad_riesgo_predicha" in df_lote.columns:

    riesgo["Probabilidad predicha (%)"] = (
        pd.to_numeric(
            df_lote["probabilidad_riesgo_predicha"],
            errors="coerce"
        ).to_numpy() * 100
    )


if "target_riesgo_alto_4sem_real" in df_lote.columns:

    riesgo["Resultado verificado (0/100)"] = (
        pd.to_numeric(
            df_lote["target_riesgo_alto_4sem_real"],
            errors="coerce"
        ).to_numpy() * 100
    )


if "umbral_utilizado" in df_lote.columns:

    riesgo["Umbral del modelo (%)"] = (
        pd.to_numeric(
            df_lote["umbral_utilizado"],
            errors="coerce"
        ).to_numpy() * 100
    )


if len(riesgo.columns) and not riesgo.dropna(how="all").empty:

    st.line_chart(
        riesgo,
        y_label="Porcentaje / etiqueta (0–100)"
    )

    st.caption(
        "Target histórico y resultado verificado: 0 = no hubo episodio "
        "de riesgo alto; 100 = sí hubo. La probabilidad y el umbral "
        "son porcentajes continuos."
    )

else:

    st.info("No hay columnas de riesgo disponibles para graficar.")


# ============================================================
# TABLA DE PREDICCIONES Y RESULTADOS DEL LOTE
# ============================================================

cols = [
    c
    for c in [
        "fecha",
        "_origen",
        "probabilidad_riesgo_predicha",
        "umbral_utilizado",
        "riesgo_alto_predicho",
        "target_riesgo_alto_4sem",
        "verificado",
        "target_riesgo_alto_4sem_real",
        "intervencion_realizada",
        "modelo_utilizado"
    ]
    if c in df_lote.columns
]


if cols:

    st.dataframe(
        df_lote[cols].rename(columns={
            "fecha": "Fecha",
            "_origen": "Fuente",
            "probabilidad_riesgo_predicha": "Probabilidad predicha",
            "umbral_utilizado": "Umbral",
            "riesgo_alto_predicho": "Riesgo predicho",
            "target_riesgo_alto_4sem": "Target histórico (4 semanas)",
            "verificado": "Verificado",
            "target_riesgo_alto_4sem_real": "Resultado real (4 semanas)",
            "intervencion_realizada": "Intervención",
            "modelo_utilizado": "Modelo"
        }),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# 2. VARIABLES DEL LOTE INDIVIDUAL
# ============================================================

st.divider()

st.subheader("2. Evolución de las variables del lote")


disponibles = [
    c
    for c in VARIABLES
    if c in df_lote.columns
    and pd.to_numeric(
        df_lote[c],
        errors="coerce"
    ).notna().any()
]


if disponibles:

    predeterminadas = [
        c
        for c in [
            "casos_respiratorios",
            "casos_diarreicos",
            "condicion_pastura_indice",
            "condicion_corporal_prom",
            "temperatura_media_c"
        ]
        if c in disponibles
    ][:4]


    elegidas = st.multiselect(
        "Variables que desea comparar",
        disponibles,
        default=predeterminadas,
        format_func=lambda c: VARIABLES[c],
        key="variables_lote_individual"
    )


    if elegidas:

        grafico = df_lote[
            ["fecha"] + elegidas
        ].copy()

        for c in elegidas:

            grafico[c] = pd.to_numeric(
                grafico[c],
                errors="coerce"
            )

        grafico = grafico.set_index("fecha")

        grafico.columns = [
            VARIABLES[c] for c in grafico.columns
        ]

        st.line_chart(grafico)

        st.caption(
            "Las variables pueden tener unidades y escalas diferentes. "
            "Para compararlas con precisión, grafique juntas variables "
            "con escalas similares."
        )

    else:

        st.info("Seleccione al menos una variable.")

else:

    st.info(
        "No se encontraron variables numéricas conocidas "
        "en las columnas disponibles."
    )


# ============================================================
# DESCARGAR DATOS DEL LOTE INDIVIDUAL
# ============================================================

csv = (
    df_lote
    .drop(columns=["_prioridad"], errors="ignore")
    .to_csv(index=False)
    .encode("utf-8-sig")
)


st.download_button(
    "📥 Descargar datos de este lote (CSV)",
    data=csv,
    file_name=f"evolucion_{lote}.csv",
    mime="text/csv",
    key="descargar_lote_individual"
)


# ============================================================
# ACLARACIÓN SOBRE LA MORTALIDAD
# ============================================================

with st.expander(
    "Importante: riesgo no equivale a mortalidad observada"
):

    st.markdown(
        "Las columnas `target_riesgo_alto_4sem` y "
        "`target_riesgo_alto_4sem_real` indican si hubo al menos "
        "un episodio de riesgo alto durante la ventana futura de "
        "cuatro semanas. No son un conteo ni una tasa de animales "
        "fallecidos. Para graficar mortalidad real se necesita una "
        "variable explícita con animales muertos y, para una tasa, "
        "el número de animales expuestos."
    )