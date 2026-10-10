import streamlit as st

st.set_page_config(
    page_title="SIPREM-BOVINO",
    page_icon="🐄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================================================
# CONFIGURACIÓN VISUAL
# ==================================================
st.markdown("""
<style>
    :root {
        --bg: #171411;
        --sidebar: #201A16;
        --card: #282019;
        --brown: #A8794E;
        --brown-light: #C49A70;
        --text: #FFFFFF;
        --muted: #D0C5BA;
        --border: #403329;
    }

    /* FONDO GENERAL */
    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"] {
        background-color: var(--bg);
        color: var(--text);
    }

    .block-container {
        max-width: 1250px;
        padding-top: 3rem;
        padding-bottom: 2rem;
    }

    /* OCULTAR ELEMENTOS INNECESARIOS */
    #MainMenu,
    footer {
        visibility: hidden;
    }

    header[data-testid="stHeader"] {
        background: transparent;
    }

    /* ==============================================
       MENÚ LATERAL
    ============================================== */

    section[data-testid="stSidebar"],
    section[data-testid="stSidebar"] > div,
    section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
        background-color: var(--sidebar) !important;
    }

    section[data-testid="stSidebar"] {
        border-right: 1px solid var(--border);
    }

    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] h4,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] a,
    section[data-testid="stSidebar"] li,
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span,
    section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
        color: #FFFFFF !important;
    }

    /* Opciones del menú automático de páginas */
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a,
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] span,
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] p {
        color: #FFFFFF !important;
    }

    /* Elementos interactivos del menú */
    section[data-testid="stSidebar"] button {
        color: #FFFFFF !important;
    }

    /* MARCA */
    .brand {
        color: var(--brown-light) !important;
        font-size: 13px;
        font-weight: 800;
        letter-spacing: 3px;
        margin-bottom: 20px;
    }

    .sidebar-description {
        color: #FFFFFF !important;
        font-size: 13px;
        line-height: 1.8;
    }

    /* ==============================================
       ENCABEZADO PRINCIPAL
    ============================================== */

    .hero {
        background: linear-gradient(
            135deg,
            #302319 0%,
            #211A15 70%
        );
        border: 1px solid var(--border);
        border-left: 4px solid var(--brown);
        border-radius: 14px;
        padding: 45px;
        margin-bottom: 35px;
    }

    .hero-label {
        color: var(--brown-light) !important;
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 2.5px;
        text-transform: uppercase;
        margin-bottom: 20px;
    }

    .hero h1 {
        color: #FFFFFF !important;
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

    /* ==============================================
       TÍTULOS DE SECCIÓN
    ============================================== */

    .section-title {
        color: #FFFFFF !important;
        font-size: 22px;
        font-weight: 750;
        margin: 10px 0 8px 0;
    }

    .section-description {
        color: var(--muted) !important;
        font-size: 14px;
        margin-bottom: 24px;
    }

    /* ==============================================
       TARJETAS
    ============================================== */

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
        color: var(--brown-light) !important;
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 2px;
        margin-bottom: 22px;
    }

    .info-card h3 {
        color: #FFFFFF !important;
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

    /* SEPARADORES */
    hr {
        border-color: var(--border) !important;
    }

    /* ==============================================
       BOTONES
    ============================================== */

    .stButton > button {
        background-color: var(--brown);
        color: #FFFFFF !important;
        border: 1px solid var(--brown);
        border-radius: 8px;
        font-weight: 700;
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        background-color: var(--brown-light);
        border-color: var(--brown-light);
        color: #171411 !important;
    }

    /* PIE DE PÁGINA */
    .footer-text {
        color: #B7AA9C !important;
        font-size: 12px;
        text-align: center;
        padding-top: 15px;
    }

    /* ==============================================
       RESPONSIVE
    ============================================== */

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


# ==================================================
# MENÚ LATERAL
# ==================================================
with st.sidebar:

    st.markdown(
        '<div class="brand">SIPREM / BOVINO</div>',
        unsafe_allow_html=True
    )

    st.markdown("---")

    st.markdown("### Navegación")

    st.markdown(
        """
        <div class="sidebar-description">
            Selecciona una página del menú para explorar
            las funcionalidades del sistema.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    st.markdown(
        """
        <div class="sidebar-description">
            Sistema predictivo<br>
            Monitoreo y prevención ganadera
        </div>
        """,
        unsafe_allow_html=True
    )


# ==================================================
# ENCABEZADO PRINCIPAL
# ==================================================
st.markdown(
    """
    <div class="hero">
        <div class="hero-label">
            Sistema de monitoreo ganadero
        </div>

        <h1>SIPREM-<span>BOVINO</span></h1>

        <p>
            Sistema Predictivo de Riesgo de Mortalidad Bovina.
            Transforma los datos ganaderos en información útil
            para identificar riesgos y apoyar la toma de decisiones.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)


# ==================================================
# PANEL PRINCIPAL
# ==================================================
st.markdown(
    '<div class="section-title">Panel de inicio</div>',
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="section-description">
        Explora las principales funcionalidades del sistema.
    </div>
    """,
    unsafe_allow_html=True
)

col1, col2, col3 = st.columns(3, gap="medium")


# TARJETA 1
with col1:
    st.markdown(
        """
        <div class="info-card">
            <div class="card-number">01 / DATOS</div>

            <h3>Monitoreo ganadero</h3>

            <p>
                Consulta información de los lotes y las variables
                que influyen en las condiciones del ganado.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )


# TARJETA 2
with col2:
    st.markdown(
        """
        <div class="info-card">
            <div class="card-number">02 / MACHINE LEARNING</div>

            <h3>Predicción de riesgo</h3>

            <p>
                Identifica los lotes que podrían presentar
                un riesgo elevado de mortalidad en las próximas semanas.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )


# TARJETA 3
with col3:
    st.markdown(
        """
        <div class="info-card">
            <div class="card-number">03 / PREVENCIÓN</div>

            <h3>Apoyo a decisiones</h3>

            <p>
                Utiliza las predicciones como apoyo para priorizar
                la revisión y el seguimiento de los lotes.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )


# ==================================================
# PIE DE PÁGINA
# ==================================================
st.markdown("---")

st.markdown(
    """
    <div class="footer-text">
        SIPREM-BOVINO · Sistema Predictivo de Riesgo de Mortalidad Bovina
    </div>
    """,
    unsafe_allow_html=True
)
