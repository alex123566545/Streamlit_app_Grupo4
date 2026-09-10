import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta, timezone

from utils.database import get_connection

st.set_page_config(
    page_title="SIPREM-BOVINO | Verificación",
    page_icon="🐄",
    layout="wide",
)

HORIZONTE_DIAS = 28
TIMEZONE_PERU = timezone(timedelta(hours=-5))
HOY = datetime.now(TIMEZONE_PERU).date()


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
    Actualiza solo los campos de seguimiento.
    No modifica las features ni la salida original del modelo.
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
                    "No se encontró exactamente una predicción para actualizar."
                )

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


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


st.title("🐄 SIPREM-BOVINO")
st.subheader("Verificación y seguimiento de predicciones")
st.caption(
    "Registre la intervención y, cuando hayan transcurrido 4 semanas "
    "desde la predicción, confirme el resultado real."
)

try:
    df = cargar_predicciones()
except Exception as e:
    st.error("❌ No se pudo leer gold_ml.predicciones.")
    st.exception(e)
    st.stop()

if df.empty:
    st.info("No existen predicciones registradas.")
    st.stop()

df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce").dt.date
df["riesgo_texto"] = df["riesgo_alto_predicho"].apply(texto_riesgo)
df["estado_texto"] = df["verificado"].fillna(False).apply(
    lambda x: "VERIFICADO" if bool(x) else "PENDIENTE"
)
df["dias_desde_prediccion"] = df["fecha"].apply(
    lambda f: (HOY - f).days if pd.notna(f) else None
)

total = len(df)
pendientes = int((~df["verificado"].fillna(False)).sum())
verificados = int(df["verificado"].fillna(False).sum())
listas_verificar = int(
    (
        (~df["verificado"].fillna(False))
        & (df["dias_desde_prediccion"] >= HORIZONTE_DIAS)
    ).sum()
)
fechas_futuras = int((df["dias_desde_prediccion"] < 0).sum())

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total", total)
c2.metric("Pendientes", pendientes)
c3.metric("Listas para verificar", listas_verificar)
c4.metric("Verificadas", verificados)
c5.metric("Fechas futuras", fechas_futuras)

st.divider()

st.subheader("🔎 Filtros")
c1, c2, c3, c4 = st.columns(4)

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
        "riesgo_texto",
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
        "riesgo_texto": "Riesgo",
        "intervencion_realizada": "Intervención",
        "estado_texto": "Verificación",
    },
    inplace=True,
)

tabla["Probabilidad"] = (
    tabla["Probabilidad"].astype(float) * 100
).round(2).astype(str) + "%"

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
st.subheader("🩺 Verificar / actualizar una predicción")

opciones = []
for _, fila in df_filtrado.iterrows():
    prob = float(fila["probabilidad_riesgo_predicha"])
    opciones.append(
        (
            f"{fila['id_lote']} | {fila['fecha']} | "
            f"{fila['riesgo_texto']} | {prob:.2%} | "
            f"{fila['estado_texto']}",
            fila["id_lote"],
            fila["fecha"],
            fila["modelo_utilizado"],
        )
    )

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

c1, c2, c3, c4 = st.columns(4)
c1.write("**Lote**")
c1.write(str(id_lote))
c2.write("**Fecha**")
c2.write(str(fecha_prediccion))
c3.write("**Riesgo predicho**")
c3.write("🔴 ALTO" if bool(fila["riesgo_alto_predicho"]) else "🟢 BAJO")
c4.write("**Probabilidad**")
c4.write(f"{float(fila['probabilidad_riesgo_predicha']):.2%}")

dias_transcurridos = (HOY - fecha_prediccion).days
fecha_verificable = fecha_prediccion + timedelta(days=HORIZONTE_DIAS)

if dias_transcurridos < 0:
    st.warning(
        f"🕐 Esta predicción es futura ({fecha_prediccion}). "
        f"No puede verificarse todavía. "
        f"Podrá verificarse desde aproximadamente {fecha_verificable}."
    )
    puede_verificar = False
elif dias_transcurridos < HORIZONTE_DIAS:
    faltan = HORIZONTE_DIAS - dias_transcurridos
    st.warning(
        f"⏳ Han transcurrido {dias_transcurridos} días. "
        f"Faltan {faltan} días para completar las 4 semanas. "
        f"Fecha de verificación: {fecha_verificable}."
    )
    puede_verificar = False
