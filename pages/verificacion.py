
import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta, timezone

from utils.database import get_connection

st.set_page_config(
    page_title="SIPREM-BOVINO | Verificación",
    page_icon="🐄",
    layout="wide",
)

# ==============================================================
# ESTILO VISUAL: SIPREM-BOVINO
# ==============================================================
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
            background-color: var(--bg);
            color: var(--text);
        }

        .block-container {
            max-width: 1500px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        /* Solo los nombres de las páginas del menú lateral */
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a,
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a span {
            color: #FFFFFF !important;
        }

        section[data-testid="stSidebar"] {
            background-color: var(--sidebar);
            border-right: 1px solid var(--border);
        }

        h1, h2, h3, h4 {
            color: #FFFFFF !important;
            letter-spacing: -0.35px;
        }

        p, .stMarkdown, .stCaption {
            color: var(--muted);
        }

        /* Tarjetas de métricas */
        [data-testid="stMetric"] {
            background: var(--card);
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

        /* Tablas */
        [data-testid="stDataFrame"] {
            border: 1px solid var(--border);
            border-radius: 10px;
            overflow: hidden;
        }

        /* Campos de entrada */
        .stSelectbox div[data-baseweb="select"] > div,
        .stTextInput input,
        .stTextArea textarea,
        .stDateInput input,
        [data-baseweb="input"] {
            background-color: var(--card) !important;
            color: #FFFFFF !important;
            border-color: var(--border) !important;
            border-radius: 8px;
        }

        /* Opciones desplegables */
        [data-baseweb="select"] *,
        [data-baseweb="popover"] *,
        [role="listbox"] *,
        [role="option"] {
            color: #FFFFFF !important;
        }

        .stRadio label,
        .stCheckbox label {
            color: #FFFFFF !important;
        }

        /* Botones */
        .stButton > button {
            background-color: var(--brown);
            color: #FFFFFF !important;
            border: 1px solid var(--brown);
            border-radius: 9px;
            font-weight: 650;
            min-height: 42px;
            transition: all 0.2s ease;
        }

        .stButton > button:hover {
            background-color: var(--brown-light);
            border-color: var(--brown-light);
            color: #171411 !important;
        }

        .stButton > button:disabled {
            background-color: #514438;
            color: #BDB1A5 !important;
            border-color: #514438;
        }

        hr {
            border-color: var(--border) !important;
        }

        [data-testid="stAlert"] {
            border-radius: 10px;
        }

        /* Encabezado principal */
        .siprem-hero {
            background: linear-gradient(135deg, #302319, #211A15);
            border: 1px solid #403329;
            border-left: 4px solid #A8794E;
            border-radius: 15px;
            padding: 28px 32px;
            margin-bottom: 24px;
        }

        .siprem-eyebrow {
            color: #C49A70;
            font-size: 12px;
            font-weight: 800;
            letter-spacing: 2px;
            margin-bottom: 10px;
        }

        .siprem-hero-title {
            color: #FFFFFF;
            font-size: 32px;
            font-weight: 800;
            margin: 0 0 10px 0;
            line-height: 1.2;
        }

        .siprem-hero-text {
            color: #D0C5BA;
            font-size: 15px;
            line-height: 1.7;
            margin: 0;
        }

        @media (max-width: 768px) {
            .block-container {
                padding: 1.2rem 1rem 2rem 1rem;
            }

            .siprem-hero {
                padding: 22px 20px;
            }

            .siprem-hero-title {
                font-size: 26px;
            }
        }
        
/* Header superior de Streamlit */
header[data-testid="stHeader"] {
    background-color: #171411 !important;
}

/* Barra de herramientas del header */
header[data-testid="stHeader"] [data-testid="stToolbar"] {
    background-color: #171411 !important;
}

/* Eliminar el efecto blanco translúcido */
header[data-testid="stHeader"] {
    background-image: none !important;
    box-shadow: none !important;
}

/* Fondo de la zona superior principal */
[data-testid="stAppViewContainer"] {
    background-color: #171411 !important;
}

    </style>
    """,
    unsafe_allow_html=True,
)

# ==============================================================
# CONFIGURACIÓN
# ==============================================================
HORIZONTE_DIAS = 28
TIMEZONE_PERU = timezone(timedelta(hours=-5))
HOY = datetime.now(TIMEZONE_PERU).date()
MARGEN_ALERTA_UMBRAL = 0.10


# ==============================================================
# CARGAR PREDICCIONES
# ==============================================================
@st.cache_data(ttl=30)
def cargar_predicciones():
    conn = get_connection()
    try:
        query = """
            SELECT
                id_lote,
                fecha,
                distrito,
                categoria_zootecnica,
                raza_predominante,
                modelo_utilizado,
                umbral_utilizado,
                probabilidad_riesgo_predicha,
                riesgo_alto_predicho,
                intervencion_realizada,
                tipo_intervencion,
                fecha_intervencion,
                resultado_intervencion,
                verificado,
                target_riesgo_alto_4sem_real,
                fecha_verificacion,
                predicho_en
            FROM gold_ml.predicciones
            ORDER BY fecha DESC, id_lote ASC;
        """
        return pd.read_sql(query, conn)
    finally:
        conn.close()


# ==============================================================
# ACTUALIZAR PREDICCIÓN
# ==============================================================
def actualizar_prediccion(
    id_lote,
    fecha_prediccion,
    modelo_utilizado,
    intervencion_realizada,
    tipo_intervencion,
    fecha_intervencion,
    resultado_intervencion,
    verificado,
    target_real,
):
    """
    Actualiza los campos de seguimiento.
    No modifica las características ni la predicción original.
    """
    conn = get_connection()

    try:
        query = """
            UPDATE gold_ml.predicciones
            SET
                intervencion_realizada = %s,
                tipo_intervencion = %s,
                fecha_intervencion = %s,
                resultado_intervencion = %s,
                verificado = %s,
                target_riesgo_alto_4sem_real = %s,
                fecha_verificacion =
                    CASE
                        WHEN %s = TRUE
                        THEN COALESCE(fecha_verificacion, NOW())
                        ELSE fecha_verificacion
                    END
            WHERE
                id_lote = %s
                AND fecha = %s
                AND modelo_utilizado = %s;
        """

        valores = (
            intervencion_realizada,
            tipo_intervencion,
            fecha_intervencion,
            resultado_intervencion,
            verificado,
            target_real,
            verificado,
            id_lote,
            fecha_prediccion,
            modelo_utilizado,
        )

        with conn.cursor() as cur:
            cur.execute(query, valores)

            if cur.rowcount != 1:
                raise ValueError(
                    "No se encontró exactamente una predicción "
                    "para actualizar."
                )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


# ==============================================================
# FUNCIONES AUXILIARES
# ==============================================================
def texto_riesgo(valor):
    if valor is True:
        return "ALTO"
    if valor is False:
        return "BAJO"
    return "DESCONOCIDO"


def fecha_a_date(valor):
    if valor is None or pd.isna(valor):
        return None

    if hasattr(valor, "date"):
        return valor.date()

    if isinstance(valor, date):
        return valor

    return None


def opcion_intervencion_actual(valor):
    if pd.isna(valor):
        return "No registrado todavía"

    return "Sí" if bool(valor) else "No"


def es_zona_gris(
    riesgo_alto_predicho,
    probabilidad,
    umbral,
    margen=MARGEN_ALERTA_UMBRAL,
):
    """
    Detecta predicciones BAJO cuya probabilidad está cerca del umbral.
    """
    if riesgo_alto_predicho is True:
        return False

    if pd.isna(probabilidad) or pd.isna(umbral):
        return False

    return (umbral - probabilidad) < margen


# ==============================================================
# ENCABEZADO
# ==============================================================
st.markdown(
    """
    <div class="siprem-hero">
        <div class="siprem-eyebrow">SIPREM / BOVINO</div>
        <div class="siprem-hero-title">
            Verificación de predicciones
        </div>
        <p class="siprem-hero-text">
            Revisa las predicciones, registra las intervenciones y confirma
            los resultados reales una vez completada la ventana de 28 días.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

if "guardado_en_proceso" not in st.session_state:
    st.session_state.guardado_en_proceso = False


# ==============================================================
# CARGA DE DATOS
# ==============================================================
try:
    df = cargar_predicciones()

except Exception as e:
    st.error("No se pudo leer gold_ml.predicciones.")
    st.exception(e)
    st.stop()

if df.empty:
    st.info("No existen predicciones registradas.")
    st.stop()


# ==============================================================
# PREPARACIÓN DE DATOS
# ==============================================================
df["fecha"] = pd.to_datetime(
    df["fecha"],
    errors="coerce",
).dt.date

df["riesgo_texto"] = df["riesgo_alto_predicho"].apply(texto_riesgo)

df["estado_texto"] = df["verificado"].fillna(False).apply(
    lambda x: "VERIFICADO" if bool(x) else "PENDIENTE"
)

df["dias_desde_prediccion"] = df["fecha"].apply(
    lambda f: (HOY - f).days if pd.notna(f) else None
)

df["zona_gris"] = df.apply(
    lambda f: es_zona_gris(
        f["riesgo_alto_predicho"],
        f["probabilidad_riesgo_predicha"],
        f["umbral_utilizado"],
    ),
    axis=1,
)


# ==============================================================
# MÉTRICAS GENERALES
# ==============================================================
total = len(df)

pendientes = int(
    (~df["verificado"].fillna(False)).sum()
)

verificados = int(
    df["verificado"].fillna(False).sum()
)

listas_verificar = int(
    (
        (~df["verificado"].fillna(False))
        & (df["dias_desde_prediccion"] >= HORIZONTE_DIAS)
    ).sum()
)

fechas_futuras = int(
    (df["dias_desde_prediccion"] < 0).sum()
)

en_zona_gris = int(df["zona_gris"].sum())

st.markdown("### Resumen general")

c1, c2, c3, c4, c5, c6 = st.columns(6)

c1.metric("Total", total)
c2.metric("Pendientes", pendientes)
c3.metric("Listas para verificar", listas_verificar)
c4.metric("Verificadas", verificados)
c5.metric("Fechas futuras", fechas_futuras)

c6.metric(
    "Cerca del umbral",
    en_zona_gris,
    help=(
        "Predicciones BAJO cuya probabilidad está cerca del umbral. "
        "Esto no significa por sí solo que exista un error."
    ),
)

st.divider()


# ==============================================================
# ESTADO ACTUAL POR LOTE
# Solo la predicción más reciente de cada lote.
# ==============================================================
st.subheader("📌 Estado actual por lote")

st.caption(
    "Vista rápida de la predicción más reciente de cada lote. "
    "Las predicciones anteriores siguen disponibles para verificarse."
)

df_estado_actual = (
    df.sort_values("fecha")
    .groupby("id_lote", as_index=False)
    .tail(1)
    .sort_values("fecha", ascending=False)
    .copy()
)

tabla_estado_actual = df_estado_actual[
    [
        "id_lote",
        "distrito",
        "fecha",
        "probabilidad_riesgo_predicha",
        "riesgo_texto",
        "zona_gris",
        "estado_texto",
    ]
].copy()

tabla_estado_actual.rename(
    columns={
        "id_lote": "Lote",
        "distrito": "Distrito",
        "fecha": "Última predicción",
        "probabilidad_riesgo_predicha": "Probabilidad",
        "riesgo_texto": "Riesgo",
        "zona_gris": "Cerca del umbral",
        "estado_texto": "Verificación",
    },
    inplace=True,
)

tabla_estado_actual["Probabilidad"] = (
    tabla_estado_actual["Probabilidad"].astype(float) * 100
).round(1).astype(str) + "%"

tabla_estado_actual["Cerca del umbral"] = (
    tabla_estado_actual["Cerca del umbral"]
    .map({True: "⚠️ Sí", False: "—"})
)

st.dataframe(
    tabla_estado_actual,
    use_container_width=True,
    hide_index=True,
)

st.divider()


# ==============================================================
# PREDICCIONES LISTAS PARA VERIFICAR
# ==============================================================
st.subheader("✅ Predicciones listas para verificar")

df_listas = df[
    (~df["verificado"].fillna(False))
    & (df["dias_desde_prediccion"] >= HORIZONTE_DIAS)
].copy()

if df_listas.empty:
    st.info(
        "No hay predicciones listas para verificar en este momento."
    )

else:
    st.success(
        f"{len(df_listas)} predicción(es) ya cumplen las 4 semanas "
        "y pueden verificarse."
    )

    tabla_listas = df_listas[
        [
            "id_lote",
            "fecha",
            "probabilidad_riesgo_predicha",
            "umbral_utilizado",
            "riesgo_texto",
            "zona_gris",
        ]
    ].copy()

    tabla_listas.rename(
        columns={
            "id_lote": "Lote",
            "fecha": "Fecha",
            "probabilidad_riesgo_predicha": "Probabilidad",
            "umbral_utilizado": "Umbral",
            "riesgo_texto": "Riesgo",
            "zona_gris": "Cerca del umbral",
        },
        inplace=True,
    )

    tabla_listas["Probabilidad"] = (
        tabla_listas["Probabilidad"].astype(float) * 100
    ).round(1).astype(str) + "%"

    tabla_listas["Umbral"] = (
        tabla_listas["Umbral"].astype(float) * 100
    ).round(1).astype(str) + "%"

    tabla_listas["Cerca del umbral"] = (
        tabla_listas["Cerca del umbral"]
        .map({True: "⚠️ Sí", False: "—"})
    )

    st.dataframe(
        tabla_listas,
        use_container_width=True,
        hide_index=True,
    )

st.divider()


# ==============================================================
# FILTROS
# ==============================================================
st.subheader("🔎 Filtros")

c1, c2, c3, c4, c5, c6 = st.columns(6)

with c1:
    lotes = ["Todos"] + sorted(
        df["id_lote"].dropna().astype(str).unique().tolist()
    )

    filtro_lote = st.selectbox("Lote", lotes)

with c2:
    filtro_riesgo = st.selectbox(
        "Riesgo predicho",
        ["Todos", "ALTO", "BAJO"],
    )

with c3:
    filtro_estado = st.selectbox(
        "Estado",
        ["Todos", "PENDIENTE", "VERIFICADO"],
    )

with c4:
    distritos = ["Todos"] + sorted(
        df["distrito"].dropna().astype(str).unique().tolist()
    )

    filtro_distrito = st.selectbox("Distrito", distritos)

with c5:
    filtro_zona_gris = st.selectbox(
        "Cerca del umbral",
        ["Todas", "Solo cerca del umbral"],
    )

with c6:
    filtro_verificables = st.selectbox(
        "Disponibilidad",
        ["Todas", "Solo listas para verificar"],
    )


# Aplicar filtros.
df_filtrado = df.copy()

if filtro_lote != "Todos":
    df_filtrado = df_filtrado[
        df_filtrado["id_lote"].astype(str) == filtro_lote
    ]

if filtro_riesgo != "Todos":
    df_filtrado = df_filtrado[
        df_filtrado["riesgo_texto"] == filtro_riesgo
    ]

if filtro_estado != "Todos":
    df_filtrado = df_filtrado[
        df_filtrado["estado_texto"] == filtro_estado
    ]

if filtro_distrito != "Todos":
    df_filtrado = df_filtrado[
        df_filtrado["distrito"].astype(str) == filtro_distrito
    ]

if filtro_zona_gris == "Solo cerca del umbral":
    df_filtrado = df_filtrado[df_filtrado["zona_gris"]]

if filtro_verificables == "Solo listas para verificar":
    df_filtrado = df_filtrado[
        (~df_filtrado["verificado"].fillna(False))
        & (df_filtrado["dias_desde_prediccion"] >= HORIZONTE_DIAS)
    ]


# ==============================================================
# TABLA DE PREDICCIONES
# ==============================================================
st.subheader("📋 Predicciones")

if df_filtrado.empty:
    st.info("No hay registros con los filtros seleccionados.")
    st.stop()

tabla = df_filtrado[
    [
        "id_lote",
        "fecha",
        "distrito",
        "probabilidad_riesgo_predicha",
        "umbral_utilizado",
        "riesgo_texto",
        "zona_gris",
        "intervencion_realizada",
        "estado_texto",
    ]
].copy()

tabla.rename(
    columns={
        "id_lote": "Lote",
        "fecha": "Fecha",
        "distrito": "Distrito",
        "probabilidad_riesgo_predicha": "Probabilidad",
        "umbral_utilizado": "Umbral",
        "riesgo_texto": "Riesgo",
        "zona_gris": "Zona gris",
        "intervencion_realizada": "Intervención",
        "estado_texto": "Verificación",
    },
    inplace=True,
)

tabla["Probabilidad"] = (
    tabla["Probabilidad"].astype(float) * 100
).round(2).astype(str) + "%"

tabla["Umbral"] = (
    tabla["Umbral"].astype(float) * 100
).round(1).astype(str) + "%"

tabla["Zona gris"] = tabla["Zona gris"].map(
    {True: "⚠️ Sí", False: "—"}
)

tabla["Intervención"] = (
    tabla["Intervención"]
    .map({True: "Sí", False: "No"})
    .fillna("No registrada")
)

st.dataframe(
    tabla,
    use_container_width=True,
    hide_index=True,
)

st.divider()


# ==============================================================
# SELECCIÓN DE PREDICCIÓN PARA ACTUALIZAR
# ==============================================================
st.subheader("🩺 Verificar o actualizar una predicción")

st.caption(
    "Puedes registrar una intervención antes de que finalicen las cuatro "
    "semanas. La confirmación del resultado real solo se permite al cumplir "
    "los 28 días."
)

df_listas_sel = df_filtrado[
    (~df_filtrado["verificado"].fillna(False))
    & (df_filtrado["dias_desde_prediccion"] >= HORIZONTE_DIAS)
].copy()

df_pendientes_sel = df_filtrado[
    (~df_filtrado["verificado"].fillna(False))
    & (df_filtrado["dias_desde_prediccion"] < HORIZONTE_DIAS)
].copy()

df_verificadas_sel = (
    df_filtrado[df_filtrado["verificado"].fillna(False)]
    .sort_values("fecha")
    .groupby("id_lote", as_index=False)
    .tail(1)
    .sort_values("fecha", ascending=False)
    .copy()
)


def construir_opciones(df_origen):
    opciones_local = []

    for _, fila in df_origen.iterrows():
        prob = float(fila["probabilidad_riesgo_predicha"])
        marca_zona_gris = " ⚠️" if fila["zona_gris"] else ""

        if bool(fila["verificado"]):
            estado = "VERIFICADA"

        elif fila["dias_desde_prediccion"] >= HORIZONTE_DIAS:
            estado = "LISTA PARA VERIFICAR"

        elif fila["dias_desde_prediccion"] < 0:
            estado = "PENDIENTE (futura)"

        else:
            faltan = HORIZONTE_DIAS - fila["dias_desde_prediccion"]
            estado = f"PENDIENTE (faltan {faltan} días)"

        opciones_local.append(
            (
                f"{fila['id_lote']} | {fila['fecha']} | "
                f"{fila['riesgo_texto']} | {prob:.2%} | "
                f"{estado}{marca_zona_gris}",
                fila["id_lote"],
                fila["fecha"],
                fila["modelo_utilizado"],
            )
        )

    return opciones_local


fuente = st.radio(
    "¿Qué predicciones quieres ver?",
    [
        f"✅ Listas para verificar ({len(df_listas_sel)})",
        f"⏳ Pendientes — aún no cumplen 4 semanas ({len(df_pendientes_sel)})",
        f"📗 Ya verificadas ({len(df_verificadas_sel)})",
    ],
    horizontal=True,
)

if fuente.startswith("✅"):
    df_origen_seleccion = df_listas_sel

elif fuente.startswith("⏳"):
    df_origen_seleccion = df_pendientes_sel

else:
    df_origen_seleccion = df_verificadas_sel

if df_origen_seleccion.empty:
    st.info(
        "No hay predicciones en esta categoría con los filtros actuales."
    )
    st.stop()

opciones = construir_opciones(df_origen_seleccion)

seleccion = st.selectbox(
    "Seleccione la predicción",
    opciones,
    format_func=lambda x: x[0],
)

_, id_lote, fecha_prediccion, modelo = seleccion

fila = df_filtrado[
    (df_filtrado["id_lote"] == id_lote)
    & (df_filtrado["fecha"] == fecha_prediccion)
    & (df_filtrado["modelo_utilizado"] == modelo)
].iloc[0]


# ==============================================================
# RESUMEN DE LA PREDICCIÓN SELECCIONADA
# ==============================================================
with st.container(border=True):
    st.markdown("#### Resumen de la predicción seleccionada")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.caption("Lote")
        st.markdown(f"**{id_lote}**")

    with c2:
        st.caption("Fecha")
        st.markdown(f"**{fecha_prediccion}**")

    with c3:
        st.caption("Riesgo predicho")

        if bool(fila["riesgo_alto_predicho"]):
            st.markdown("**🔴 ALTO**")
        else:
            st.markdown("**🟢 BAJO**")

    with c4:
        st.caption("Probabilidad")
        st.markdown(
            f"**{float(fila['probabilidad_riesgo_predicha']):.2%}**"
        )

st.info(
    "📅 Esta predicción evalúa la posibilidad de **al menos un episodio "
    "de riesgo alto durante las próximas 4 semanas**. La predicción se "
    "genera semanalmente, pero no representa solo la semana siguiente."
)


# ==============================================================
# ADVERTENCIA DE ZONA GRIS
# ==============================================================
if bool(fila["zona_gris"]):
    st.warning(
        f"⚠️ Cerca del umbral: probabilidad "
        f"{float(fila['probabilidad_riesgo_predicha']):.1%} "
        f"vs. umbral {float(fila['umbral_utilizado']):.1%}. "
        "El modelo clasificó BAJO; esta señal indica que estuvo cerca "
        "del punto de decisión."
    )


# ==============================================================
# VALIDAR SI YA TRANSCURRIERON LOS 28 DÍAS
# ==============================================================
dias_transcurridos = (HOY - fecha_prediccion).days

fecha_verificable = fecha_prediccion + timedelta(
    days=HORIZONTE_DIAS
)

if dias_transcurridos < 0:
    st.warning(
        f"🕐 Predicción futura. Disponible para verificación desde "
        f"{fecha_verificable}."
    )
    puede_verificar = False

elif dias_transcurridos < HORIZONTE_DIAS:
    faltan = HORIZONTE_DIAS - dias_transcurridos

    st.warning(
        f"⏳ Aún no disponible. Faltan {faltan} días para completar "
        "las 4 semanas."
    )
    puede_verificar = False

else:
    st.success("✅ Predicción habilitada para verificación.")
    puede_verificar = True


# ==============================================================
# ESTADO ACTUAL
# ==============================================================
intervencion_actual = fila["intervencion_realizada"]
verificado_actual = bool(fila["verificado"])

st.markdown("### Estado actual")

c1, c2, c3 = st.columns(3)

with c1:
    if pd.isna(intervencion_actual):
        st.info("Intervención: no registrada")
    elif bool(intervencion_actual):
        st.success("Intervención: sí")
    else:
        st.write("Intervención: no")

with c2:
    if verificado_actual:
        st.success("Resultado: verificado")
    else:
        st.info("Resultado: pendiente")

with c3:
    target_actual = fila["target_riesgo_alto_4sem_real"]

    if pd.isna(target_actual):
        st.info("Resultado real: pendiente")
    elif bool(target_actual):
        st.error("Resultado real: RIESGO ALTO")
    else:
        st.success("Resultado real: NO RIESGO ALTO")

st.divider()


# ==============================================================
# 1. INTERVENCIÓN
# ==============================================================
st.markdown("## 1️⃣ Intervención")

opciones_intervencion = [
    "No registrado todavía",
    "Sí",
    "No",
]

intervencion_actual = fila["intervencion_realizada"]
opcion_actual = opcion_intervencion_actual(intervencion_actual)

if "intervencion_ui" not in st.session_state:
    st.session_state.intervencion_ui = opcion_actual

opcion_intervencion = st.radio(
    "¿Se realizó una intervención?",
    opciones_intervencion,
    index=opciones_intervencion.index(
        st.session_state.intervencion_ui
    ),
    horizontal=True,
    key=f"intervencion_{id_lote}_{fecha_prediccion}_{modelo}",
)

st.session_state.intervencion_ui = opcion_intervencion

tipo_actual = (
    ""
    if pd.isna(fila["tipo_intervencion"])
    else str(fila["tipo_intervencion"])
)

resultado_actual = (
    ""
    if pd.isna(fila["resultado_intervencion"])
    else str(fila["resultado_intervencion"])
)

fecha_intervencion_actual = fecha_a_date(
    fila["fecha_intervencion"]
)

if opcion_intervencion == "Sí":
    st.markdown(
        """
        <div style="
            background:#282019;
            border:1px solid #403329;
            border-left:4px solid #A8794E;
            border-radius:12px;
            padding:1rem;
            margin:0.5rem 0 1rem 0;">
            <b style="color:white;">🩺 Datos de la intervención</b>
            <p style="color:#D0C5BA; margin:0.4rem 0 0 0;">
                Registra el tipo de atención, la fecha y el resultado observado.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tipo_intervencion = st.text_input(
        "Tipo de intervención",
        value=tipo_actual,
        placeholder=(
            "Ej.: tratamiento veterinario, ajuste alimentario..."
        ),
    )

    fecha_intervencion = st.date_input(
        "Fecha de intervención",
        value=(
            fecha_intervencion_actual
            if fecha_intervencion_actual is not None
            else HOY
        ),
    )

    resultado_intervencion = st.text_area(
        "Resultado de la intervención",
        value=resultado_actual,
        placeholder="Ej.: mejora, respuesta parcial, sin cambios...",
    )

else:
    tipo_intervencion = ""
    fecha_intervencion = None
    resultado_intervencion = ""


# ==============================================================
# 2. VERIFICACIÓN DEL RESULTADO REAL
# ==============================================================
st.markdown("## 2️⃣ Resultado de las próximas 4 semanas")

st.caption(
    "La confirmación del resultado real solo se habilita cuando han "
    "transcurrido 28 días desde la predicción."
)

resultados_posibles = [
    "Hubo al menos un episodio de riesgo alto",
    "No hubo ningún episodio de riesgo alto",
]

if verificado_actual:
    st.success("✅ Esta predicción ya está verificada.")

    target_actual_bool = (
        None
        if pd.isna(fila["target_riesgo_alto_4sem_real"])
        else bool(fila["target_riesgo_alto_4sem_real"])
    )

    resultado_default = (
        resultados_posibles[0]
        if target_actual_bool is True
        else resultados_posibles[1]
    )

    resultado_verificacion = st.radio(
        "Resultado real de la ventana de 4 semanas",
        resultados_posibles,
        index=resultados_posibles.index(resultado_default),
        horizontal=True,
    )

    confirmar_verificacion = True

elif puede_verificar:
    confirmar_verificacion = st.checkbox(
        "Confirmar resultado real de las 4 semanas"
    )

    resultado_verificacion = st.radio(
        "Resultado real",
        resultados_posibles,
        horizontal=True,
    )

else:
    confirmar_verificacion = False
    resultado_verificacion = None

    st.info(
        "Todavía no está habilitada para verificación."
    )


# ==============================================================
# GUARDAR CAMBIOS
# ==============================================================
guardar = st.button(
    "💾 Guardar cambios",
    use_container_width=True,
    disabled=st.session_state.guardado_en_proceso,
)

if guardar:

    # ----------------------------------------------------------
    # INTERVENCIÓN
    # ----------------------------------------------------------
    if opcion_intervencion == "Sí":
        intervencion_db = True

        if not tipo_intervencion.strip():
            st.error("❌ Indique el tipo de intervención.")
            st.stop()

        tipo_db = tipo_intervencion.strip()
        fecha_db = fecha_intervencion

        resultado_db = (
            resultado_intervencion.strip()
            if resultado_intervencion.strip()
            else None
        )

    elif opcion_intervencion == "No":
        intervencion_db = False
        tipo_db = None
        fecha_db = None
        resultado_db = None

    else:
        # NULL significa que aún no se conoce la intervención.
        intervencion_db = None

        tipo_db = (
            None
            if pd.isna(fila["tipo_intervencion"])
            else fila["tipo_intervencion"]
        )

        fecha_db = (
            None
            if pd.isna(fila["fecha_intervencion"])
            else fila["fecha_intervencion"]
        )

        resultado_db = (
            None
            if pd.isna(fila["resultado_intervencion"])
            else fila["resultado_intervencion"]
        )

    # ----------------------------------------------------------
    # VALIDAR FECHA DE INTERVENCIÓN
    # ----------------------------------------------------------
    if fecha_db is not None:
        fecha_db_date = fecha_a_date(fecha_db)

        if fecha_db_date is not None:

            if fecha_db_date > HOY:
                st.error(
                    "❌ La fecha de intervención no puede ser futura."
                )
                st.stop()

            if fecha_db_date < fecha_prediccion:
                st.error(
                    "❌ La fecha de intervención no puede ser anterior "
                    "a la fecha de predicción."
                )
                st.stop()

    # ----------------------------------------------------------
    # VERIFICACIÓN DEL RESULTADO REAL
    # ----------------------------------------------------------
    if verificado_actual:
        verificado_db = True

        target_db = (
            True
            if resultado_verificacion == resultados_posibles[0]
            else False
        )

    elif confirmar_verificacion:

        if not puede_verificar:
            st.error(
                "❌ Todavía no han transcurrido las 4 semanas. "
                "No se puede verificar."
            )
            st.stop()

        verificado_db = True

        target_db = (
            True
            if resultado_verificacion == resultados_posibles[0]
            else False
        )

    else:
        verificado_db = False

        # El resultado real permanece NULL hasta ser confirmado.
        target_db = None

    # ----------------------------------------------------------
    # GUARDAR EN SUPABASE
    # ----------------------------------------------------------
    try:
        actualizar_prediccion(
            id_lote=id_lote,
            fecha_prediccion=fecha_prediccion,
            modelo_utilizado=modelo,
            intervencion_realizada=intervencion_db,
            tipo_intervencion=tipo_db,
            fecha_intervencion=fecha_db,
            resultado_intervencion=resultado_db,
            verificado=verificado_db,
            target_real=target_db,
        )

        if verificado_db:
            st.success(
                "✅ Predicción verificada. El registro ya cumple "
                "las condiciones para aparecer en la vista de verificadas."
            )
        else:
            st.success(
                "✅ Seguimiento guardado. La predicción continúa "
                "pendiente de verificación."
            )

        st.cache_data.clear()
        st.rerun()

    except Exception as e:
        st.error("❌ No se pudo actualizar la predicción.")
        st.exception(e)
