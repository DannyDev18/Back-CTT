from typing import List, Optional, Dict, Any
from sqlmodel import Session
from datetime import datetime
from src.models.enrollment import (
    Enrollment,
    EnrollmentCreate,
    EnrollmentUpdate,
    EnrollmentStatus
)
from src.repositories.enrollment_repository import EnrollmentRepository
from src.repositories.course_repository import CourseRepository
from src.utils.Helpers.pagination_helper import PaginationHelper

class EnrollmentController:
    """Controlador para manejar la lógica de negocio de inscripciones"""
    
    @staticmethod
    def create_enrollment(enrollment_data: EnrollmentCreate, db: Session) -> Dict[str, Any]:
        """Crea una nueva inscripción"""
        # Validar que el curso existe
        course = CourseRepository.get_course_with_relations(enrollment_data.id_course, db)
        if not course:
            raise ValueError(f"Curso con ID {enrollment_data.id_course} no encontrado")
        
        # Validar que el usuario existe
        from src.models.user_platform import UserPlatform
        user_statement = db.query(UserPlatform).filter(UserPlatform.id == enrollment_data.id_user_platform)
        user = user_statement.first() if hasattr(user_statement, 'first') else None
        
        if not user:
            # Intentar con exec de SQLModel
            from sqlmodel import select
            user = db.exec(select(UserPlatform).where(UserPlatform.id == enrollment_data.id_user_platform)).first()
            if not user:
                raise ValueError(f"Usuario con ID {enrollment_data.id_user_platform} no encontrado")
        
        # Verificar si ya existe una inscripción activa
        existing = EnrollmentRepository.check_existing_enrollment(
            enrollment_data.id_user_platform,
            enrollment_data.id_course,
            db
        )
        if existing:
            raise ValueError(
                f"El usuario ya está inscrito en este curso (Inscripción ID: {existing.id})"
            )
        
        # Crear la inscripción
        enrollment = Enrollment(
            id_user_platform=enrollment_data.id_user_platform,
            id_course=enrollment_data.id_course,
            enrollment_date=datetime.utcnow(),
            status=enrollment_data.status,
            payment_order_url=enrollment_data.payment_order_url
        )
        
        db.add(enrollment)
        db.commit()
        db.refresh(enrollment)
        
        return {
            "message": "Inscripción creada exitosamente",
            "enrollment_id": enrollment.id,
            "data": {
                "id": enrollment.id,
                "id_user_platform": enrollment.id_user_platform,
                "id_course": enrollment.id_course,
                "enrollment_date": enrollment.enrollment_date.isoformat(),
                "status": enrollment.status.value,
                "payment_order_url": enrollment.payment_order_url
            }
        }
    
    @staticmethod
    def get_enrollment_by_id(enrollment_id: int, db: Session) -> Dict[str, Any]:
        """Obtiene una inscripción por ID con detalles"""
        result = EnrollmentRepository.get_enrollment_with_details(enrollment_id, db)
        
        if not result:
            raise ValueError(f"Inscripción con ID {enrollment_id} no encontrada")
        
        enrollment, first_name, first_last_name, email, course_title, course_category_id = result
        
        return {
            "id": enrollment.id,
            "id_user_platform": enrollment.id_user_platform,
            "id_course": enrollment.id_course,
            "enrollment_date": enrollment.enrollment_date.isoformat(),
            "status": enrollment.status.value,
            "payment_order_url": enrollment.payment_order_url,
            "user_name": f"{first_name} {first_last_name}",
            "user_email": email,
            "course_title": course_title,
            "course_category_id": course_category_id
        }
    
    @staticmethod
    def update_enrollment(
        enrollment_id: int,
        enrollment_data: EnrollmentUpdate,
        db: Session
    ) -> Dict[str, Any]:
        """Actualiza una inscripción"""
        enrollment = EnrollmentRepository.get_enrollment_by_id(enrollment_id, db)
        
        if not enrollment:
            raise ValueError(f"Inscripción con ID {enrollment_id} no encontrada")
        
        # Actualizar campos
        if enrollment_data.status is not None:
            enrollment.status = enrollment_data.status
        
        if enrollment_data.payment_order_url is not None:
            enrollment.payment_order_url = enrollment_data.payment_order_url
        
        db.add(enrollment)
        db.commit()
        db.refresh(enrollment)
        
        return {
            "message": "Inscripción actualizada exitosamente",
            "enrollment_id": enrollment.id,
            "data": {
                "id": enrollment.id,
                "id_user_platform": enrollment.id_user_platform,
                "id_course": enrollment.id_course,
                "enrollment_date": enrollment.enrollment_date.isoformat(),
                "status": enrollment.status.value,
                "payment_order_url": enrollment.payment_order_url
            }
        }
    
    @staticmethod
    def delete_enrollment(enrollment_id: int, db: Session) -> Dict[str, str]:
        """Anula una inscripción (soft delete)"""
        enrollment = EnrollmentRepository.get_enrollment_by_id(enrollment_id, db)
        
        if not enrollment:
            raise ValueError(f"Inscripción con ID {enrollment_id} no encontrada")
        
        enrollment.status = EnrollmentStatus.ANULADO
        db.add(enrollment)
        db.commit()
        
        return {"message": f"Inscripción {enrollment_id} anulada exitosamente"}
    
    @staticmethod
    def get_enrollments_by_user(
        user_id: int,
        db: Session,
        status: Optional[EnrollmentStatus] = None
    ) -> List[Dict[str, Any]]:
        """Obtiene todas las inscripciones de un usuario con detalles del curso"""
        results = EnrollmentRepository.get_enrollments_with_details_by_user(user_id, db)
        
        enrollments = []
        for enrollment, course_title, course_category_id, course_category_name, course_category_description, course_category_svgurl, course_image in results:
            if status is None or enrollment.status == status:
                enrollments.append({
                    "id": enrollment.id,
                    "id_course": enrollment.id_course,
                    "enrollment_date": enrollment.enrollment_date.isoformat(),
                    "status": enrollment.status.value,
                    "payment_order_url": enrollment.payment_order_url,
                    "course_title": course_title,
                    "course_category_id": course_category_id,
                    "course_category_name": course_category_name,
                    "course_category_description": course_category_description,
                    "course_category_svgurl": course_category_svgurl,
                    "course_image": course_image
                })
        
        return enrollments
    
    @staticmethod
    def get_enrollments_by_course(
        course_id: int,
        db: Session,
        page: int = 1,
        page_size: int = 10,
        status: Optional[EnrollmentStatus] = None,
        search_term: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Obtiene todas las inscripciones de un curso con detalles del usuario"""
        results, total = EnrollmentRepository.get_enrollments_with_details_by_course_paginated(
            db, course_id, page, page_size, status, search_term
        )
        
        enrollments = []
        for enrollment, first_name, first_last_name, email, cellphone in results:
            if status is None or enrollment.status == status:
                enrollments.append({
                    "id": enrollment.id,
                    "id_user_platform": enrollment.id_user_platform,
                    "enrollment_date": enrollment.enrollment_date.isoformat(),
                    "status": enrollment.status.value,
                    "payment_order_url": enrollment.payment_order_url,
                    "user_name": f"{first_name} {first_last_name}",
                    "user_email": email,
                    "user_cellphone": cellphone
                })
        pagination = PaginationHelper.create_pagination_metadata(
            total_items=total,
            page=page,
            page_size=page_size
        )
        return {
            "course_id": course_id,
            "items": enrollments,
            "pagination": pagination
        }
    
    @staticmethod
    def get_enrollments_paginated(
        db: Session,
        page: int = 1,
        page_size: int = 10,
        status: Optional[EnrollmentStatus] = None,
        user_id: Optional[int] = None,
        course_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Obtiene inscripciones paginadas con filtros"""
        enrollments, total = EnrollmentRepository.get_enrollments_paginated(
            db, page, page_size, status, user_id, course_id
        )
        
        # Serializar enrollments
        items = []
        for enrollment in enrollments:
            items.append({
                "id": enrollment.id,
                "id_user_platform": enrollment.id_user_platform,
                "id_course": enrollment.id_course,
                "enrollment_date": enrollment.enrollment_date.isoformat(),
                "status": enrollment.status.value,
                "payment_order_url": enrollment.payment_order_url
            })
        
        pagination = PaginationHelper.create_pagination_metadata(
            total_items=total,
            page=page,
            page_size=page_size
        )
        
        return {
            "items": items,
            "pagination": pagination
        }
    
    @staticmethod
    def get_course_enrollment_stats(course_id: int, db: Session) -> Dict[str, Any]:
        """Obtiene estadísticas de inscripciones de un curso"""
        # Validar que el curso existe
        course = CourseRepository.get_course_with_relations(course_id, db)
        if not course:
            raise ValueError(f"Curso con ID {course_id} no encontrado")
        
        stats = {
            "course_id": course_id,
            "course_title": course.title,
            "total_inscriptions": 0,
            "by_status": {}
        }
        
        # Contar por cada estado
        for status in EnrollmentStatus:
            count = EnrollmentRepository.count_enrollments_by_course_and_status(
                course_id, status, db
            )
            stats["by_status"][status.value] = count
            stats["total_inscriptions"] += count
        
        return stats
