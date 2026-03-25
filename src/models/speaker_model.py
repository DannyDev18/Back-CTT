from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional, TYPE_CHECKING
from pydantic import BaseModel, field_validator
from .base import SpeakerType

if TYPE_CHECKING:
    from .congress_model import Congress
    from .sesion_cronograma_model import SesionCronograma


# === Modelo SQLModel ===
class Speaker(SQLModel, table=True):
    __tablename__ = "speakers"

    id_speaker: Optional[int] = Field(default=None, primary_key=True)
    id_congreso: int = Field(foreign_key="congresos.id_congreso")
    nombres_completos: str = Field(max_length=200)
    titulo_academico: str = Field(max_length=50)
    institucion: str = Field(max_length=200)
    pais: str = Field(max_length=100)
    foto_url: str = Field(max_length=300)
    tipo_speaker: str = Field(max_length=20)

    # Relaciones (usando forward references)
    congreso: Optional["Congress"] = Relationship(back_populates="speakers")
    sesiones: List["SesionCronograma"] = Relationship(back_populates="speaker")


# === Modelos Pydantic ===
class SpeakerRead(BaseModel):
    """Modelo de lectura para Speaker"""
    id_speaker: int
    id_congreso: int
    nombres_completos: str
    titulo_academico: str
    institucion: str
    pais: str
    foto_url: str
    tipo_speaker: str

    class Config:
        from_attributes = True


class SpeakerCreate(BaseModel):
    """Modelo de creación para Speaker"""
    id_congreso: int
    nombres_completos: str
    titulo_academico: str
    institucion: str
    pais: str
    foto_url: Optional[str] = "https://via.placeholder.com/150"
    tipo_speaker: str

    @field_validator('nombres_completos')
    @classmethod
    def validate_nombres_completos(cls, v):
        if len(v.strip()) < 3:
            raise ValueError('Los nombres completos deben tener al menos 3 caracteres')
        # Validar que tenga al menos nombre y apellido
        words = v.strip().split()
        if len(words) < 2:
            raise ValueError('Debe incluir al menos nombre y apellido')
        return v.strip()

    @field_validator('foto_url')
    @classmethod
    def validate_foto_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            v = 'https://' + v
        return v

    @field_validator('tipo_speaker')
    @classmethod
    def validate_tipo_speaker(cls, v):
        valid_types = [e.value for e in SpeakerType]
        if v not in valid_types:
            raise ValueError(f'Tipo de speaker debe ser uno de: {", ".join(valid_types)}')
        return v

    @field_validator('pais')
    @classmethod
    def validate_pais(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('El país debe tener al menos 2 caracteres')
        return v.strip().title()

    class Config:
        str_strip_whitespace = True


class SpeakerUpdate(BaseModel):
    """Modelo de actualización para Speaker"""
    nombres_completos: Optional[str] = None
    titulo_academico: Optional[str] = None
    institucion: Optional[str] = None
    pais: Optional[str] = None
    foto_url: Optional[str] = None
    tipo_speaker: Optional[str] = None

    @field_validator('nombres_completos')
    @classmethod
    def validate_nombres_completos(cls, v):
        if v is not None:
            if len(v.strip()) < 3:
                raise ValueError('Los nombres completos deben tener al menos 3 caracteres')
            words = v.strip().split()
            if len(words) < 2:
                raise ValueError('Debe incluir al menos nombre y apellido')
        return v.strip() if v else v

    @field_validator('foto_url')
    @classmethod
    def validate_foto_url(cls, v):
        if v is not None and not v.startswith(('http://', 'https://')):
            v = 'https://' + v
        return v

    @field_validator('tipo_speaker')
    @classmethod
    def validate_tipo_speaker(cls, v):
        if v is not None:
            valid_types = [e.value for e in SpeakerType]
            if v not in valid_types:
                raise ValueError(f'Tipo de speaker debe ser uno de: {", ".join(valid_types)}')
        return v

    @field_validator('pais')
    @classmethod
    def validate_pais(cls, v):
        if v is not None and len(v.strip()) < 2:
            raise ValueError('El país debe tener al menos 2 caracteres')
        return v.strip().title() if v else v

    class Config:
        str_strip_whitespace = True