"""
Repositorios para operaciones de base de datos.

Este módulo centraliza todos los repositorios del proyecto, incluyendo:
- Repositorios existentes (cursos, usuarios, posts, etc.)
- Nuevos repositorios para el sistema de congresos
- Clase base reutilizable para operaciones CRUD

Los repositorios proporcionan una capa de abstracción entre los controladores
y la base de datos, manejando operaciones complejas, consultas optimizadas
y lógica de negocio relacionada con datos.
"""

# Importar repositorios existentes
from src.repositories.course_repository import CourseRepository
from src.repositories.user_platform_repository import UserPlatformRepository
from src.repositories.post_repository import PostRepository

# Importar clase base y utilidades
from src.repositories.base_repository import (
    BaseRepository,
    RepositoryError,
    NotFoundError,
    DuplicateError,
    handle_repository_errors
)

# Importar nuevos repositorios de congresos
from src.repositories.congress_repository import (
    CongressRepository,
    congress_repository
)
from src.repositories.sponsor_repository import (
    SponsorRepository,
    sponsor_repository
)
from src.repositories.speaker_repository import (
    SpeakerRepository,
    speaker_repository
)
from src.repositories.sesion_cronograma_repository import (
    SesionCronogramaRepository,
    sesion_cronograma_repository
)
from src.repositories.congreso_sponsor_repository import (
    CongresoSponsorRepository,
    congreso_sponsor_repository
)

# Instancias predefinidas para uso directo (patrón singleton)
CONGRESS_REPOSITORIES = {
    'congress': congress_repository,
    'sponsor': sponsor_repository,
    'speaker': speaker_repository,
    'sesion_cronograma': sesion_cronograma_repository,
    'congreso_sponsor': congreso_sponsor_repository,
}

# Lista de todas las clases de repositorio
REPOSITORY_CLASSES = [
    # Repositorios existentes
    CourseRepository,
    UserPlatformRepository,
    PostRepository,

    # Nuevos repositorios de congresos
    CongressRepository,
    SponsorRepository,
    SpeakerRepository,
    SesionCronogramaRepository,
    CongresoSponsorRepository,
]

# Exportar todo para facilitar importación
__all__ = [
    # Repositorios existentes
    "CourseRepository",
    "UserPlatformRepository",
    "PostRepository",

    # Clase base y utilidades
    "BaseRepository",
    "RepositoryError",
    "NotFoundError",
    "DuplicateError",
    "handle_repository_errors",

    # Nuevos repositorios de congresos (clases)
    "CongressRepository",
    "SponsorRepository",
    "SpeakerRepository",
    "SesionCronogramaRepository",
    "CongresoSponsorRepository",

    # Nuevos repositorios de congresos (instancias)
    "congress_repository",
    "sponsor_repository",
    "speaker_repository",
    "sesion_cronograma_repository",
    "congreso_sponsor_repository",

    # Utilidades
    "CONGRESS_REPOSITORIES",
    "REPOSITORY_CLASSES",
]


def get_congress_repository(repository_name: str):
    """
    Obtener repositorio de congresos por nombre.

    Args:
        repository_name: Nombre del repositorio ('congress', 'sponsor', etc.)

    Returns:
        Instancia del repositorio o None si no existe
    """
    return CONGRESS_REPOSITORIES.get(repository_name)


def get_all_congress_repositories() -> dict:
    """
    Obtener todas las instancias de repositorios de congresos.

    Returns:
        dict: Diccionario con todas las instancias de repositorios
    """
    return CONGRESS_REPOSITORIES.copy()


class RepositoryManager:
    """
    Gestor centralizado de repositorios.

    Proporciona acceso unificado a todos los repositorios del sistema
    y funciones de utilidad para operaciones comunes.
    """

    def __init__(self):
        # Repositorios de congresos
        self.congress = congress_repository
        self.sponsor = sponsor_repository
        self.speaker = speaker_repository
        self.sesion_cronograma = sesion_cronograma_repository
        self.congreso_sponsor = congreso_sponsor_repository

        # Repositorios existentes se pueden agregar aquí si se necesita

    def get_repository(self, name: str):
        """Obtener repositorio por nombre."""
        return getattr(self, name, None)

    def get_all_repositories(self) -> dict:
        """Obtener todos los repositorios disponibles."""
        return {
            'congress': self.congress,
            'sponsor': self.sponsor,
            'speaker': self.speaker,
            'sesion_cronograma': self.sesion_cronograma,
            'congreso_sponsor': self.congreso_sponsor,
        }


# Instancia global del gestor de repositorios
repository_manager = RepositoryManager()
