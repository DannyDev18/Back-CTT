from sqlmodel import SQLModel, Field
from typing import List, Optional
from datetime import date, time
import json

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
    total_hours: int = Field()
    in_person_hours: int = Field()
    autonomous_hours: int = Field()
    modality: str = Field()
    certification: str = Field()
    prerequisites: str = Field()  # JSON string
    prices: str = Field()  # JSON string

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
    category: str = Field()
    status: str = Field()
    objectives: str = Field()  # JSON string
    organizers: str = Field()  # JSON string
    materials: str = Field()   # JSON string
    target_audience: str = Field()  # JSON string

class CourseBase(SQLModel):
    title: str = Field()
    description: str = Field()
    place: str = Field()
    course_image: str = Field()
    category: str = Field()
    status: str = Field()
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
    total_hours: int = Field()
    in_person_hours: int = Field()
    autonomous_hours: int = Field()
    modality: str = Field()
    certification: str = Field()
    prerequisites: List[str] = Field()
    prices: List[dict] = Field()

class CourseContentTopicBase(SQLModel):
    unit: str = Field()
    title: str = Field()

class CourseContentBase(SQLModel):
    unit: str = Field()
    title: str = Field()
    topics: List[CourseContentTopicBase] = Field()
