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

# Importar modelos de Congress para que SQLAlchemy pueda resolver las foreign keys
from src.models.congress_model import Congress
from src.models.sponsor_model import Sponsor
from src.models.speaker_model import Speaker
from src.models.sesion_cronograma_model import SesionCronograma
from src.models.congreso_sponsor_model import CongresoSponsor
from src.models.base import Base


@pytest.fixture(name="session")
def session_fixture():
    """
    Crea una sesión de base de datos en memoria para tests.
    Se resetea después de cada test y cierra correctamente la conexión SQLite.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Ahora Base y SQLModel comparten el mismo metadata, solo necesitamos una llamada
    SQLModel.metadata.create_all(engine)

    session = Session(engine)
    try:
        yield session
    finally:
        session.close()      # cierra la Session
        engine.dispose()     # cierra la conexión del pool (evita ResourceWarning)


@pytest.fixture
def sample_category(session):
    """Crea una categoría de prueba"""
    from src.models.category import Category, CategoryStatus
    from src.models.user import User
    
    # Crear usuario para la categoría
    user = User(
        name="Admin",
        last_name="Test",
        email="admin_cat@test.com",
        password="hashed_password"
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    # Crear categoría
    category = Category(
        name="Programación",
        description="Cursos de programación",
        status=CategoryStatus.ACTIVO,
        created_by=user.id
    )
    session.add(category)
    session.commit()
    session.refresh(category)
    return category

@pytest.fixture
def sample_course_data(sample_category):
    """Datos de ejemplo para crear un curso"""
    from src.models.course import CourseCreate
    
    return CourseCreate(
        title="Curso de Python",
        description="Aprende Python desde cero",
        place="Aula 101",
        course_image="python.jpg",
        course_image_detail="python_detail.jpg",
        category_id=sample_category.id,
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


@pytest.fixture
def sample_category_data():
    """Datos de ejemplo para crear una categoría"""
    from src.models.category import CategoryStatus
    
    return {
        "name": "Programación",
        "description": "Cursos de programación y desarrollo de software",
        "svgurl": "https://example.com/icons/programming.svg",
        "status": CategoryStatus.ACTIVO
    }


@pytest.fixture(name="db")
def db_fixture(session):
    """Alias para la sesión de base de datos"""
    return session


@pytest.fixture
def sample_user_platform(session):
    """Crea y retorna un usuario de plataforma de prueba"""
    from src.models.user_platform import UserPlatform, UserPlatformType
    
    user = UserPlatform(
        identification="1234567890",
        first_name="Pedro",
        second_name="Luis",
        first_last_name="Martínez",
        second_last_name="López",
        cellphone="0987654321",
        email="pedro.test@example.com",
        address="Calle Test 123",
        type=UserPlatformType.ESTUDIANTE,
        password="hashed_password_123"
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def sample_course(session, sample_category):
    """Crea y retorna un curso de prueba completo"""
    from src.models.course import Course, CourseRequirement, CourseStatus
    from datetime import date, time
    import json

    # Crear curso
    course = Course(
        title="Curso de Python Test",
        description="Curso de prueba",
        place="Aula 101",
        course_image="python.jpg",
        course_image_detail="python_detail.jpg",
        category_id=sample_category.id,
        status=CourseStatus.ACTIVO,
        objectives=json.dumps(["Objetivo 1", "Objetivo 2"]),
        organizers=json.dumps(["Universidad"]),
        materials=json.dumps(["Laptop"]),
        target_audience=json.dumps(["Estudiantes"])
    )
    session.add(course)
    session.commit()
    session.refresh(course)
    
    # Crear requisitos
    requirements = CourseRequirement(
        course_id=course.id,
        start_date_registration=date(2024, 1, 1),
        end_date_registration=date(2024, 1, 31),
        start_date_course=date(2024, 2, 1),
        end_date_course=date(2024, 3, 31),
        days=json.dumps(["Lunes", "Miércoles"]),
        start_time=time(14, 0),
        end_time=time(18, 0),
        location="Aula Virtual",
        min_quota=10,
        max_quota=30,
        in_person_hours=40,
        autonomous_hours=20,
        modality="Híbrida",
        certification="Certificado",
        prerequisites=json.dumps(["Ninguno"]),
        prices=json.dumps([{"type": "Estudiante", "amount": 100}])
    )
    session.add(requirements)
    session.commit()
    
    return course


@pytest.fixture
def sample_enrollment(session, sample_user_platform, sample_course):
    """Inscripción de prueba a un curso"""
    from src.models.enrollment import Enrollment, EnrollmentStatus
    from datetime import datetime

    enrollment = Enrollment(
        id_user_platform=sample_user_platform.id,
        id_course=sample_course.id,
        enrollment_date=datetime.utcnow(),
        status=EnrollmentStatus.INTERESADO
    )
    session.add(enrollment)
    session.commit()
    session.refresh(enrollment)
    return enrollment


@pytest.fixture
def sample_congress_enrollment(session, sample_user_platform, sample_congress):
    """Inscripción de prueba a un congreso"""
    from src.models.enrollment import Enrollment, EnrollmentStatus
    from datetime import datetime

    enrollment = Enrollment(
        id_user_platform=sample_user_platform.id,
        id_congress=sample_congress.id_congreso,  # Usar id_congreso del nuevo modelo
        enrollment_date=datetime.utcnow(),
        status=EnrollmentStatus.INTERESADO
    )
    session.add(enrollment)
    session.commit()
    session.refresh(enrollment)
    return enrollment


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
    
    from src.routes.congress_router import congress_router as congresses_router
    from src.routes.sponsor_router import sponsor_router
    from src.routes.speaker_router import speaker_router
    from src.routes.sesion_cronograma_router import sesion_cronograma_router
    from src.routes.congreso_sponsor_router import congreso_sponsor_router
    from src.routes.categories_router import categories_router
    from src.routes.congress_categories_router import congress_categories_router

    # Incluir routers
    test_app.include_router(auth_router)
    test_app.include_router(courses_router)
    test_app.include_router(platform_auth_router)
    test_app.include_router(categories_router)
    test_app.include_router(congress_categories_router)
    test_app.include_router(congresses_router)
    test_app.include_router(sponsor_router)
    test_app.include_router(speaker_router)
    test_app.include_router(sesion_cronograma_router)
    test_app.include_router(congreso_sponsor_router)

    # Crear cliente de test
    with TestClient(test_app) as test_client:
        yield test_client


# ==========================================
# Fixtures para Congresos
# ==========================================

# @pytest.fixture
# def sample_congress_data(sample_category):
#     """Datos de ejemplo para crear un congreso - OBSOLETO: usar sample_congress_new_data"""
#     from src.models.congress import CongressCreate, CongressStatus
#
#     return CongressCreate(
#         title="Congreso de Inteligencia Artificial",
#         description="Evento académico sobre IA y Machine Learning",
#         place="Auditorio Central FISEI",
#         congress_image="ia_congress.jpg",
#         congress_image_detail="ia_congress_detail.jpg",
#         category_id=sample_category.id,
#         status=CongressStatus.ACTIVO,
#         objectives=["Explorar avances en IA", "Fomentar la investigación"],
#         organizers=["FISEI-UTA", "Ing. Carlos Mora"],
#         materials=["Presentaciones digitales", "Credencial"],
#         target_audience=["Investigadores", "Estudiantes", "Profesionales"],
#     )


# @pytest.fixture
# def sample_congress_requirements_data():
#     """Datos de ejemplo para requisitos de congreso - OBSOLETO"""
#     from src.models.congress import CongressRequirementCreate
#
#     return CongressRequirementCreate(
#         start_date_registration=date(2025, 8, 1),
#         end_date_registration=date(2025, 9, 15),
#         start_date_congress=date(2025, 10, 8),
#         end_date_congress=date(2025, 10, 10),
#         days=["Miércoles", "Jueves", "Viernes"],
#         start_time=time(8, 30),
#         end_time=time(18, 0),
#         location="Auditorio Central FISEI",
#         min_quota=30,
#         max_quota=200,
#         in_person_hours=24,
#         autonomous_hours=8,
#         modality="Presencial",
#         certification="Certificado digital con validación QR",
#         prerequisites=["Conocimientos básicos en computación (recomendado)"],
#         prices=[
#             {"amount": 20, "category": "Estudiantes"},
#             {"amount": 50, "category": "Público general"},
#         ],
#     )


# @pytest.fixture
# def sample_congress_contents_data():
#     """Datos de ejemplo para contenidos de congreso - OBSOLETO"""
#     from src.models.congress import CongressContentCreate, CongressContentTopicRead
#
#     return [
#         CongressContentCreate(
#             unit="Día 1",
#             title="Fundamentos de IA",
#             topics=[
#                 CongressContentTopicRead(unit="Sesión 1", title="Keynote: El futuro de la IA Generativa"),
#                 CongressContentTopicRead(unit="Sesión 2", title="Machine Learning aplicado"),
#             ],
#         ),
#         CongressContentCreate(
#             unit="Día 2",
#             title="IA en la Industria",
#             topics=[
#                 CongressContentTopicRead(unit="Sesión 1", title="IA en salud y bienestar"),
#                 CongressContentTopicRead(unit="Panel", title="Ética en la IA"),
#             ],
#         ),
#     ]


@pytest.fixture
def sample_congress(session, sample_category):
    """Crea y retorna un congreso completo en la BD usando el nuevo modelo"""
    from src.models.congress_model import Congress
    from datetime import date

    # Note: Ahora usa el nuevo modelo Congress del congress_model
    congress = Congress(
        nombre="Congreso de Prueba",
        edicion="CP-2024-01",
        anio=2026,
        fecha_inicio=date(2026, 10, 1),
        fecha_fin=date(2026, 10, 3),
        descripcion_general="Congreso creado para tests",
        poster_cover_url="https://example.com/test.jpg"
    )
    session.add(congress)
    session.commit()
    session.refresh(congress)

    return congress


# ==========================================
# Fixtures para Nuevos Modelos CTT
# ==========================================

@pytest.fixture
def sample_congress_new_data():
    """Datos de ejemplo para crear un congreso nuevo"""
    from src.models.congress_model import CongressCreate
    from datetime import date

    return CongressCreate(
        nombre="Congreso Internacional de Teología 2024",
        edicion="CIT-2024-01",
        anio=2026,
        fecha_inicio=date(2026, 9, 15),
        fecha_fin=date(2026, 9, 17),
        descripcion_general="Congreso anual de teología con expertos internacionales.",
        poster_cover_url="https://example.com/poster2024.jpg"
    )


@pytest.fixture
def sample_congress_new(session):
    """Crea y retorna un congreso nuevo completo en la BD"""
    from src.models.congress_model import Congress
    from datetime import date

    congress = Congress(
        nombre="Congreso de Prueba Nuevo",
        edicion="CPN-2024-01",
        anio=2026,
        fecha_inicio=date(2026, 9, 15),
        fecha_fin=date(2026, 9, 17),
        descripcion_general="Congreso creado para tests del nuevo sistema",
        poster_cover_url="https://example.com/test_poster.jpg"
    )
    session.add(congress)
    session.commit()
    session.refresh(congress)
    return congress


@pytest.fixture
def sample_sponsor_data():
    """Datos de ejemplo para crear un sponsor"""
    from src.models.sponsor_model import SponsorCreate

    return SponsorCreate(
        nombre="Editorial Teológica Internacional",
        logo_url="https://example.com/logo.png",
        sitio_web="https://editorialteologica.com",
        descripcion="Editorial especializada en literatura teológica cristiana."
    )


@pytest.fixture
def sample_sponsor(session):
    """Crea y retorna un sponsor completo en la BD"""
    from src.models.sponsor_model import Sponsor

    sponsor = Sponsor(
        nombre="Sponsor de Prueba",
        logo_url="https://example.com/test_logo.png",
        sitio_web="https://testcompany.com",
        descripcion="Sponsor creado para pruebas unitarias"
    )
    session.add(sponsor)
    session.commit()
    session.refresh(sponsor)
    return sponsor


@pytest.fixture
def sample_speaker_data(sample_congress_new):
    """Datos de ejemplo para crear un speaker"""
    from src.models.speaker_model import SpeakerCreate

    return SpeakerCreate(
        id_congreso=sample_congress_new.id_congreso,
        nombres_completos="Dr. Juan Carlos Martínez",
        titulo_academico="Doctor en Teología",
        institucion="Universidad Teológica Latinoamericana",
        pais="Colombia",
        foto_url="https://example.com/speaker1.jpg",
        tipo_speaker="keynote"
    )


@pytest.fixture
def sample_speaker(session, sample_congress_new):
    """Crea y retorna un speaker completo en la BD"""
    from src.models.speaker_model import Speaker

    speaker = Speaker(
        id_congreso=sample_congress_new.id_congreso,
        nombres_completos="Dr. María González Test",
        titulo_academico="Doctora en Teología",
        institucion="Universidad de Prueba",
        pais="Ecuador",
        foto_url="https://example.com/test_speaker.jpg",
        tipo_speaker="keynote"
    )
    session.add(speaker)
    session.commit()
    session.refresh(speaker)
    return speaker


@pytest.fixture
def sample_sesion_cronograma_data(sample_congress_new, sample_speaker):
    """Datos de ejemplo para crear una sesión del cronograma"""
    from src.models.sesion_cronograma_model import SesionCronogramaCreate
    from datetime import date, time

    return SesionCronogramaCreate(
        id_congreso=sample_congress_new.id_congreso,
        id_speaker=sample_speaker.id_speaker,
        fecha=date(2026, 9, 15),
        hora_inicio=time(9, 0),
        hora_fin=time(10, 30),
        titulo_sesion="Teología Sistemática en el Siglo XXI",
        jornada="mañana",
        lugar="Auditorio Principal"
    )


@pytest.fixture
def sample_sesion_cronograma(session, sample_congress_new, sample_speaker):
    """Crea y retorna una sesión completa en la BD"""
    from src.models.sesion_cronograma_model import SesionCronograma
    from datetime import date, time

    sesion = SesionCronograma(
        id_congreso=sample_congress_new.id_congreso,
        id_speaker=sample_speaker.id_speaker,
        fecha=date(2026, 9, 15),
        hora_inicio=time(10, 0),
        hora_fin=time(11, 30),
        titulo_sesion="Sesión de Prueba",
        jornada="mañana",
        lugar="Aula Test"
    )
    session.add(sesion)
    session.commit()
    session.refresh(sesion)
    return sesion


@pytest.fixture
def sample_congreso_sponsor_data(sample_congress_new, sample_sponsor):
    """Datos de ejemplo para crear un sponsorship"""
    from src.models.congreso_sponsor_model import CongresoSponsorCreate
    from decimal import Decimal

    return CongresoSponsorCreate(
        id_congreso=sample_congress_new.id_congreso,
        id_sponsor=sample_sponsor.id_sponsor,
        categoria="oro",
        aporte=Decimal("5000.00")
    )


@pytest.fixture
def sample_congreso_sponsor(session, sample_congress_new, sample_sponsor):
    """Crea y retorna un sponsorship completo en la BD"""
    from src.models.congreso_sponsor_model import CongresoSponsor
    from decimal import Decimal

    sponsorship = CongresoSponsor(
        id_congreso=sample_congress_new.id_congreso,
        id_sponsor=sample_sponsor.id_sponsor,
        categoria="plata",
        aporte=Decimal("3000.00")
    )
    session.add(sponsorship)
    session.commit()
    session.refresh(sponsorship)
    return sponsorship


# ==========================================
# Fixtures para Congress Categories
# ==========================================

@pytest.fixture
def sample_congress_category(session):
    """Crea una categoría de congreso de prueba"""
    from src.models.congress_category import CongressCategory, CongressCategoryStatus
    from src.models.user import User

    # Crear usuario para la categoría
    user = User(
        name="Admin",
        last_name="Test",
        email="admin_congress_cat@test.com",
        password="hashed_password"
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    # Crear categoría de congreso
    category = CongressCategory(
        name="Tecnología",
        description="Congresos de tecnología e innovación",
        status=CongressCategoryStatus.ACTIVO,
        created_by=user.id
    )
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


@pytest.fixture
def sample_congress_category_data():
    """Datos de ejemplo para crear una categoría de congreso"""
    from src.models.congress_category import CongressCategoryStatus

    return {
        "name": "Tecnología",
        "description": "Congresos de tecnología e innovación",
        "svgurl": "https://example.com/icons/technology.svg",
        "status": CongressCategoryStatus.ACTIVO
    }

