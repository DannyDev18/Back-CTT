from __future__ import annotations
from sqlalchemy import String, Integer, DateTime, ForeignKey, Enum as SQLEnum, Date, Time, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional, TYPE_CHECKING
from datetime import date, time, datetime
from enum import Enum
from pydantic import BaseModel, field_validator, computed_field
from .base import Base

if TYPE_CHECKING:
    from .category import Category


class CourseStatus(str, Enum):
    ACTIVO = "activo"
    INACTIVO = "inactivo"

# === Modelo SQLAlchemy ===
class Course(Base):
    __tablename__ = "course"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    place: Mapped[str] = mapped_column(String(200), nullable=False)
    course_image: Mapped[str] = mapped_column(String(500), nullable=False)
    course_image_detail: Mapped[str] = mapped_column(String(500), nullable=False)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    status: Mapped[CourseStatus] = mapped_column(
        SQLEnum(CourseStatus),
        nullable=False,
        default=CourseStatus.ACTIVO
    )
    objectives: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string
    organizers: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string
    materials: Mapped[str] = mapped_column(Text, nullable=False)   # JSON string
    target_audience: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string

    # Relaciones
    category_rel: Mapped[Category] = relationship("Category", back_populates="courses")
    requirement: Mapped[Optional[CourseRequirement]] = relationship("CourseRequirement", back_populates="course")
    contents: Mapped[List[CourseContent]] = relationship("CourseContent", back_populates="course")

class CourseRequirement(Base):
    __tablename__ = "courserequirement"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey("course.id"), unique=True, nullable=False)
    start_date_registration: Mapped[date] = mapped_column(Date, nullable=False)
    end_date_registration: Mapped[date] = mapped_column(Date, nullable=False)
    start_date_course: Mapped[date] = mapped_column(Date, nullable=False)
    end_date_course: Mapped[date] = mapped_column(Date, nullable=False)
    days: Mapped[str] = mapped_column(Text, nullable=False)  # JSON: List[str]
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    location: Mapped[str] = mapped_column(String(200), nullable=False)
    min_quota: Mapped[int] = mapped_column(Integer, nullable=False)
    max_quota: Mapped[int] = mapped_column(Integer, nullable=False)
    in_person_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    autonomous_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    modality: Mapped[str] = mapped_column(String(100), nullable=False)
    certification: Mapped[str] = mapped_column(String(200), nullable=False)
    prerequisites: Mapped[str] = mapped_column(Text, nullable=False)  # JSON: List[str]
    prices: Mapped[str] = mapped_column(Text, nullable=False)  # JSON: List[dict]

    # Relación
    course: Mapped[Optional[Course]] = relationship("Course", back_populates="requirement")


class CourseContent(Base):
    __tablename__ = "coursecontent"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey("course.id"), nullable=False)
    unit: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    topics: Mapped[str] = mapped_column(Text, nullable=False)  # JSON: List[dict]

    # Relación
    course: Mapped[Optional[Course]] = relationship("Course", back_populates="contents")

# === Modelos Pydantic ===
class CourseRequirementRead(BaseModel):
    """Modelo de lectura para CourseRequirement"""
    id: int
    course_id: int
    start_date_registration: date
    end_date_registration: date
    start_date_course: date
    end_date_course: date
    days: List[str]
    start_time: time
    end_time: time
    location: str
    min_quota: int
    max_quota: int
    in_person_hours: int
    autonomous_hours: int
    modality: str
    certification: str
    prerequisites: List[str]
    prices: List[dict]

    @computed_field
    @property
    def total_hours(self) -> int:
        return self.in_person_hours + self.autonomous_hours

    class Config:
        from_attributes = True


class CourseContentTopicRead(BaseModel):
    """Modelo de lectura para temas de contenido"""
    unit: str
    title: str

    class Config:
        from_attributes = True


class CourseContentRead(BaseModel):
    """Modelo de lectura para CourseContent"""
    id: int
    unit: str
    title: str
    topics: List[CourseContentTopicRead]

    class Config:
        from_attributes = True


class CourseRead(BaseModel):
    """Modelo de lectura para Course"""
    id: int
    title: str
    description: str
    place: str
    course_image: str
    course_image_detail: str
    category: str
    status: CourseStatus
    objectives: List[str]
    organizers: List[str]
    materials: List[str]
    target_audience: List[str]
    requirement: Optional[CourseRequirementRead] = None
    contents: List[CourseContentRead] = []

    class Config:
        from_attributes = True

