# Instrucciones de Dockerización para CTT-API

## Requisitos Previos

1. Docker instalado en tu sistema
2. Docker Compose instalado
3. Acceso a un servidor SQL Server

## Configuración

### 1. Configurar Variables de Entorno

Copia el archivo `env.template` a `.env` y configura tus variables:

```bash
cp env.template .env
```

Edita el archivo `.env` con tus configuraciones reales:

```env
SQL_SERVER=tu_servidor_sql_server
SQL_PORT=1433
SQL_DB=tu_nombre_base_datos
SQL_USER=tu_usuario_sql
SQL_PASSWORD=tu_contraseña_sql
JWT_SECRET_KEY=tu_clave_secreta_jwt_muy_segura_y_larga
DEBUG=False
```

### 2. Construir la Imagen Docker

```bash
docker build -t ctt-api .
```

### 3. Ejecutar con Docker Compose (Recomendado)

**IMPORTANTE**: Si ya tienes un contenedor SQL Server corriendo, deténlo primero:

```bash
# Detener contenedor SQL Server existente
docker stop sqlserver
docker rm sqlserver

# Ejecutar ambos servicios con docker-compose
docker-compose up -d
```

### 4. Ejecutar Directamente con Docker

```bash
docker run -d \
  --name ctt-fastapi \
  -p 8000:8000 \
  --env-file .env \
  ctt-api
```

## Verificación

1. La API estará disponible en: http://localhost:8000
2. Documentación Swagger: http://localhost:8000/docs
3. Documentación ReDoc: http://localhost:8000/redoc

## Comandos Útiles

### Ver logs del contenedor
```bash
docker-compose logs -f ctt-api
# o
docker logs -f ctt-fastapi
```

### Detener los servicios
```bash
docker-compose down
```

### Reconstruir la imagen
```bash
docker-compose build --no-cache
docker-compose up -d
```

### Acceder al contenedor para debugging
```bash
docker exec -it ctt-fastapi bash
```

## Características de la Dockerización

### ODBC Driver 18 para SQL Server
- Instalación automática del driver ODBC 18 de Microsoft
- Configuración correcta para conexiones seguras con SQL Server
- Soporte para TrustServerCertificate para conexiones locales

### Optimizaciones
- Imagen basada en Python 3.12 slim para menor tamaño
- Cache de dependencias pip optimizado
- .dockerignore configurado para excluir archivos innecesarios
- Limpieza de paquetes temporales para reducir tamaño de imagen

### Seguridad
- Variables de entorno para configuración sensible
- No inclusión de archivos .env en la imagen
- Usuario no-root (configurado automáticamente por la imagen Python)

## Solución de Problemas

### Error de conexión a SQL Server
1. Verifica que las variables de entorno estén correctamente configuradas
2. Asegúrate de que el servidor SQL Server sea accesible desde el contenedor
3. Verifica que el puerto 1433 esté abierto

### Error de ODBC Driver
Si encuentras errores relacionados con ODBC:
```bash
# Verificar drivers instalados en el contenedor
docker exec -it ctt-fastapi odbcinst -q -d
```

### Error "apt-key: not found"
Este error ocurre en versiones recientes de Debian/Ubuntu donde `apt-key` ha sido deprecado. El Dockerfile actual usa el método moderno con `gpg --dearmor` y gestión de claves en `/usr/share/keyrings/`.

### Error de construcción de imagen
Si la construcción falla, intenta:
```bash
# Limpiar cache de Docker
docker system prune -a
# Reconstruir sin cache
docker build --no-cache -t ctt-api .
```

### Logs de debugging
Activa el modo debug configurando `DEBUG=True` en tu archivo .env y reinicia el contenedor.

## Notas Importantes

- El contenedor se conecta a una base de datos SQL Server externa
- Los seeds de datos se ejecutan automáticamente al iniciar
- La aplicación crea las tablas automáticamente si no existen
- El puerto 8000 está expuesto y mapeado por defecto
