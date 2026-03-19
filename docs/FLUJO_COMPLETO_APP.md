# 📘 Guía Completa: Flujo de la Aplicación CTT-BACK

## 📋 Tabla de Contenidos

1. [Estructura de Directorios del Proyecto](#1-estructura-de-directorios-del-proyecto)
2. [Activación del Entorno Virtual](#2-activación-del-entorno-virtual)
3. [Configuración de Variables de Entorno](#3-configuración-de-variables-de-entorno)
4. [Inicialización de la Base de Datos](#4-inicialización-de-la-base-de-datos)
5. [Sistema de Semillas (Seeds)](#5-sistema-de-semillas-seeds)
6. [Ejecución de la Aplicación](#6-ejecución-de-la-aplicación)
7. [Modificar Enums de Estados](#7-modificar-enums-de-estados)
8. [Añadir Nuevos Campos a la Base de Datos](#8-añadir-nuevos-campos-a-la-base-de-datos)
9. [Migración de Datos](#9-migración-de-datos)
10. [Añadir Nuevas Funcionalidades](#10-añadir-nuevas-funcionalidades)

---

## � 1. Estructura de Directorios del Proyecto

### Vista General del Proyecto

```
CTT-BACK/
├── src/                      # ⭐ Código fuente principal
│   ├── config/              # Configuración de la app
│   ├── controllers/         # Lógica de negocio
│   ├── dependencies/        # Dependencias FastAPI
│   ├── middleware/          # Middleware personalizado
│   ├── models/              # Modelos de base de datos (SQLModel)
│   ├── repositories/        # Acceso a datos (queries)
│   ├── routes/              # Endpoints de la API
│   ├── utils/               # Utilidades y helpers
│   │   ├── Helpers/         # Funciones auxiliares
│   │   ├── seeds/           # Datos de prueba
│   │   └── serializers/     # Transformación de datos
│   └── main.py              # Punto de entrada de la app
├── tests/                   # Tests unitarios e integración
├── static/                  # Archivos estáticos (imágenes)
├── logs/                    # Logs de la aplicación
├── docs/                    # Documentación
├── venv/                    # Entorno virtual (NO subir a Git)
├── .env                     # Variables de entorno (NO subir a Git)
├── requirements.txt         # Dependencias Python
└── docker-compose.yml       # Configuración Docker
```

---

### 📂 `src/config/` - Configuración de la Aplicación

**Propósito**: Centraliza toda la configuración de la aplicación (BD, logging, etc.)

#### Archivos existentes:

##### `db.py` - Configuración de Base de Datos

```python
from sqlmodel import create_engine
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = f"mssql+pyodbc://{SQL_USER}:{SQL_PASSWORD}@{SQL_SERVER}..."
engine = create_engine(DATABASE_URL, echo=DEBUG)
```

**¿Cuándo modificar?**
- Cambiar tipo de base de datos (PostgreSQL, MySQL, etc.)
- Ajustar parámetros de conexión
- Configurar pool de conexiones

##### `logging_config.py` - Configuración de Logs

```python
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/app.log'),
            logging.StreamHandler()
        ]
    )
```

**¿Cuándo modificar?**
- Cambiar nivel de logging (DEBUG, INFO, WARNING, ERROR)
- Añadir nuevos handlers (archivos, Sentry, etc.)
- Modificar formato de logs

#### ✅ Añadir nueva configuración

**Ejemplo**: Añadir configuración de email

```python
# src/config/email.py
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_FROM = os.getenv("EMAIL_FROM", "noreply@ctt.edu.ec")
```

Luego añadir en `.env`:
```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=tu_email@gmail.com
EMAIL_PASSWORD=tu_password
EMAIL_FROM=noreply@ctt.edu.ec
```

---

### 🗂️ `src/models/` - Modelos de Base de Datos

**Propósito**: Define la estructura de las tablas y los esquemas de validación

#### Estructura de un modelo completo:

```python
# src/models/ejemplo.py
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from enum import Enum
from datetime import datetime

# 1. ENUM (Estados)
class StatusEnum(str, Enum):
    ACTIVO = "activo"
    INACTIVO = "inactivo"

# 2. MODELO DE TABLA (Base de datos)
class Ejemplo(SQLModel, table=True):
    __tablename__ = "ejemplos"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=100)
    status: StatusEnum = Field(default=StatusEnum.ACTIVO)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relaciones
    items: List["EjemploItem"] = Relationship(back_populates="ejemplo")

# 3. MODELO DE CREACIÓN (Request)
class EjemploCreate(SQLModel):
    nombre: str = Field(max_length=100)
    status: StatusEnum = StatusEnum.ACTIVO

# 4. MODELO DE ACTUALIZACIÓN (Request)
class EjemploUpdate(SQLModel):
    nombre: Optional[str] = None
    status: Optional[StatusEnum] = None

# 5. MODELO DE RESPUESTA (Response)
class EjemploResponse(SQLModel):
    id: int
    nombre: str
    status: StatusEnum
    created_at: datetime
```

#### ✅ Añadir un nuevo modelo

**Paso 1**: Crear archivo en `src/models/`

```python
# src/models/notification.py
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class NotificationType(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"

class Notification(SQLModel, table=True):
    __tablename__ = "notifications"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users_platform.id")
    type: NotificationType
    title: str = Field(max_length=200)
    message: str
    is_read: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class NotificationCreate(SQLModel):
    user_id: int
    type: NotificationType
    title: str
    message: str

class NotificationResponse(SQLModel):
    id: int
    user_id: int
    type: NotificationType
    title: str
    message: str
    is_read: bool
    created_at: datetime
```

**Paso 2**: Importar en `main.py` para crear la tabla

```python
# src/main.py
from src.models.notification import Notification  # ✅ Añadir esta línea

SQLModel.metadata.create_all(engine)
```

---

### 🎯 `src/controllers/` - Lógica de Negocio

**Propósito**: Contiene la lógica de negocio y orquesta las operaciones

#### Responsabilidades:

✅ Validar datos de negocio  
✅ Orquestar múltiples operaciones  
✅ Manejar transacciones  
✅ Transformar datos entre capas  
❌ NO hacer queries directas (usar repositories)  
❌ NO manejar request/response (usar routes)  

#### Ejemplo: `course_controller.py`

```python
class CourseController:
    @staticmethod
    def create_course_with_details(
        session: Session,
        course_data: CourseCreate,
        requirements_data: CourseRequirementCreate,
        contents_data: List[CourseContentCreate]
    ) -> dict:
        """Crea un curso completo con todos sus detalles"""
        
        # 1. Validaciones de negocio
        if requirements_data.max_quota < requirements_data.min_quota:
            raise ValueError("max_quota debe ser >= min_quota")
        
        # 2. Usar repository para crear el curso
        course = CourseRepository.create_course(session, course_data)
        
        # 3. Crear relaciones
        requirements = CourseRepository.create_requirements(
            session, course.id, requirements_data
        )
        
        # 4. Crear contenidos
        for content_data in contents_data:
            CourseRepository.create_content(session, course.id, content_data)
        
        # 5. Serializar respuesta
        return CourseSerializer.course_to_dict(course, requirements, contents)
```

#### ✅ Añadir nuevo controlador

```python
# src/controllers/notification_controller.py
from sqlmodel import Session
from src.models.notification import Notification, NotificationCreate
from src.repositories.notification_repository import NotificationRepository

class NotificationController:
    @staticmethod
    def send_notification(
        session: Session,
        notification_data: NotificationCreate
    ) -> Notification:
        """Envía una notificación a un usuario"""
        
        # 1. Validar que el usuario existe
        from src.repositories.user_platform_repository import UserPlatformRepository
        user = UserPlatformRepository.get_by_id(session, notification_data.user_id)
        if not user:
            raise ValueError("Usuario no encontrado")
        
        # 2. Crear notificación
        notification = NotificationRepository.create(session, notification_data)
        
        # 3. Enviar según el tipo (email, SMS, push)
        if notification.type == "email":
            # Lógica de envío de email
            pass
        
        return notification
```

---

### 🗄️ `src/repositories/` - Acceso a Datos

**Propósito**: Capa de acceso a datos (queries a la BD)

#### Responsabilidades:

✅ Ejecutar queries SQL/ORM  
✅ Cargar relaciones (eager/lazy loading)  
✅ Paginación de datos  
✅ Filtros y búsquedas  
❌ NO contener lógica de negocio  
❌ NO validar datos de negocio  

#### Ejemplo: `course_repository.py`

```python
class CourseRepository:
    @staticmethod
    def get_course_with_relations(course_id: int, db: Session) -> Optional[Course]:
        """Obtiene un curso con todas sus relaciones"""
        statement = (
            select(Course)
            .where(Course.id == course_id)
            .options(
                selectinload(Course.requirement),  # Evita N+1
                selectinload(Course.contents)
            )
        )
        return db.exec(statement).first()
    
    @staticmethod
    def get_courses_paginated(
        db: Session,
        page: int,
        page_size: int,
        status: CourseStatus
    ):
        """Obtiene cursos paginados"""
        offset = (page - 1) * page_size
        
        statement = (
            select(Course)
            .where(Course.status == status)
            .offset(offset)
            .limit(page_size)
        )
        
        courses = db.exec(statement).all()
        total = db.exec(select(func.count(Course.id)).where(Course.status == status)).one()
        
        return courses, total
```

#### ✅ Añadir nuevo repository

```python
# src/repositories/notification_repository.py
from sqlmodel import Session, select
from typing import List, Optional
from src.models.notification import Notification, NotificationCreate

class NotificationRepository:
    @staticmethod
    def create(session: Session, data: NotificationCreate) -> Notification:
        """Crea una notificación"""
        notification = Notification(**data.model_dump())
        session.add(notification)
        session.commit()
        session.refresh(notification)
        return notification
    
    @staticmethod
    def get_by_user(session: Session, user_id: int) -> List[Notification]:
        """Obtiene todas las notificaciones de un usuario"""
        statement = select(Notification).where(Notification.user_id == user_id)
        return session.exec(statement).all()
    
    @staticmethod
    def mark_as_read(session: Session, notification_id: int) -> Optional[Notification]:
        """Marca una notificación como leída"""
        notification = session.get(Notification, notification_id)
        if notification:
            notification.is_read = True
            session.add(notification)
            session.commit()
            session.refresh(notification)
        return notification
```

---

### 🛣️ `src/routes/` - Endpoints de la API

**Propósito**: Define los endpoints y maneja HTTP request/response

#### Responsabilidades:

✅ Definir rutas y métodos HTTP  
✅ Validar parámetros de request  
✅ Manejar autenticación/autorización  
✅ Formatear respuestas HTTP  
✅ Manejar errores HTTP  
❌ NO contener lógica de negocio (usar controllers)  

#### Ejemplo: `courses_router.py`

```python
from fastapi import APIRouter, HTTPException, Depends, Query
from src.controllers.course_controller import CourseController
from src.dependencies.db_session import SessionDep
from src.models.course import CourseCreate, CourseResponse

courses_router = APIRouter(prefix="/api/v1/courses", tags=["courses"])

@courses_router.post("/", response_model=CourseResponse, status_code=201)
def create_course(
    request: CourseCreateRequest,
    session: SessionDep  # Dependency injection
):
    """Crea un nuevo curso"""
    try:
        result = CourseController.create_course_with_details(
            session,
            request.course,
            request.requirements,
            request.contents
        )
        return {"message": "Curso creado", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno")

@courses_router.get("/{course_id}")
def get_course(course_id: int, session: SessionDep):
    """Obtiene un curso por ID"""
    course = CourseController.get_course_by_id(session, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    return course
```

#### ✅ Añadir nuevo router

```python
# src/routes/notifications_router.py
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from src.controllers.notification_controller import NotificationController
from src.dependencies.db_session import SessionDep
from src.models.notification import NotificationCreate, NotificationResponse

notifications_router = APIRouter(
    prefix="/api/v1/notifications",
    tags=["notifications"]
)

@notifications_router.post("/", response_model=NotificationResponse, status_code=201)
def send_notification(
    notification: NotificationCreate,
    session: SessionDep
):
    """Envía una notificación"""
    try:
        result = NotificationController.send_notification(session, notification)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@notifications_router.get("/user/{user_id}", response_model=List[NotificationResponse])
def get_user_notifications(user_id: int, session: SessionDep):
    """Obtiene notificaciones de un usuario"""
    notifications = NotificationController.get_user_notifications(session, user_id)
    return notifications

@notifications_router.patch("/{notification_id}/read")
def mark_notification_read(notification_id: int, session: SessionDep):
    """Marca una notificación como leída"""
    notification = NotificationController.mark_as_read(session, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    return {"message": "Notificación marcada como leída"}
```

**Paso 2**: Registrar router en `main.py`

```python
# src/main.py
from src.routes.notifications_router import notifications_router

app.include_router(notifications_router)  # ✅ Añadir esta línea
```

---

### 🔧 `src/utils/` - Utilidades

#### Subcarpetas:

##### `serializers/` - Transformación de Datos

**Propósito**: Convertir modelos de BD a diccionarios/JSON y viceversa

```python
# src/utils/serializers/notification_serializer.py
from src.models.notification import Notification

class NotificationSerializer:
    @staticmethod
    def to_dict(notification: Notification) -> dict:
        """Convierte Notification a diccionario"""
        return {
            "id": notification.id,
            "user_id": notification.user_id,
            "type": notification.type.value,
            "title": notification.title,
            "message": notification.message,
            "is_read": notification.is_read,
            "created_at": notification.created_at.isoformat()
        }
```

##### `Helpers/` - Funciones Auxiliares

**Propósito**: Funciones reutilizables

Ejemplo: `pagination_helper.py` para paginación

```python
class PaginationHelper:
    @staticmethod
    def build_pagination_response(
        items: List[Any],
        total: int,
        page: int,
        page_size: int
    ) -> Dict:
        """Construye respuesta paginada estándar"""
        total_pages = (total + page_size - 1) // page_size
        return {
            "total": total,
            "total_pages": total_pages,
            "page": page,
            "page_size": page_size,
            "items": items
        }
```

##### `seeds/` - Datos de Prueba

Ver sección [4. Sistema de Semillas](#4-sistema-de-semillas-seeds)

##### Otros archivos comunes:

- `jwt_utils.py` - Manejo de tokens JWT
- `image_utils.py` - Procesamiento de imágenes
- `email_utils.py` - Envío de emails

---

### 🛡️ `src/middleware/` - Middleware Personalizado

**Propósito**: Intercepta requests/responses para procesamiento global

#### Ejemplo: `error_handler.py`

```python
async def error_handler_middleware(request: Request, call_next):
    """Maneja errores globalmente"""
    try:
        response = await call_next(request)
        return response
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Database Error", "message": "Error de BD"}
        )
```

#### ✅ Añadir nuevo middleware

```python
# src/middleware/request_logger.py
import time
import logging
from fastapi import Request

logger = logging.getLogger(__name__)

async def request_logger_middleware(request: Request, call_next):
    """Registra todas las peticiones HTTP"""
    start_time = time.time()
    
    # Log de request
    logger.info(f"Request: {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    # Log de response con tiempo
    duration = time.time() - start_time
    logger.info(
        f"Response: {response.status_code} | "
        f"Duration: {duration:.2f}s | "
        f"Path: {request.url.path}"
    )
    
    return response
```

**Registrar en `main.py`:**

```python
from src.middleware.request_logger import request_logger_middleware

app.middleware("http")(request_logger_middleware)
```

---

### 📦 `src/dependencies/` - Dependencias FastAPI

**Propósito**: Dependency Injection para reutilizar código

#### Ejemplo: `db_session.py`

```python
from fastapi import Depends
from sqlmodel import Session
from src.config.db import engine

def get_db():
    """Proporciona sesión de BD a los endpoints"""
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_db)]
```

#### ✅ Añadir nueva dependencia

```python
# src/dependencies/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.utils.jwt_utils import decode_token
from src.models.user import User
from src.dependencies.db_session import SessionDep

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: SessionDep = Depends()
) -> User:
    """Obtiene el usuario autenticado desde el token JWT"""
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )
    
    user_id = payload.get("sub")
    user = session.get(User, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    return user

# Uso en routes:
@router.get("/profile")
def get_profile(current_user: User = Depends(get current_user)):
    return current_user
```

---

### 🧪 `tests/` - Tests

**Propósito**: Tests unitarios e integración

#### Estructura recomendada:

```
tests/
├── test_controllers/
│   ├── test_course_controller.py
│   └── test_notification_controller.py
├── test_routes/
│   ├── test_courses_router.py
│   └── test_notifications_router.py
├── conftest.py          # Fixtures compartidos
└── README.md            # Guía de testing
```

#### Ejemplo de test:

```python
# tests/test_routes/test_notifications_router.py
import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_send_notification():
    """Test de envío de notificación"""
    notification_data = {
        "user_id": 1,
        "type": "email",
        "title": "Test",
        "message": "Mensaje de prueba"
    }
    
    response = client.post("/api/v1/notifications/", json=notification_data)
    
    assert response.status_code == 201
    assert response.json()["title"] == "Test"
```

---

### 📄 `static/` - Archivos Estáticos

**Propósito**: Almacenar imágenes, archivos subidos por usuarios

```
static/
└── images/
    └── courses/
        ├── course-1.jpg
        ├── course-2.png
        └── .gitkeep
```

#### Configuración en `main.py`:

```python
from fastapi.staticfiles import StaticFiles

app.mount("/static", StaticFiles(directory="static"), name="static")
```

Ahora las imágenes son accesibles en:
```
http://localhost:8000/static/images/courses/course-1.jpg
```

---

### 📊 `logs/` - Logs de Aplicación

**Propósito**: Almacenar logs de la aplicación

```
logs/
├── app.log
├── error.log
└── .gitkeep
```

---

## 🚀 2. Activación del Entorno Virtual

### Windows PowerShell

```powershell
# 1. Navegar al proyecto
cd C:\Ctt\CTT-BACK

# 2. Activar entorno virtual
.\venv\Scripts\Activate.ps1

# Verificar que esté activo (debe aparecer (venv) al inicio)
# (venv) PS C:\Ctt\CTT-BACK>
```

### Si tienes problemas de permisos:

```powershell
# Cambiar política de ejecución
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Luego activar nuevamente
.\venv\Scripts\Activate.ps1
```

### Si el venv está corrupto:

```powershell
# Eliminar y recrear
Remove-Item -Path .\venv -Recurse -Force
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Instalar dependencias:

```powershell
pip install -r requirements.txt
```

---

## 🔧 3. Configuración de Variables de Entorno

### Crear archivo `.env` en la raíz del proyecto:

```bash
# === CONFIGURACIÓN DE BASE DE DATOS ===
SQL_SERVER=localhost
SQL_PORT=1433
SQL_DB=CTT_DB
SQL_USER=sa
SQL_PASSWORD=TuPassword123!

# === CONFIGURACIÓN DE SEGURIDAD ===
SECRET_KEY=tu-clave-secreta-super-segura-aqui-cambiar-en-produccion
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# === CONFIGURACIÓN DE LA APLICACIÓN ===
DEBUG=True
ENVIRONMENT=development

# === CONFIGURACIÓN DE PLATAFORMA ===
PLATFORM_SECRET_KEY=otra-clave-secreta-para-plataforma
PLATFORM_ALGORITHM=HS256
PLATFORM_ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### ⚠️ IMPORTANTE:
- **NUNCA subas el archivo `.env` a GitHub**
- Crea un `.env.example` con valores de ejemplo (sin contraseñas reales)
- Cambia `SECRET_KEY` en producción

---

## 🗄️ 4. Inicialización de la Base de Datos

### Arquitectura de la Base de Datos

Tu aplicación usa **SQL Server** con **SQLModel** (ORM basado en SQLAlchemy).

#### Archivo de configuración: `src/config/db.py`

```python
import os
from sqlmodel import create_engine
from dotenv import load_dotenv

load_dotenv()

SQL_SERVER = os.getenv("SQL_SERVER")
SQL_PORT = os.getenv("SQL_PORT")
SQL_DB = os.getenv("SQL_DB")
SQL_USER = os.getenv("SQL_USER")
SQL_PASSWORD = os.getenv("SQL_PASSWORD")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

DATABASE_URL = f"mssql+pyodbc://{SQL_USER}:{SQL_PASSWORD}@{SQL_SERVER}:{SQL_PORT}/{SQL_DB}?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"

engine = create_engine(DATABASE_URL, echo=DEBUG)
```

### Creación automática de tablas

En `src/main.py`, las tablas se crean automáticamente al iniciar la app:

```python
from sqlmodel import SQLModel
from src.config.db import engine

# Importar TODOS los modelos para que SQLModel los registre
from src.models.user import User
from src.models.course import Course
from src.models.user_platform import UserPlatform
from src.models.post import Post
from src.models.enrollment import Enrollment

# Crear todas las tablas
SQLModel.metadata.create_all(engine)
```

### Orden de creación:

1. **SQLModel detecta** todos los modelos importados
2. **Analiza las relaciones** (foreign keys)
3. **Crea las tablas** en el orden correcto
4. **Ejecuta los seeds** (datos de prueba)

---

## 🌱 5. Sistema de Semillas (Seeds)

Las semillas populan la base de datos con datos iniciales. Se ejecutan automáticamente en el **startup** de la aplicación.

### Ubicación: `src/utils/seeds/`

```
seeds/
├── __init__.py
├── user_seed.py           # Usuarios admin de prueba
├── user_platform_seed.py  # Usuarios de la plataforma
└── courses_seed.py        # Cursos con contenido completo
```

### Ejecución automática en `main.py`:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializar directorio de imágenes
    init_upload_directory()
    
    # Ejecutar seeds automáticamente
    seed_users()           # 1. Usuarios admin
    seed_courses()         # 2. Cursos
    seed_users_platform()  # 3. Usuarios de plataforma
    
    yield

app = FastAPI(lifespan=lifespan)
```

### Ejemplo: `user_seed.py`

```python
from sqlmodel import Session
from src.config.db import engine
from src.models.user import User

def seed_users():
    with Session(engine) as session:
        print("Seeding users...")
        
        # Verificar si ya existe (evita duplicados)
        existing_user = session.get(User, 1)
        
        if not existing_user:
            hashed_password = User.hash_password("securepassword")
            session.add(User(
                name="Daniel",
                last_name="Jerez",
                email="daniel.jerez@example.com",
                password=hashed_password,
                id=1
            ))
            session.commit()
            print("✅ Usuario creado")
        else:
            print("⚠️ Usuario ya existe, omitiendo seed")
```

### Ejemplo: `courses_seed.py` (simplificado)

```python
from datetime import date, time
from sqlmodel import Session, select
from src.config.db import engine
from src.models.course import Course, CourseCreate, CourseStatus

def seed_courses():
    with Session(engine) as session:
        print("Seeding courses...")
        
        # Verificar si ya existe
        existing_course = session.exec(
            select(Course).where(Course.id == 1)
        ).first()
        
        if existing_course:
            print("⚠️ Curso ya existe, omitiendo seed")
            return
        
        try:
            # Usar el controlador para crear el curso completo
            from src.controllers.course_controller import CourseController
            
            course_data = CourseCreate(
                title="Arduino desde cero",
                description="Curso completo de Arduino",
                place="Talleres CTT-FISEI",
                course_image="https://...",
                course_image_detail="https://...",
                category="TICS",
                status=CourseStatus.ACTIVO,
                objectives=["Objetivo 1", "Objetivo 2"],
                organizers=["Ing. Luis Pomaquero"],
                materials=["Arduino UNO", "Sensores"],
                target_audience=["Estudiantes", "Docentes"]
            )
            
            # El controlador maneja requirements y contents también
            CourseController.create_course_with_details(
                session,
                course_data,
                requirements_data,
                contents_data
            )
            
            print("✅ Curso creado exitosamente")
            
        except Exception as e:
            print(f"❌ Error al crear curso: {e}")
            session.rollback()
```

### 🔑 Buenas prácticas para Seeds:

1. **Siempre verificar si existen datos** antes de insertar
2. **Usar try-except** para manejar errores
3. **Hacer rollback** si algo falla
4. **Logs claros** para depuración
5. **Datos realistas** para testing

---

## 🏃 6. Ejecución de la Aplicación

### Iniciar el servidor de desarrollo:

```powershell
# Con venv activado
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Parámetros:
- `--reload`: Recarga automática al detectar cambios
- `--host 0.0.0.0`: Permite acceso desde otras máquinas
- `--port 8000`: Puerto (cambia si está ocupado)

### Flujo de inicio:

```
1. Cargar variables de entorno (.env)
   ↓
2. Crear conexión a la base de datos
   ↓
3. Importar todos los modelos
   ↓
4. Crear/actualizar tablas (SQLModel.metadata.create_all)
   ↓
5. Ejecutar lifecycle startup (@asynccontextmanager)
   ├── Inicializar directorio de imágenes
   ├── Ejecutar seed_users()
   ├── Ejecutar seed_courses()
   └── Ejecutar seed_users_platform()
   ↓
6. Registrar rutas (routers)
   ↓
7. Aplicar middlewares (CORS, error handler)
   ↓
8. ✅ Aplicación lista en http://localhost:8000
```

### Verificar que funciona:

```powershell
# Abrir en navegador
http://localhost:8000/docs  # Swagger UI (documentación interactiva)
http://localhost:8000/redoc # ReDoc (documentación alternativa)
```

---

## 🔄 7. Modificar Enums de Estados

### Caso de uso: Cambiar estados de Enrollment

Actualmente en `src/models/enrollment.py`:

```python
class EnrollmentStatus(str, Enum):
    INTERESADO = "Interesado"
    ORDEN_GENERADA = "Generada la orden"
    PAGADO = "Pagado"
    FACTURADO = "Facturado"
    ANULADO = "Anulado"
```

### ✏️ Escenario 1: Cambiar "INTERESADO" por "PRE_INSCRITO"

#### Paso 1: Actualizar el Enum en el modelo

```python
class EnrollmentStatus(str, Enum):
    PRE_INSCRITO = "Pre-inscrito"  # ✅ Nuevo nombre
    ORDEN_GENERADA = "Generada la orden"
    PAGADO = "Pagado"
    FACTURADO = "Facturado"
    ANULADO = "Anulado"
```

#### Paso 2: Actualizar el valor por defecto

```python
class Enrollment(SQLModel, table=True):
    # ...
    status: EnrollmentStatus = Field(
        sa_column=Column(SQLEnum(EnrollmentStatus), nullable=False),
        default=EnrollmentStatus.PRE_INSCRITO  # ✅ Cambiar aquí también
    )
```

#### Paso 3: Actualizar seeds

```python
# En src/utils/seeds/enrollment_seed.py (si existe)
enrollment = Enrollment(
    id_user_platform=1,
    id_course=1,
    status=EnrollmentStatus.PRE_INSCRITO  # ✅ Actualizar
)
```

#### Paso 4: Migración de datos existentes

```python
# Script de migración: scripts/migrate_enrollment_status.py
from sqlmodel import Session, select
from src.config.db import engine
from src.models.enrollment import Enrollment

def migrate_status():
    with Session(engine) as session:
        # Obtener todos los registros con el estado antiguo
        stmt = select(Enrollment).where(
            Enrollment.status == "Interesado"  # Valor antiguo en BD
        )
        enrollments = session.exec(stmt).all()
        
        for enrollment in enrollments:
            enrollment.status = "Pre-inscrito"  # Nuevo valor
        
        session.commit()
        print(f"✅ Migrados {len(enrollments)} registros")

if __name__ == "__main__":
    migrate_status()
```

#### Paso 5: Ejecutar migración

```powershell
python scripts/migrate_enrollment_status.py
```

### ✏️ Escenario 2: Añadir nuevos estados

```python
class EnrollmentStatus(str, Enum):
    INTERESADO = "Interesado"
    ORDEN_GENERADA = "Generada la orden"
    PAGADO = "Pagado"
    FACTURADO = "Facturado"
    ANULADO = "Anulado"
    # ✅ NUEVOS ESTADOS
    EN_PROCESO_PAGO = "En proceso de pago"
    REEMBOLSADO = "Reembolsado"
    SUSPENDIDO = "Suspendido"
```

⚠️ **IMPORTANTE**: Al añadir valores, no necesitas migrar datos existentes, pero debes:
1. Actualizar la documentación
2. Actualizar los tests
3. Actualizar el frontend (si existe)

### ✏️ Escenario 3: Eliminar un estado

❌ **NO RECOMENDADO** - En su lugar, márcalo como deprecated:

```python
class EnrollmentStatus(str, Enum):
    INTERESADO = "Interesado"
    # DEPRECATED - Usar EN_PROCESO_PAGO en su lugar
    # ORDEN_GENERADA = "Generada la orden"  
    PAGADO = "Pagado"
    FACTURADO = "Facturado"
    ANULADO = "Anulado"
    EN_PROCESO_PAGO = "En proceso de pago"  # Reemplazo
```

### 🔑 Checklist para cambiar Enums:

- [ ] Actualizar definición del Enum
- [ ] Actualizar valores por defecto en modelos
- [ ] Actualizar seeds
- [ ] Crear script de migración para datos existentes
- [ ] Ejecutar migración en desarrollo
- [ ] Actualizar tests
- [ ] Actualizar documentación
- [ ] Actualizar frontend (si aplica)
- [ ] Ejecutar migración en producción

---

## 📊 8. Añadir Nuevos Campos a la Base de Datos

### Ejemplo: Añadir campo "discount_percentage" a Enrollment

#### Paso 1: Actualizar el modelo principal

```python
# src/models/enrollment.py

class Enrollment(SQLModel, table=True):
    __tablename__ = "enrollments"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    id_user_platform: int = Field(foreign_key="users_platform.id", nullable=False)
    id_course: int = Field(foreign_key="course.id", nullable=False)
    enrollment_date: datetime = Field(
        sa_column=Column(DateTime, nullable=False, default=datetime.utcnow)
    )
    status: EnrollmentStatus = Field(
        sa_column=Column(SQLEnum(EnrollmentStatus), nullable=False),
        default=EnrollmentStatus.INTERESADO
    )
    payment_order_url: Optional[str] = Field(default=None, max_length=500)
    
    # ✅ NUEVO CAMPO
    discount_percentage: Optional[float] = Field(
        default=0.0,
        ge=0.0,  # Mayor o igual a 0
        le=100.0,  # Menor o igual a 100
        description="Porcentaje de descuento aplicado (0-100)"
    )
```

#### Paso 2: Actualizar modelos de Request/Response

```python
# Modelo de creación
class EnrollmentCreate(SQLModel):
    id_user_platform: int
    id_course: int
    status: EnrollmentStatus = EnrollmentStatus.INTERESADO
    payment_order_url: Optional[str] = None
    discount_percentage: Optional[float] = Field(default=0.0, ge=0, le=100)  # ✅

# Modelo de actualización
class EnrollmentUpdate(SQLModel):
    status: Optional[EnrollmentStatus] = None
    payment_order_url: Optional[str] = None
    discount_percentage: Optional[float] = Field(default=None, ge=0, le=100)  # ✅

# Modelo de respuesta
class EnrollmentResponse(SQLModel):
    id: int
    id_user_platform: int
    id_course: int
    enrollment_date: datetime
    status: EnrollmentStatus
    payment_order_url: Optional[str]
    discount_percentage: Optional[float]  # ✅
```

#### Paso 3: Actualizar controlador (si es necesario)

```python
# src/controllers/enrollment_controller.py

class EnrollmentController:
    @staticmethod
    def create_enrollment(
        session: Session,
        enrollment_data: EnrollmentCreate
    ) -> Enrollment:
        # El campo discount_percentage se incluye automáticamente
        enrollment = Enrollment(
            id_user_platform=enrollment_data.id_user_platform,
            id_course=enrollment_data.id_course,
            status=enrollment_data.status,
            payment_order_url=enrollment_data.payment_order_url,
            discount_percentage=enrollment_data.discount_percentage  # ✅
        )
        session.add(enrollment)
        session.commit()
        session.refresh(enrollment)
        return enrollment
```

#### Paso 4: Actualizar seeds (opcional)

```python
# src/utils/seeds/enrollment_seed.py (si existe)

def seed_enrollments():
    with Session(engine) as session:
        enrollment = Enrollment(
            id_user_platform=1,
            id_course=1,
            status=EnrollmentStatus.INTERESADO,
            discount_percentage=10.0  # ✅ Descuento de ejemplo
        )
        session.add(enrollment)
        session.commit()
```

#### Paso 5: Recrear la base de datos (DESARROLLO)

```powershell
# OPCIÓN A: Dejar que SQLModel actualice automáticamente (si está en modo DEBUG)
# Solo reiniciar la app
uvicorn src.main:app --reload

# OPCIÓN B: Eliminar y recrear la BD completamente (datos se pierden)
# En SQL Server Management Studio:
DROP DATABASE CTT_DB;
CREATE DATABASE CTT_DB;

# Luego reiniciar la app para que cree las tablas
uvicorn src.main:app --reload
```

### ⚠️ En producción: Usar migraciones

SQLModel/SQLAlchemy **NO hace migraciones automáticas**. Para producción usa **Alembic**:

#### Instalar Alembic:

```powershell
pip install alembic
alembic init alembic
```

#### Configurar `alembic.ini`:

```ini
# Reemplazar
sqlalchemy.url = driver://user:pass@localhost/dbname

# Por tu conexión
sqlalchemy.url = mssql+pyodbc://sa:password@localhost:1433/CTT_DB?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes
```

#### Crear migración:

```powershell
# Genera automáticamente la migración detectando cambios
alembic revision --autogenerate -m "add discount_percentage to enrollment"

# Aplicar migración
alembic upgrade head
```

---

## 🔄 9. Migración de Datos

### Tipos de migraciones comunes:

#### A. Añadir campo con valor por defecto

```python
# scripts/migrations/add_discount_field.py
from sqlmodel import Session
from src.config.db import engine
from sqlalchemy import text

def migrate():
    with Session(engine) as session:
        # SQL Server
        session.exec(text("""
            ALTER TABLE enrollments 
            ADD discount_percentage FLOAT DEFAULT 0.0
        """))
        session.commit()
        print("✅ Campo añadido")

if __name__ == "__main__":
    migrate()
```

#### B. Actualizar valores existentes

```python
# scripts/migrations/update_enrollment_discounts.py
from sqlmodel import Session, select
from src.config.db import engine
from src.models.enrollment import Enrollment

def apply_discounts():
    with Session(engine) as session:
        # Aplicar 15% de descuento a estudiantes
        stmt = select(Enrollment).where(
            Enrollment.status == "Interesado"
        )
        enrollments = session.exec(stmt).all()
        
        for enrollment in enrollments:
            # Lógica de negocio
            if enrollment.id_user_platform in range(1, 100):
                enrollment.discount_percentage = 15.0
        
        session.commit()
        print(f"✅ Aplicados descuentos a {len(enrollments)} registros")

if __name__ == "__main__":
    apply_discounts()
```

#### C. Eliminar campo (con cuidado)

```python
# scripts/migrations/remove_old_field.py
from sqlmodel import Session
from src.config.db import engine
from sqlalchemy import text

def migrate():
    with Session(engine) as session:
        # SQL Server
        session.exec(text("""
            ALTER TABLE enrollments 
            DROP COLUMN old_field_name
        """))
        session.commit()
        print("✅ Campo eliminado")

if __name__ == "__main__":
    migrate()
```

---

## 📝 Ejemplo Completo: Añadir Estado "EN_ESPERA" a Enrollment

### 1. Actualizar el Enum

```python
# src/models/enrollment.py

class EnrollmentStatus(str, Enum):
    INTERESADO = "Interesado"
    EN_ESPERA = "En espera"  # ✅ NUEVO
    ORDEN_GENERADA = "Generada la orden"
    PAGADO = "Pagado"
    FACTURADO = "Facturado"
    ANULADO = "Anulado"
```

### 2. Actualizar seeds

```python
# src/utils/seeds/enrollment_seed.py

def seed_enrollments():
    enrollments = [
        Enrollment(
            id_user_platform=1,
            id_course=1,
            status=EnrollmentStatus.EN_ESPERA  # ✅ Usar nuevo estado
        ),
        # ... más enrollments
    ]
```

### 3. Actualizar rutas/controladores

```python
# src/routes/enrollments_router.py

@router.patch("/{enrollment_id}/status")
def update_enrollment_status(
    enrollment_id: int,
    new_status: EnrollmentStatus,  # ✅ Acepta el nuevo estado automáticamente
    session: Session = Depends(get_session)
):
    # Validar transiciones permitidas
    valid_transitions = {
        EnrollmentStatus.INTERESADO: [EnrollmentStatus.EN_ESPERA, EnrollmentStatus.ORDEN_GENERADA],
        EnrollmentStatus.EN_ESPERA: [EnrollmentStatus.ORDEN_GENERADA, EnrollmentStatus.ANULADO],
        # ... más transiciones
    }
    # ... lógica
```

### 4. Reiniciar aplicación

```powershell
# Con --reload, FastAPI detecta los cambios automáticamente
# Si no, reinicia manualmente con Ctrl+C y vuelve a ejecutar:
uvicorn src.main:app --reload
```

---

## 🎯 Resumen del Flujo Completo

```
┌─────────────────────────────────────────┐
│ 1. ACTIVAR ENTORNO VIRTUAL              │
│    venv\Scripts\Activate.ps1            │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ 2. CARGAR VARIABLES (.env)              │
│    - Credenciales BD                    │
│    - SECRET_KEY                         │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ 3. INICIAR APP (uvicorn)                │
│    - Conectar a BD                      │
│    - Crear tablas (SQLModel)            │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ 4. EJECUTAR SEEDS (lifespan)            │
│    - seed_users()                       │
│    - seed_courses()                     │
│    - seed_users_platform()              │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ 5. REGISTRAR RUTAS                      │
│    - /auth, /courses, /enrollments      │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ 6. APLICAR MIDDLEWARES                  │
│    - CORS                               │
│    - Error Handler                      │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ ✅ APP LISTA en http://localhost:8000   │
│    - /docs (Swagger)                    │
│    - /redoc (ReDoc)                     │
└─────────────────────────────────────────┘
```

---

## 🛠️ Comandos Rápidos de Referencia

```powershell
# Activar venv
.\venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt

# Iniciar app
uvicorn src.main:app --reload

# Ver logs
# Los logs están en logs/app.log

# Crear nueva migración (con Alembic)
alembic revision --autogenerate -m "descripción"
alembic upgrade head

# Ejecutar tests
pytest

# Ver documentación
# http://localhost:8000/docs
```

---

## 📚 Recursos Adicionales

- **FastAPI**: https://fastapi.tiangolo.com/
- **SQLModel**: https://sqlmodel.tiangolo.com/
- **Alembic**: https://alembic.sqlalchemy.org/
- **Pydantic**: https://docs.pydantic.dev/

---

## ❓ Preguntas Frecuentes

### ¿Cómo elimino todos los datos y empiezo de cero?

```sql
-- En SQL Server Management Studio
DROP DATABASE CTT_DB;
CREATE DATABASE CTT_DB;
```

Luego reinicia la app para que las tablas se creen automáticamente.

### ¿Cómo evito que los seeds se ejecuten múltiples veces?

Los seeds ya tienen validación:

```python
existing_user = session.get(User, 1)
if not existing_user:
    # Crear usuario
```

### ¿Puedo deshabilitar los seeds temporalmente?

Sí, comenta las líneas en `main.py`:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_upload_directory()
    # seed_users()        # ← Comentar
    # seed_courses()      # ← Comentar
    # seed_users_platform()  # ← Comentar
    yield
```

### ¿Cómo sé qué tablas existen en la BD?

```sql
-- En SQL Server
SELECT TABLE_NAME 
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_TYPE = 'BASE TABLE';
```

O usa SQL Server Management Studio (SSMS) para explorar visualmente.

---

## 🚀 10. Añadir Nuevas Funcionalidades

### Guía Paso a Paso: Sistema de Notificaciones

Vamos a crear un **sistema de notificaciones completo** como ejemplo práctico.

---

#### ✅ Paso 1: Crear el Modelo

```python
# src/models/notification.py
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Enum as SQLEnum, DateTime

class NotificationType(str, Enum):
    """Tipos de notificación"""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"

class NotificationStatus(str, Enum):
    """Estado de la notificación"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    READ = "read"

class Notification(SQLModel, table=True):
    """Modelo de notificación"""
    __tablename__ = "notifications"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users_platform.id", nullable=False)
    type: NotificationType = Field(
        sa_column=Column(SQLEnum(NotificationType), nullable=False)
    )
    status: NotificationStatus = Field(
        sa_column=Column(SQLEnum(NotificationStatus), nullable=False),
        default=NotificationStatus.PENDING
    )
    title: str = Field(max_length=200)
    message: str = Field(max_length=1000)
    link: Optional[str] = Field(default=None, max_length=500)
    is_read: bool = Field(default=False)
    read_at: Optional[datetime] = Field(
        sa_column=Column(DateTime, nullable=True),
        default=None
    )
    created_at: datetime = Field(
        sa_column=Column(DateTime, nullable=False, default=datetime.utcnow)
    )
    sent_at: Optional[datetime] = Field(
        sa_column=Column(DateTime, nullable=True),
        default=None
    )
    
    # Relación con usuario
    # user: "UserPlatform" = Relationship(back_populates="notifications")

# === Modelos de Request ===
class NotificationCreate(SQLModel):
    """Modelo para crear notificación"""
    user_id: int
    type: NotificationType
    title: str = Field(max_length=200)
    message: str = Field(max_length=1000)
    link: Optional[str] = Field(default=None, max_length=500)

class NotificationUpdate(SQLModel):
    """Modelo para actualizar notificación"""
    status: Optional[NotificationStatus] = None
    is_read: Optional[bool] = None

# === Modelos de Response ===
class NotificationResponse(SQLModel):
    """Respuesta de notificación"""
    id: int
    user_id: int
    type: NotificationType
    status: NotificationStatus
    title: str
    message: str
    link: Optional[str]
    is_read: bool
    read_at: Optional[datetime]
    created_at: datetime
    sent_at: Optional[datetime]

class NotificationList(SQLModel):
    """Lista de notificaciones con paginación"""
    total: int
    unread_count: int
    notifications: list[NotificationResponse]
```

**Importar en `main.py`:**

```python
from src.models.notification import Notification  # ✅ Añadir
```

---

#### ✅ Paso 2: Crear el Repository

```python
# src/repositories/notification_repository.py
from sqlmodel import Session, select, func
from typing import List, Optional, Tuple
from src.models.notification import (
    Notification,
    NotificationCreate,
    NotificationStatus,
    NotificationType
)
from datetime import datetime

class NotificationRepository:
    """Maneja operaciones de BD para notificaciones"""
    
    @staticmethod
    def create(session: Session, data: NotificationCreate) -> Notification:
        """Crea una nueva notificación"""
        notification = Notification(**data.model_dump())
        session.add(notification)
        session.commit()
        session.refresh(notification)
        return notification
    
    @staticmethod
    def get_by_id(session: Session, notification_id: int) -> Optional[Notification]:
        """Obtiene una notificación por ID"""
        return session.get(Notification, notification_id)
    
    @staticmethod
    def get_by_user(
        session: Session,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Notification], int]:
        """Obtiene notificaciones de un usuario (paginadas)"""
        # Query para obtener notificaciones
        statement = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        notifications = session.exec(statement).all()
        
        # Contar total
        count_stmt = (
            select(func.count(Notification.id))
            .where(Notification.user_id == user_id)
        )
        total = session.exec(count_stmt).one()
        
        return notifications, total
    
    @staticmethod
    def get_unread_count(session: Session, user_id: int) -> int:
        """Cuenta notificaciones no leídas"""
        statement = (
            select(func.count(Notification.id))
            .where(Notification.user_id == user_id)
            .where(Notification.is_read == False)
        )
        return session.exec(statement).one()
    
    @staticmethod
    def mark_as_read(
        session: Session,
        notification_id: int
    ) -> Optional[Notification]:
        """Marca una notificación como leída"""
        notification = session.get(Notification, notification_id)
        if notification and not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            session.add(notification)
            session.commit()
            session.refresh(notification)
        return notification
    
    @staticmethod
    def mark_all_as_read(session: Session, user_id: int) -> int:
        """Marca todas las notificaciones de un usuario como leídas"""
        statement = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .where(Notification.is_read == False)
        )
        notifications = session.exec(statement).all()
        
        count = 0
        for notification in notifications:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            session.add(notification)
            count += 1
        
        session.commit()
        return count
    
    @staticmethod
    def delete(session: Session, notification_id: int) -> bool:
        """Elimina una notificación"""
        notification = session.get(Notification, notification_id)
        if notification:
            session.delete(notification)
            session.commit()
            return True
        return False
    
    @staticmethod
    def update_status(
        session: Session,
        notification_id: int,
        status: NotificationStatus
    ) -> Optional[Notification]:
        """Actualiza el estado de una notificación"""
        notification = session.get(Notification, notification_id)
        if notification:
            notification.status = status
            if status == NotificationStatus.SENT:
                notification.sent_at = datetime.utcnow()
            session.add(notification)
            session.commit()
            session.refresh(notification)
        return notification
```

---

#### ✅ Paso 3: Crear el Controller

```python
# src/controllers/notification_controller.py
from sqlmodel import Session
from typing import List, Dict, Any
from src.models.notification import (
    Notification,
    NotificationCreate,
    NotificationStatus,
    NotificationType
)
from src.repositories.notification_repository import NotificationRepository
from src.utils.serializers.notification_serializer import NotificationSerializer

class NotificationController:
    """Lógica de negocio para notificaciones"""
    
    @staticmethod
    def send_notification(
        session: Session,
        notification_data: NotificationCreate
    ) -> Dict[str, Any]:
        """Envía una notificación"""
        
        # 1. Validar que el usuario existe
        from src.models.user_platform import UserPlatform
        user = session.get(UserPlatform, notification_data.user_id)
        if not user:
            raise ValueError("Usuario no encontrado")
        
        # 2. Crear notificación
        notification = NotificationRepository.create(session, notification_data)
        
        # 3. Enviar según el tipo
        try:
            if notification_data.type == NotificationType.EMAIL:
                # Aquí iría la lógica de envío de email
                # send_email(user.email, notification.title, notification.message)
                pass
            elif notification_data.type == NotificationType.SMS:
                # send_sms(user.phone, notification.message)
                pass
            elif notification_data.type == NotificationType.PUSH:
                # send_push_notification(user.device_token, notification.title)
                pass
            
            # 4. Actualizar estado a enviado
            NotificationRepository.update_status(
                session,
                notification.id,
                NotificationStatus.SENT
            )
            
        except Exception as e:
            # Marcar como fallida
            NotificationRepository.update_status(
                session,
                notification.id,
                NotificationStatus.FAILED
            )
            raise ValueError(f"Error al enviar notificación: {str(e)}")
        
        return NotificationSerializer.to_dict(notification)
    
    @staticmethod
    def get_user_notifications(
        session: Session,
        user_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Obtiene notificaciones de un usuario"""
        offset = (page - 1) * page_size
        
        notifications, total = NotificationRepository.get_by_user(
            session,
            user_id,
            limit=page_size,
            offset=offset
        )
        
        unread_count = NotificationRepository.get_unread_count(session, user_id)
        
        return {
            "total": total,
            "unread_count": unread_count,
            "page": page,
            "page_size": page_size,
            "notifications": [
                NotificationSerializer.to_dict(n) for n in notifications
            ]
        }
    
    @staticmethod
    def mark_as_read(
        session: Session,
        notification_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """Marca una notificación como leída"""
        notification = NotificationRepository.get_by_id(session, notification_id)
        
        if not notification:
            raise ValueError("Notificación no encontrada")
        
        if notification.user_id != user_id:
            raise ValueError("No tienes permiso para marcar esta notificación")
        
        notification = NotificationRepository.mark_as_read(session, notification_id)
        return NotificationSerializer.to_dict(notification)
    
    @staticmethod
    def mark_all_as_read(session: Session, user_id: int) -> Dict[str, Any]:
        """Marca todas las notificaciones como leídas"""
        count = NotificationRepository.mark_all_as_read(session, user_id)
        return {
            "message": f"{count} notificaciones marcadas como leídas",
            "count": count
        }
    
    @staticmethod
    def delete_notification(
        session: Session,
        notification_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """Elimina una notificación"""
        notification = NotificationRepository.get_by_id(session, notification_id)
        
        if not notification:
            raise ValueError("Notificación no encontrada")
        
        if notification.user_id != user_id:
            raise ValueError("No tienes permiso para eliminar esta notificación")
        
        NotificationRepository.delete(session, notification_id)
        return {"message": "Notificación eliminada"}
```

---

#### ✅ Paso 4: Crear el Serializer

```python
# src/utils/serializers/notification_serializer.py
from typing import Dict, Any
from src.models.notification import Notification

class NotificationSerializer:
    """Serializa notificaciones"""
    
    @staticmethod
    def to_dict(notification: Notification) -> Dict[str, Any]:
        """Convierte Notification a diccionario"""
        return {
            "id": notification.id,
            "user_id": notification.user_id,
            "type": notification.type.value,
            "status": notification.status.value,
            "title": notification.title,
            "message": notification.message,
            "link": notification.link,
            "is_read": notification.is_read,
            "read_at": notification.read_at.isoformat() if notification.read_at else None,
            "created_at": notification.created_at.isoformat(),
            "sent_at": notification.sent_at.isoformat() if notification.sent_at else None
        }
```

---

#### ✅ Paso 5: Crear el Router

```python
# src/routes/notifications_router.py
from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import Annotated
from src.controllers.notification_controller import NotificationController
from src.dependencies.db_session import SessionDep
from src.models.notification import NotificationCreate, NotificationResponse
from src.utils.platform_jwt_utils import decode_platform_token
from src.models.user_platform import UserPlatform

notifications_router = APIRouter(
    prefix="/api/v1/notifications",
    tags=["notifications"]
)

# Dependency para obtener usuario autenticado
def get_current_platform_user(
    token: Annotated[str, Depends(decode_platform_token)]
) -> int:
    """Obtiene el ID del usuario desde el token"""
    return token.get("sub")  # Asumiendo que el token tiene el user_id en 'sub'

@notifications_router.post(
    "/",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Enviar notificación"
)
def send_notification(
    notification: NotificationCreate,
    session: SessionDep
):
    """
    Envía una notificación a un usuario.
    
    - **user_id**: ID del usuario destinatario
    - **type**: Tipo de notificación (email, sms, push, in_app)
    - **title**: Título de la notificación
    - **message**: Mensaje de la notificación
    - **link**: Link opcional (para notificaciones in-app)
    """
    try:
        result = NotificationController.send_notification(session, notification)
        return {
            "message": "Notificación enviada exitosamente",
            "data": result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al enviar notificación")

@notifications_router.get(
    "/",
    response_model=dict,
    summary="Obtener mis notificaciones"
)
def get_my_notifications(
    session: SessionDep,
    user_id: Annotated[int, Depends(get_current_platform_user)],
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(20, ge=1, le=100, description="Tamaño de página")
):
    """
    Obtiene las notificaciones del usuario autenticado.
    
    - Ordenadas por fecha de creación (más recientes primero)
    - Incluye contador de notificaciones no leídas
    - Paginadas
    """
    try:
        result = NotificationController.get_user_notifications(
            session,
            user_id,
            page,
            page_size
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al obtener notificaciones")

@notifications_router.get(
    "/unread/count",
    response_model=dict,
    summary="Contar notificaciones no leídas"
)
def get_unread_count(
    session: SessionDep,
    user_id: Annotated[int, Depends(get_current_platform_user)]
):
    """Obtiene el número de notificaciones no leídas"""
    from src.repositories.notification_repository import NotificationRepository
    
    count = NotificationRepository.get_unread_count(session, user_id)
    return {"unread_count": count}

@notifications_router.patch(
    "/{notification_id}/read",
    response_model=dict,
    summary="Marcar como leída"
)
def mark_notification_read(
    notification_id: int,
    session: SessionDep,
    user_id: Annotated[int, Depends(get_current_platform_user)]
):
    """Marca una notificación específica como leída"""
    try:
        result = NotificationController.mark_as_read(
            session,
            notification_id,
            user_id
        )
        return {
            "message": "Notificación marcada como leída",
            "data": result
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al actualizar notificación")

@notifications_router.patch(
    "/read/all",
    response_model=dict,
    summary="Marcar todas como leídas"
)
def mark_all_notifications_read(
    session: SessionDep,
    user_id: Annotated[int, Depends(get_current_platform_user)]
):
    """Marca todas las notificaciones del usuario como leídas"""
    try:
        result = NotificationController.mark_all_as_read(session, user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al actualizar notificaciones")

@notifications_router.delete(
    "/{notification_id}",
    response_model=dict,
    summary="Eliminar notificación"
)
def delete_notification(
    notification_id: int,
    session: SessionDep,
    user_id: Annotated[int, Depends(get_current_platform_user)]
):
    """Elimina una notificación"""
    try:
        result = NotificationController.delete_notification(
            session,
            notification_id,
            user_id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al eliminar notificación")
```

---

#### ✅ Paso 6: Registrar el Router

```python
# src/main.py

from src.routes.notifications_router import notifications_router  # ✅ Importar

# ... resto del código ...

# Registrar routers
app.include_router(auth_router)
app.include_router(courses_router)
app.include_router(notifications_router)  # ✅ Añadir esta línea
# ... más routers ...
```

---

#### ✅ Paso 7: Crear Seed (Opcional)

```python
# src/utils/seeds/notification_seed.py
from sqlmodel import Session
from src.config.db import engine
from src.models.notification import (
    Notification,
    NotificationType,
    NotificationStatus
)

def seed_notifications():
    """Crea notificaciones de prueba"""
    with Session(engine) as session:
        print("Seeding notifications...")
        
        # Verificar si ya existen
        existing = session.get(Notification, 1)
        if existing:
            print("⚠️ Notificaciones ya existen, omitiendo seed")
            return
        
        notifications = [
            Notification(
                user_id=1,
                type=NotificationType.IN_APP,
                status=NotificationStatus.SENT,
                title="¡Bienvenido a CTT!",
                message="Gracias por registrarte en nuestra plataforma",
                link="/profile"
            ),
            Notification(
                user_id=1,
                type=NotificationType.EMAIL,
                status=NotificationStatus.SENT,
                title="Nuevo curso disponible",
                message="El curso 'Arduino desde cero' ya está disponible",
                link="/courses/1"
            ),
        ]
        
        for notification in notifications:
            session.add(notification)
        
        session.commit()
        print("✅ Notificaciones creadas")

# Llamar en main.py
# from src.utils.seeds.notification_seed import seed_notifications
# seed_notifications()
```

---

#### ✅ Paso 8: Crear Tests

```python
# tests/test_routes/test_notifications_router.py
import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_send_notification():
    """Test de envío de notificación"""
    notification_data = {
        "user_id": 1,
        "type": "email",
        "title": "Test Notification",
        "message": "Este es un mensaje de prueba"
    }
    
    response = client.post("/api/v1/notifications/", json=notification_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "Notificación enviada exitosamente"
    assert "data" in data

def test_get_notifications(auth_token):
    """Test de obtención de notificaciones"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    response = client.get("/api/v1/notifications/", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "notifications" in data
    assert "total" in data
    assert "unread_count" in data

def test_mark_as_read(auth_token):
    """Test de marcar como leída"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    response = client.patch(
        "/api/v1/notifications/1/read",
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Notificación marcada como leída"
```

---

### 📝 Checklist para Nuevas Funcionalidades

Cada vez que añadas una nueva funcionalidad, sigue estos pasos:

- [ ] **1. Modelo** (`src/models/`) - Define estructura de datos
- [ ] **2. Repository** (`src/repositories/`) - Queries a BD
- [ ] **3. Controller** (`src/controllers/`) - Lógica de negocio
- [ ] **4. Serializer** (`src/utils/serializers/`) - Transformación de datos
- [ ] **5. Router** (`src/routes/`) - Endpoints API
- [ ] **6. Registrar Router** en `main.py`
- [ ] **7. Importar Modelo** en `main.py` (para crear tabla)
- [ ] **8. Seed** (`src/utils/seeds/`) - Datos de prueba (opcional)
- [ ] **9. Tests** (`tests/`) - Tests unitarios/integración
- [ ] **10. Documentación** - Actualizar README o docs

---

### 🎯 Arquitectura de Capas (Resumen)

```
┌─────────────────────────────────────────┐
│         CLIENTE (Frontend)              │
└────────────────┬────────────────────────┘
                 │ HTTP Request
                 ▼
┌─────────────────────────────────────────┐
│  CAPA DE RUTAS (Routes)                 │
│  - Valida parámetros HTTP               │
│  - Maneja autenticación                 │
│  - Formatea respuestas                  │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  CAPA DE CONTROLADORES (Controllers)    │
│  - Lógica de negocio                    │
│  - Validaciones de negocio              │
│  - Orquesta operaciones                 │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  CAPA DE REPOSITORIOS (Repositories)    │
│  - Acceso a base de datos               │
│  - Queries SQL/ORM                      │
│  - Paginación y filtros                 │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  BASE DE DATOS (SQL Server)             │
└─────────────────────────────────────────┘
```

**Flujo de datos:**

1. **Request** → Router valida y extrae datos
2. **Router** → Controller ejecuta lógica de negocio
3. **Controller** → Repository accede a BD
4. **Repository** → BD ejecuta queries
5. **BD** → Repository devuelve datos
6. **Repository** → Controller transforma datos
7. **Controller** → Router formatea respuesta
8. **Response** → Cliente recibe JSON

---

**¡Listo!** Ahora tienes una guía completa del flujo de la aplicación. 🚀

