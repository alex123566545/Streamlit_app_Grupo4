import streamlit as st
import pandas as pd
import pickle
from datetime import date, datetime, timedelta, timezone

from supabase import create_client

from utils.database import get_connection, SUPABASE_URL, SUPABASE_KEY
from src.config.settings import FEATURES

st.set_page_config(
    page_title="SIPREM-BOVINO | Nueva predicción",
    page_icon="🔮",
    layout="wide",
)

TIMEZONE_PERU = timezone(timedelta(hours=-5))
HOY = datetime.now(TIMEZONE_PERU).date()

# ------------------------------------------------------------------
# CAMBIO DE ENFOQUE:
#
# Antes, la app tomaba SIEMPRE la fila de features MÁS RECIENTE de
# cada lote (MAX(fecha)). Esto tiene un problema serio: si un lote
# tiene varias semanas de features ya cargadas pero todavía sin
# predecir (por ejemplo, un backlog histórico), la app saltaba
# directo a la última semana y las anteriores JAMÁS se predecían
# -- perdiendo para siempre esos datos, que son justo los que
# después alimentan el reentrenamiento vía verificación.
#
# Ahora, para cada lote, se busca la PRIMERA semana pendiente (la
# más antigua que todavía no tenga una predicción con este modelo)
# y se avanza en orden, una semana a la vez -- igual que ya vienen
# espaciadas en gold_ml.dataset_prediccion (cada 7 días).
#
# La única restricción real que se mantiene es no predecir una
# semana cuya fecha todavía no ha llegado (fecha > HOY): eso sí
# seguiría siendo "predecir el futuro antes de tiempo".
# ------------------------------------------------------------------

MODELO_NOMBRE = "random_forest_sin_lote29_v1"

BUCKET_NAME = "models"

MODEL_FILE = "model.pkl"
ENCODERS_FILE = "encoders.pkl"
THRESHOLD_FILE = "threshold_rf_sin_lote29.pkl"


# ============================================================
# CARGA DE MODELO, ENCODERS Y UMBRAL DESDE SUPABASE STORAGE
# ============================================================

@st.cache_resource
def obtener_cliente_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def descargar_pickle(cliente, nombre_archivo):
    contenido = cliente.storage.from_(BUCKET_NAME).download(nombre_archivo)
    return pickle.loads(contenido)


@st.cache_resource
def cargar_artefactos_modelo():
    cliente = obtener_cliente_supabase()
    modelo = descargar_pickle(cliente, MODEL_FILE)
    encoders = descargar_pickle(cliente, ENCODERS_FILE)
    umbral = descargar_pickle(cliente, THRESHOLD_FILE)
    return modelo, encoders, umbral


# ============================================================
# DATOS: TODAS las semanas pendientes de predecir, por lote
# ============================================================

@st.cache_data(ttl=30)
def cargar_features_pendientes(modelo_utilizado):
    """
    Trae TODAS las filas de gold_ml.dataset_prediccion que todavía
    NO tienen una predicción guardada con este modelo (LEFT JOIN +
    IS NULL), ordenadas por lote y fecha ASCENDENTE -- para poder
    procesar el backlog respetando el orden cronológico real.
    """
    conn = get_connection()
    try:
        query = """
            SELECT dp.*
            FROM gold_ml.dataset_prediccion dp
            LEFT JOIN gold_ml.predicciones p
                ON p.id_lote = dp.id_lote
                AND p.fecha = dp.fecha
                AND p.modelo_utilizado = %s
            WHERE p.id IS NULL
            ORDER BY dp.id_lote, dp.fecha ASC;
        """
        return pd.read_sql(query, conn, params=(modelo_utilizado,))
    finally:
        conn.close()


@st.cache_data(ttl=30)
def cargar_ultima_prediccion_por_lote(modelo_utilizado):
    """
    Última fecha ya predicha por lote con este modelo -- se usa solo
    como referencia informativa (para mostrar el "salto" real en
    días entre la última predicción y la siguiente pendiente).
    """
    conn = get_connection()
    try:
        query = """
            SELECT id_lote, MAX(fecha) AS ultima_fecha_predicha
            FROM gold_ml.predicciones
            WHERE modelo_utilizado = %s
            GROUP BY id_lote;
        """
        return pd.read_sql(query, conn, params=(modelo_utilizado,))
    finally:
        conn.close()


# ============================================================
# TRANSFORMACIÓN DE FEATURES (misma lógica que en entrenamiento)
# ============================================================

