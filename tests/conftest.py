"""
Configuración de fixtures para pytest
Este archivo contiene fixtures compartidos que pueden ser usados en todos los tests
"""
import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from datetime import date, time
from src.models.course import CourseStatus
import json


@pytest.fixture(name="session")
def session_fixture():
    """
    Crea una sesión de base de datos en memoria para tests
    Se resetea después de cada test
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def sample_course_data():
    """Datos de ejemplo para crear un curso"""
    from src.models.course import CourseCreate
    
    return CourseCreate(
        title="Curso de Python",
        description="Aprende Python desde cero",
        place="Aula 101",
        course_image="python.jpg",
        course_image_detail="python_detail.jpg",
        category="Programación",
        status=CourseStatus.ACTIVO,
        objectives=["Aprender sintaxis básica", "Crear aplicaciones"],
        organizers=["Universidad XYZ"],
        materials=["Laptop", "Internet"],
        target_audience=["Estudiantes", "Profesionales"]
    )


@pytest.fixture
def sample_requirements_data():
    """Datos de ejemplo para requisitos de curso"""
    from src.models.course import CourseRequirementCreate
    
    return CourseRequirementCreate(
        start_date_registration=date(2024, 1, 1),
        end_date_registration=date(2024, 1, 31),
        start_date_course=date(2024, 2, 1),
        end_date_course=date(2024, 3, 31),
        days=["Lunes", "Miércoles", "Viernes"],
        start_time=time(14, 0),
        end_time=time(18, 0),
        location="Aula Virtual",
        min_quota=10,
        max_quota=30,
        in_person_hours=40,
        autonomous_hours=20,
        modality="Híbrida",
        certification="Certificado de participación",
        prerequisites=["Conocimientos básicos de computación"],
        prices=[{"type": "Estudiante", "amount": 100}, {"type": "General", "amount": 150}]
    )


@pytest.fixture
def sample_contents_data():
    """Datos de ejemplo para contenidos de curso"""
    from src.models.course import CourseContentCreate, CourseContentTopicRead
    
    return [
        CourseContentCreate(
            unit="1",
            title="Introducción a Python",
            topics=[
                CourseContentTopicRead(unit="1.1", title="Variables y tipos de datos"),
                CourseContentTopicRead(unit="1.2", title="Operadores")
            ]
        ),
        CourseContentCreate(
            unit="2",
            title="Estructuras de control",
            topics=[
                CourseContentTopicRead(unit="2.1", title="Condicionales"),
                CourseContentTopicRead(unit="2.2", title="Bucles")
            ]
        )
    ]


@pytest.fixture
def sample_user_data():
    """Datos de ejemplo para crear un usuario"""
    from src.models.user import User
    
    return User(
        name="Juan",
        last_name="Pérez",
        email="test@example.com",
        password="hashed_password_123"
    )


@pytest.fixture
def sample_user_platform_data():
    """Datos de ejemplo para crear un usuario de plataforma"""
    from src.models.user_platform import UserPlatform, UserPlatformType
    
    return UserPlatform(
        identification="1234567890",
        first_name="Pedro",
        second_name="Luis",
        first_last_name="Martínez",
        second_last_name="López",
        cellphone="0987654321",
        email="pedro.martinez@example.com",
        address="Calle Test 123",
        type=UserPlatformType.ESTUDIANTE,
        password="hashed_password_123"
    )


# ==========================================
# Fixtures para Tests de Endpoints (Routes)
# ==========================================

@pytest.fixture
def client(session):
    """
    Cliente de prueba de FastAPI con BD en memoria
    
    Usa una app FastAPI temporal configurada para tests
    """
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from src.routes.auth_router import auth_router
    from src.routes.courses_router import courses_router
    from src.routes.platform_auth_router import platform_auth_router
    from src.dependencies.db_session import get_db
    from fastapi.middleware.cors import CORSMiddleware
    
    # Crear app temporal para tests
    test_app = FastAPI()
    
    # Override de la dependencia de BD
    def override_get_db():
        try:
            yield session
        finally:
            pass  # No cerrar la sesión porque la maneja el fixture
    
    test_app.dependency_overrides[get_db] = override_get_db
    
    # Agregar CORS
    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Incluir routers
    test_app.include_router(auth_router)
    test_app.include_router(courses_router)
    test_app.include_router(platform_auth_router)
    
    # Crear cliente de test
    with TestClient(test_app) as test_client:
        yield test_client
