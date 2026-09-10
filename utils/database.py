import psycopg2
import os

from dotenv import load_dotenv

load_dotenv()


def get_connection():
    return psycopg2.connect(
        host=os.environ["SUPABASE_DB_HOST"],
        port=os.environ.get("SUPABASE_DB_PORT", "5432"),
        database=os.environ.get("SUPABASE_DB_NAME", "postgres"),
        user=os.environ["SUPABASE_DB_USER"],
        password=os.environ["SUPABASE_DB_PASSWORD"],
        sslmode="require",
    )


# ------------------------------------------------------------------
# Credenciales para la API de Storage (distintas a las de Postgres).
# Se exponen aquí para que otras páginas de la app (como
# nueva_prediccion.py) las reutilicen sin duplicar la lectura del
# .env en cada archivo.
# ------------------------------------------------------------------
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]