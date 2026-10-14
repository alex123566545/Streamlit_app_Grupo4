import streamlit as st
import pandas as pd
import numpy as np
from utils.database import get_connection

st.set_page_config(page_title="SIPREM-BOVINO | Evolución por lote", page_icon="🐄", layout="wide")
st.title("🐄 Evolución histórica por lote")
st.caption("Explore los cambios semanales de cada lote y contraste el riesgo histórico con las predicciones y los resultados verificados.")

# Ubicación sugerida: pages/5_Evolucion_lotes.py
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

@st.cache_data(ttl=60)
def cargar_tablas():
    conn = get_connection()
    try:
        historico = pd.read_sql_query(
            "SELECT * FROM gold_ml.dataset_features ORDER BY id_lote, fecha;", conn
        )
        predicciones = pd.read_sql_query(
            "SELECT * FROM gold_ml.predicciones ORDER BY id_lote, fecha;", conn
        )
        return historico, predicciones
    finally:
        conn.close()

try:
    historico, predicciones = cargar_tablas()
except Exception as exc:
    st.error("No se pudieron leer gold_ml.dataset_features y gold_ml.predicciones. Revise la conexión y los permisos.")
    st.exception(exc)
    st.stop()

for df in (historico, predicciones):
    if not {"id_lote", "fecha"}.issubset(df.columns):
        st.error("Ambas tablas deben contener las columnas id_lote y fecha.")
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

# Unifica las fuentes sin asumir que tienen exactamente las mismas columnas.
# Si hay histórico y predicción para el mismo lote/fecha, prevalece la fotografía
# almacenada con la predicción. Si hay varias versiones, se prioriza la más reciente.
datos = pd.concat([historico, predicciones], ignore_index=True, sort=False)
if "predicho_en" in datos.columns:
    datos["predicho_en"] = pd.to_datetime(datos["predicho_en"], errors="coerce")
    datos = datos.sort_values(["id_lote", "fecha", "_prioridad", "predicho_en"], na_position="first")
else:
    datos = datos.sort_values(["id_lote", "fecha", "_prioridad"])
datos = datos.drop_duplicates(["id_lote", "fecha"], keep="last").sort_values(["id_lote", "fecha"])

lotes = sorted(datos["id_lote"].dropna().unique().tolist())
if not lotes:
    st.info("No se encontraron lotes válidos.")
    st.stop()

col1, col2 = st.columns([1, 2])
with col1:
    lote = st.selectbox("Seleccione el lote", lotes)
df_lote_completo = datos[datos["id_lote"] == lote].copy()
fecha_min = df_lote_completo["fecha"].min().date()
fecha_max = df_lote_completo["fecha"].max().date()
with col2:
    rango = st.date_input("Periodo", value=(fecha_min, fecha_max), min_value=fecha_min, max_value=fecha_max)

df_lote = df_lote_completo.copy()
if isinstance(rango, (tuple, list)) and len(rango) == 2:
    inicio, fin = rango
    df_lote = df_lote[(df_lote["fecha"].dt.date >= inicio) & (df_lote["fecha"].dt.date <= fin)]
df_lote = df_lote.sort_values("fecha")
if df_lote.empty:
    st.warning("No hay datos para el periodo seleccionado.")
    st.stop()

n_fechas = df_lote["fecha"].nunique()
n_pred = int((df_lote["_origen"] == "Predicción operativa").sum())
n_verif = int(df_lote["verificado"].fillna(False).astype(bool).sum()) if "verificado" in df_lote.columns else 0
m1, m2, m3 = st.columns(3)
m1.metric("Fechas observadas", n_fechas)
m2.metric("Predicciones registradas", n_pred)
m3.metric("Predicciones verificadas", n_verif)

st.divider()
st.subheader("1. Evolución del riesgo de mortalidad")
st.caption("El modelo estima si ocurrirá al menos un episodio de riesgo alto en las cuatro semanas posteriores a cada fecha. Estas etiquetas no representan por sí mismas el número de animales fallecidos.")

riesgo = pd.DataFrame({"fecha": df_lote["fecha"]}).set_index("fecha")
if "target_riesgo_alto_4sem" in df_lote.columns:
    riesgo["Target histórico (0/100)"] = pd.to_numeric(df_lote["target_riesgo_alto_4sem"], errors="coerce").to_numpy() * 100
if "probabilidad_riesgo_predicha" in df_lote.columns:
    riesgo["Probabilidad predicha (%)"] = pd.to_numeric(df_lote["probabilidad_riesgo_predicha"], errors="coerce").to_numpy() * 100
