from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional, TYPE_CHECKING
from pydantic import BaseModel, field_validator, HttpUrl

if TYPE_CHECKING:
    from .congreso_sponsor_model import CongresoSponsor


# === Modelo SQLModel ===
class Sponsor(SQLModel, table=True):
    __tablename__ = "sponsors"

    id_sponsor: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=150)
    logo_url: str = Field(max_length=300)
    sitio_web: str = Field(max_length=200)
    descripcion: str

    # Relaciones (usando forward references)
    congreso_sponsors: List["CongresoSponsor"] = Relationship(back_populates="sponsor")


# === Modelos Pydantic ===
class SponsorRead(BaseModel):
    """Modelo de lectura para Sponsor"""
    id_sponsor: int
    nombre: str
    logo_url: str
    sitio_web: str
    descripcion: str

    class Config:
        from_attributes = True


class SponsorCreate(BaseModel):
    """Modelo de creación para Sponsor"""
    nombre: str
    logo_url: Optional[str] = "https://via.placeholder.com/150"
    sitio_web: str
    descripcion: str

    @field_validator('nombre')
    @classmethod
    def validate_nombre(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('El nombre del sponsor debe tener al menos 2 caracteres')
        return v.strip()

    @field_validator('sitio_web')
    @classmethod
    def validate_sitio_web(cls, v):
        if not v.startswith(('http://', 'https://')):
            v = 'https://' + v
        return v

    @field_validator('logo_url')
    @classmethod
    def validate_logo_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            v = 'https://' + v
        return v

    class Config:
        str_strip_whitespace = True


class SponsorUpdate(BaseModel):
    """Modelo de actualización para Sponsor"""
    nombre: Optional[str] = None
    logo_url: Optional[str] = None
    sitio_web: Optional[str] = None
    descripcion: Optional[str] = None

    @field_validator('nombre')
    @classmethod
    def validate_nombre(cls, v):
        if v is not None and len(v.strip()) < 2:
            raise ValueError('El nombre del sponsor debe tener al menos 2 caracteres')
        return v.strip() if v else v

    @field_validator('sitio_web')
    @classmethod
    def validate_sitio_web(cls, v):
        if v is not None and not v.startswith(('http://', 'https://')):
            v = 'https://' + v
        return v

    @field_validator('logo_url')
    @classmethod
    def validate_logo_url(cls, v):
        if v is not None and not v.startswith(('http://', 'https://')):
            v = 'https://' + v
        return v

    class Config:
        str_strip_whitespace = True