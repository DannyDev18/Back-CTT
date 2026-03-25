from sqlalchemy.orm import DeclarativeBase
from sqlmodel import SQLModel
from enum import Enum


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models that shares metadata with SQLModel"""
    # Usar el mismo metadata que SQLModel para permitir foreign keys entre ambos sistemas
    metadata = SQLModel.metadata


class CongressStatus(str, Enum):
    ACTIVO = "activo"
    INACTIVO = "inactivo"


class SponsorCategory(str, Enum):
    PLATINO = "platino"
    ORO = "oro"
    PLATA = "plata"
    BRONCE = "bronce"
    COLABORADOR = "colaborador"


class SpeakerType(str, Enum):
    KEYNOTE = "keynote"
    CONFERENCIA = "conferencia"
    TALLER = "taller"
    PANEL = "panel"


class Jornada(str, Enum):
    MANANA = "mañana"
    TARDE = "tarde"
    NOCHE = "noche"