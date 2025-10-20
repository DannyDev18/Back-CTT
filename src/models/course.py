from sqlmodel import SQLModel, Field
from typing import List, Optional
from datetime import date, time
import json
from enum import Enum

class CourseStatus(str, Enum):
    activo = "activo"
    inactivo = "inactivo"

class CourseRequirement(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    course_id: int = Field(foreign_key="course.id")
    start_date_registration: date = Field()
    end_date_registration: date = Field()
    start_date_course: date = Field()
    end_date_course: date = Field()
    days: str = Field()  # JSON string
    start_time: str = Field()
    end_time: str = Field()
    location: str = Field()
    min_quota: int = Field()
    max_quota: int = Field()
    total_hours: int = Field()  # Calculado automáticamente
    in_person_hours: int = Field()
    autonomous_hours: int = Field()
    modality: str = Field()
    certification: str = Field()
    prerequisites: str = Field()  # JSON string
    prices: str = Field()  # JSON string

    @property
    def total_hours(self) -> int:
        """Calcula el total de horas como la suma de horas presenciales y autónomas"""
        return self.in_person_hours + self.autonomous_hours

class CourseContentTopic(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    course_id: int = Field(foreign_key="course.id")
    content_id: int = Field(foreign_key="coursecontent.id")
    unit: str = Field()
    title: str = Field()

class CourseContent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    course_id: int = Field(foreign_key="course.id")
    unit: str = Field()
    title: str = Field()
    topics_data: str = Field()  # JSON string para topics

class Course(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field()
    description: str = Field()
    place: str = Field()
    course_image: str = Field()
    course_image_detail: str = Field()
    category: str = Field()
    status: CourseStatus = Field(default=CourseStatus.activo)
    objectives: str = Field()  # JSON string
    organizers: str = Field()  # JSON string
    materials: str = Field()   # JSON string
    target_audience: str = Field()  # JSON string

class CourseBase(SQLModel):
    title: str = Field()
    description: str = Field()
    place: str = Field()
    course_image: str = Field()
    course_image_detail: str = Field()
    category: str = Field()
    status: CourseStatus = Field()
    objectives: List[str] = Field()
    organizers: List[str] = Field()
    materials: List[str] = Field()
    target_audience: List[str] = Field()

class CourseRequirementBase(SQLModel):
    start_date_registration: date = Field()
    end_date_registration: date = Field()
    start_date_course: date = Field()
    end_date_course: date = Field()
    days: List[str] = Field()
    start_time: time = Field()
    end_time: time = Field()
    location: str = Field()
    min_quota: int = Field()
    max_quota: int = Field()
    in_person_hours: int = Field()
    autonomous_hours: int = Field()
    modality: str = Field()
    certification: str = Field()
    prerequisites: List[str] = Field()
    prices: List[dict] = Field()

    @property
    def total_hours(self) -> int:
        """Calcula el total de horas como la suma de horas presenciales y autónomas"""
        return self.in_person_hours + self.autonomous_hours

class CourseContentTopicBase(SQLModel):
    unit: str = Field()
    title: str = Field()

class CourseContentBase(SQLModel):
    unit: str = Field()
    title: str = Field()
    topics: List[CourseContentTopicBase] = Field()

# Modelos para actualización (todos los campos opcionales)
class CourseUpdate(SQLModel):
    title: Optional[str] = None
    description: Optional[str] = None
    place: Optional[str] = None
    course_image: Optional[str] = None
    course_image_detail: Optional[str] = None
    category: Optional[str] = None
    status: Optional[CourseStatus] = None
    objectives: Optional[List[str]] = None
    organizers: Optional[List[str]] = None
    materials: Optional[List[str]] = None
    target_audience: Optional[List[str]] = None

class CourseRequirementUpdate(SQLModel):
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

class CourseContentUpdate(SQLModel):
    unit: Optional[str] = None
    title: Optional[str] = None
    topics: Optional[List[CourseContentTopicBase]] = None
