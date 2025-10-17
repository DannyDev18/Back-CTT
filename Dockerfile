# Usar Python 3.12 slim como imagen base
FROM python:3.12-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    apt-utils \
    gnupg2 \
    gpg \
    unixodbc \
    unixodbc-dev && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --upgrade pip

# Agregar la clave de Microsoft y el repositorio usando el método moderno
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg && \
    echo "deb [arch=amd64,arm64,armhf signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/repos/microsoft-debian-bullseye-prod bullseye main" > /etc/apt/sources.list.d/mssql-release.list

# Actualizar lista de paquetes e instalar ODBC Driver 18 para SQL Server
RUN apt-get update && \
    env ACCEPT_EULA=Y apt-get install -y msodbcsql18

# Copiar y configurar archivo odbc.ini
COPY odbc.ini /tmp/odbc.ini
RUN odbcinst -i -s -f /tmp/odbc.ini -l

# Verificar la instalación del driver ODBC (opcional, para debugging)
RUN cat /etc/odbc.ini

# Copiar requirements.txt e instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY . .

# Crear directorio para imágenes con permisos
RUN mkdir -p /app/static/images/courses && \
    chmod -R 755 /app/static

# Exponer el puerto 8000
EXPOSE 8000

# Crear script para esperar a SQL Server
RUN echo '#!/bin/bash\n\
echo "Esperando a que SQL Server esté listo..."\n\
for i in {30..0}; do\n\
  if python -c "import pyodbc; pyodbc.connect(\"DRIVER={ODBC Driver 18 for SQL Server};SERVER=$SQL_SERVER;PORT=$SQL_PORT;DATABASE=$SQL_DB;UID=$SQL_USER;PWD=$SQL_PASSWORD;TrustServerCertificate=yes\")" &> /dev/null; then\n\
    echo "SQL Server está listo!"\n\
    break\n\
  fi\n\
  echo "SQL Server no está listo aún. Esperando $i segundos más..."\n\
  sleep 2\n\
done\n\
\n\
if [ "$i" = 0 ]; then\n\
  echo "SQL Server no está disponible después de 60 segundos"\n\
  exit 1\n\
fi\n\
\n\
echo "Iniciando aplicación..."\n\
exec uvicorn src.main:app --host 0.0.0.0 --port 8000' > /wait-for-sql.sh && \
    chmod +x /wait-for-sql.sh

# Comando para ejecutar la aplicación con espera
CMD ["/wait-for-sql.sh"]
