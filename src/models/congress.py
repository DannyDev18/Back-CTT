from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional
from datetime import date, time
from enum import Enum
from pydantic import field_validator, computed_field


class CongressStatus(str, Enum):
    ACTIVO = "activo"
    INACTIVO = "inactivo"

# === Modelos de Tabla ===
class Congress(SQLModel, table=True):

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str 
    description: str
    place: str
    congress_image: str
    congress_image_detail: str
    category_id: int = Field(foreign_key="categories.id", nullable=False, index=True)
    status: CongressStatus = Field(default=CongressStatus.ACTIVO)
    objectives: str  # JSON string
    organizers: str  # JSON string
    materials: str   # JSON string
    target_audience: str  # JSON string
    
    # Relaciones
    category_rel: "Category" = Relationship(back_populates="congresss")
    requirement: Optional["CongressRequirement"] = Relationship(back_populates="congress")
    contents: List["CongressContent"] = Relationship(back_populates="congress")

class CongressRequirement(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    congress_id: int = Field(foreign_key="congress.id", unique=True)
    start_date_registration: date
    end_date_registration: date
    start_date_congress: date
    end_date_congress: date
    days: str  # JSON: List[str]
    start_time: time  # Cambiado de str a time
    end_time: time    # Cambiado de str a time
    location: str
    min_quota: int = Field(ge=1)
    max_quota: int = Field(ge=1)
    in_person_hours: int = Field(ge=0)
    autonomous_hours: int = Field(ge=0)
    modality: str
    certification: str
    prerequisites: str  # JSON: List[str]
    prices: str  # JSON: List[dict]
    
    # Relación
    congress: Optional[Congress] = Relationship(back_populates="requirement")
    
    @field_validator('max_quota')
    @classmethod
    def validate_quotas(cls, v, info):
        if 'min_quota' in info.data and v < info.data['min_quota']:
            raise ValueError('max_quota debe ser mayor o igual a min_quota')
        return v

class CongressContent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    congress_id: int = Field(foreign_key="congress.id")
    unit: str
    title: str
    topics: str  # JSON: List[dict] - Simplificado, no necesitas tabla separada
    
    # Relación
    congress: Optional[Congress] = Relationship(back_populates="contents")

# === Modelos de Respuesta (con campos computados) ===
class CongressRequirementRead(SQLModel):
    id: int
    congress_id: int
    start_date_registration: date
    end_date_registration: date
    start_date_congress: date
    end_date_congress: date
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

class CongressContentTopicRead(SQLModel):
    unit: str
    title: str

class CongressContentRead(SQLModel):
    id: int
    unit: str
    title: str
    topics: List[CongressContentTopicRead]

class CongressRead(SQLModel):
    id: int
    title: str
    description: str
    place: str
    congress_image: str
    congress_image_detail: str
    category: str
    status: CongressStatus
    objectives: List[str]
    organizers: List[str]
    materials: List[str]
    target_audience: List[str]
    requirement: Optional[CongressRequirementRead] = None
    contents: List[CongressContentRead] = []

# === Modelos de Creación ===
class CongressRequirementCreate(SQLModel):
    start_date_registration: date
    end_date_registration: date
    start_date_congress: date
    end_date_congress: date
    days: List[str]
    start_time: time
    end_time: time
    location: str
    min_quota: int = Field(ge=1)
    max_quota: int = Field(ge=1)
    in_person_hours: int = Field(ge=0)
    autonomous_hours: int = Field(ge=0)
    modality: str
    certification: str
    prerequisites: List[str] = []
    prices: List[dict] = []

class CongressContentCreate(SQLModel):
    unit: str
    title: str
    topics: List[CongressContentTopicRead] = []

class CongressCreate(SQLModel):
    title: str
    description: str
    place: str
    congress_image: str
    congress_image_detail: str
    category_id: int
    status: CongressStatus = CongressStatus.ACTIVO
    objectives: List[str] = []
    organizers: List[str] = []
    materials: List[str] = []
    target_audience: List[str] = []

# === Modelos de Actualización ===
class CongressUpdate(SQLModel):
    title: Optional[str] = None
    description: Optional[str] = None
    place: Optional[str] = None
    congress_image: Optional[str] = None
    congress_image_detail: Optional[str] = None
    category: Optional[str] = None
    status: Optional[CongressStatus] = None
    objectives: Optional[List[str]] = None
    organizers: Optional[List[str]] = None
    materials: Optional[List[str]] = None
    target_audience: Optional[List[str]] = None

class CongressRequirementUpdate(SQLModel):
    start_date_registration: Optional[date] = None
    end_date_registration: Optional[date] = None
    start_date_congress: Optional[date] = None
    end_date_congress: Optional[date] = None
    days: Optional[List[str]] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    location: Optional[str] = None
    min_quota: Optional[int] = Field(default=None, ge=1)
    max_quota: Optional[int] = Field(default=None, ge=1)
    in_person_hours: Optional[int] = Field(default=None, ge=0)
    autonomous_hours: Optional[int] = Field(default=None, ge=0)
    modality: Optional[str] = None
    certification: Optional[str] = None
    prerequisites: Optional[List[str]] = None
    prices: Optional[List[dict]] = None

class CongressContentUpdate(SQLModel):
    unit: Optional[str] = None
    title: Optional[str] = None
    topics: Optional[List[CongressContentTopicRead]] = None
# al final de congress.py

Congress.update_forward_refs()

from src.models.category import Category