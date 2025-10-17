"""
Configuración de fixtures para pytest
Este archivo contiene fixtures compartidos que pueden ser usados en todos los tests
"""
import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from datetime import date, time
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
    from src.models.course import CourseBase
    
    return CourseBase(
        title="Curso de Python",
        description="Aprende Python desde cero",
        place="Aula 101",
        course_image="python.jpg",
        category="Programación",
        status="active",
        objectives=["Aprender sintaxis básica", "Crear aplicaciones"],
        organizers=["Universidad XYZ"],
        materials=["Laptop", "Internet"],
        target_audience=["Estudiantes", "Profesionales"]
    )


@pytest.fixture
def sample_requirements_data():
    """Datos de ejemplo para requisitos de curso"""
    from src.models.course import CourseRequirementBase
    
    return CourseRequirementBase(
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
    from src.models.course import CourseContentBase, CourseContentTopicBase
    
    return [
        CourseContentBase(
            unit="1",
            title="Introducción a Python",
            topics=[
                CourseContentTopicBase(unit="1.1", title="Variables y tipos de datos"),
                CourseContentTopicBase(unit="1.2", title="Operadores")
            ]
        ),
        CourseContentBase(
            unit="2",
            title="Estructuras de control",
            topics=[
                CourseContentTopicBase(unit="2.1", title="Condicionales"),
                CourseContentTopicBase(unit="2.2", title="Bucles")
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