# === Modelos de Creación ===
class CourseRequirementCreate(BaseModel):
    """Modelo de creación para CourseRequirement"""
    start_date_registration: date
    end_date_registration: date
    start_date_course: date
    end_date_course: date
    days: List[str]
    start_time: time
    end_time: time
    location: str
    min_quota: int
    max_quota: int
    in_person_hours: int = 0
    autonomous_hours: int = 0
    modality: str
    certification: str
    prerequisites: List[str] = []
    prices: List[dict] = []

    @field_validator('min_quota', 'max_quota')
    @classmethod
    def validate_quotas(cls, v):
        if v < 1:
            raise ValueError('Las cuotas deben ser mayor a 0')
        return v

    @field_validator('in_person_hours', 'autonomous_hours')
    @classmethod
    def validate_hours(cls, v):
        if v < 0:
            raise ValueError('Las horas deben ser mayor o igual a 0')
        return v

    class Config:
        str_strip_whitespace = True


class CourseContentCreate(BaseModel):
    """Modelo de creación para CourseContent"""
    unit: str
    title: str
    topics: List[CourseContentTopicRead] = []

    @field_validator('unit', 'title')
    @classmethod
    def validate_required_fields(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Los campos unit y title son requeridos')
        return v.strip()

    class Config:
        str_strip_whitespace = True


class CourseCreate(BaseModel):
    """Modelo de creación para Course"""
    title: str
    description: str
    place: str
    course_image: str
    course_image_detail: str
    category_id: int
    status: CourseStatus = CourseStatus.ACTIVO
    objectives: List[str] = []
    organizers: List[str] = []
    materials: List[str] = []
    target_audience: List[str] = []

    @field_validator('title', 'description', 'place')
    @classmethod
    def validate_required_fields(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Los campos title, description y place son requeridos')
        return v.strip()

    @field_validator('category_id')
    @classmethod
    def validate_category_id(cls, v):
        if v <= 0:
            raise ValueError('category_id debe ser mayor a 0')
        return v

    class Config:
        str_strip_whitespace = True

# === Modelos de Actualización ===
class CourseUpdate(BaseModel):
    """Modelo de actualización para Course"""
    title: Optional[str] = None
    description: Optional[str] = None
    place: Optional[str] = None
    course_image: Optional[str] = None
    course_image_detail: Optional[str] = None
    category_id: Optional[int] = None
    status: Optional[CourseStatus] = None
    objectives: Optional[List[str]] = None
    organizers: Optional[List[str]] = None
    materials: Optional[List[str]] = None
    target_audience: Optional[List[str]] = None

    @field_validator('title', 'description', 'place')
    @classmethod
    def validate_fields(cls, v):
        if v is not None and (not v or len(v.strip()) == 0):
            raise ValueError('Los campos no pueden estar vacíos')
        return v.strip() if v else v

    @field_validator('category_id')
    @classmethod
    def validate_category_id(cls, v):
        if v is not None and v <= 0:
            raise ValueError('category_id debe ser mayor a 0')
        return v

    class Config:
        str_strip_whitespace = True


class CourseRequirementUpdate(BaseModel):
    """Modelo de actualización para CourseRequirement"""
    start_date_registration: Optional[date] = None
    end_date_registration: Optional[date] = None
    start_date_course: Optional[date] = None
    end_date_course: Optional[date] = None
    days: Optional[List[str]] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    location: Optional[str] = None
    min_quota: Optional[int] = None
    max_quota: Optional[int] = None
    in_person_hours: Optional[int] = None
    autonomous_hours: Optional[int] = None
    modality: Optional[str] = None
    certification: Optional[str] = None
    prerequisites: Optional[List[str]] = None
    prices: Optional[List[dict]] = None

    @field_validator('min_quota', 'max_quota')
    @classmethod
    def validate_quotas(cls, v):
        if v is not None and v < 1:
            raise ValueError('Las cuotas deben ser mayor a 0')
        return v

    @field_validator('in_person_hours', 'autonomous_hours')
    @classmethod
    def validate_hours(cls, v):
        if v is not None and v < 0:
            raise ValueError('Las horas deben ser mayor o igual a 0')
        return v

    class Config:
        str_strip_whitespace = True


class CourseContentUpdate(BaseModel):
    """Modelo de actualización para CourseContent"""
    unit: Optional[str] = None
    title: Optional[str] = None
    topics: Optional[List[CourseContentTopicRead]] = None

    @field_validator('unit', 'title')
    @classmethod
    def validate_fields(cls, v):
        if v is not None and (not v or len(v.strip()) == 0):
            raise ValueError('Los campos no pueden estar vacíos')
        return v.strip() if v else v

    class Config:
        str_strip_whitespace = True