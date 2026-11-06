# ── Base image ────────────────────────────────────────────────────────────────
FROM python:3.12-slim-bookworm

# ── Sistema: gosu para cambiar a usuario no-root al arrancar ────────────────
RUN apt-get update && \
    apt-get install -y --no-install-recommends gosu && \
    rm -rf /var/lib/apt/lists/*

# ── Usuario no root ───────────────────────────────────────────────────────────
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
COPY scripts/wait-for-db.sh /wait-for-db.sh
RUN sed -i 's/\r$//' /wait-for-db.sh && chmod +x /wait-for-db.sh

# ── Codigo de la aplicacion ───────────────────────────────────────────────────
COPY --chown=appuser:appgroup . .

# ── Directorios de datos con permisos correctos ───────────────────────────────
RUN mkdir -p /app/static/images/courses /app/logs && \
    chown -R appuser:appgroup /app/static /app/logs

# ── Puerto expuesto ───────────────────────────────────────────────────────────
EXPOSE 8000

# ── IMPORTANTE: NO cambiar a appuser aquí ─────────────────────────────────────
# El script wait-for-db.sh necesita ejecutarse como root para crear directorios
# en volúmenes montados. Luego cambia a appuser antes de lanzar uvicorn.

# ── Arranque: espera PostgreSQL y luego lanza uvicorn ─────────────────────────
CMD ["/wait-for-db.sh"]
