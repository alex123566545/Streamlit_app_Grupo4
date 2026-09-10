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
# REGLA: un mismo lote solo puede volver a predecirse cada 7 días.
#
# La fuente de verdad es gold_ml.dataset_prediccion: cada lote
# recibe una fila nueva de features cada 7 días (cadencia semanal).
# Comparamos la fecha de features MÁS RECIENTE disponible para el
# lote contra la fecha de la ÚLTIMA predicción ya guardada para ese
# lote (con este modelo). Si la diferencia es menor a 7 días, no se
# permite predecir de nuevo.
# ------------------------------------------------------------------
DIAS_MINIMOS_ENTRE_PREDICCIONES = 7

MODELO_NOMBRE = "random_forest_sin_lote29_v1"

# ------------------------------------------------------------------
# SUPABASE STORAGE
#
# Los .pkl ya no están en disco local, están en el Storage de
# Supabase, dentro del bucket "models" (ajustar BUCKET_NAME si el
# bucket real tiene otro nombre).
#
# SUPABASE_URL y SUPABASE_KEY se importan de utils.database, que ya
# las lee desde el .env (ver database.py).
# ------------------------------------------------------------------
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
    """
    Descarga un archivo del bucket de Storage y lo deserializa
    directamente en memoria (sin escribir a disco).
    """
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
# DATOS: última fila de features disponible por lote
# ============================================================

@st.cache_data(ttl=30)
def cargar_ultimas_features():
    """
    Trae, para cada lote, únicamente la fila de features MÁS
    RECIENTE en gold_ml.dataset_prediccion.
    """
    conn = get_connection()
    try:
        query = """
            SELECT DISTINCT ON (id_lote) *
            FROM gold_ml.dataset_prediccion
            ORDER BY id_lote, fecha DESC;
        """
        return pd.read_sql(query, conn)
    finally:
        conn.close()


