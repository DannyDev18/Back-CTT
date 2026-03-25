from __future__ import annotations
from sqlalchemy import String, Integer, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional, TYPE_CHECKING
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, field_validator
from .base import Base

if TYPE_CHECKING:
    from .course import Course
    from .user import User


class CategoryStatus(str, Enum):
    ACTIVO = "activo"
    INACTIVO = "inactivo"


# === Modelo SQLAlchemy ===
class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    svgurl: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[CategoryStatus] = mapped_column(
        SQLEnum(CategoryStatus),
        nullable=False,
        default=CategoryStatus.ACTIVO
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)

    # Relaciones
    courses: Mapped[List[Course]] = relationship("Course", back_populates="category_rel")
    creator: Mapped[User] = relationship("User", back_populates="categories")


# === Modelos Pydantic ===
class CategoryRead(BaseModel):
    """Modelo de lectura para Category"""
    id: int
    name: str
    description: Optional[str]
    svgurl: Optional[str]
    status: CategoryStatus
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: int

    class Config:
        from_attributes = True


class CategoryCreate(BaseModel):
    """Modelo de creación para Category"""
    name: str
    description: Optional[str] = None
    svgurl: Optional[str] = None
    status: CategoryStatus = CategoryStatus.ACTIVO

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


class CategoryUpdate(BaseModel):
    """Modelo de actualización para Category"""
    name: Optional[str] = None
    description: Optional[str] = None
    svgurl: Optional[str] = None
    status: Optional[CategoryStatus] = None

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


class CategoryWithCreator(BaseModel):
    """Modelo de respuesta con información del creador"""
    id: int
    name: str
    description: Optional[str]
    svgurl: Optional[str]
    status: CategoryStatus
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: int
    creator_name: Optional[str]
    creator_email: Optional[str]
    courses_count: int

    class Config:
        from_attributes = True


class CategoryWithCourses(BaseModel):
    """Modelo de respuesta con cursos asociados"""
    id: int
    name: str
    description: Optional[str]
    svgurl: Optional[str]
    status: CategoryStatus
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: int
    courses: List[Course]

    class Config:
        from_attributes = True