def preparar_nulos(X):
    X = X.copy()
    if "actividad_sensor_indice" in X.columns:
        X["actividad_sensor_indice"] = X["actividad_sensor_indice"].fillna(-1)
    return X


def transformar_features(X, encoders):
    X = X.copy()
    for col, encoder in encoders.items():
        if col not in X.columns:
            continue
        valores = X[col].astype(str)
        mapping = {clase: i for i, clase in enumerate(encoder.classes_)}
        X[col] = valores.map(mapping).fillna(-1).astype(int)
    return X


def predecir_fila(modelo, encoders, umbral, fila_features):
    X = pd.DataFrame([fila_features[FEATURES]])
    X = preparar_nulos(X)
    X = transformar_features(X, encoders)

    probabilidad = float(modelo.predict_proba(X)[:, 1][0])
    riesgo_alto = probabilidad >= umbral

    return probabilidad, riesgo_alto


# ============================================================
# GUARDAR PREDICCIÓN
# ============================================================

def guardar_prediccion(fila, probabilidad, riesgo_alto, umbral, modelo_utilizado):
    conn = get_connection()
    try:
        query = """
            INSERT INTO gold_ml.predicciones (
                id_lote, fecha,
                distrito, categoria_zootecnica, raza_predominante,
                altitud_msnm, distancia_centro_veterinario_km,
                tamano_lote_cabezas, lote_sensorizado, uso_registro_digital,
                cobertura_vacunacion_pct, dias_desde_desparasitacion,
                animales_nuevos_30d, casos_respiratorios, casos_diarreicos,
                temperatura_min_c, temperatura_media_c, temperatura_max_c,
                humedad_relativa_pct, precipitacion_semanal_mm,
                condicion_pastura_indice, indice_ndvi_satelital,
                consumo_ms_kg_animal_dia, agua_l_animal_dia,
                actividad_sensor_indice, condicion_corporal_prom,
                precio_leche_local_s_kg,
                semana_sin, semana_cos,
                media_movil_4s_pastura, media_movil_4s_condicion_corporal,
                media_movil_4s_temperatura,
                modelo_utilizado, umbral_utilizado,
                probabilidad_riesgo_predicha, riesgo_alto_predicho
            )
            VALUES (
                %(id_lote)s, %(fecha)s,
                %(distrito)s, %(categoria_zootecnica)s, %(raza_predominante)s,
                %(altitud_msnm)s, %(distancia_centro_veterinario_km)s,
                %(tamano_lote_cabezas)s, %(lote_sensorizado)s, %(uso_registro_digital)s,
                %(cobertura_vacunacion_pct)s, %(dias_desde_desparasitacion)s,
                %(animales_nuevos_30d)s, %(casos_respiratorios)s, %(casos_diarreicos)s,
                %(temperatura_min_c)s, %(temperatura_media_c)s, %(temperatura_max_c)s,
                %(humedad_relativa_pct)s, %(precipitacion_semanal_mm)s,
                %(condicion_pastura_indice)s, %(indice_ndvi_satelital)s,
                %(consumo_ms_kg_animal_dia)s, %(agua_l_animal_dia)s,
                %(actividad_sensor_indice)s, %(condicion_corporal_prom)s,
                %(precio_leche_local_s_kg)s,
                %(semana_sin)s, %(semana_cos)s,
                %(media_movil_4s_pastura)s, %(media_movil_4s_condicion_corporal)s,
                %(media_movil_4s_temperatura)s,
                %(modelo_utilizado)s, %(umbral_utilizado)s,
                %(probabilidad_riesgo_predicha)s, %(riesgo_alto_predicho)s
            )
            ON CONFLICT (id_lote, fecha, modelo_utilizado) DO NOTHING;
        """

        valores = fila.to_dict()
        valores["modelo_utilizado"] = modelo_utilizado
        valores["umbral_utilizado"] = umbral
        valores["probabilidad_riesgo_predicha"] = probabilidad
        valores["riesgo_alto_predicho"] = bool(riesgo_alto)

        with conn.cursor() as cur:
            cur.execute(query, valores)
            insertadas = cur.rowcount

        conn.commit()
        return insertadas == 1
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ============================================================
# INTERFAZ
# ============================================================

st.title("🔮 SIPREM-BOVINO")
st.subheader("Generar nueva predicción")
st.caption(
    "Cada lote se predice en orden cronológico: primero la semana "
    "más antigua que aún no tenga predicción, respetando la "
    "secuencia real de fechas del historial. No se predicen semanas "
    "cuya fecha todavía no ha llegado."
)

try:
    modelo, encoders, umbral = cargar_artefactos_modelo()
