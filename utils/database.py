import psycopg2
import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def obtener_config(clave, requerido=True):
    """
    Busca una clave de configuración primero en las variables de
    entorno (para desarrollo local con .env) y, si no la encuentra,
    en st.secrets (para Streamlit Cloud, donde no existe .env).
    """
    valor = os.environ.get(clave)

    if valor is not None:
        return valor

    try:
        return st.secrets[clave]
    except (KeyError, FileNotFoundError):
        if requerido:
            raise KeyError(
                f"Falta configurar '{clave}'. Defínela en tu archivo "
                f".env (local) o en Settings > Secrets (Streamlit Cloud)."
            )
        return None


def get_connection():
    return psycopg2.connect(
        host=obtener_config("SUPABASE_DB_HOST"),
        port=obtener_config("SUPABASE_DB_PORT", requerido=False) or "5432",
        database=obtener_config("SUPABASE_DB_NAME", requerido=False) or "postgres",
        user=obtener_config("SUPABASE_DB_USER"),
        password=obtener_config("SUPABASE_DB_PASSWORD"),
        sslmode="require",
    )


# ------------------------------------------------------------------
# Credenciales para la API de Storage (distintas a las de Postgres).
# Se exponen aquí para que otras páginas de la app (como
# nueva_prediccion.py) las reutilicen sin duplicar la lectura del
# .env / secrets en cada archivo.
# ------------------------------------------------------------------
SUPABASE_URL = obtener_config("SUPABASE_URL")
SUPABASE_KEY = obtener_config("SUPABASE_KEY")