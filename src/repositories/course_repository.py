from sqlmodel import Session, select
from typing import List, Optional
from sqlalchemy.orm import selectinload
from src.models.course import (
    Course,
    CourseRequirement,
    CourseContent,
    CourseRequirementCreate,
    CourseContentCreate,
    CourseStatus,
)

from src.utils.serializers.general_serializer import GeneralSerializer
from src.utils.serializers.course_serializer import CourseSerializer

class CourseRepository:
    """Maneja las operaciones de base de datos"""
    
    @staticmethod
    def get_course_with_relations(course_id: int, db: Session) -> Optional[Course]:
        """Obtiene un curso con todas sus relaciones cargadas (evita N+1)"""
        statement = (
            select(Course)
            .where(Course.id == course_id)
            .options(
                selectinload(Course.requirement),
                selectinload(Course.contents)
            )
        )
        return db.exec(statement).first()
    
    @staticmethod
    def get_courses_paginated(
        db: Session,
        page: int,
        page_size: int,
        status: CourseStatus,
        category: Optional[str] = None
    ):
        """Obtiene cursos paginados con todas sus relaciones (evita N+1)"""
        from sqlalchemy import func
        
        # Query base
        statement = (
            select(Course)
            .where(Course.status == status)
            .options(
                selectinload(Course.requirement),
                selectinload(Course.contents)
            )
        )
        
        # Query para contar
        count_statement = (
            select(func.count())
            .select_from(Course)
            .where(Course.status == status)
        )
        
        # Filtro por categoría
        if category:
            statement = statement.where(Course.category == category)
            count_statement = count_statement.where(Course.category == category)
        
        # Ordenar
        statement = statement.order_by(Course.id)
        
        # Contar total
        total = db.exec(count_statement).one()
        
        # Paginar
        offset = (page - 1) * page_size
        courses = db.exec(statement.offset(offset).limit(page_size)).all()
        
        return courses, total
    
    @staticmethod
    def create_course_requirements(
        course_id: int,
        requirements_data: CourseRequirementCreate,
        db: Session
    ) -> CourseRequirement:
        """Crea los requisitos de un curso"""
        requirements = CourseRequirement(
            course_id=course_id,
            start_date_registration=requirements_data.start_date_registration,
            end_date_registration=requirements_data.end_date_registration,
            start_date_course=requirements_data.start_date_course,
            end_date_course=requirements_data.end_date_course,
            days=GeneralSerializer.serialize_json_field(requirements_data.days),
            start_time=requirements_data.start_time,  # Ya es tipo time
            end_time=requirements_data.end_time,
            location=requirements_data.location,
            min_quota=requirements_data.min_quota,
            max_quota=requirements_data.max_quota,
            in_person_hours=requirements_data.in_person_hours,
            autonomous_hours=requirements_data.autonomous_hours,
            modality=requirements_data.modality,
            certification=requirements_data.certification,
            prerequisites=GeneralSerializer.serialize_json_field(requirements_data.prerequisites),
            prices=GeneralSerializer.serialize_json_field(requirements_data.prices)
        )
        db.add(requirements)
        return requirements
    
    @staticmethod
    def create_course_contents(
        course_id: int,
        contents_data: List[CourseContentCreate],
        db: Session
    ) -> List[CourseContent]:
        """Crea los contenidos de un curso"""
        contents = []
        for content_data in contents_data:
            content = CourseContent(
                course_id=course_id,
                unit=content_data.unit,
                title=content_data.title,
                topics=GeneralSerializer.serialize_json_field(
                    [{"unit": t.unit, "title": t.title} for t in content_data.topics]
                )
            )
            db.add(content)
            contents.append(content)
        return contents
    
    @staticmethod
    def delete_course_contents(course_id: int, db: Session) -> None:
        """Elimina todos los contenidos de un curso"""
        contents = db.exec(
            select(CourseContent).where(CourseContent.course_id == course_id)
        ).all()
        for content in contents:
            db.delete(content)

