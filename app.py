import streamlit as st

st.set_page_config(
    page_title="SIPREM-BOVINO",
    page_icon="🐄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# CONFIGURACIÓN VISUAL
# =========================
st.markdown("""
<style>
    :root {
        --bg: #171411;
        --sidebar: #201A16;
        --card: #282019;
        --brown: #A8794E;
        --brown-light: #C49A70;
        --text: #F3EDE6;
        --muted: #B7AA9C;
        --border: #403329;
    }

    /* Fondo general */
    .stApp,
    [data-testid="stAppViewContainer"] {
        background-color: var(--bg);
        color: var(--text);
    }

    .block-container {
        max-width: 1250px;
        padding-top: 3rem;
        padding-bottom: 2rem;
    }

    /* Ocultar elementos de Streamlit */
    #MainMenu,
    footer {
        visibility: hidden;
    }

    header[data-testid="stHeader"] {
        background: transparent;
    }

    /* Barra lateral */
    section[data-testid="stSidebar"] {
        background-color: var(--sidebar);
        border-right: 1px solid var(--border);
    }
    /* Solo los nombres de las páginas del menú */
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a,
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a span {
    color: #FFFFFF !important;
    }


    section[data-testid="stSidebar"] > div {
        background-color: var(--sidebar);
    }

    /* Textos de Streamlit */
    .stMarkdown,
    .stMarkdown p,
    .stMarkdown li {
        color: var(--text);
    }

    /* Identidad de marca */
    .brand {
        color: var(--brown-light);
        font-size: 13px;
        font-weight: 800;
        letter-spacing: 3px;
        margin-bottom: 20px;
    }

    .sidebar-description {
        color: var(--muted);
        font-size: 13px;
        line-height: 1.7;
    }

    /* Hero principal */
    .hero {
        background: linear-gradient(135deg, #302319 0%, #211A15 70%);
        border: 1px solid var(--border);
        border-left: 4px solid var(--brown);
        border-radius: 14px;
        padding: 45px;
        margin-bottom: 35px;
    }

    .hero-label {
        color: var(--brown-light);
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 2.5px;
        text-transform: uppercase;
        margin-bottom: 20px;
    }

    .hero h1 {
        color: var(--text) !important;
        font-size: clamp(34px, 5vw, 56px);
        font-weight: 800;
        letter-spacing: -1.5px;
        line-height: 1.15;
        margin: 0 0 20px 0;
    }

    .hero h1 span {
        color: var(--brown-light) !important;
    }

    .hero p {
        color: var(--muted) !important;
        font-size: 16px;
        line-height: 1.9;
        max-width: 720px;
        margin: 0;
    }

    /* Título de sección */
    .section-title {
        color: var(--text);
        font-size: 22px;
        font-weight: 750;
        margin: 10px 0 8px 0;
    }

    .section-description {
        color: var(--muted);
        font-size: 14px;
        margin-bottom: 24px;
    }

    /* Tarjetas */
    .info-card {
        background-color: var(--card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 25px;
        min-height: 175px;
        transition: border-color 0.2s ease;
    }

    .info-card:hover {
        border-color: var(--brown);
    }

    .card-number {
        color: var(--brown-light);
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 2px;
        margin-bottom: 22px;
    }

    .info-card h3 {
        color: var(--text) !important;
        font-size: 18px;
        font-weight: 700;
        margin: 0 0 12px 0;
    }

    .info-card p {
        color: var(--muted) !important;
        font-size: 13px;
        line-height: 1.8;
        margin: 0;
    }

    /* Separadores */
    hr {
        border-color: var(--border) !important;
    }

    /* Botones */
    .stButton > button {
        background-color: var(--brown);
        color: #FFFFFF;
        border: 1px solid var(--brown);
        border-radius: 8px;
        font-weight: 700;
    }

    .stButton > button:hover {
        background-color: var(--brown-light);
        border-color: var(--brown-light);
        color: #171411;
    }

    /* Pie */
    .footer-text {
        color: #918274;
        font-size: 12px;
        text-align: center;
        padding-top: 15px;
    }

    /* Móvil */
    @media (max-width: 768px) {
        .block-container {
            padding: 1.5rem 1rem;
        }

        .hero {
            padding: 28px 22px;
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

    st.markdown("### Navegación")
    st.markdown(
        '<div class="sidebar-description">'
        'Selecciona una página del menú para explorar '
        'las funcionalidades del sistema.'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown("---")

    st.markdown(
        '<div class="sidebar-description">'
        'Sistema predictivo<br>Monitoreo y prevención ganadera'
        '</div>',
        unsafe_allow_html=True
    )


# =========================
# ENCABEZADO PRINCIPAL
# =========================
st.markdown("""
<div class="hero">
    <div class="hero-label">Sistema de monitoreo ganadero</div>
    <h1>SIPREM-<span>BOVINO</span></h1>
    <p>
        Sistema Predictivo de Riesgo de Mortalidad Bovina.
        Transforma los datos ganaderos en información útil
        para identificar riesgos y apoyar la toma de decisiones.
    </p>
</div>
""", unsafe_allow_html=True)


# =========================
# PANEL PRINCIPAL
# =========================
st.markdown(
    '<div class="section-title">Panel de inicio</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-description">'
    'Explora las principales funcionalidades del sistema.'
    '</div>',
    unsafe_allow_html=True
)

col1, col2, col3 = st.columns(3, gap="medium")

with col1:
    st.markdown("""
    <div class="info-card">
        <div class="card-number">01 / DATOS</div>
        <h3>Monitoreo ganadero</h3>
        <p>
            Consulta información de los lotes y las variables
            que influyen en las condiciones del ganado.
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="info-card">
        <div class="card-number">02 / MACHINE LEARNING</div>
        <h3>Predicción de riesgo</h3>
        <p>
            Identifica los lotes que podrían presentar
            un riesgo elevado de mortalidad en las próximas semanas.
        </p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="info-card">
        <div class="card-number">03 / PREVENCIÓN</div>
        <h3>Apoyo a decisiones</h3>
        <p>
            Utiliza las predicciones como apoyo para priorizar
            la revisión y el seguimiento de los lotes.
        </p>
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
