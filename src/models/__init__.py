"""
Modelos de SQLAlchemy para el sistema de congresos.

Este módulo contiene todos los modelos de base de datos organizados por tabla:
- Congress: Información principal de congresos
- Sponsor: Patrocinadores/sponsors
- Speaker: Ponentes/expositores
- SesionCronograma: Cronograma de sesiones
- CongresoSponsor: Relación muchos-a-muchos entre congresos y sponsors
- User: Usuarios del sistema
- Category: Categorías para cursos
- CongressCategory: Categorías para congresos
- Course: Cursos educativos
- CourseRequirement: Requisitos de cursos
- CourseContent: Contenido de cursos

Cada modelo incluye:
- Clase SQLAlchemy para ORM
- Modelos Pydantic para validación (Read, Create, Update)
- Validaciones personalizadas
"""

# Importar base y enums
from .base import Base, CongressStatus, SponsorCategory, SpeakerType, Jornada

# Importar modelos SQLAlchemy
from .congress_model import Congress
from .sponsor_model import Sponsor
from .speaker_model import Speaker
from .sesion_cronograma_model import SesionCronograma
from .congreso_sponsor_model import CongresoSponsor
from .user import User
from .category import Category, CategoryStatus
from .congress_category import CongressCategory, CongressCategoryStatus
from .course import Course, CourseRequirement, CourseContent, CourseStatus

# Importar modelos Pydantic para Congress
from .congress_model import (
    CongressRead, CongressCreate, CongressUpdate,
    CongressLegacyRead, CongressLegacyCreate, CongressLegacyUpdate
)

# Importar modelos Pydantic para Sponsor
from .sponsor_model import (
    SponsorRead, SponsorCreate, SponsorUpdate
)

# Importar modelos Pydantic para Speaker
from .speaker_model import (
    SpeakerRead, SpeakerCreate, SpeakerUpdate
)

# Importar modelos Pydantic para SesionCronograma
from .sesion_cronograma_model import (
    SesionCronogramaRead, SesionCronogramaCreate, SesionCronogramaUpdate,
    SesionCronogramaWithSpeaker
)

# Importar modelos Pydantic para CongresoSponsor
from .congreso_sponsor_model import (
    CongresoSponsorRead, CongresoSponsorCreate, CongresoSponsorUpdate,
    CongresoSponsorWithDetails, CongresoSponsorSummary
)

# Importar modelos Pydantic para User
from .user import (
    UserRead, UserCreate, UserUpdate, UserWithStats
)

# Importar modelos Pydantic para Category
from .category import (
    CategoryRead, CategoryCreate, CategoryUpdate,
    CategoryWithCreator, CategoryWithCourses
)

# Importar modelos Pydantic para CongressCategory
from .congress_category import (
    CongressCategoryRead, CongressCategoryCreate, CongressCategoryUpdate,
    CongressCategoryWithCreator, CongressCategoryWithCongresses
)

# Importar modelos Pydantic para Course
from .course import (
    CourseRead, CourseCreate, CourseUpdate,
    CourseRequirementRead, CourseRequirementCreate, CourseRequirementUpdate,
    CourseContentRead, CourseContentCreate, CourseContentUpdate,
    CourseContentTopicRead
)

# Lista de todos los modelos SQLAlchemy para crear tablas
SQLALCHEMY_MODELS = [
    Congress,
    Sponsor,
    Speaker,
    SesionCronograma,
    CongresoSponsor,
    User,
    Category,
    CongressCategory,
    Course,
    CourseRequirement,
    CourseContent
]

