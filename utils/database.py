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
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN1eHBwaWpkZHBpdWF4d3lzd2ZiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NjQ5Mjc0NCwiZXhwIjoyMTAyMDY4NzQ0fQ.YhAz188CHfNLhQTEUca-y5EOXuSXMWthZgo02oYFaxw"