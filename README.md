# BACK-CTT

Una aplicación de gestión de usuarios y cursos construida con FastAPI, SQLModel y SQL Server.

## Descripción

Este proyecto implementa un sistema completo que incluye:
- **Autenticación de usuarios**: Registro, login y obtención de perfil con JWT
- **Gestión de cursos**: Creación, consulta y administración de cursos con información completa
- **Sistema de inscripciones**: Gestión completa del proceso de inscripción de usuarios en cursos
- **Base de datos relacional**: Todas las tablas se crean automáticamente al iniciar la aplicación

Utiliza JWT para la autenticación de tokens, hashing de contraseñas para seguridad, y maneja datos complejos estructurados para cursos.

## Tecnologías Utilizadas

- **FastAPI**: Framework web para APIs REST.
- **SQLModel**: ORM para SQLAlchemy con soporte para Pydantic.
- **SQL Server**: Base de datos relacional.
- **PyODBC**: Driver para conectar a SQL Server.
- **Python-JOSE**: Para codificar/decodificar JWT.
- **Passlib**: Para hashing de contraseñas con bcrypt.
- **Uvicorn**: Servidor ASGI para FastAPI.
- **Python-Dotenv**: Para cargar variables de entorno.
- **Python-Multipart**: Para manejo de archivos en formularios.
- **Aiofiles**: Para operaciones asíncronas con archivos.

## Instalación

1. Clona el repositorio:
   ```bash
   git clone <url-del-repositorio>
   cd BACK-CTT
   ```

2. Crea un entorno virtual:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # En Windows
   ```

3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## Configuración

1. Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:
   ```
   SQL_SERVER=tu_servidor_sql
   SQL_PORT=1433
   SQL_DB=tu_base_de_datos
   SQL_USER=tu_usuario
   SQL_PASSWORD=tu_contraseña
   JWT_SECRET_KEY=tu_clave_secreta_para_jwt
   DEBUG=False
   BACKEND_URL=http://localhost:8000
   ```
   
   **Nota**: Para producción, cambia `BACKEND_URL` a tu dominio real (ej: `https://api.tudominio.com`).

2. Asegúrate de tener SQL Server corriendo y accesible.

## Estructura del Proyecto

```
BACK-CTT/
├── requirements.txt
├── static/
│   └── images/
│       └── courses/                  # Imágenes subidas por usuarios
├── src/
│   ├── main.py                       # Aplicación principal FastAPI
│   ├── config/
│   │   ├── db.py                     # Configuración de la base de datos
│   │   └── logging_config.py         # Configuración de logs
│   ├── controllers/                  # Capa de Servicio (Lógica de Negocio)
│   │   ├── user_controller.py        # Lógica de negocio de usuarios
│   │   ├── course_controller.py      # Lógica de negocio de cursos
│   │   ├── enrollment_controller.py  # Lógica de negocio de inscripciones
│   │   └── image_controller.py       # Lógica de negocio de imágenes
│   ├── repositories/                 # Capa de Datos (Acceso a BD)
│   │   ├── course_repository.py      # Operaciones de base de datos para cursos
│   │   └── enrollment_repository.py  # Operaciones de base de datos para inscripciones
│   ├── dependencies/
│   │   └── db_session.py             # Dependencia de sesión de DB
│   ├── models/
│   │   ├── user.py                   # Modelo de Usuario
│   │   ├── course.py                 # Modelos de Curso y estructuras relacionadas
│   │   └── enrollment.py             # Modelo de Inscripción
│   ├── routes/                       # Capa de Presentación (API REST)
│   │   ├── auth_router.py            # Endpoints de autenticación
│   │   ├── courses_router.py         # Endpoints de cursos
│   │   ├── enrollments_router.py     # Endpoints de inscripciones
│   │   └── images_router.py          # Endpoints de imágenes
│   ├── middleware/
│   │   └── error_handler.py          # Manejo centralizado de errores
│   └── utils/
│       ├── image_utils.py            # Utilidades para manejo de imágenes
│       ├── jwt_utils.py              # Utilidades para JWT
│       ├── serializers/              # Serialización/Deserialización
│       │   ├── general_serializer.py # Serialización de campos JSON
│       │   ├── course_serializer.py  # Serialización de cursos
│       │   └── enrollment_serializer.py  # Serialización de inscripciones
│       ├── Helpers/                  # Funcionalidades Auxiliares
│       │   └── pagination_helper.py  # Helper de paginación
│       └── seeds/
│           ├── user_seed.py          # Seed de datos iniciales de usuarios
│           └── courses_seed.py       # Seed de datos iniciales de cursos
└── README.md
```

## Arquitectura en Capas

El proyecto sigue una **arquitectura en capas limpia** que separa responsabilidades y facilita el mantenimiento:

### 📊 Flujo de Datos

