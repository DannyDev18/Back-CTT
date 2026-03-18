#!/bin/sh




MAX_RETRIES=30
RETRY=0

echo "Esperando a que SQL Server este listo..."
echo "Servidor : $SQL_SERVER"
echo "Puerto   : $SQL_PORT"
echo "Base     : $SQL_DB"
echo "Usuario  : $SQL_USER"

# check_sql.py:
#   - Fase setup: conecta como SA (MSSQL_SA_PASSWORD) — solo para preparar el entorno.
#   - Crea la base de datos si no existe.
#   - Crea un login/usuario de aplicacion con permisos minimos (no SA).
#   - El usuario de aplicacion (SQL_USER) solo puede SELECT/INSERT/UPDATE/DELETE.
#   - La aplicacion nunca usa SA — solo el usuario limitado.
cat > /tmp/check_sql.py << 'PYEOF'
import pyodbc, os, sys

sa_conn_str = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=" + os.environ["SQL_SERVER"] + "," + os.environ["SQL_PORT"] + ";"
    "DATABASE=master;"
    "UID=sa;"
    "PWD=" + os.environ["MSSQL_SA_PASSWORD"] + ";"
    "TrustServerCertificate=yes"
)

try:
    conn = pyodbc.connect(sa_conn_str, timeout=3, autocommit=True)
    cursor = conn.cursor()

    db       = os.environ["SQL_DB"]
    app_user = os.environ["SQL_USER"]
    app_pass = os.environ["SQL_PASSWORD"]

    # 1. Crear base de datos si no existe
    cursor.execute(
        "IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'{0}') "
        "CREATE DATABASE [{0}]".format(db)
    )

    # 2. Crear login de aplicacion si no existe
    cursor.execute(
        "IF NOT EXISTS (SELECT name FROM sys.sql_logins WHERE name = N'{0}') "
        "CREATE LOGIN [{0}] WITH PASSWORD = N'{1}', CHECK_POLICY = OFF".format(app_user, app_pass)
    )

    # 3. Crear usuario en la BD si no existe
    cursor.execute(
        "USE [{0}]; "
        "IF NOT EXISTS (SELECT name FROM sys.database_principals WHERE name = N'{1}') "
        "CREATE USER [{1}] FOR LOGIN [{1}]".format(db, app_user)
    )

    # 4. Permisos DML sobre el schema (SELECT/INSERT/UPDATE/DELETE)
    cursor.execute(
        "USE [{0}]; "
        "GRANT SELECT, INSERT, UPDATE, DELETE ON SCHEMA::dbo TO [{1}]".format(db, app_user)
    )

    # 5. Permisos DDL para que SQLAlchemy pueda ejecutar create_all()
    #    - CREATE TABLE  : crear tablas nuevas
    #    - CREATE VIEW   : crear vistas si las usa el ORM
    #    - ALTER ON SCHEMA::dbo : modificar tablas existentes (FK, constraints, indices)
    #    No se asigna db_owner ni db_ddladmin para mantener minimos privilegios.
    for stmt in [
        "USE [{0}]; GRANT CREATE TABLE            TO [{1}]",
        "USE [{0}]; GRANT CREATE VIEW             TO [{1}]",
        "USE [{0}]; GRANT ALTER      ON SCHEMA::dbo TO [{1}]",
        "USE [{0}]; GRANT REFERENCES ON SCHEMA::dbo TO [{1}]",
    ]:
        cursor.execute(stmt.format(db, app_user))

    cursor.close()
    conn.close()
    print("Setup OK. Base '{}' y usuario '{}' listos.".format(db, app_user))
    sys.exit(0)

except Exception as e:
    print("Error: {}".format(e), file=sys.stderr)
    sys.exit(1)
PYEOF

until python /tmp/check_sql.py; do
    RETRY=$((RETRY + 1))
    if [ "$RETRY" -ge "$MAX_RETRIES" ]; then
        echo "ERROR: SQL Server no disponible despues de $MAX_RETRIES intentos. Abortando."
        rm -f /tmp/check_sql.py
        exit 1
    fi
    echo "Intento $RETRY/$MAX_RETRIES - SQL Server no listo. Reintentando en 5s..."
    sleep 5
done

rm -f /tmp/check_sql.py
echo "SQL Server listo. Iniciando aplicacion..."
exec uvicorn src.main:app --host 0.0.0.0 --port 8000
