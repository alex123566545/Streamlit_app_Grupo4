import psycopg2


def get_connection():

    return psycopg2.connect(
        host="aws-0-us-west-2.pooler.supabase.com",
        port=5432,
        database="postgres",
        user="postgres.cuxppijddpiuaxwyswfb",
        password="alex20151615665451",
        sslmode="require"
    )


# ------------------------------------------------------------------
# Credenciales para la API de Storage (distintas a las de Postgres).
# Reemplaza SUPABASE_KEY por tu key real de este proyecto
# (Project Settings > API Keys en el dashboard de Supabase).
# ------------------------------------------------------------------
SUPABASE_URL = "https://cuxppijddpiuaxwyswfb.supabase.co"
SUPABASE_KEY = "sb_publishable_y1wP5ZIz5elf33-CJkYmvw_gYI6dAyA"