@st.cache_data(ttl=30)
def cargar_ultima_prediccion_por_lote(modelo_utilizado):
    """
    Trae, para cada lote, la fecha de features de la predicción
    MÁS RECIENTE ya guardada con este modelo. Esto es lo que se usa
    para calcular cuántos días faltan para poder volver a predecir.
    """
    conn = get_connection()
    try:
        query = """
            SELECT
                id_lote,
                MAX(fecha) AS ultima_fecha_predicha
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
    f"Un mismo lote solo puede volver a predecirse cuando hayan "
    f"transcurrido al menos {DIAS_MINIMOS_ENTRE_PREDICCIONES} días "
    "desde su última predicción."
)

try:
    modelo, encoders, umbral = cargar_artefactos_modelo()
except Exception as e:
    st.error("❌ No se pudo cargar el modelo, los encoders o el umbral.")
    st.exception(e)
    st.stop()

try:
    df_ultimas_features = cargar_ultimas_features()
except Exception as e:
    st.error("❌ No se pudo leer gold_ml.dataset_prediccion.")
    st.exception(e)
    st.stop()

if df_ultimas_features.empty:
    st.warning("No hay datos de features en gold_ml.dataset_prediccion.")
    st.stop()

df_ultimas_features["fecha"] = pd.to_datetime(
    df_ultimas_features["fecha"]
).dt.date

try:
    df_ultima_prediccion = cargar_ultima_prediccion_por_lote(MODELO_NOMBRE)
except Exception as e:
    st.warning("⚠️ No se pudo leer el historial de predicciones.")
    st.exception(e)
    df_ultima_prediccion = pd.DataFrame(columns=["id_lote", "ultima_fecha_predicha"])

if not df_ultima_prediccion.empty:
    df_ultima_prediccion["ultima_fecha_predicha"] = pd.to_datetime(
        df_ultima_prediccion["ultima_fecha_predicha"]
    ).dt.date

# ------------------------------------------------------------------
# Unir última fila de features con la última fecha ya predicha
# por lote, y calcular elegibilidad.
# ------------------------------------------------------------------
df = df_ultimas_features.merge(
    df_ultima_prediccion,
    on="id_lote",
    how="left",
)


def calcular_estado(fila):
    ultima_fecha = fila["ultima_fecha_predicha"]

    if pd.isna(ultima_fecha):
        return pd.Series(
            {
                "dias_desde_ultima_prediccion": None,
                "puede_predecir": True,
                "motivo": "Nunca predicho con este modelo",
            }
        )

    dias = (fila["fecha"] - ultima_fecha).days

    if dias >= DIAS_MINIMOS_ENTRE_PREDICCIONES:
        return pd.Series(
            {
                "dias_desde_ultima_prediccion": dias,
                "puede_predecir": True,
                "motivo": f"Última predicción hace {dias} días",
            }
        )

    faltan = DIAS_MINIMOS_ENTRE_PREDICCIONES - dias
    return pd.Series(
        {
            "dias_desde_ultima_prediccion": dias,
            "puede_predecir": False,
            "motivo": f"Debe esperar {faltan} día(s) más",
        }
    )


df[["dias_desde_ultima_prediccion", "puede_predecir", "motivo"]] = df.apply(
    calcular_estado, axis=1
)

st.divider()

total_lotes = len(df)
elegibles = int(df["puede_predecir"].sum())
bloqueados = total_lotes - elegibles

c1, c2, c3 = st.columns(3)
c1.metric("Total de lotes", total_lotes)
c2.metric("Elegibles para predecir", elegibles)
c3.metric("Bloqueados (< 7 días)", bloqueados)

st.divider()

# ============================================================
# TABLA DE ESTADO POR LOTE
# ============================================================

st.subheader("📋 Estado de cada lote")

tabla_estado = df[
    ["id_lote", "distrito", "fecha", "ultima_fecha_predicha", "motivo", "puede_predecir"]
].copy()

tabla_estado.rename(
    columns={
        "id_lote": "Lote",
        "distrito": "Distrito",
        "fecha": "Features disponibles (fecha)",
        "ultima_fecha_predicha": "Última predicción",
        "motivo": "Estado",
        "puede_predecir": "Elegible",
    },
    inplace=True,
)

tabla_estado["Última predicción"] = tabla_estado["Última predicción"].apply(
    lambda x: "Nunca" if pd.isna(x) else str(x)
)

tabla_estado["Elegible"] = tabla_estado["Elegible"].map({True: "✅", False: "⏳"})

st.dataframe(tabla_estado, use_container_width=True, hide_index=True)

st.divider()

# ============================================================
# PREDICCIÓN INDIVIDUAL
# ============================================================

st.subheader("🐄 Predecir un lote")

df_elegibles = df[df["puede_predecir"]]

if df_elegibles.empty:
    st.info(
        f"Ningún lote es elegible todavía. Todos deben esperar al menos "
        f"{DIAS_MINIMOS_ENTRE_PREDICCIONES} días desde su última predicción."
    )
else:
    opciones = [
        (
            f"{fila['id_lote']} | features del {fila['fecha']} | {fila['motivo']}",
            idx,
        )
        for idx, fila in df_elegibles.iterrows()
    ]

    seleccion = st.selectbox(
        "Seleccione un lote elegible",
        opciones,
        format_func=lambda x: x[0],
    )

    _, idx_seleccionado = seleccion
    fila_seleccionada = df_elegibles.loc[idx_seleccionado]

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
                fila_seleccionada,
                probabilidad,
                riesgo_alto,
                umbral,
                MODELO_NOMBRE,
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
# PREDICCIÓN MASIVA (todos los elegibles de una vez)
# ============================================================

st.subheader("⚡ Predecir todos los lotes elegibles")
st.caption(
    "Genera y guarda predicciones para todos los lotes que ya "
    f"cumplieron los {DIAS_MINIMOS_ENTRE_PREDICCIONES} días desde "
    "su última predicción."
)

if st.button("Ejecutar predicción masiva"):
    if df_elegibles.empty:
        st.info("No hay lotes elegibles en este momento.")
    else:
        progreso = st.progress(0.0)
        resultados = []
        total = len(df_elegibles)

        for i, (_, fila) in enumerate(df_elegibles.iterrows(), start=1):
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
        st.success(f"Proceso terminado: {len(df_resultados)} lotes procesados.")
        st.dataframe(df_resultados, use_container_width=True, hide_index=True)

        st.cache_data.clear()