except Exception as e:
    st.error("❌ No se pudo cargar el modelo, los encoders o el umbral desde Supabase Storage.")
    st.exception(e)
    st.stop()

try:
    df_pendientes_todas = cargar_features_pendientes(MODELO_NOMBRE)
except Exception as e:
    st.error("❌ No se pudo leer gold_ml.dataset_prediccion / gold_ml.predicciones.")
    st.exception(e)
    st.stop()

if df_pendientes_todas.empty:
    st.success(
        "✅ No hay semanas pendientes de predecir: todos los lotes "
        "están al día con este modelo."
    )
    st.stop()

df_pendientes_todas["fecha"] = pd.to_datetime(df_pendientes_todas["fecha"]).dt.date

# ------------------------------------------------------------------
# Solo se consideran elegibles las semanas cuya fecha ya llegó
# (fecha <= HOY). Las de fecha futura quedan en espera, pero no se
# ocultan del backlog -- se muestran aparte para que quede claro
# que existen pero todavía no corresponde predecirlas.
# ------------------------------------------------------------------
df_pendientes_todas["es_futura"] = df_pendientes_todas["fecha"] > HOY

try:
    df_ultima_prediccion = cargar_ultima_prediccion_por_lote(MODELO_NOMBRE)
    if not df_ultima_prediccion.empty:
        df_ultima_prediccion["ultima_fecha_predicha"] = pd.to_datetime(
            df_ultima_prediccion["ultima_fecha_predicha"]
        ).dt.date
except Exception as e:
    st.warning("⚠️ No se pudo leer el historial de predicciones previas.")
    st.exception(e)
    df_ultima_prediccion = pd.DataFrame(columns=["id_lote", "ultima_fecha_predicha"])

# ------------------------------------------------------------------
# La "siguiente semana a predecir" de cada lote es la más antigua
# de su backlog pendiente (primera fila tras ordenar por fecha ASC).
# ------------------------------------------------------------------
df_elegible_backlog = df_pendientes_todas[~df_pendientes_todas["es_futura"]].copy()

df_siguiente = (
    df_elegible_backlog.sort_values(["id_lote", "fecha"])
    .groupby("id_lote", as_index=False)
    .head(1)
    .copy()
)

df_siguiente = df_siguiente.merge(df_ultima_prediccion, on="id_lote", how="left")


def calcular_info_orden(fila):
    ultima = fila["ultima_fecha_predicha"]
    if pd.isna(ultima):
        return "Primera predicción de este lote"
    dias = (fila["fecha"] - ultima).days
    if dias == 7:
        return "Continúa la secuencia semanal (7 días después)"
    return f"⚠️ Salto de {dias} días desde la última predicción (revisar continuidad)"


df_siguiente["info_orden"] = df_siguiente.apply(calcular_info_orden, axis=1)

# Backlog restante por lote (cuántas semanas pendientes tiene en total,
# incluyendo la que se predecirá ahora).
backlog_por_lote = (
    df_elegible_backlog.groupby("id_lote")
    .size()
    .rename("semanas_pendientes")
    .reset_index()
)
df_siguiente = df_siguiente.merge(backlog_por_lote, on="id_lote", how="left")

st.divider()

total_lotes_con_backlog = df_siguiente["id_lote"].nunique()
total_semanas_pendientes = len(df_elegible_backlog)
total_futuras = int(df_pendientes_todas["es_futura"].sum())

c1, c2, c3 = st.columns(3)
c1.metric("Lotes con backlog pendiente", total_lotes_con_backlog)
c2.metric("Semanas pendientes (elegibles)", total_semanas_pendientes)
c3.metric("Semanas futuras (aún no llegan)", total_futuras)

st.divider()

# ============================================================
# TABLA: siguiente semana a predecir por lote
# ============================================================

st.subheader("📋 Siguiente semana pendiente por lote")

tabla_estado = df_siguiente[
    ["id_lote", "distrito", "fecha", "semanas_pendientes", "info_orden"]
].copy()

tabla_estado.rename(
    columns={
        "id_lote": "Lote",
        "distrito": "Distrito",
        "fecha": "Próxima semana a predecir",
        "semanas_pendientes": "Semanas pendientes (total)",
        "info_orden": "Continuidad",
    },
    inplace=True,
)

st.dataframe(tabla_estado, use_container_width=True, hide_index=True)

if total_futuras > 0:
    with st.expander(f"Ver {total_futuras} semana(s) futura(s) aún no elegibles"):
        tabla_futuras = df_pendientes_todas[df_pendientes_todas["es_futura"]][
            ["id_lote", "distrito", "fecha"]
        ].sort_values(["id_lote", "fecha"])
        st.dataframe(tabla_futuras, use_container_width=True, hide_index=True)

