from src.config.database import get_connection

# ============================================================
# SIPREM-BOVINO
# VERIFICACIÓN DE PREDICCIONES
# ============================================================

import streamlit as st
import pandas as pd
from datetime import date, timedelta

from src.config.database import get_connection


# ============================================================
# CONFIGURACIÓN
# ============================================================

st.set_page_config(
    page_title="SIPREM-BOVINO | Verificación",
    page_icon="🐄",
    layout="wide"
)


# ============================================================
# ESTILOS
# ============================================================

st.title("🐄 SIPREM-BOVINO")
st.subheader("Verificación y seguimiento de predicciones")

st.caption(
    "Registre intervenciones y confirme el resultado real "
    "de las predicciones después del periodo de 4 semanas."
)


# ============================================================
# CONEXIÓN / CONSULTA
# ============================================================

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

            ORDER BY fecha DESC, id_lote;
        """

        df = pd.read_sql(query, conn)

        return df

    finally:
        conn.close()


# ============================================================
# ACTUALIZAR PREDICCIÓN
# ============================================================

def actualizar_prediccion(
    id_lote,
    fecha,
    modelo_utilizado,
    intervencion_realizada,
    tipo_intervencion,
    fecha_intervencion,
    resultado_intervencion,
    verificado,
    target_real
):

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
                        THEN NOW()
                        ELSE fecha_verificacion
                    END

            WHERE
                id_lote = %s
                AND fecha = %s
                AND modelo_utilizado = %s;
        """

        with conn.cursor() as cur:

            cur.execute(
                query,
                (
                    intervencion_realizada,
                    tipo_intervencion,
                    fecha_intervencion,
                    resultado_intervencion,
                    verificado,
                    target_real,
                    verificado,

                    id_lote,
                    fecha,
                    modelo_utilizado
                )
            )

        conn.commit()

    except Exception:

        conn.rollback()
        raise

    finally:
        conn.close()


# ============================================================
# CARGAR DATOS
# ============================================================

try:

    df = cargar_predicciones()

except Exception as e:

    st.error(
        "❌ No se pudo conectar o leer gold_ml.predicciones."
    )

    st.exception(e)

    st.stop()


if df.empty:

    st.warning(
        "No existen predicciones registradas."
    )

    st.stop()


# ============================================================
# PREPARAR DATOS
# ============================================================

df["fecha"] = pd.to_datetime(
    df["fecha"]
).dt.date

df["riesgo_texto"] = df[
    "riesgo_alto_predicho"
].map(
    {
        True: "ALTO",
        False: "BAJO"
    }
)

df["estado_verificacion"] = df[
    "verificado"
].map(
    {
        True: "VERIFICADO",
        False: "PENDIENTE"
    }
)


# ============================================================
# RESUMEN
# ============================================================

total = len(df)

pendientes = int(
    (~df["verificado"]).sum()
)

verificados = int(
    df["verificado"].sum()
)

hoy = date.today()

fecha_limite = hoy - timedelta(days=28)

listas_verificar = int(
    (
        (~df["verificado"])
        &
        (df["fecha"] <= fecha_limite)
    ).sum()
)


col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total predicciones",
        total
    )

with col2:
    st.metric(
        "Pendientes",
        pendientes
    )

with col3:
    st.metric(
        "Listas para verificar",
        listas_verificar
    )

with col4:
    st.metric(
        "Verificadas",
        verificados
    )


st.divider()


# ============================================================
# FILTROS
# ============================================================

st.subheader("🔎 Filtros")

col1, col2, col3, col4 = st.columns(4)


with col1:

    lotes = [
        "Todos"
    ] + sorted(
        df["id_lote"].dropna().unique().tolist()
    )

    filtro_lote = st.selectbox(
        "Lote",
        lotes
    )


with col2:

    riesgos = [
        "Todos",
        "ALTO",
        "BAJO"
    ]

    filtro_riesgo = st.selectbox(
        "Riesgo",
        riesgos
    )


with col3:

    estados = [
        "Todos",
        "PENDIENTE",
        "VERIFICADO"
    ]

    filtro_estado = st.selectbox(
        "Estado",
        estados
    )