```
Cliente HTTP → Routes → Controllers → Repositories → Database
                  ↓          ↓             ↓
               Schemas   Serializers   SQLModel
```

### 🏗️ Capas de la Aplicación

#### 1. **Capa de Presentación (Routes)**
- **Ubicación**: `src/routes/`
- **Responsabilidad**: Maneja las peticiones HTTP y respuestas
- **Funciones**:
  - Define endpoints y métodos HTTP
  - Valida parámetros de entrada con Pydantic
  - Gestiona autenticación y autorización
  - Llama a los Controllers
- **Archivos**: `auth_router.py`, `courses_router.py`, `images_router.py`

#### 2. **Capa de Servicio (Controllers)**
- **Ubicación**: `src/controllers/`
- **Responsabilidad**: Contiene la lógica de negocio
- **Funciones**:
  - Orquesta operaciones complejas
  - Aplica reglas de negocio
  - Coordina llamadas a múltiples Repositories
  - Maneja transacciones
  - Transforma datos usando Serializers
- **Archivos**: `user_controller.py`, `course_controller.py`, `image_controller.py`

#### 3. **Capa de Datos (Repositories)**
- **Ubicación**: `src/repositories/`
- **Responsabilidad**: Acceso y manipulación de datos en la base de datos
- **Funciones**:
  - Ejecuta queries a la base de datos
  - Operaciones CRUD optimizadas
  - Manejo de relaciones (eager loading)
  - Evita problema N+1
- **Archivos**: `course_repository.py`

#### 4. **Capa de Serialización (Serializers)**
- **Ubicación**: `src/utils/serializers/`
- **Responsabilidad**: Conversión entre formatos de datos
- **Funciones**:
  - Convierte objetos SQLModel a diccionarios
  - Serializa/deserializa campos JSON
  - Estructura datos para respuestas API
- **Archivos**:
  - `general_serializer.py`: Serialización de campos JSON genéricos
  - `course_serializer.py`: Serialización específica de cursos

#### 5. **Capa de Modelos (Models)**
- **Ubicación**: `src/models/`
- **Responsabilidad**: Define la estructura de datos
- **Funciones**:
  - Modelos de base de datos (SQLModel)
  - Schemas de validación (Pydantic)
  - Relaciones entre tablas
- **Archivos**: `user.py`, `course.py`

#### 6. **Utilidades (Utils & Helpers)**
- **Ubicación**: `src/utils/`
- **Responsabilidad**: Funcionalidades auxiliares reutilizables
- **Funciones**:
  - **Helpers**: Paginación, formateo de datos
  - **Utils**: Manejo de JWT, imágenes
  - **Seeds**: Datos iniciales para desarrollo
- **Archivos**: 
  - `Helpers/pagination_helper.py`: Lógica de paginación
  - `image_utils.py`, `jwt_utils.py`

### ✨ Ventajas de esta Arquitectura

1. **Separación de Responsabilidades**: Cada capa tiene un propósito único y bien definido
2. **Mantenibilidad**: Fácil localizar y modificar funcionalidad específica
3. **Testabilidad**: Cada capa se puede testear de forma independiente
4. **Escalabilidad**: Agregar nuevas características sin afectar código existente
5. **Reutilización**: Los Repositories y Serializers pueden ser usados por múltiples Controllers
6. **Performance**: Queries optimizadas con eager loading en Repositories

### 🔄 Ejemplo de Flujo Completo

**Crear un Curso**:

1. **Route** (`courses_router.py`): Recibe `POST /api/v1/courses`
   - Valida datos de entrada con Pydantic
   - Verifica autenticación JWT
   
2. **Controller** (`course_controller.py`): Lógica de negocio
   - Valida reglas de negocio
   - Serializa campos JSON usando `GeneralSerializer`
   
3. **Repository** (`course_repository.py`): Acceso a datos
   - Crea registros en BD (Course, Requirements, Contents)
   - Maneja transacciones
   
4. **Serializer** (`course_serializer.py`): Formatea respuesta
   - Convierte objetos a diccionarios
   - Estructura datos para API
   
5. **Route**: Retorna respuesta HTTP 201 con datos del curso creado

## Uso

### Ejecutar con Docker (Recomendado)

```bash
# Construir y ejecutar los contenedores
docker-compose up --build

# En segundo plano
docker-compose up -d

# Detener los contenedores
docker-compose down
```

La aplicación estará disponible en `http://localhost:8000`.

**Nota**: Las imágenes subidas se guardan en `./static/images/` y persisten entre reinicios.

### Ejecutar la Aplicación (Sin Docker)

```bash
uvicorn src.main:app -p 8000 --reload
```

La aplicación estará disponible en `http://127.0.0.1:8000`.

### Documentación de la API

Visita `http://127.0.0.1:8000/docs` para la documentación interactiva de Swagger.

