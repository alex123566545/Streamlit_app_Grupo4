import streamlit as st
import pandas as pd

from utils.database import get_connection

st.set_page_config(
    page_title="SIPREM-BOVINO | Efectividad de intervenciones",
    page_icon="💉",
    layout="wide",
)


@st.cache_data(ttl=30)
def cargar_intervenciones():
    conn = get_connection()
    try:
        query = """
            SELECT
                id_lote,
                fecha,
                tipo_intervencion,
                fecha_intervencion,
                resultado_intervencion,
                riesgo_alto_predicho,
                probabilidad_riesgo_predicha,
                umbral_utilizado,
                target_riesgo_alto_4sem_real
            FROM gold_ml.predicciones_verificadas_con_intervencion
            ORDER BY fecha DESC;
        """
        return pd.read_sql(query, conn)
    finally:
        conn.close()


st.title("💉 SIPREM-BOVINO")
st.subheader("Efectividad de las intervenciones")
st.caption(
    "Analiza qué tan efectivas fueron las intervenciones realizadas "
    "tras una alerta de riesgo alto. **Esta vista es solo para análisis "
    "operativo — nunca se usa para reentrenar el modelo de riesgo**, "
    "ya que la intervención altera el desenlace natural que el modelo "
    "intentaba predecir."
)

try:
    df = cargar_intervenciones()
except Exception as e:
    st.error("❌ No se pudo leer gold_ml.predicciones_verificadas_con_intervencion.")
    st.exception(e)
    st.stop()

if df.empty:
    st.info(
        "Todavía no hay predicciones verificadas con intervención "
        "registrada. Esta sección se llenará a medida que se "
        "confirmen resultados reales de lotes intervenidos."
    )
    st.stop()

df["fecha"] = pd.to_datetime(df["fecha"]).dt.date
df["fecha_intervencion"] = pd.to_datetime(
    df["fecha_intervencion"], errors="coerce"
).dt.date

# ------------------------------------------------------------------
# "Efectiva" = la intervención se hizo tras predecir riesgo alto,
# y el resultado real terminó SIN riesgo alto.
# ------------------------------------------------------------------
df["intervencion_efectiva"] = df["target_riesgo_alto_4sem_real"] == False  # noqa: E712

st.divider()

# ============================================================
# RESUMEN EJECUTIVO
# ============================================================

total = len(df)
efectivas = int(df["intervencion_efectiva"].sum())
no_efectivas = total - efectivas
pct_efectividad = (efectivas / total * 100) if total > 0 else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total intervenciones verificadas", total)
c2.metric("Efectivas (evitaron riesgo)", efectivas)
c3.metric("No efectivas (igual hubo riesgo)", no_efectivas)
c4.metric("% de efectividad", f"{pct_efectividad:.1f}%")

st.divider()

# ============================================================
# EFECTIVIDAD POR TIPO DE INTERVENCIÓN
# ============================================================

st.subheader("📊 Efectividad por tipo de intervención")

df["tipo_intervencion"] = df["tipo_intervencion"].fillna("No especificado")

resumen_tipo = (
    df.groupby("tipo_intervencion")
    .agg(
        total_casos=("intervencion_efectiva", "count"),
        efectivas=("intervencion_efectiva", "sum"),
    )
    .reset_index()
)
resumen_tipo["no_efectivas"] = resumen_tipo["total_casos"] - resumen_tipo["efectivas"]
resumen_tipo["pct_efectividad"] = (
    resumen_tipo["efectivas"] / resumen_tipo["total_casos"] * 100
).round(1)
resumen_tipo = resumen_tipo.sort_values("pct_efectividad", ascending=False)

tabla_tipo = resumen_tipo.rename(
    columns={
        "tipo_intervencion": "Tipo de intervención",
        "total_casos": "Total casos",
        "efectivas": "Efectivas",
        "no_efectivas": "No efectivas",
        "pct_efectividad": "% Efectividad",
    }
)
tabla_tipo["% Efectividad"] = tabla_tipo["% Efectividad"].astype(str) + "%"

st.dataframe(tabla_tipo, use_container_width=True, hide_index=True)

if len(resumen_tipo) > 1:
    st.bar_chart(
        resumen_tipo.set_index("tipo_intervencion")["pct_efectividad"],
        y_label="% Efectividad",
    )

st.divider()

# ============================================================
# DETALLE POR LOTE
# ============================================================

st.subheader("📋 Detalle de casos intervenidos")

c1, c2 = st.columns(2)
with c1:
    tipos = ["Todos"] + sorted(df["tipo_intervencion"].unique().tolist())
    filtro_tipo = st.selectbox("Filtrar por tipo de intervención", tipos)
with c2:
    filtro_resultado = st.selectbox(
        "Filtrar por resultado",
        ["Todos", "Efectiva", "No efectiva"],
    )

df_filtrado = df.copy()
if filtro_tipo != "Todos":
    df_filtrado = df_filtrado[df_filtrado["tipo_intervencion"] == filtro_tipo]
if filtro_resultado == "Efectiva":
    df_filtrado = df_filtrado[df_filtrado["intervencion_efectiva"]]
elif filtro_resultado == "No efectiva":
    df_filtrado = df_filtrado[~df_filtrado["intervencion_efectiva"]]

tabla_detalle = df_filtrado[
    [
        "id_lote",
        "fecha",
        "tipo_intervencion",
        "fecha_intervencion",
        "probabilidad_riesgo_predicha",
        "resultado_intervencion",
        "intervencion_efectiva",
    ]
].copy()

tabla_detalle["probabilidad_riesgo_predicha"] = (
    tabla_detalle["probabilidad_riesgo_predicha"].astype(float) * 100
).round(1).astype(str) + "%"

tabla_detalle["intervencion_efectiva"] = tabla_detalle["intervencion_efectiva"].map(
    {True: "✅ Efectiva", False: "❌ No efectiva"}
)

tabla_detalle.rename(
    columns={
        "id_lote": "Lote",
        "fecha": "Fecha predicción",
        "tipo_intervencion": "Tipo intervención",
        "fecha_intervencion": "Fecha intervención",
        "probabilidad_riesgo_predicha": "Probabilidad predicha",
        "resultado_intervencion": "Notas de la intervención",
        "intervencion_efectiva": "Resultado",
    },
    inplace=True,
)

st.dataframe(tabla_detalle, use_container_width=True, hide_index=True)