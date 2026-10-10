import streamlit as st

st.set_page_config(
    page_title="SIPREM-BOVINO",
    page_icon="🐄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# ESTILOS PERSONALIZADOS
# =========================
st.markdown("""
<style>
    /* Paleta: blanco, marrón y negro */
    :root {
        --brown: #795438;
        --brown-dark: #513824;
        --black: #191919;
        --white: #FFFFFF;
        --border: #E8E1D9;
    }

    /* Fondo principal */
    .stApp {
        background-color: var(--white);
        color: var(--black);
    }

    /* Ocultar elementos predeterminados */
    #MainMenu, footer {
        visibility: hidden;
    }

    header[data-testid="stHeader"] {
        background-color: transparent;
    }

    .block-container {
        max-width: 1200px;
        padding-top: 3rem;
        padding-bottom: 3rem;
    }

    /* Barra lateral */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid var(--border);
    }

    section[data-testid="stSidebar"] > div {
        padding-top: 2rem;
    }

    /* Marca */
    .brand {
        font-size: 13px;
        font-weight: 700;
        letter-spacing: 3px;
        color: var(--brown);
        margin-bottom: 12px;
    }

    /* Encabezado */
    .hero {
        padding: 42px;
        background-color: #FFFFFF;
        border: 1px solid var(--border);
        border-radius: 16px;
        margin-bottom: 28px;
    }

    .hero-label {
        color: var(--brown);
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 14px;
    }

    .hero h1 {
        color: var(--black);
        font-size: clamp(32px, 4vw, 48px);
        font-weight: 750;
        letter-spacing: -1.8px;
        line-height: 1.15;
        margin: 0 0 18px 0;
    }

    .hero p {
        color: #55504B;
        font-size: 16px;
        line-height: 1.8;
        max-width: 680px;
        margin-bottom: 0;
    }

    .accent {
        color: var(--brown);
    }

    /* Tarjetas informativas */
    .info-card {
        padding: 25px;
        border: 1px solid var(--border);
        border-radius: 12px;
        background: #FFFFFF;
        min-height: 155px;
    }

    .card-number {
        color: var(--brown);
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 1.5px;
        margin-bottom: 18px;
    }

    .info-card h3 {
        color: var(--black);
        font-size: 18px;
        font-weight: 650;
        margin: 0 0 10px 0;
    }

    .info-card p {
        color: #625D57;
        font-size: 14px;
        line-height: 1.6;
        margin: 0;
    }

    /* Separadores y textos secundarios */
    .section-title {
        color: var(--black);
        font-size: 21px;
        font-weight: 700;
        margin: 35px 0 18px 0;
    }

    .footer-text {
        color: #77716A;
        font-size: 12px;
        text-align: center;
        padding-top: 30px;
    }

    /* Botones */
    .stButton > button {
        background-color: var(--brown);
        color: var(--white);
        border: 1px solid var(--brown);
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
        transition: background-color 0.2s ease;
    }

    .stButton > button:hover {
        background-color: var(--brown-dark);
        border-color: var(--brown-dark);
        color: var(--white);
    }

    /* Adaptación a pantallas pequeñas */
    @media (max-width: 768px) {
        .block-container {
            padding: 1.5rem 1rem;
        }

        .hero {
            padding: 26px;
        }
    }
</style>
""", unsafe_allow_html=True)


# =========================
# BARRA LATERAL
# =========================
with st.sidebar:
    st.markdown(
        '<div class="brand">SIPREM / BOVINO</div>',
        unsafe_allow_html=True
    )

    st.markdown("---")

    st.markdown("**SISTEMA**")
    st.caption("Sistema predictivo de riesgo de mortalidad bovina")

    st.markdown("---")
    st.caption("Selecciona una página desde el menú de navegación.")


# =========================
# ENCABEZADO PRINCIPAL
# =========================
st.markdown("""
<div class="hero">
    <div class="hero-label">Sistema de monitoreo ganadero</div>

    <h1>
        SIPREM-<span class="accent">BOVINO</span>
    </h1>

    <p>
        Sistema Predictivo de Riesgo de Mortalidad Bovina.
        Transforma los datos ganaderos en información útil
        para identificar riesgos y apoyar la toma de decisiones.
    </p>
</div>
""", unsafe_allow_html=True)


# =========================
# SECCIÓN INFORMATIVA
# =========================
st.markdown(
    '<div class="section-title">Panel de inicio</div>',
    unsafe_allow_html=True
)

col1, col2, col3 = st.columns(3, gap="medium")

with col1:
    st.markdown("""
    <div class="info-card">
        <div class="card-number">01 / DATOS</div>
        <h3>Monitoreo ganadero</h3>
        <p>Consulta la información de los lotes y sus variables relevantes.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="info-card">
        <div class="card-number">02 / MODELO ML</div>
        <h3>Predicción de riesgo</h3>
        <p>Identifica lotes que podrían presentar un riesgo elevado de mortalidad.</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="info-card">
        <div class="card-number">03 / DECISIONES</div>
        <h3>Apoyo preventivo</h3>
        <p>Utiliza las predicciones como apoyo para priorizar la revisión de los lotes.</p>
    </div>
    """, unsafe_allow_html=True)


# =========================
# PIE DE PÁGINA
# =========================
st.markdown("---")

st.markdown("""
<div class="footer-text">
    SIPREM-BOVINO · Sistema Predictivo de Riesgo de Mortalidad Bovina
</div>
""", unsafe_allow_html=True)