with col4:

    distritos = [
        "Todos"
    ] + sorted(
        df["distrito"].dropna().unique().tolist()
    )

    filtro_distrito = st.selectbox(
        "Distrito",
        distritos
    )


# ============================================================
# APLICAR FILTROS
# ============================================================

df_filtrado = df.copy()


if filtro_lote != "Todos":

    df_filtrado = df_filtrado[
        df_filtrado["id_lote"] == filtro_lote
    ]


if filtro_riesgo != "Todos":

    df_filtrado = df_filtrado[
        df_filtrado["riesgo_texto"] == filtro_riesgo
    ]


if filtro_estado != "Todos":

    df_filtrado = df_filtrado[
        df_filtrado["estado_verificacion"] == filtro_estado
    ]


if filtro_distrito != "Todos":

    df_filtrado = df_filtrado[
        df_filtrado["distrito"] == filtro_distrito
    ]


# ============================================================
# TABLA DE PREDICCIONES
# ============================================================

st.subheader("📋 Predicciones registradas")

columnas_mostrar = [
    "id_lote",
    "fecha",
    "distrito",
    "probabilidad_riesgo_predicha",
    "riesgo_texto",
    "intervencion_realizada",
    "verificado"
]

tabla = df_filtrado[
    columnas_mostrar
].copy()

tabla = tabla.rename(
    columns={
        "id_lote": "Lote",
        "fecha": "Fecha",
        "distrito": "Distrito",
        "probabilidad_riesgo_predicha": "Probabilidad",
        "riesgo_texto": "Riesgo",
        "intervencion_realizada": "Intervención",
        "verificado": "Verificado"
    }
)

tabla["Probabilidad"] = (
    tabla["Probabilidad"] * 100
).round(2)


