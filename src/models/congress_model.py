from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional, TYPE_CHECKING
from datetime import date
from pydantic import BaseModel, field_validator, model_validator
from .base import CongressStatus

if TYPE_CHECKING:
    from .speaker_model import Speaker
    from .sesion_cronograma_model import SesionCronograma
    from .congreso_sponsor_model import CongresoSponsor


# === Modelo SQLModel ===
class Congress(SQLModel, table=True):
    __tablename__ = "congresos"

    id_congreso: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=100)
    edicion: str = Field(max_length=10)
    anio: int
    fecha_inicio: date
    fecha_fin: date
    descripcion_general: str
    poster_cover_url: str = Field(max_length=300)

    # Relaciones (usando forward references)
    speakers: List["Speaker"] = Relationship(back_populates="congreso")
    sesiones: List["SesionCronograma"] = Relationship(back_populates="congreso")
    congreso_sponsors: List["CongresoSponsor"] = Relationship(back_populates="congreso")


# === Modelos Pydantic ===
class CongressRead(BaseModel):
    """Modelo de lectura para Congress"""
    id_congreso: int
    nombre: str
    edicion: str
    anio: int
    fecha_inicio: date
    fecha_fin: date
    descripcion_general: str
    poster_cover_url: str

    class Config:
        from_attributes = True


class CongressCreate(BaseModel):
    """Modelo de creación para Congress"""
    nombre: str
    edicion: str
    anio: int
    fecha_inicio: date
    fecha_fin: date
    descripcion_general: str
    poster_cover_url: str

    @field_validator('anio')
    @classmethod
    def validate_year(cls, v):
        if v < 2000 or v > 2100:
            raise ValueError('El año debe estar entre 2000 y 2100')
        return v

    @model_validator(mode='after')
    def validate_dates(self):
        if self.fecha_fin <= self.fecha_inicio:
            raise ValueError('La fecha de fin debe ser posterior a la fecha de inicio')
        return self

    class Config:
        str_strip_whitespace = True


class CongressUpdate(BaseModel):
    """Modelo de actualización para Congress"""
    nombre: Optional[str] = None
    edicion: Optional[str] = None
    anio: Optional[int] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    descripcion_general: Optional[str] = None
    poster_cover_url: Optional[str] = None

    @field_validator('anio')
    @classmethod
    def validate_year(cls, v):
        if v is not None and (v < 2000 or v > 2100):
            raise ValueError('El año debe estar entre 2000 y 2100')
        return v

    class Config:
        str_strip_whitespace = True


# === Modelo de compatibilidad con versión anterior ===
class CongressLegacyRead(BaseModel):
    """Modelo de compatibilidad con la estructura anterior"""
    id: int  # Mapea a id_congreso
    title: str  # Mapea a nombre
    description: str  # Mapea a descripcion_general
    place: Optional[str] = None  # Campo legacy
    congress_image: Optional[str] = None  # Campo legacy
    congress_image_detail: Optional[str] = None  # Campo legacy
    category: Optional[str] = None  # Campo legacy
    status: Optional[CongressStatus] = None  # Campo legacy
    objectives: List[str] = []  # Campo legacy
    organizers: List[str] = []  # Campo legacy
    materials: List[str] = []  # Campo legacy
    target_audience: List[str] = []  # Campo legacy

    class Config:
        from_attributes = True


class CongressLegacyCreate(BaseModel):
    """Modelo de compatibilidad para creación con estructura anterior"""
    title: str  # Mapea a nombre
    description: str  # Mapea a descripcion_general
    place: Optional[str] = None
    congress_image: Optional[str] = None
    congress_image_detail: Optional[str] = None
    category_id: Optional[int] = None
    congress_category_id: Optional[int] = None
    status: CongressStatus = CongressStatus.ACTIVO
    objectives: List[str] = []
    organizers: List[str] = []
    materials: List[str] = []
    target_audience: List[str] = []

    class Config:
        str_strip_whitespace = True


class CongressLegacyUpdate(BaseModel):
    """Modelo de compatibilidad para actualización con estructura anterior"""
    title: Optional[str] = None
    description: Optional[str] = None
    place: Optional[str] = None
    congress_image: Optional[str] = None
    congress_image_detail: Optional[str] = None
    category: Optional[str] = None
    congress_category_id: Optional[int] = None
    status: Optional[CongressStatus] = None
    objectives: Optional[List[str]] = None
    organizers: Optional[List[str]] = None
    materials: Optional[List[str]] = None
    target_audience: Optional[List[str]] = None

    class Config:
        str_strip_whitespace = True