## Cambios y Mejoras Recientes

### ✅ Refactorización de Arquitectura en Capas (Nuevo)

**Mejora Importante**: Reorganización completa del código siguiendo principios de arquitectura limpia.

**Cambios realizados**:

#### 1. Nueva Capa de Repositorios
- ✅ **Creada carpeta** `src/repositories/`
- ✅ **Archivo**: `course_repository.py` 
- ✅ **Responsabilidad**: Manejo de operaciones de base de datos
- ✅ **Beneficios**: 
  - Queries optimizadas con `selectinload` (evita N+1)
  - Código reutilizable
  - Fácil testeo de acceso a datos

**Funciones movidas**:
```python
# Antes: En CourseController
# Ahora: En CourseRepository
- get_course_with_relations()
- get_courses_paginated()
- create_course_requirements()
- create_course_contents()
- delete_course_contents()
```

#### 2. Nueva Capa de Serializers
- ✅ **Creada carpeta** `src/utils/serializers/`
- ✅ **Archivos**: 
  - `general_serializer.py`: Serialización genérica de JSON
  - `course_serializer.py`: Serialización específica de cursos
- ✅ **Responsabilidad**: Conversión entre objetos y diccionarios
- ✅ **Beneficios**: 
  - Lógica de transformación centralizada
  - Fácil modificar formato de respuestas
  - Separación clara de responsabilidades

**Funciones movidas**:
```python
# Antes: Clase CourseSerializer dentro de course_controller.py
# Ahora: Módulos separados
- GeneralSerializer.serialize_json_field()
- GeneralSerializer.deserialize_json_field()
- CourseSerializer.course_to_dict()
- CourseSerializer._requirements_to_dict()
- CourseSerializer._content_to_dict()
```

#### 3. Nueva Capa de Helpers
- ✅ **Creada carpeta** `src/utils/Helpers/`
- ✅ **Archivo**: `pagination_helper.py`
- ✅ **Responsabilidad**: Lógica de paginación reutilizable
- ✅ **Beneficios**: 
  - Paginación consistente en toda la app
  - Construcción automática de links prev/next
  - Fácil mantener formato de respuesta

**Funciones movidas**:
```python
# Antes: Clase PaginationHelper dentro de course_controller.py
# Ahora: Módulo separado
- PaginationHelper.build_pagination_response()
```

#### 4. Controller Simplificado
- ✅ **Archivo reducido**: De ~450 líneas a ~200 líneas
- ✅ **Enfoque único**: Solo lógica de negocio
- ✅ **Imports limpios**: Utiliza las nuevas capas

**Antes**:
```python
# course_controller.py (450 líneas)
# - Clases CourseSerializer, CourseRepository, PaginationHelper
# - Lógica de negocio
# - Acceso a datos
# - Serialización
```

**Después**:
```python
# course_controller.py (200 líneas)
from src.repositories.course_repository import CourseRepository
from src.utils.serializers.course_serializer import CourseSerializer
from src.utils.serializers.general_serializer import GeneralSerializer
from src.utils.Helpers.pagination_helper import PaginationHelper

# Solo lógica de negocio
```

#### 5. Mejoras de Performance
- ✅ **Eager Loading**: Queries optimizadas usando `selectinload`
- ✅ **Evita N+1**: Carga relaciones en una sola query
- ✅ **Queries eficientes**: Separación entre count y select

**Ejemplo**:
```python
# Repository con eager loading
statement = (
    select(Course)
    .where(Course.id == course_id)
    .options(
        selectinload(Course.requirement),
        selectinload(Course.contents)
    )
)
# Una sola query carga Course + Requirements + Contents
```

### ✅ Sistema de Gestión de Imágenes

**Nueva Funcionalidad**: Sistema completo para subir y gestionar imágenes de cursos.

**Características**:
- ✅ **Subida de imágenes**: Endpoint dedicado para subir imágenes
- ✅ **Almacenamiento local**: Las imágenes se guardan en `static/images/courses/`
- ✅ **Sin dependencias externas**: No requiere servicios de terceros
- ✅ **Validaciones**: Tipo de archivo, tamaño máximo (5MB), extensiones permitidas
- ✅ **Nombres únicos**: Usa UUID para evitar conflictos
- ✅ **Persistencia**: Las imágenes persisten entre reinicios con Docker volumes
- ✅ **Eliminación**: Endpoint para eliminar imágenes del servidor

**Flujo de uso**:
1. El usuario **primero sube la imagen** usando `POST /api/v1/images/upload`
2. El servidor **retorna la URL** de la imagen guardada (ej: `/static/images/courses/uuid.jpg`)
3. El usuario **crea el curso** enviando esa URL en el campo `course_image`

**Extensiones permitidas**: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`

**Ejemplo**:
```javascript
// 1. Subir imagen
const formData = new FormData();
formData.append('file', imageFile);

