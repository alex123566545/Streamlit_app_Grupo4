import streamlit as st


st.set_page_config(
    page_title="SIPREM-BOVINO",
    page_icon="🐄",
    layout="wide"
)


st.title("🐄 SIPREM-BOVINO")

st.markdown(
    """
    ## Sistema Predictivo de Riesgo de Mortalidad Bovina

    Dashboard para visualizar las predicciones generadas
    por el modelo Random Forest.
    """
)

st.info(
    "Utiliza el menú lateral para navegar entre las páginas."
)
