from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from decimal import Decimal
from pydantic import BaseModel, field_validator
from .base import SponsorCategory

if TYPE_CHECKING:
    from .congress_model import Congress
    from .sponsor_model import Sponsor


# === Modelo SQLModel ===
class CongresoSponsor(SQLModel, table=True):
    __tablename__ = "congreso_sponsors"

    # Clave primaria compuesta
    id_congreso: int = Field(foreign_key="congresos.id_congreso", primary_key=True)
    id_sponsor: int = Field(foreign_key="sponsors.id_sponsor", primary_key=True)
    categoria: str = Field(max_length=50)
    aporte: Decimal = Field(max_digits=10, decimal_places=2)

    # Relaciones (usando forward references)
    congreso: Optional["Congress"] = Relationship(back_populates="congreso_sponsors")
    sponsor: Optional["Sponsor"] = Relationship(back_populates="congreso_sponsors")


# === Modelos Pydantic ===
class CongresoSponsorRead(BaseModel):
    """Modelo de lectura para CongresoSponsor"""
    id_congreso: int
    id_sponsor: int
    categoria: str
    aporte: Decimal

    class Config:
        from_attributes = True


class CongresoSponsorCreate(BaseModel):
    """Modelo de creación para CongresoSponsor"""
    id_congreso: int
    id_sponsor: int
    categoria: str
    aporte: Decimal

    @field_validator('categoria')
    @classmethod
    def validate_categoria(cls, v):
        valid_categories = [e.value for e in SponsorCategory]
        if v not in valid_categories:
            raise ValueError(f'La categoría debe ser una de: {", ".join(valid_categories)}')
        return v

    @field_validator('aporte')
    @classmethod
    def validate_aporte(cls, v):
        if v < 0:
            raise ValueError('El aporte no puede ser negativo')
        if v > 999999.99:
            raise ValueError('El aporte no puede exceder 999,999.99')
        return v

    class Config:
        str_strip_whitespace = True


class CongresoSponsorUpdate(BaseModel):
    """Modelo de actualización para CongresoSponsor"""
    categoria: Optional[str] = None
    aporte: Optional[Decimal] = None

    @field_validator('categoria')
    @classmethod
    def validate_categoria(cls, v):
        if v is not None:
            valid_categories = [e.value for e in SponsorCategory]
            if v not in valid_categories:
                raise ValueError(f'La categoría debe ser una de: {", ".join(valid_categories)}')
        return v

    @field_validator('aporte')
    @classmethod
    def validate_aporte(cls, v):
        if v is not None:
            if v < 0:
                raise ValueError('El aporte no puede ser negativo')
            if v > 999999.99:
                raise ValueError('El aporte no puede exceder 999,999.99')
        return v

    class Config:
        str_strip_whitespace = True


# === Modelo extendido con información completa ===
class CongresoSponsorWithDetails(BaseModel):
    """Modelo de lectura completo con información del congreso y sponsor"""
    id_congreso: int
    id_sponsor: int
    categoria: str
    aporte: Decimal
    congreso_nombre: str
    congreso_edicion: str
    sponsor_nombre: str
    sponsor_logo_url: str

    class Config:
        from_attributes = True


# === Modelo para consultas agregadas ===
class CongresoSponsorSummary(BaseModel):
    """Modelo para resumen de sponsorships por congreso"""
    id_congreso: int
    congreso_nombre: str
    total_sponsors: int
    total_aporte: Decimal
    sponsors_por_categoria: dict

    class Config:
        from_attributes = True