const response = await fetch('/api/v1/images/upload', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` },
  body: formData
});

const { image_url } = await response.json();
// image_url = "http://localhost:8000/static/images/courses/abc-123.jpg"

// 2. Crear curso con la URL de la imagen
await fetch('/api/v1/courses', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    course: {
      title: "Mi Curso",
      course_image: image_url, // Usar la URL obtenida
      // ...otros campos
    },
    // ...
  })
});
```

### ✅ Cálculo Automático de Horas Totales

**Problema**: El campo `total_hours` se enviaba manualmente y podía no coincidir con la suma de `in_person_hours` + `autonomous_hours`.

**Solución**: Implementé cálculo automático del total de horas:

- ✅ **Eliminé** `total_hours` del input de creación de cursos
- ✅ **Agregué** propiedad calculada en el modelo `CourseRequirement`
- ✅ **Cálculo automático**: `total_hours = in_person_hours + autonomous_hours`
- ✅ **Consistencia garantizada**: El total siempre coincide con la suma de las partes

**Ejemplo de uso**:
```json
{
  "requirements": {
    "in_person_hours": 24,
    "autonomous_hours": 16,
    // total_hours se calcula automáticamente = 40
    ...
  }
}
```

### ✅ Reorganización de Prefijos API

**Problema**: El prefijo `/api` en FastAPI principal no aparecía en la documentación de Swagger.

**Solución**: Moví los prefijos a los routers individuales:

- ✅ **FastAPI principal**: Sin prefijo
- ✅ **Auth Router**: Prefijo `/api/v1/auth`
- ✅ **Courses Router**: Prefijo `/api/v1/courses`

**URLs resultantes**:
- `POST /api/v1/auth/register` - Registro de usuarios
- `GET /api/v1/courses/` - Obtener todos los cursos
- `GET /api/v1/courses/hours-range?min_hours=20&max_hours=50` - Filtrar por horas

### ✅ Nuevos Endpoints para Filtrar por Horas

**Agregué** endpoints especializados para filtrar cursos por horas totales:

#### Filtrar por Horas Exactas
- **GET** `/api/v1/courses/hours/{total_hours}`
- **Descripción**: Obtiene cursos con un total de horas específico
- **Ejemplo**: `GET /api/v1/courses/hours/40`

#### Filtrar por Rango de Horas
- **GET** `/api/v1/courses/hours-range?min_hours=X&max_hours=Y`
- **Descripción**: Obtiene cursos dentro de un rango de horas totales
- **Ejemplo**: `GET /api/v1/courses/hours-range?min_hours=20&max_hours=50`
- **Validaciones**: Parámetros query con validación automática (≥ 1)

### ✅ Optimización de Rutas

**Problema**: Conflictos entre rutas genéricas y específicas.

**Solución**: Reorganicé el orden de las rutas:

1. **Rutas específicas primero**: `/hours-range`, `/hours/{total_hours}`, `/category/{category}`
2. **Rutas genéricas después**: `/{course_id}`

**Resultado**: Las rutas ahora funcionan correctamente sin conflictos.

### ✅ Sistema de Inscripciones (Enrollments)

**Nueva Funcionalidad**: Sistema completo para gestionar inscripciones de usuarios en cursos.

**Características**:
- ✅ **CRUD completo**: Crear, leer, actualizar y anular inscripciones
- ✅ **Sistema de estados**: Seguimiento del proceso de inscripción (Interesado → Pagado → Facturado)
- ✅ **Validaciones de negocio**: Previene inscripciones duplicadas, valida permisos
- ✅ **Gestión de pagos**: Almacena URL de órdenes de pago
- ✅ **Consultas optimizadas**: Queries eficientes con joins para evitar N+1
- ✅ **Seguridad**: Usuarios solo pueden gestionar sus propias inscripciones
- ✅ **Estadísticas**: Reportes de inscripciones por curso y estado
- ✅ **Soft delete**: Las inscripciones anuladas se marcan como "Anulado" sin eliminar datos
- ✅ **Tests completos**: 32 tests (17 controlador + 15 router) con 100% de cobertura

**Estados de inscripción**:
1. **Interesado** - Usuario se inscribió (estado inicial)
2. **Generada la orden** - Se generó orden de pago
3. **Pagado** - Pago completado
4. **Facturado** - Factura emitida
5. **Anulado** - Inscripción cancelada

**Estructura de datos**:
```sql
Table enrollments {
  id int [primary key]
  id_user_platform int [foreign key]
  id_course int [foreign key]
  enrollment_date datetime
  status enum  # Interesado, Generada la orden, Pagado, Facturado, Anulado
  payment_order_url varchar
}
```

**Flujo típico**:
1. Usuario se inscribe en un curso (estado: "Interesado")
2. Sistema genera orden de pago (estado: "Generada la orden")
3. Usuario completa el pago (estado: "Pagado")
4. Administrador emite factura (estado: "Facturado")

**Validaciones implementadas**:
- ✅ Usuario solo puede inscribirse a sí mismo
- ✅ No permite inscripciones duplicadas en el mismo curso
- ✅ Valida existencia de curso y usuario
- ✅ Usuario solo puede ver/modificar sus propias inscripciones
- ✅ Autenticación JWT requerida en todos los endpoints

**Documentación detallada**: Ver `docs/ENROLLMENTS_SERVICE.md` y `docs/ENROLLMENTS_QUICK_START.md` para más información.

### Endpoints

#### Gestión de Imágenes

##### Subir Imagen
- **POST** `/api/v1/images/upload`
- **Descripción**: Sube una imagen al servidor y retorna la URL para usar en cursos
- **Headers**: `Authorization: Bearer <token>` (requiere autenticación)
- **Body**: `multipart/form-data` con campo `file`
- **Validaciones**:
  - Extensiones permitidas: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`
  - Tamaño máximo: 5MB
  - Debe ser una imagen válida
**Respuesta:**
```json
{
  "message": "Imagen subida exitosamente",
  "image_url": "http://localhost:8000/static/images/courses/abc-123.jpg"
}
```

**Nota**: La URL ahora incluye el dominio completo del backend para que funcione correctamente en frontends separados.

##### Eliminar Imagen
- **DELETE** `/api/v1/images/delete?image_url=/static/images/courses/abc-123.jpg`
- **Descripción**: Elimina una imagen del servidor
- **Headers**: `Authorization: Bearer <token>` (requiere autenticación)
- **Query Params**: `image_url` - URL de la imagen a eliminar
- **Respuesta**: `{"message": "Imagen eliminada exitosamente"}`

##### Acceder a Imágenes
- **GET** `/static/images/courses/{filename}`
- **Descripción**: Sirve las imágenes estáticas
- **Ejemplo**: `http://localhost:8000/static/images/courses/abc-123.jpg`
- **Nota**: No requiere autenticación (público)

### Gestión de Categorías

#### Crear Categoría
- **POST** `/api/v1/categories/`
- **Descripción**: Crea una nueva categoría para organizar cursos
- **Headers**: `Authorization: Bearer <token>` (requiere autenticación)
- **Body**:
```json
{
  "name": "Programación",
  "description": "Cursos de desarrollo de software",
  "svgurl": "/static/svg/categories/programming.svg",
  "status": "activo"
}
```
- **Validaciones**:
  - El nombre debe ser único
  - Longitud mínima del nombre: 1 carácter
  - Longitud máxima del nombre: 150 caracteres
  - Descripción máxima: 500 caracteres
- **Respuesta**:
```json
{
  "id": 1,
  "name": "Programación",
  "description": "Cursos de desarrollo de software",
  "svgurl": "/static/svg/categories/programming.svg",
  "status": "activo",
  "created_at": "2025-01-19T10:30:00",
  "updated_at": "2025-01-19T10:30:00",
  "created_by": 1
}
```

#### Obtener Categorías Activas (Público)
- **GET** `/api/v1/categories/enabled`
- **Descripción**: Obtiene todas las categorías en estado activo (endpoint público para frontend)
- **No requiere autenticación**
- **Respuesta**:
```json
[
  {
    "id": 1,
    "name": "TICS",
    "description": "Tecnologías de la información y comunicación",
    "svgurl": "/static/svg/categories/tics.svg",
    "status": "activo"
  },
  {
    "id": 2,
    "name": "Electrónica",
    "description": "Cursos de electrónica y hardware",
    "svgurl": "/static/svg/categories/electronics.svg",
    "status": "activo"
  }
]
```

#### Listar Todas las Categorías (Paginado)
- **GET** `/api/v1/categories/?page=1&page_size=10`
- **Descripción**: Obtiene todas las categorías con paginación y filtros
- **Headers**: `Authorization: Bearer <token>` (requiere autenticación)
- **Query Params**:
  - `page` (default: 1) - Número de página
  - `page_size` (default: 10) - Tamaño de página
  - `status_filter` (opcional) - Filtrar por estado (`activo` o `inactivo`)
  - `include_inactive` (default: false) - Incluir categorías inactivas
- **Ejemplos**:
  - `GET /api/v1/categories/` - Primera página con categorías activas
  - `GET /api/v1/categories/?page=2&page_size=20` - Segunda página con 20 items
  - `GET /api/v1/categories/?status_filter=activo` - Solo categorías activas
  - `GET /api/v1/categories/?include_inactive=true` - Incluir inactivas
- **Respuesta**:
```json
{
  "items": [
    {
      "id": 1,
      "name": "TICS",
      "description": "Tecnologías de la información y comunicación",
      "svgurl": "/static/svg/categories/tics.svg",
      "status": "activo",
      "created_at": "2025-01-15T08:00:00",
      "updated_at": "2025-01-15T08:00:00",
      "created_by": 1
    }
  ],
  "total": 15,
  "page": 1,
  "page_size": 10,
  "total_pages": 2,
  "has_next": true,
  "has_prev": false,
  "next_page": "http://localhost:8000/api/v1/categories/?page=2&page_size=10",
  "prev_page": null
}
```

#### Obtener Categoría por ID
- **GET** `/api/v1/categories/{category_id}`
- **Descripción**: Obtiene una categoría específica por su ID
- **No requiere autenticación**
- **Ejemplo**: `GET /api/v1/categories/1`
- **Respuesta**:
```json
{
  "id": 1,
  "name": "TICS",
  "description": "Tecnologías de la información y comunicación",
  "svgurl": "/static/svg/categories/tics.svg",
  "status": "activo",
  "created_at": "2025-01-15T08:00:00",
  "updated_at": "2025-01-15T08:00:00",
  "created_by": 1
}
```
- **Error 404**: Si la categoría no existe

#### Obtener Categoría por Nombre
- **GET** `/api/v1/categories/by-name/{name}`
- **Descripción**: Busca una categoría por su nombre exacto
- **No requiere autenticación**
- **Ejemplo**: `GET /api/v1/categories/by-name/TICS`
- **Respuesta**:
```json
{
  "id": 1,
  "name": "TICS",
  "description": "Tecnologías de la información y comunicación",
  "svgurl": "/static/svg/categories/tics.svg",
  "status": "activo",
  "created_at": "2025-01-15T08:00:00",
  "updated_at": "2025-01-15T08:00:00",
  "created_by": 1
}
```
- **Error 404**: Si no existe una categoría con ese nombre

#### Actualizar Categoría
- **PUT** `/api/v1/categories/{category_id}`
- **Descripción**: Actualiza los datos de una categoría existente
- **Headers**: `Authorization: Bearer <token>` (requiere autenticación)
- **Body**: Todos los campos son opcionales
```json
{
  "name": "Tecnologías de la Información",
  "description": "Cursos de TICS y computación",
  "svgurl": "/static/svg/categories/tics-updated.svg",
  "status": "inactivo"
}
```
- **Validaciones**:
  - Solo se actualizan los campos proporcionados
  - El nombre debe ser único si se modifica
- **Respuesta**:
```json
{
  "id": 1,
  "name": "Tecnologías de la Información",
  "description": "Cursos de TICS y computación",
  "svgurl": "/static/svg/categories/tics-updated.svg",
  "status": "inactivo",
  "created_at": "2025-01-15T08:00:00",
  "updated_at": "2025-01-19T14:20:00",
  "created_by": 1
}
```
- **Error 404**: Si la categoría no existe

#### Eliminar Categoría (Soft Delete)
- **DELETE** `/api/v1/categories/{category_id}`
- **Descripción**: Desactiva una categoría (soft delete - cambia estado a "inactivo")
- **Headers**: `Authorization: Bearer <token>` (requiere autenticación)
- **Comportamiento**:
  - Si la categoría tiene cursos asociados, solo cambia el estado a "inactivo"
  - La categoría permanece en la base de datos para mantener integridad referencial
  - Los cursos asociados no se ven afectados
- **Respuesta**: Status 204 No Content (sin body)
- **Error 404**: Si la categoría no existe

#### Estados de Categorías

Las categorías pueden tener dos estados:
- **`activo`**: La categoría está disponible y visible en el sistema
- **`inactivo`**: La categoría fue desactivada (soft delete) pero permanece en BD

#### Autenticación

#### Registro de Usuario
- **POST** `/api/v1/auth/register`
- Descripción: Registra un nuevo usuario.
- Body: JSON con `name`, `last_name`, `email`, `password`.
- Respuesta: Mensaje de éxito o error.

#### Login
- **POST** `/api/v1/auth/token`
- Descripción: Inicia sesión y obtiene un token JWT.
- Body: Form data con `username` (email) y `password`.
- Respuesta: `{"access_token": "token", "token_type": "bearer"}`

#### Perfil de Usuario
- **GET** `/api/v1/auth/profile`
- Descripción: Obtiene el perfil del usuario autenticado.
- Headers: `Authorization: Bearer <token>`
- Respuesta: JSON con `id`, `name`, `last_name`, `email`.

### Gestión de Cursos

#### Crear Curso
- **POST** `/api/v1/courses/`
- Descripción: Crea un nuevo curso con toda su información (requisitos, contenidos, etc.)
- **Headers**: `Authorization: Bearer <token>` (requiere autenticación)
- Body: JSON con `course`, `requirements`, y `contents`
- **Nota**: `total_hours` se calcula automáticamente como `in_person_hours + autonomous_hours`
- Respuesta: `{"message": "Course created successfully", "course_id": 1}`

#### Obtener Todos los Cursos
- **GET** `/api/v1/courses/`
- Descripción: Obtiene todos los cursos con información completa
- **Headers**: `Authorization: Bearer <token>` (requiere autenticación)
- Respuesta: Lista de cursos con datos completos (requirements, contents, topics, etc.)

#### Obtener Curso Específico
- **GET** `/api/v1/courses/{course_id}`
- Descripción: Obtiene un curso específico con toda su información detallada
- **Headers**: `Authorization: Bearer <token>` (requiere autenticación)
- Respuesta: Datos completos del curso incluyendo requisitos y contenidos

#### Filtrar Cursos por Categoría
- **GET** `/api/v1/courses/category/{category}`
- Descripción: Obtiene cursos filtrados por categoría
- **Headers**: `Authorization: Bearer <token>` (requiere autenticación)
- Ejemplo: `GET /api/v1/courses/category/Software`

#### Filtrar Cursos por Horas Exactas
- **GET** `/api/v1/courses/hours/{total_hours}`
- Descripción: Obtiene cursos con un total de horas específico
- **Headers**: `Authorization: Bearer <token>` (requiere autenticación)
- Ejemplo: `GET /api/v1/courses/hours/40`

#### Filtrar Cursos por Rango de Horas
- **GET** `/api/v1/courses/hours-range?min_hours=X&max_hours=Y`
- Descripción: Obtiene cursos dentro de un rango de horas totales
- **Headers**: `Authorization: Bearer <token>` (requiere autenticación)
- Validaciones: Los parámetros deben ser ≥ 1 y min_hours ≤ max_hours
- Ejemplo: `GET /api/v1/courses/hours-range?min_hours=20&max_hours=50`

### Gestión de Inscripciones

#### Crear Inscripción
- **POST** `/api/v1/enrollments/`
- **Descripción**: Permite a un usuario inscribirse en un curso
- **Headers**: `Authorization: Bearer <platform_token>` (requiere autenticación de usuario de plataforma)
- **Body**: JSON con `id_user_platform`, `id_course`, `status` (opcional), `payment_order_url` (opcional)
- **Validaciones**:
  - Usuario solo puede inscribirse a sí mismo
  - No permite inscripciones duplicadas
  - Valida existencia de curso y usuario
- **Respuesta**:
```json
{
  "message": "Inscripción creada exitosamente",
  "enrollment_id": 1,
  "data": {
    "id": 1,
    "id_user_platform": 1,
    "id_course": 5,
    "enrollment_date": "2025-10-28T10:30:00",
    "status": "Interesado",
    "payment_order_url": null
  }
}
```

#### Obtener Inscripción por ID
- **GET** `/api/v1/enrollments/{enrollment_id}`
- **Descripción**: Obtiene los detalles de una inscripción específica
- **Headers**: `Authorization: Bearer <platform_token>`
- **Validación**: Usuario solo puede ver sus propias inscripciones
- **Respuesta**: Datos de la inscripción incluyendo información del usuario y curso

#### Actualizar Inscripción
- **PUT** `/api/v1/enrollments/{enrollment_id}`
- **Descripción**: Actualiza el estado o la URL de pago de una inscripción
- **Headers**: `Authorization: Bearer <platform_token>`
- **Body**: JSON con `status` y/o `payment_order_url`
- **Ejemplo**:
```json
{
  "status": "Pagado",
  "payment_order_url": "https://payment.example.com/order123"
}
```

#### Anular Inscripción
- **DELETE** `/api/v1/enrollments/{enrollment_id}`
- **Descripción**: Anula una inscripción (soft delete - cambia estado a "Anulado")
- **Headers**: `Authorization: Bearer <platform_token>`
- **Validación**: Usuario solo puede anular sus propias inscripciones
- **Respuesta**: `{"message": "Inscripción {id} anulada exitosamente"}`

#### Obtener Inscripciones por Usuario
- **GET** `/api/v1/enrollments/user/{user_id}`
- **Descripción**: Obtiene todas las inscripciones de un usuario con detalles de los cursos
- **Headers**: `Authorization: Bearer <platform_token>`
- **Query Params**: `enrollment_status` (opcional) - Filtrar por estado
- **Validación**: Usuario solo puede ver sus propias inscripciones
- **Ejemplo**: `GET /api/v1/enrollments/user/1?enrollment_status=Pagado`

#### Obtener Inscripciones por Curso
- **GET** `/api/v1/enrollments/course/{course_id}`
- **Descripción**: Obtiene todas las inscripciones de un curso con detalles de los usuarios
- **Headers**: `Authorization: Bearer <platform_token>`
- **Query Params**: `enrollment_status` (opcional) - Filtrar por estado
- **Nota**: Este endpoint debería estar restringido a administradores

#### Listar Inscripciones Paginadas
- **GET** `/api/v1/enrollments/?page=1&page_size=10`
- **Descripción**: Obtiene un listado paginado de inscripciones del usuario autenticado
- **Headers**: `Authorization: Bearer <platform_token>`
- **Query Params**:
  - `page` (default: 1) - Número de página
  - `page_size` (default: 10, max: 100) - Tamaño de página
  - `enrollment_status` (opcional) - Filtrar por estado
  - `course_id` (opcional) - Filtrar por curso
- **Respuesta**: Lista paginada con metadata de paginación

#### Obtener Estadísticas por Curso
- **GET** `/api/v1/enrollments/stats/course/{course_id}`
- **Descripción**: Obtiene estadísticas de inscripciones de un curso agrupadas por estado
- **Headers**: `Authorization: Bearer <platform_token>`
- **Respuesta**:
```json
{
  "course_id": 5,
  "course_title": "Curso de Python",
  "total_inscriptions": 25,
  "by_status": {
    "Interesado": 10,
    "Generada la orden": 5,
    "Pagado": 8,
    "Facturado": 2,
    "Anulado": 0
  }
}
```

### Seed de Datos

Al iniciar la aplicación, se ejecutan automáticamente seeds que crean datos de prueba:

#### Usuario de Prueba
- Email: `daniel.jerez@example.com`
- Password: `securepassword`

#### Curso de Prueba
Se crea automáticamente un curso de Arduino con toda la información:
- **Título**: "Arduino desde cero: Electrónica, Programación y Automatización"
- **Incluye**: Requisitos completos, horarios, precios, contenidos y topics
- **Datos**: Basado en el archivo `courses.json` del proyecto

## Desarrollo

- Las tablas se crean automáticamente al iniciar la aplicación.
- El directorio para imágenes se crea automáticamente al iniciar.
- Para debugging, establece `DEBUG=True` en el `.env`.
- **Endpoints de autenticación**: Bajo el prefijo `/api/v1/auth`
- **Endpoints de cursos**: Bajo el prefijo `/api/v1/courses` (requieren autenticación JWT)
- **Endpoints de imágenes**: Bajo el prefijo `/api/v1/images` (requieren autenticación JWT)
- Los cursos incluyen información estructurada compleja: requisitos, contenidos, topics, precios, horarios, etc.
- Los datos se almacenan de forma eficiente usando JSON en la base de datos para campos complejos.
- Los endpoints POST de cursos e imágenes requieren token de autenticación válido.
- Los cursos incluyen campos de categoría y estado para mejor organización.
- Las imágenes se almacenan localmente en `static/images/courses/` con nombres únicos (UUID).
- Las imágenes persisten entre reinicios usando Docker volumes.

### Estructura de Datos para Crear Cursos

Para crear un curso, el body debe incluir tres objetos principales:

#### course
```json
{
  "title": "string",
  "description": "string",
  "place": "string",
  "course_image": "/static/images/courses/uuid.jpg",  // URL obtenida de POST /api/v1/images/upload
  "category": "TICS",
  "status": "Activo",
  "objectives": ["string1", "string2"],
  "organizers": ["string1", "string2"],
  "materials": ["string1", "string2"],
  "target_audience": ["string1", "string2"]
}
```

**Nota sobre course_image**: 
- Primero debes subir la imagen usando `POST /api/v1/images/upload`
- Luego usar la URL retornada en este campo
- Ejemplo de URL: `http://localhost:8000/static/images/courses/abc-123.jpg`
- La URL incluye el dominio completo para compatibilidad con frontends separados

#### requirements
```json
{
  "start_date_registration": "2025-05-19",
  "end_date_registration": "2025-06-04",
  "start_date_course": "2025-06-07",
  "end_date_course": "2025-06-30",
  "days": ["Sábado"],
  "start_time": "08:00:00",
  "end_time": "14:00:00",
  "location": "string",
  "min_quota": 15,
  "max_quota": 25,
  "in_person_hours": 24,
  "autonomous_hours": 16,
  "modality": "string",
  "certification": "string",
  "prerequisites": ["string1", "string2"],
  "prices": [
    {"amount": 40, "category": "Estudiantes"},
    {"amount": 50, "category": "Profesionales"}
  ]
}
```
**Nota**: `total_hours` se calcula automáticamente como `in_person_hours + autonomous_hours` (24 + 16 = 40)

#### contents
```json
[
  {
    "unit": "Módulo 1",
    "title": "Título del módulo",
    "topics": [
      {"unit": "Capítulo 1", "title": "Título del capítulo"},
      {"unit": "Capítulo 2", "title": "Título del capítulo"}
    ]
  }
]
```
## Licencia

Este proyecto está bajo la Licencia MIT.