else:
    st.success(
        f"✅ Han transcurrido {dias_transcurridos} días. "
        "El registro ya puede verificarse."
    )
    puede_verificar = True

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
    st.success("Resultado: verificado") if verificado_actual else st.info(
        "Resultado: pendiente"
    )

with c3:
    target_actual = fila["target_riesgo_alto_4sem_real"]
    if pd.isna(target_actual):
        st.info("Resultado real: pendiente")
    elif bool(target_actual):
        st.error("Resultado real: RIESGO ALTO")
    else:
        st.success("Resultado real: NO RIESGO ALTO")

st.divider()

with st.form("form_verificacion"):

    st.markdown("## 1️⃣ Registro de intervención")

    opciones_intervencion = [
        "No registrado todavía",
        "Sí",
        "No",
    ]

    opcion_actual = opcion_intervencion_actual(intervencion_actual)

    opcion_intervencion = st.selectbox(
        "¿Se realizó una intervención?",
        opciones_intervencion,
        index=opciones_intervencion.index(opcion_actual),
    )

    tipo_actual = (
        "" if pd.isna(fila["tipo_intervencion"])
        else str(fila["tipo_intervencion"])
    )

    resultado_actual = (
        "" if pd.isna(fila["resultado_intervencion"])
        else str(fila["resultado_intervencion"])
    )

    fecha_intervencion_actual = fecha_a_date(
        fila["fecha_intervencion"]
    )

    if opcion_intervencion == "Sí":
        tipo_intervencion = st.text_input(
            "Tipo de intervención",
            value=tipo_actual,
            placeholder=(
                "Ej.: tratamiento veterinario, ajuste alimentario, "
                "aislamiento..."
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
            placeholder=(
                "Ej.: mejora del estado general, respuesta parcial..."
            ),
        )
    else:
        tipo_intervencion = ""
        fecha_intervencion = None
        resultado_intervencion = ""

    st.divider()
    st.markdown("## 2️⃣ Verificación del resultado a 4 semanas")

    if verificado_actual:
        st.success("✅ Esta predicción ya fue verificada.")

        target_actual_bool = (
            None
            if pd.isna(fila["target_riesgo_alto_4sem_real"])
            else bool(fila["target_riesgo_alto_4sem_real"])
        )

        resultado_default = (
            "Riesgo alto"
            if target_actual_bool is True
            else "No hubo riesgo alto"
        )

        resultado_verificacion = st.radio(
            "Resultado real registrado",
            ["Riesgo alto", "No hubo riesgo alto"],
            index=["Riesgo alto", "No hubo riesgo alto"].index(
                resultado_default
            ),
            horizontal=True,
        )

        confirmar_verificacion = st.checkbox(
            "Mantener la verificación confirmada",
            value=True,
        )

    elif puede_verificar:
        st.success("✅ Ya se cumplieron las 4 semanas.")

        confirmar_verificacion = st.checkbox(
            "Confirmar que ya se verificó el resultado real"
        )

        resultado_verificacion = st.radio(
            "Resultado real después de las 4 semanas",
            ["Riesgo alto", "No hubo riesgo alto"],
            horizontal=True,
        )

    else:
        confirmar_verificacion = False
        resultado_verificacion = None
        st.info(
            f"La verificación se habilitará cuando se cumplan "
            f"{HORIZONTE_DIAS} días desde la fecha de predicción."
        )

    st.divider()

    guardar = st.form_submit_button(
        "💾 Guardar cambios",
        use_container_width=True,
    )

if guardar:

    # -----------------------------
    # Intervención
    # -----------------------------
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
        # NULL = todavía no se conoce la intervención.
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

    # -----------------------------
    # Validar fecha intervención
    # -----------------------------
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

    # -----------------------------
    # Verificación
    # -----------------------------
    if verificado_actual:
        verificado_db = True

        target_db = (
            True
            if resultado_verificacion == "Riesgo alto"
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
            if resultado_verificacion == "Riesgo alto"
            else False
        )

    else:
        verificado_db = False

        # Mientras no se confirme el desenlace real,
        # el target permanece NULL.
        target_db = None

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
                "✅ Predicción verificada. "
                "El registro ya cumple las condiciones para aparecer "
                "en la vista de verificadas."
            )
        else:
            st.success(
                "✅ Seguimiento guardado. "
                "La predicción continúa pendiente de verificación."
            )

        st.cache_data.clear()
        st.rerun()

    except Exception as e:
        st.error("❌ No se pudo actualizar la predicción.")
        st.exception(e)
