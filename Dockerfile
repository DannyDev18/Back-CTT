# ── Base image ────────────────────────────────────────────────────────────────
FROM python:3.12-slim-bookworm

# ── Sistema: dependencias + ODBC Driver 18 en una sola capa ──────────────────
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        gnupg2 \
        build-essential \
        unixodbc \
        unixodbc-dev \
        gosu && \
    # Registrar repositorio de Microsoft
    curl -fsSL https://packages.microsoft.com/keys/microsoft.asc \
        | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg && \
    echo "deb [arch=amd64,arm64,armhf signed-by=/usr/share/keyrings/microsoft-prod.gpg] \
https://packages.microsoft.com/repos/microsoft-debian-bookworm-prod bookworm main" \
        > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    env ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 mssql-tools18 && \
    rm -rf /var/lib/apt/lists/*

# ── Usuario no root ───────────────────────────────────────────────────────────
# Nota: msodbcsql18 registra el driver correctamente en /etc/odbcinst.ini
# durante la instalacion. No se necesita odbcinst manual.
RUN groupadd -r appgroup && \
    useradd -r -g appgroup -d /app -s /usr/sbin/nologin appuser

# ── Directorio de trabajo ─────────────────────────────────────────────────────
WORKDIR /app

# ── Dependencias Python (cacheado si requirements.txt no cambia) ──────────────
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── Script de espera ──────────────────────────────────────────────────────────
# sed elimina \r (CRLF) por si el archivo fue editado en Windows.
# Sin esto el shebang queda "#!/bin/sh\r" y Linux da "no such file or directory".
COPY scripts/wait-for-sql.sh /wait-for-sql.sh
RUN sed -i 's/\r$//' /wait-for-sql.sh && chmod +x /wait-for-sql.sh

# ── Codigo de la aplicacion ───────────────────────────────────────────────────
COPY --chown=appuser:appgroup . .

# ── Directorios de datos con permisos correctos ───────────────────────────────
RUN mkdir -p /app/static/images/courses /app/logs && \
    chown -R appuser:appgroup /app/static /app/logs

# ── Puerto expuesto ───────────────────────────────────────────────────────────
EXPOSE 8000

# ── IMPORTANTE: NO cambiar a appuser aquí ─────────────────────────────────────
# El script wait-for-sql.sh necesita ejecutarse como root para crear directorios
# en volúmenes montados. Luego cambia a appuser antes de lanzar uvicorn.

# ── Arranque: espera SQL Server y luego lanza uvicorn ─────────────────────────
CMD ["/wait-for-sql.sh"]
