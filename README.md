# BACK-CTT

Una aplicación de gestión de usuarios y cursos construida con FastAPI, SQLModel y SQL Server.

## Descripción

Este proyecto implementa un sistema completo que incluye:
- **Autenticación de usuarios**: Registro, login y obtención de perfil con JWT
- **Gestión de cursos**: Creación, consulta y administración de cursos con información completa
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
   ```

2. Asegúrate de tener SQL Server corriendo y accesible.

## Estructura del Proyecto

```
BACK-CTT/
├── requirements.txt
├── src/
│   ├── main.py                 # Aplicación principal FastAPI
│   ├── config/
│   │   └── db.py               # Configuración de la base de datos
│   ├── controllers/
│   │   ├── user_controller.py  # Controlador para usuarios
│   │   └── course_controller.py # Controlador para cursos
│   ├── dependencies/
│   │   └── db_session.py       # Dependencia de sesión de DB
│   ├── models/
│   │   ├── user.py             # Modelo de Usuario
│   │   └── course.py            # Modelos de Curso y estructuras relacionadas
│   ├── routes/
│   │   ├── auth_router.py      # Endpoints de autenticación
│   │   └── courses_router.py    # Endpoints de cursos
│   └── utils/
│       └── seeds/
│           ├── user_seed.py     # Seed de datos iniciales de usuarios
│           └── courses_seed.py  # Seed de datos iniciales de cursos
└── README.md
```

## Uso

### Ejecutar la Aplicación

```bash
uvicorn src.main:app -p 8000 --reload
```

La aplicación estará disponible en `http://127.0.0.1:8000`.

### Documentación de la API

Visita `http://127.0.0.1:8000/docs` para la documentación interactiva de Swagger.

## Cambios y Mejoras Recientes

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
  "requirements_data": {
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

### Endpoints

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
- Body: JSON con `course_data`, `requirements_data`, y `contents_data`
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
- Para debugging, establece `DEBUG=True` en el `.env`.
- **Endpoints de autenticación**: Bajo el prefijo `/api/v1/auth`
- **Endpoints de cursos**: Bajo el prefijo `/api/v1/courses` (requieren autenticación JWT)
- Los cursos incluyen información estructurada compleja: requisitos, contenidos, topics, precios, horarios, etc.
- Los datos se almacenan de forma eficiente usando JSON en la base de datos para campos complejos.
- El endpoints POST de cursos requieren token de autenticación válido.
- Los cursos incluyen campos de categoría y estado para mejor organización.

### Estructura de Datos para Crear Cursos

Para crear un curso, el body debe incluir tres objetos principales:

#### course_data
```json
{
  "title": "string",
  "description": "string",
  "place": "string",
  "course_image": "https://example.com/image.png",
  "category": "TICS",
  "status": "Activo",
  "objectives": ["string1", "string2"],
  "organizers": ["string1", "string2"],
  "materials": ["string1", "string2"],
  "target_audience": ["string1", "string2"]
}
```

#### requirements_data
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

#### contents_data
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

## Contribución

1. Fork el proyecto.
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`).
3. Commit tus cambios (`git commit -am 'Agrega nueva funcionalidad'`).
4. Push a la rama (`git push origin feature/nueva-funcionalidad`).
5. Abre un Pull Request.

## Licencia

Este proyecto está bajo la Licencia MIT.