st.divider()

# ============================================================
# PREDICCIÓN INDIVIDUAL (siempre la siguiente en orden del lote)
# ============================================================

st.subheader("🐄 Predecir un lote (siguiente semana en orden)")

opciones = [
    (
        f"{fila['id_lote']} | siguiente: {fila['fecha']} | "
        f"{fila['semanas_pendientes']} semana(s) pendiente(s) | {fila['info_orden']}",
        idx,
    )
    for idx, fila in df_siguiente.iterrows()
]

seleccion = st.selectbox(
    "Seleccione un lote",
    opciones,
    format_func=lambda x: x[0],
)

_, idx_seleccionado = seleccion
fila_seleccionada = df_siguiente.loc[idx_seleccionado]

if fila_seleccionada["semanas_pendientes"] > 1:
    st.info(
        f"ℹ️ Este lote tiene {int(fila_seleccionada['semanas_pendientes'])} "
        "semanas pendientes en total. Se predecirá primero la más antigua "
        f"({fila_seleccionada['fecha']}); las demás quedarán disponibles "
        "para predecirse después, en su propio turno."
    )

with st.expander("Ver features utilizadas", expanded=False):
    st.dataframe(
        fila_seleccionada[FEATURES].to_frame(name="valor"),
        use_container_width=True,
    )

if st.button("🔮 Generar predicción", type="primary"):
    try:
        probabilidad, riesgo_alto = predecir_fila(
            modelo, encoders, umbral, fila_seleccionada
        )

        st.markdown("### Resultado")
        c1, c2 = st.columns(2)
        c1.metric("Probabilidad de riesgo alto", f"{probabilidad:.1%}")
        c2.metric(
            "Predicción",
            "🔴 RIESGO ALTO" if riesgo_alto else "🟢 RIESGO BAJO",
        )
        st.caption(f"Umbral utilizado: {umbral:.1%}")

        guardado = guardar_prediccion(
            fila_seleccionada, probabilidad, riesgo_alto, umbral, MODELO_NOMBRE
        )

        if guardado:
            st.success("✅ Predicción guardada en gold_ml.predicciones.")
            st.cache_data.clear()
        else:
            st.warning(
                "⚠️ Ya existía una predicción para este lote/fecha/"
                "modelo — no se duplicó."
            )

    except Exception as e:
        st.error("❌ No se pudo generar o guardar la predicción.")
        st.exception(e)

st.divider()

# ============================================================
# PREDICCIÓN MASIVA: procesa TODO el backlog en orden, por lote
# ============================================================

st.subheader("⚡ Procesar todo el backlog pendiente")
st.caption(
    "Recorre cada lote y predice, en orden, TODAS sus semanas "
    "pendientes (de la más antigua a la más reciente), sin saltar "
    "directamente a la última. No procesa semanas futuras."
)

if st.button("Ejecutar procesamiento masivo del backlog"):
    if df_elegible_backlog.empty:
        st.info("No hay semanas pendientes por procesar.")
    else:
        # Se procesa en el orden natural (lote, fecha ASC) ya
        # aplicado en la query -- así cada lote avanza semana por
        # semana en el mismo recorrido.
        df_orden = df_elegible_backlog.sort_values(["id_lote", "fecha"]).copy()

        progreso = st.progress(0.0)
        resultados = []
        total = len(df_orden)

        for i, (_, fila) in enumerate(df_orden.iterrows(), start=1):
            try:
                probabilidad, riesgo_alto = predecir_fila(
                    modelo, encoders, umbral, fila
                )
                guardado = guardar_prediccion(
                    fila, probabilidad, riesgo_alto, umbral, MODELO_NOMBRE
                )
                resultados.append(
                    {
                        "id_lote": fila["id_lote"],
                        "fecha": fila["fecha"],
                        "probabilidad": probabilidad,
                        "riesgo_alto": riesgo_alto,
                        "guardado": guardado,
                    }
                )
            except Exception as e:
                resultados.append(
                    {
                        "id_lote": fila["id_lote"],
                        "fecha": fila["fecha"],
                        "error": str(e),
                    }
                )

            progreso.progress(i / total)

        df_resultados = pd.DataFrame(resultados)
        st.success(f"Proceso terminado: {len(df_resultados)} semanas procesadas.")
        st.dataframe(df_resultados, use_container_width=True, hide_index=True)

        st.cache_data.clear()