st.dataframe(
    tabla,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# SELECCIÓN DE PREDICCIÓN
# ============================================================

if df_filtrado.empty:

    st.info(
        "No existen registros con los filtros seleccionados."
    )

    st.stop()


st.divider()

st.subheader("🩺 Verificar una predicción")


# ============================================================
# OPCIONES DE SELECCIÓN
# ============================================================

opciones = []

for _, fila in df_filtrado.iterrows():

    etiqueta = (
        f"{fila['id_lote']} | "
        f"{fila['fecha']} | "
        f"{fila['riesgo_texto']} | "
        f"{fila['probabilidad_riesgo_predicha']:.2%}"
    )

    opciones.append(
        (
            etiqueta,
            fila["id_lote"],
            fila["fecha"],
            fila["modelo_utilizado"]
        )
    )


opcion_seleccionada = st.selectbox(
    "Seleccione la predicción",
    opciones,
    format_func=lambda x: x[0]
)


_, id_lote, fecha_prediccion, modelo = (
    opcion_seleccionada
)


fila = df_filtrado[
    (df_filtrado["id_lote"] == id_lote)
    &
    (df_filtrado["fecha"] == fecha_prediccion)
    &
    (df_filtrado["modelo_utilizado"] == modelo)
].iloc[0]


# ============================================================
# INFORMACIÓN DE LA PREDICCIÓN
# ============================================================

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.write("**Lote**")
    st.write(id_lote)

with c2:
    st.write("**Fecha**")
    st.write(fecha_prediccion)

with c3:
    st.write("**Riesgo predicho**")
    st.write(
        "🔴 ALTO"
        if fila["riesgo_alto_predicho"]
        else "🟢 BAJO"
    )

with c4:
    st.write("**Probabilidad**")
    st.write(
        f"{fila['probabilidad_riesgo_predicha']:.2%}"
    )


st.divider()


# ============================================================
# FORMULARIO
# ============================================================

with st.form("form_verificacion"):

    st.subheader(
        "1️⃣ Registro de intervención"
    )

    intervencion = st.selectbox(
        "¿Se realizó una intervención?",
        [
            "No registrar todavía",
            "Sí",
            "No"
        ],
        index=0
    )


    tipo_intervencion = st.text_input(
        "Tipo de intervención",
        value=(
            fila["tipo_intervencion"]
            if pd.notna(fila["tipo_intervencion"])
            else ""
        ),
        placeholder=(
            "Ej.: tratamiento veterinario, "
            "ajuste alimentario..."
        )
    )


    fecha_intervencion = st.date_input(
        "Fecha de intervención",
        value=(
            fila["fecha_intervencion"].date()
            if pd.notna(fila["fecha_intervencion"])
            else hoy
        )
    )


    resultado_intervencion = st.text_area(
        "Resultado de la intervención",
        value=(
            fila["resultado_intervencion"]
            if pd.notna(fila["resultado_intervencion"])
            else ""
        ),
        placeholder=(
            "Ej.: mejora del estado general..."
        )
    )


    st.divider()


    st.subheader(
        "2️⃣ Verificación del resultado a 4 semanas"
    )


    dias_transcurridos = (
        hoy - fecha_prediccion
    ).days


    puede_verificar = (
        dias_transcurridos >= 28
    )


    if puede_verificar:

        st.success(
            f"Han transcurrido {dias_transcurridos} días. "
            "El registro puede ser verificado."
        )

        verificar = st.checkbox(
            "Confirmar que ya se verificó el resultado real"
        )

        resultado_real = st.radio(
            "Resultado real después de las 4 semanas",
            [
                "Riesgo alto",
                "No hubo riesgo alto"
            ],
            horizontal=True
        )

    else:

        st.warning(
            f"Han transcurrido {dias_transcurridos} días. "
            "Todavía no han pasado las 4 semanas."
        )

        verificar = False
        resultado_real = None


    guardar = st.form_submit_button(
        "💾 Guardar información",
        use_container_width=True
    )


# ============================================================
# GUARDAR
# ============================================================

if guardar:

    # --------------------------------------------------------
    # INTERVENCIÓN
    # --------------------------------------------------------

    if intervencion == "Sí":

        intervencion_realizada = True

    elif intervencion == "No":

        intervencion_realizada = False

    else:

        # NULL = todavía desconocido
        intervencion_realizada = None


    # --------------------------------------------------------
    # CAMPOS DE INTERVENCIÓN
    # --------------------------------------------------------

    if intervencion_realizada is True:

        tipo_db = (
            tipo_intervencion.strip()
            if tipo_intervencion.strip()
            else None
        )

        fecha_db = fecha_intervencion

        resultado_db = (
            resultado_intervencion.strip()
            if resultado_intervencion.strip()
            else None
        )

    elif intervencion_realizada is False:

        tipo_db = None
        fecha_db = None
        resultado_db = None

    else:

        # Todavía no sabemos
        tipo_db = fila["tipo_intervencion"]
        fecha_db = fila["fecha_intervencion"]
        resultado_db = fila["resultado_intervencion"]


    # --------------------------------------------------------
    # RESULTADO REAL
    # --------------------------------------------------------

    if verificar:

        if resultado_real == "Riesgo alto":

            target_real = True

        else:

            target_real = False

        verificado_db = True

    else:

        # Todavía no se ha confirmado
        target_real = fila[
            "target_riesgo_alto_4sem_real"
        ]

        verificado_db = bool(
            fila["verificado"]
        )


    # --------------------------------------------------------
    # VALIDACIÓN
    # --------------------------------------------------------

    if verificar and not puede_verificar:

        st.error(
            "❌ Todavía no han transcurrido "
            "4 semanas."
        )

        st.stop()


    if verificar:

        if resultado_real is None:

            st.error(
                "❌ Debe seleccionar el resultado real."
            )

            st.stop()


    # --------------------------------------------------------
    # ACTUALIZAR
    # --------------------------------------------------------

    try:

        actualizar_prediccion(
            id_lote=id_lote,
            fecha=fecha_prediccion,
            modelo_utilizado=modelo,

            intervencion_realizada=
                intervencion_realizada,

            tipo_intervencion=
                tipo_db,

            fecha_intervencion=
                fecha_db,

            resultado_intervencion=
                resultado_db,

            verificado=
                verificado_db,

            target_real=
                target_real
        )

        st.success(
            "✅ Información guardada correctamente."
        )

        st.cache_data.clear()

        st.rerun()

    except Exception as e:

        st.error(
            "❌ No se pudo actualizar la predicción."
        )

        st.exception(e)