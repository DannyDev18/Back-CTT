import json
from datetime import datetime, date, time
from typing import List, Optional, Dict, Any
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from src.models.course import (
    Course,
    CourseRequirement,
    CourseContent,
    CourseCreate,
    CourseUpdate,
    CourseRequirementCreate,
    CourseRequirementUpdate,
    CourseContentCreate,
    CourseStatus,
)


class CourseSerializer:
    """Maneja la serialización/deserialización de datos JSON"""
    
    @staticmethod
    def serialize_json_field(data: List | Dict | None) -> str:
        """Convierte una lista o dict a JSON string"""
        return json.dumps(data) if data else json.dumps([])
    
    @staticmethod
    def deserialize_json_field(data: str | None) -> List | Dict:
        """Convierte un JSON string a lista o dict"""
        if not data:
            return []
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return []
    
    @staticmethod
    def course_to_dict(course: Course, requirements: Optional[CourseRequirement] = None, 
                      contents: List[CourseContent] = None) -> Dict[str, Any]:
        """Convierte un curso y sus relaciones a diccionario"""
        course_dict = {
            "id": course.id,
            "title": course.title,
            "description": course.description,
            "place": course.place,
            "course_image": course.course_image,
            "course_image_detail": course.course_image_detail,
            "category": course.category,
            "status": course.status,
            "objectives": CourseSerializer.deserialize_json_field(course.objectives),
            "organizers": CourseSerializer.deserialize_json_field(course.organizers),
            "materials": CourseSerializer.deserialize_json_field(course.materials),
            "target_audience": CourseSerializer.deserialize_json_field(course.target_audience),
            "requirements": None,
            "contents": []
        }
        
        if requirements:
            course_dict["requirements"] = CourseSerializer._requirements_to_dict(
                requirements, 
                CourseSerializer.deserialize_json_field(course.target_audience)
            )
        
        if contents:
            course_dict["contents"] = [
                CourseSerializer._content_to_dict(content) 
                for content in contents
            ]
        
        return course_dict
    
    @staticmethod
    def _requirements_to_dict(req: CourseRequirement, target_audience: List[str]) -> Dict[str, Any]:
        """Convierte requisitos a diccionario"""
        return {
            "registration": {
                "startDate": str(req.start_date_registration),
                "endDate": str(req.end_date_registration)
            },
            "courseSchedule": {
                "startDate": str(req.start_date_course),
                "endDate": str(req.end_date_course),
                "days": CourseSerializer.deserialize_json_field(req.days),
                "startTime": req.start_time,
                "endTime": req.end_time
            },
            "location": req.location,
            "quota": {
                "min": req.min_quota,
                "max": req.max_quota
            },
            "prices": CourseSerializer.deserialize_json_field(req.prices),
            "hours": {
                "total": req.in_person_hours + req.autonomous_hours,  # Calculado aquí
                "inPerson": req.in_person_hours,
                "autonomous": req.autonomous_hours
            },
            "targetAudience": target_audience,
            "modality": req.modality,
            "certification": req.certification,
            "prerequisites": CourseSerializer.deserialize_json_field(req.prerequisites)
        }
    
    @staticmethod
    def _content_to_dict(content: CourseContent) -> Dict[str, Any]:
        """Convierte contenido a diccionario"""
        topics = CourseSerializer.deserialize_json_field(content.topics)
        return {
            "unit": content.unit,
            "title": content.title,
            "topics": topics
        }


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
            days=CourseSerializer.serialize_json_field(requirements_data.days),
            start_time=requirements_data.start_time,  # Ya es tipo time
            end_time=requirements_data.end_time,
            location=requirements_data.location,
            min_quota=requirements_data.min_quota,
            max_quota=requirements_data.max_quota,
            in_person_hours=requirements_data.in_person_hours,
            autonomous_hours=requirements_data.autonomous_hours,
            modality=requirements_data.modality,
            certification=requirements_data.certification,
            prerequisites=CourseSerializer.serialize_json_field(requirements_data.prerequisites),
            prices=CourseSerializer.serialize_json_field(requirements_data.prices)
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
                topics=CourseSerializer.serialize_json_field(
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


class PaginationHelper:
    """Maneja la lógica de paginación"""
    
    @staticmethod
    def build_pagination_response(
        items: List[Any],
        total: int,
        page: int,
        page_size: int,
        base_path: str,
        status: CourseStatus,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Construye la respuesta de paginación"""
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        has_next = page < total_pages
        has_prev = page > 1 and total_pages > 0
        
        status_str = status.value if isinstance(status, CourseStatus) else str(status)
        category_param = f"&category={category}" if category else ""
        
        links = {
            "self": f"{base_path}?page={page}&page_size={page_size}&status={status_str}{category_param}",
            "next": f"{base_path}?page={page + 1}&page_size={page_size}&status={status_str}{category_param}" if has_next else None,
            "prev": f"{base_path}?page={page - 1}&page_size={page_size}&status={status_str}{category_param}" if has_prev else None,
        }
        
        return {
            "total": total,
            "total_pages": total_pages,
            "page": page,
            "page_size": page_size,
            "has_next": has_next,
            "has_prev": has_prev,
            "links": links,
            "courses": items,
        }


class CourseController:
    """Controlador principal de cursos - capa de servicio"""
    
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
            category=course_data.category,
            status=course_data.status,
            objectives=CourseSerializer.serialize_json_field(course_data.objectives),
            organizers=CourseSerializer.serialize_json_field(course_data.organizers),
            materials=CourseSerializer.serialize_json_field(course_data.materials),
            target_audience=CourseSerializer.serialize_json_field(course_data.target_audience)
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
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Obtiene todos los cursos con paginación"""
        # Obtener cursos con relaciones (evita N+1)
        courses, total = CourseRepository.get_courses_paginated(
            db, page, page_size, status, category
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
        return PaginationHelper.build_pagination_response(
            courses_dict,
            total,
            page,
            page_size,
            "/api/v1/courses",
            status,
            category
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
    def get_courses_by_category(category: str, db: Session) -> List[Dict[str, Any]]:
        """Obtiene cursos por categoría"""
        statement = (
            select(Course)
            .where(Course.category == category)
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
                    setattr(course, key, CourseSerializer.serialize_json_field(value))
                else:
                    setattr(course, key, value)
        
        # Actualizar requisitos
        if requirements_data and course.requirement:
            update_dict = requirements_data.model_dump(exclude_unset=True)
            for key, value in update_dict.items():
                if key in ['days', 'prerequisites', 'prices']:
                    setattr(course.requirement, key, CourseSerializer.serialize_json_field(value))
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