if "target_riesgo_alto_4sem_real" in df_lote.columns:
    riesgo["Resultado verificado (0/100)"] = pd.to_numeric(df_lote["target_riesgo_alto_4sem_real"], errors="coerce").to_numpy() * 100
if "umbral_utilizado" in df_lote.columns:
    riesgo["Umbral del modelo (%)"] = pd.to_numeric(df_lote["umbral_utilizado"], errors="coerce").to_numpy() * 100

if len(riesgo.columns) and not riesgo.dropna(how="all").empty:
    st.line_chart(riesgo, y_label="Porcentaje / etiqueta (0–100)")
    st.caption("Target histórico y resultado verificado: 0 = no hubo episodio de riesgo alto; 100 = sí hubo. La probabilidad y el umbral son porcentajes continuos.")
else:
    st.info("No hay columnas de riesgo disponibles para graficar.")

cols = [c for c in ["fecha", "_origen", "probabilidad_riesgo_predicha", "umbral_utilizado",
                     "riesgo_alto_predicho", "target_riesgo_alto_4sem", "verificado",
                     "target_riesgo_alto_4sem_real", "intervencion_realizada", "modelo_utilizado"]
        if c in df_lote.columns]
if cols:
    st.dataframe(df_lote[cols].rename(columns={
        "fecha": "Fecha", "_origen": "Fuente",
        "probabilidad_riesgo_predicha": "Probabilidad predicha",
        "umbral_utilizado": "Umbral", "riesgo_alto_predicho": "Riesgo predicho",
        "target_riesgo_alto_4sem": "Target histórico (4 semanas)",
        "verificado": "Verificado", "target_riesgo_alto_4sem_real": "Resultado real (4 semanas)",
        "intervencion_realizada": "Intervención", "modelo_utilizado": "Modelo",
    }), use_container_width=True, hide_index=True)

st.divider()
st.subheader("2. Evolución de las variables del lote")
disponibles = [c for c in VARIABLES if c in df_lote.columns and pd.to_numeric(df_lote[c], errors="coerce").notna().any()]
if disponibles:
    predeterminadas = [c for c in ["casos_respiratorios", "casos_diarreicos", "condicion_pastura_indice",
                                    "condicion_corporal_prom", "temperatura_media_c"] if c in disponibles][:4]
    elegidas = st.multiselect("Variables que desea comparar", disponibles, default=predeterminadas,
                             format_func=lambda c: VARIABLES[c])
    if elegidas:
        grafico = df_lote[["fecha"] + elegidas].copy()
        for c in elegidas:
            grafico[c] = pd.to_numeric(grafico[c], errors="coerce")
        grafico = grafico.set_index("fecha")
        grafico.columns = [VARIABLES[c] for c in grafico.columns]
        st.line_chart(grafico)
        st.caption("Las variables pueden tener unidades y escalas diferentes. Para compararlas con precisión, grafique juntas variables con escalas similares.")
    else:
        st.info("Seleccione al menos una variable.")
else:
    st.info("No se encontraron variables numéricas conocidas en las columnas disponibles.")

st.divider()
st.subheader("3. Contexto del lote")
contexto = [c for c in ["distrito", "categoria_zootecnica", "raza_predominante", "lote_sensorizado",
                         "uso_registro_digital", "distancia_centro_veterinario_km", "altitud_msnm"]
            if c in df_lote.columns]
if contexto:
    ultima = df_lote.iloc[-1]
    columnas = st.columns(3)
    for i, c in enumerate(contexto):
        valor = ultima[c]
        texto = "Sin dato" if pd.isna(valor) else ("Sí" if isinstance(valor, (bool, np.bool_)) and valor else
                                                    "No" if isinstance(valor, (bool, np.bool_)) else str(valor))
        with columnas[i % 3]:
            st.write(f"**{c.replace('_', ' ').title()}**")
            st.write(texto)

csv = df_lote.drop(columns=["_prioridad"], errors="ignore").to_csv(index=False).encode("utf-8-sig")
st.download_button("Descargar datos de este lote (CSV)", csv, f"evolucion_{lote}.csv", "text/csv")

with st.expander("Importante: riesgo no equivale a mortalidad observada"):
    st.markdown(
        "Las columnas `target_riesgo_alto_4sem` y `target_riesgo_alto_4sem_real` indican si hubo al menos un episodio de riesgo alto durante la ventana futura de cuatro semanas. "
        "No son un conteo ni una tasa de animales fallecidos. Para graficar mortalidad real se necesita una variable explícita con animales muertos y, para una tasa, el número de animales expuestos."
    )