# Lista de todos los modelos Pydantic para validación
PYDANTIC_MODELS = {
    # Congress models
    'congress': {
        'read': CongressRead,
        'create': CongressCreate,
        'update': CongressUpdate,
        'legacy_read': CongressLegacyRead,
        'legacy_create': CongressLegacyCreate,
        'legacy_update': CongressLegacyUpdate,
    },
    # Sponsor models
    'sponsor': {
        'read': SponsorRead,
        'create': SponsorCreate,
        'update': SponsorUpdate,
    },
    # Speaker models
    'speaker': {
        'read': SpeakerRead,
        'create': SpeakerCreate,
        'update': SpeakerUpdate,
    },
    # SesionCronograma models
    'sesion_cronograma': {
        'read': SesionCronogramaRead,
        'create': SesionCronogramaCreate,
        'update': SesionCronogramaUpdate,
        'with_speaker': SesionCronogramaWithSpeaker,
    },
    # CongresoSponsor models
    'congreso_sponsor': {
        'read': CongresoSponsorRead,
        'create': CongresoSponsorCreate,
        'update': CongresoSponsorUpdate,
        'with_details': CongresoSponsorWithDetails,
        'summary': CongresoSponsorSummary,
    },
    # User models
    'user': {
        'read': UserRead,
        'create': UserCreate,
        'update': UserUpdate,
        'with_stats': UserWithStats,
    },
    # Category models
    'category': {
        'read': CategoryRead,
        'create': CategoryCreate,
        'update': CategoryUpdate,
        'with_creator': CategoryWithCreator,
        'with_courses': CategoryWithCourses,
    },
    # CongressCategory models
    'congress_category': {
        'read': CongressCategoryRead,
        'create': CongressCategoryCreate,
        'update': CongressCategoryUpdate,
        'with_creator': CongressCategoryWithCreator,
        'with_congresses': CongressCategoryWithCongresses,
    },
    # Course models
    'course': {
        'read': CourseRead,
        'create': CourseCreate,
        'update': CourseUpdate,
    },
    'course_requirement': {
        'read': CourseRequirementRead,
        'create': CourseRequirementCreate,
        'update': CourseRequirementUpdate,
    },
    'course_content': {
        'read': CourseContentRead,
        'create': CourseContentCreate,
        'update': CourseContentUpdate,
        'topic_read': CourseContentTopicRead,
    }
}

# Exportar todo para facilitar importación
__all__ = [
    # Base y enums
    'Base', 'CongressStatus', 'SponsorCategory', 'SpeakerType', 'Jornada', 'CategoryStatus', 'CongressCategoryStatus', 'CourseStatus',

    # Modelos SQLAlchemy
    'Congress', 'Sponsor', 'Speaker', 'SesionCronograma', 'CongresoSponsor', 'User', 'Category', 'CongressCategory',
    'Course', 'CourseRequirement', 'CourseContent',

    # Modelos Pydantic - Congress
    'CongressRead', 'CongressCreate', 'CongressUpdate',
    'CongressLegacyRead', 'CongressLegacyCreate', 'CongressLegacyUpdate',

    # Modelos Pydantic - Sponsor
    'SponsorRead', 'SponsorCreate', 'SponsorUpdate',

    # Modelos Pydantic - Speaker
    'SpeakerRead', 'SpeakerCreate', 'SpeakerUpdate',

    # Modelos Pydantic - SesionCronograma
    'SesionCronogramaRead', 'SesionCronogramaCreate', 'SesionCronogramaUpdate',
    'SesionCronogramaWithSpeaker',

    # Modelos Pydantic - CongresoSponsor
    'CongresoSponsorRead', 'CongresoSponsorCreate', 'CongresoSponsorUpdate',
    'CongresoSponsorWithDetails', 'CongresoSponsorSummary',

    # Modelos Pydantic - User
    'UserRead', 'UserCreate', 'UserUpdate', 'UserWithStats',

    # Modelos Pydantic - Category
    'CategoryRead', 'CategoryCreate', 'CategoryUpdate', 'CategoryWithCreator', 'CategoryWithCourses',

    # Modelos Pydantic - CongressCategory
    'CongressCategoryRead', 'CongressCategoryCreate', 'CongressCategoryUpdate',
    'CongressCategoryWithCreator', 'CongressCategoryWithCongresses',

    # Modelos Pydantic - Course
    'CourseRead', 'CourseCreate', 'CourseUpdate',
    'CourseRequirementRead', 'CourseRequirementCreate', 'CourseRequirementUpdate',
    'CourseContentRead', 'CourseContentCreate', 'CourseContentUpdate', 'CourseContentTopicRead',

    # Utilidades
    'SQLALCHEMY_MODELS', 'PYDANTIC_MODELS'
]


def create_all_tables(engine):
    """
    Crear todas las tablas en la base de datos.

    Args:
        engine: Engine de SQLAlchemy

    Returns:
        None
    """
    Base.metadata.create_all(engine)


def get_model_by_table_name(table_name: str):
    """
    Obtener modelo SQLAlchemy por nombre de tabla.

    Args:
        table_name: Nombre de la tabla

    Returns:
        Clase del modelo SQLAlchemy o None si no existe
    """
    table_mapping = {
        'congresos': Congress,
        'sponsors': Sponsor,
        'speakers': Speaker,
        'sesiones_cronograma': SesionCronograma,
        'congreso_sponsors': CongresoSponsor,
        'users': User,
        'categories': Category,
        'congress_categories': CongressCategory,
        'course': Course,
        'courserequirement': CourseRequirement,
        'coursecontent': CourseContent,
    }
    return table_mapping.get(table_name)