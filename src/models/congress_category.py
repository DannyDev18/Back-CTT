from sqlalchemy import String, Integer, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, field_validator
from .base import Base


class CongressCategoryStatus(str, Enum):
    ACTIVO = "activo"
    INACTIVO = "inactivo"


# === Modelo SQLAlchemy ===
class CongressCategory(Base):
    __tablename__ = "congress_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    svgurl: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[CongressCategoryStatus] = mapped_column(
        SQLEnum(CongressCategoryStatus),
        nullable=False,
        default=CongressCategoryStatus.ACTIVO
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)

    # Relaciones (usando forward references)
    # TODO: Descomentar cuando Congress esté disponible
    # congresss: Mapped[List["Congress"]] = relationship("Congress", back_populates="congress_category_rel")
    creator: Mapped["User"] = relationship("User", back_populates="congress_categories")


# === Modelos Pydantic ===
class CongressCategoryRead(BaseModel):
    """Modelo de lectura para CongressCategory"""
    id: int
    name: str
    description: Optional[str]
    svgurl: Optional[str]
    status: CongressCategoryStatus
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: int

    class Config:
        from_attributes = True


class CongressCategoryCreate(BaseModel):
    """Modelo de creación para CongressCategory"""
    name: str
    description: Optional[str] = None
    svgurl: Optional[str] = None
    status: CongressCategoryStatus = CongressCategoryStatus.ACTIVO

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if len(v.strip()) < 1:
            raise ValueError('El nombre de la categoría no puede estar vacío')
        if len(v.strip()) > 150:
            raise ValueError('El nombre de la categoría no puede exceder 150 caracteres')
        return v.strip()

    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        if v is not None and len(v.strip()) > 500:
            raise ValueError('La descripción no puede exceder 500 caracteres')
        return v.strip() if v else v

    @field_validator('svgurl')
    @classmethod
    def validate_svgurl(cls, v):
        if v is not None and len(v.strip()) > 500:
            raise ValueError('La URL del SVG no puede exceder 500 caracteres')
        return v.strip() if v else v

    class Config:
        str_strip_whitespace = True


class CongressCategoryUpdate(BaseModel):
    """Modelo de actualización para CongressCategory"""
    name: Optional[str] = None
    description: Optional[str] = None
    svgurl: Optional[str] = None
    status: Optional[CongressCategoryStatus] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if v is not None:
            if len(v.strip()) < 1:
                raise ValueError('El nombre de la categoría no puede estar vacío')
            if len(v.strip()) > 150:
                raise ValueError('El nombre de la categoría no puede exceder 150 caracteres')
        return v.strip() if v else v

    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        if v is not None and len(v.strip()) > 500:
            raise ValueError('La descripción no puede exceder 500 caracteres')
        return v.strip() if v else v

    @field_validator('svgurl')
    @classmethod
    def validate_svgurl(cls, v):
        if v is not None and len(v.strip()) > 500:
            raise ValueError('La URL del SVG no puede exceder 500 caracteres')
        return v.strip() if v else v

    class Config:
        str_strip_whitespace = True


class CongressCategoryWithCreator(BaseModel):
    """Modelo de respuesta con información del creador"""
    id: int
    name: str
    description: Optional[str]
    svgurl: Optional[str]
    status: CongressCategoryStatus
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: int
    creator_name: Optional[str]
    creator_email: Optional[str]
    congresss_count: int

    class Config:
        from_attributes = True


class CongressCategoryWithCongresses(BaseModel):
    """Modelo de respuesta con los congresos asociados"""
    id: int
    name: str
    description: Optional[str]
    svgurl: Optional[str]
    status: CongressCategoryStatus
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: int
    # TODO: Descomentar cuando Congress esté disponible
    # congresss: List["Congress"]

    class Config:
        from_attributes = True
