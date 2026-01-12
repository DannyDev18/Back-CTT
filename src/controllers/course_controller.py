from typing import List, Optional, Dict, Any
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from src.models.course import (
    Course,
    CourseRequirement,
    CourseCreate,
    CourseUpdate,
    CourseRequirementCreate,
    CourseRequirementUpdate,
    CourseContentCreate,
    CourseStatus,
)
from src.utils.serializers.general_serializer import GeneralSerializer
from src.utils.serializers.course_serializer import CourseSerializer
from src.repositories.course_repository import CourseRepository
from src.utils.Helpers.pagination_helper import PaginationHelper

class CourseController:
    
    @staticmethod
    def create_course_with_requirements(
        course_data: CourseCreate,
        requirements_data: CourseRequirementCreate,
        contents_data: List[CourseContentCreate],
        db: Session
    ) -> Dict[str, Any]:
        """Crea un curso completo con requisitos y contenidos"""
        # Crear curso principal
        course = Course(
            title=course_data.title,
            description=course_data.description,
            place=course_data.place,
            course_image=course_data.course_image,
            course_image_detail=course_data.course_image_detail,
            category_id=course_data.category_id,
            status=course_data.status,
            objectives=GeneralSerializer.serialize_json_field(course_data.objectives),
            organizers=GeneralSerializer.serialize_json_field(course_data.organizers),
            materials=GeneralSerializer.serialize_json_field(course_data.materials),
            target_audience=GeneralSerializer.serialize_json_field(course_data.target_audience)
        )
        db.add(course)
        db.flush()
        
        # Crear requisitos
        requirements = CourseRepository.create_course_requirements(
            course.id, requirements_data, db
        )
        
        # Crear contenidos
        contents = CourseRepository.create_course_contents(
            course.id, contents_data, db
        )
        
        db.commit()
        db.refresh(course)
        
        return CourseSerializer.course_to_dict(course, requirements, contents)
    
    @staticmethod
    def get_all_courses(
        db: Session,
        page: int = 1,
        page_size: int = 10,
        status: CourseStatus = CourseStatus.ACTIVO,
        category_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Obtiene todos los cursos con paginación"""
        # Obtener cursos con relaciones (evita N+1)
        courses, total = CourseRepository.get_courses_paginated(
            db, page, page_size, status, category_id
        )
        
        # Convertir a diccionarios
        courses_dict = [
            CourseSerializer.course_to_dict(
                course,
                course.requirement,  # Ya cargado por selectinload
                course.contents      # Ya cargado por selectinload
            )
            for course in courses
        ]
        
        # Construir respuesta paginada
        return PaginationHelper.build_courses_pagination_response(
            courses_dict,
            total,
            page,
            page_size,
            "/api/v1/courses",
            status,
            category_id
        )
    
    @staticmethod
    def get_available_courses_for_user(
        db: Session,
        user_id: int,
        page: int = 1,
        page_size: int = 10,
        status: CourseStatus = CourseStatus.ACTIVO,
        category_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Obtiene cursos disponibles para inscripción (excluye cursos donde el usuario ya está inscrito)"""
        # Obtener cursos disponibles
        courses, total = CourseRepository.get_available_courses_for_user(
            db, user_id, page, page_size, status, category_id
        )
        
        # Convertir a diccionarios
        courses_dict = [
            CourseSerializer.course_to_dict(
                course,
                course.requirement,
                course.contents
            )
            for course in courses
        ]
        
        # Construir respuesta paginada
        return PaginationHelper.build_courses_pagination_response(
            courses_dict,
            total,
            page,
            page_size,
            "/api/v1/courses/available",
            status,
            category_id
        )
    
    @staticmethod
    def get_course_by_id(course_id: int, db: Session) -> Optional[Dict[str, Any]]:
        """Obtiene un curso por ID con todos sus datos"""
        course = CourseRepository.get_course_with_relations(course_id, db)
        if not course:
            return None
        
        return CourseSerializer.course_to_dict(
            course,
            course.requirement,
            course.contents
        )
    
    @staticmethod
    def get_courses_by_category(category_id: int, db: Session) -> List[Dict[str, Any]]:
        """Obtiene cursos por categoría"""
        statement = (
            select(Course)
            .where(Course.category_id == category_id)
            .options(
                selectinload(Course.requirement),
                selectinload(Course.contents)
            )
        )
        courses = db.exec(statement).all()
        
        return [
            CourseSerializer.course_to_dict(course, course.requirement, course.contents)
            for course in courses
        ]
    
    @staticmethod
    def search_courses_by_title(search_term: str, db: Session) -> List[Dict[str, Any]]:
        """Busca cursos por título (case-insensitive)"""
        statement = (
            select(Course)
            .where(Course.title.ilike(f"%{search_term}%"))
            .options(
                selectinload(Course.requirement),
                selectinload(Course.contents)
            )
        )
        courses = db.exec(statement).all()
        
        return [
            CourseSerializer.course_to_dict(course, course.requirement, course.contents)
            for course in courses
        ]
    
    @staticmethod
    def search_available_courses_for_user(
        search_term: str,
        user_id: int,
        db: Session,
        status: CourseStatus = CourseStatus.ACTIVO
    ) -> List[Dict[str, Any]]:
        """Busca cursos disponibles por título (excluye cursos donde el usuario ya está inscrito)"""
        courses = CourseRepository.search_available_courses_for_user(
            db, user_id, search_term, status
        )
        
        return [
            CourseSerializer.course_to_dict(course, course.requirement, course.contents)
            for course in courses
        ]
    
    @staticmethod
    def get_courses_by_hours_range(
        min_hours: int,
        max_hours: int,
        db: Session
    ) -> List[Dict[str, Any]]:
        """Obtiene cursos por rango de horas"""
        statement = (
            select(Course)
            .join(CourseRequirement, Course.id == CourseRequirement.course_id)
            .where(
                (CourseRequirement.in_person_hours + CourseRequirement.autonomous_hours) >= min_hours,
                (CourseRequirement.in_person_hours + CourseRequirement.autonomous_hours) <= max_hours
            )
            .options(
                selectinload(Course.requirement),
                selectinload(Course.contents)
            )
        )
        courses = db.exec(statement).all()
        
        return [
            CourseSerializer.course_to_dict(course, course.requirement, course.contents)
            for course in courses
        ]
    
    @staticmethod
    def update_course_with_requirements(
        course_id: int,
        db: Session,
        course_data: Optional[CourseUpdate] = None,
        requirements_data: Optional[CourseRequirementUpdate] = None,
        contents_data: Optional[List[CourseContentCreate]] = None
    ) -> Dict[str, Any]:
        """Actualiza un curso y sus relaciones"""
        course = CourseRepository.get_course_with_relations(course_id, db)
        if not course:
            raise ValueError("Course not found")
        
        # Actualizar curso principal
        if course_data:
            update_dict = course_data.model_dump(exclude_unset=True)
            for key, value in update_dict.items():
                if key in ['objectives', 'organizers', 'materials', 'target_audience']:
                    setattr(course, key, GeneralSerializer.serialize_json_field(value))
                else:
                    setattr(course, key, value)
        
        # Actualizar requisitos
        if requirements_data and course.requirement:
            update_dict = requirements_data.model_dump(exclude_unset=True)
            for key, value in update_dict.items():
                if key in ['days', 'prerequisites', 'prices']:
                    setattr(course.requirement, key, GeneralSerializer.serialize_json_field(value))
                else:
                    setattr(course.requirement, key, value)
        
        # Actualizar contenidos (reemplazar todos)
        if contents_data is not None:
            CourseRepository.delete_course_contents(course_id, db)
            db.flush()
            contents = CourseRepository.create_course_contents(course_id, contents_data, db)
        else:
            contents = course.contents
        
        db.commit()
        db.refresh(course)
        
        return CourseSerializer.course_to_dict(
            course,
            course.requirement,
            contents
        )
    
    @staticmethod
    def delete_course(course_id: int, db: Session) -> None:
        """Soft delete: marca el curso como inactivo"""
        course = CourseRepository.get_course_with_relations(course_id, db)
        if not course:
            raise ValueError("Course not found")
        if course.status == CourseStatus.INACTIVO:
            raise ValueError("Course is already deleted")
        
        course.status = CourseStatus.INACTIVO
        db.commit()