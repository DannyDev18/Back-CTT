# Solución al Error de Timeout de Conexión SQL Server

## Problema Identificado

El error `Login timeout expired` indica que tu contenedor API no puede conectarse al contenedor SQL Server porque están en redes Docker diferentes y no pueden comunicarse entre sí.

## Solución Implementada

He actualizado el `docker-compose.yml` para incluir tanto SQL Server como la API en la misma red Docker, permitiendo la comunicación entre contenedores.

## Pasos para Implementar la Solución

### 1. Detener y Eliminar el Contenedor SQL Server Actual

```bash
# Detener el contenedor actual
docker stop sqlserver
# Eliminar el contenedor
docker rm sqlserver
```

### 2. Configurar Variables de Entorno

Crea el archivo `.env` basado en el template:

```bash
cp env.template .env
```

Edita el archivo `.env` con esta configuración mínima:

```env
SQL_SERVER=sqlserver
SQL_PORT=1433
SQL_DB=master
SQL_USER=sa
SQL_PASSWORD=MiContraseñaFuerte!123
JWT_SECRET_KEY=tu_clave_secreta_jwt_super_larga_y_segura_123456789
DEBUG=False
```

### 3. Ejecutar con Docker Compose

```bash
# Detener cualquier contenedor previo
docker-compose down

# Construir y ejecutar ambos servicios
docker-compose up -d

# Verificar que ambos contenedores estén corriendo
docker-compose ps
```

## Verificación de la Solución

### 1. Verificar que SQL Server esté funcionando:

```bash
# Ver logs de SQL Server
docker-compose logs sqlserver

# Debería mostrar: "SQL Server is now ready for client connections"
```

### 2. Verificar que la API se conecte correctamente:

```bash
# Ver logs de la API
docker-compose logs ctt-api

# No debería mostrar errores de timeout
```

### 3. Probar la API:

```bash
# Probar endpoint básico
curl http://localhost:8000/

# Acceder a la documentación
# http://localhost:8000/docs
```

## Características de la Nueva Configuración

### ✅ Red Docker Compartida
- Ambos contenedores están en la misma red `ctt-network`
- La API puede conectarse a SQL Server usando el nombre del servicio `sqlserver`

### ✅ Health Check
- SQL Server tiene un health check que verifica que esté listo
- La API espera a que SQL Server esté saludable antes de iniciarse

### ✅ Persistencia de Datos
- Los datos de SQL Server se guardan en un volumen Docker `sqlserver_data`
- Los datos persisten aunque elimines los contenedores

### ✅ Configuración Automatizada
- SQL Server se configura automáticamente con la contraseña especificada
- La API se conecta automáticamente usando las variables de entorno

## Solución de Problemas

### Si SQL Server no inicia:
```bash
# Verificar logs de SQL Server
docker-compose logs sqlserver

# La contraseña debe cumplir los requisitos de complejidad de SQL Server
# - Al menos 8 caracteres
# - Incluir mayúsculas, minúsculas, números y símbolos
```

### Si la API no se conecta:
```bash
# Verificar que SQL Server esté respondiendo
docker exec -it sqlserver-ctt /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "MiContraseñaFuerte!123" -Q "SELECT 1"

# Verificar variables de entorno de la API
docker exec -it ctt-fastapi env | grep SQL
```

### Si necesitas recrear todo:
```bash
# Detener y eliminar todo
docker-compose down -v

# Eliminar imágenes si es necesario
docker rmi ctt-api

# Reconstruir y ejecutar
docker-compose build --no-cache
docker-compose up -d
```

## Alternativa: Conectar a SQL Server Externo

Si prefieres mantener tu contenedor SQL Server actual separado, puedes conectar la red:

```bash
# Crear una red compartida
docker network create ctt-shared-network

# Conectar tu contenedor SQL Server existente a la red
docker network connect ctt-shared-network sqlserver

# Modificar docker-compose.yml para usar la red externa
```

## Notas Importantes

- **Persistencia**: Los datos de SQL Server se mantienen en el volumen `sqlserver_data`
- **Seguridad**: La contraseña debe cumplir los requisitos de complejidad de SQL Server
- **Red**: Los contenedores pueden comunicarse usando los nombres de servicio como hostnames
- **Orden de inicio**: La API espera a que SQL Server esté completamente iniciado antes de conectarse
