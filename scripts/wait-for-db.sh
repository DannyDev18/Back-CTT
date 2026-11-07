#!/bin/sh

MAX_RETRIES=30
RETRY=0

echo "Esperando a que PostgreSQL este listo..."
echo "Servidor : $POSTGRES_HOST"
echo "Puerto   : $POSTGRES_PORT"
echo "Base     : $POSTGRES_DB"
echo "Usuario  : $POSTGRES_USER"

# La imagen oficial de postgres crea la base y el usuario (POSTGRES_DB /
# POSTGRES_USER / POSTGRES_PASSWORD) en el primer arranque, asi que aqui solo
# hace falta esperar a que acepte conexiones con las credenciales de la app.
cat > /tmp/check_db.py << 'PYEOF'
import os, sys
import psycopg2

try:
    conn = psycopg2.connect(
        host=os.environ["POSTGRES_HOST"],
        port=os.environ["POSTGRES_PORT"],
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        connect_timeout=3,
    )
    conn.close()
    sys.exit(0)
except Exception as e:
    print("Error: {}".format(e), file=sys.stderr)
    sys.exit(1)
PYEOF

until python /tmp/check_db.py; do
    RETRY=$((RETRY + 1))
    if [ "$RETRY" -ge "$MAX_RETRIES" ]; then
        echo "ERROR: PostgreSQL no disponible despues de $MAX_RETRIES intentos. Abortando."
        rm -f /tmp/check_db.py
        exit 1
    fi
    echo "Intento $RETRY/$MAX_RETRIES - PostgreSQL no listo. Reintentando en 5s..."
    sleep 5
done

rm -f /tmp/check_db.py
echo "PostgreSQL listo."
echo ""

# ── Fase 2: Crear directorios necesarios en volúmenes montados ───────────────
echo "Inicializando directorios de datos..."

mkdir -p static/images/courses
mkdir -p static/images/articles
mkdir -p static/svg/categories
mkdir -p static/pdf
mkdir -p logs

# Asegurar ownership para appuser (el script corre como root)
chown -R appuser:appgroup static/ logs/

echo "Directorios inicializados correctamente."
echo ""

# ── Fase 3: Aplicar migraciones de base de datos ──────────────────────────────
echo "Aplicando migraciones de base de datos (alembic upgrade head)..."
gosu appuser alembic upgrade head
if [ $? -ne 0 ]; then
    echo "ERROR: Fallo al aplicar migraciones. Abortando arranque."
    exit 1
fi
echo "Migraciones aplicadas correctamente."
echo ""

# ── Fase 4: Iniciar aplicación como appuser ──────────────────────────────────
echo "Iniciando aplicacion como appuser..."
if [ "$DEBUG" = "True" ] || [ "$DEBUG" = "true" ] || [ "$RELOAD" = "true" ]; then
    echo "Modo autoreload activado (--reload --reload-dir /app/src)"
    exec gosu appuser uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir /app/src
else
    exec gosu appuser uvicorn src.main:app --host 0.0.0.0 --port 8000
fi
