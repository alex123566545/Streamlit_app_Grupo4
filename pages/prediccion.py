import streamlit as st
import pandas as pd

from utils.database import get_connection


st.set_page_config(
    page_title="Predicciones",
    page_icon="🚨",
    layout="wide"
)


st.title("🚨 Consulta de predicciones")


@st.cache_data(ttl=60)
def cargar_predicciones():

    conn = get_connection()

    try:

        query = """
            SELECT *
            FROM gold_ml.predicciones
            ORDER BY fecha DESC
        """

        df = pd.read_sql(query, conn)

    finally:

        conn.close()

    return df


df = cargar_predicciones()


if df.empty:

    st.warning(
        "No existen predicciones."
    )

    st.stop()


# ============================================================
# FILTROS
# ============================================================

col1, col2 = st.columns(2)


with col1:

    lotes = sorted(
        df["id_lote"]
        .dropna()
        .unique()
    )

    lote = st.selectbox(
        "Seleccionar lote",
        ["TODOS"] + lotes
    )


with col2:

    niveles = st.multiselect(
        "Nivel de riesgo",
        ["ALTO", "BAJO"],
        default=["ALTO", "BAJO"]
    )


# ============================================================
# FILTRADO
# ============================================================

df["nivel_riesgo"] = df[
    "riesgo_alto_predicho"
].map({
    True: "ALTO",
    False: "BAJO"
})


filtrado = df[
    df["nivel_riesgo"].isin(niveles)
].copy()


if lote != "TODOS":

    filtrado = filtrado[
        filtrado["id_lote"] == lote
    ]


# ============================================================
# RESULTADOS
# ============================================================

st.subheader(
    f"Resultados: {len(filtrado)}"
)


st.dataframe(
    filtrado[
        [
            "id_lote",
            "fecha",
            "probabilidad_riesgo_predicha",
            "riesgo_alto_predicho",
            "umbral_utilizado",
            "modelo_utilizado"
        ]
    ],
    use_container_width=True
)