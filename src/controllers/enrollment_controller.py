from typing import List, Optional, Dict, Any
from sqlmodel import Session, select
from datetime import datetime
from src.models.enrollment import (
    Enrollment,
    EnrollmentCreate,
    EnrollmentUpdate,
    EnrollmentStatus,
)
from src.repositories.enrollment_repository import EnrollmentRepository
from src.repositories.course_repository import CourseRepository
from src.repositories.congress_repository import CongressRepository
from src.utils.Helpers.pagination_helper import PaginationHelper


class EnrollmentController:
    """Lógica de negocio para inscripciones a cursos y congresos."""

    # ------------------------------------------------------------------
    # Helpers de serialización
    # ------------------------------------------------------------------

    @staticmethod
    def _serialize_enrollment(enrollment: Enrollment) -> Dict[str, Any]:
        return {
            "id": enrollment.id,
            "id_user_platform": enrollment.id_user_platform,
            "id_course": enrollment.id_course,
            "id_congress": enrollment.id_congress,
            "enrollment_date": enrollment.enrollment_date.isoformat(),
            "status": enrollment.status.value,
            "payment_order_url": enrollment.payment_order_url,
        }

    # ------------------------------------------------------------------
    # Crear inscripción
    # ------------------------------------------------------------------

    @staticmethod
    def create_enrollment(enrollment_data: EnrollmentCreate, db: Session) -> Dict[str, Any]:
        """
        Crea una inscripción a un curso o a un congreso.

        Valida:
        - Que el recurso (curso/congreso) exista.
        - Que el usuario exista.
        - Que no exista una inscripción activa previa al mismo recurso.
        Usa transacción implícita de la sesión para evitar race conditions.
        """
        is_course_enrollment = enrollment_data.id_course is not None

        # -- Validar existencia del recurso --
        if is_course_enrollment:
            resource = CourseRepository.get_course_with_relations(
                enrollment_data.id_course, db
            )
            if not resource:
                raise ValueError(f"Curso con ID {enrollment_data.id_course} no encontrado.")
        else:
            congress_repository = CongressRepository()
            resource = congress_repository.get_congress_with_relations(db, enrollment_data.id_congress)
            if not resource:
                raise ValueError(f"Congreso con ID {enrollment_data.id_congress} no encontrado.")

        # -- Validar existencia del usuario --
        from src.models.user_platform import UserPlatform
        user = db.exec(
            select(UserPlatform).where(UserPlatform.id == enrollment_data.id_user_platform)
        ).first()
        if not user:
            raise ValueError(
                f"Usuario con ID {enrollment_data.id_user_platform} no encontrado."
            )

        # -- Verificar duplicado --
        if is_course_enrollment:
            existing = EnrollmentRepository.check_existing_course_enrollment(
                enrollment_data.id_user_platform, enrollment_data.id_course, db
            )
            if existing:
                raise ValueError(
                    f"El usuario ya está inscrito en este curso (Inscripción ID: {existing.id})."
                )
        else:
            existing = EnrollmentRepository.check_existing_congress_enrollment(
                enrollment_data.id_user_platform, enrollment_data.id_congress, db
            )
            if existing:
                raise ValueError(
                    f"El usuario ya está inscrito en este congreso (Inscripción ID: {existing.id})."
                )

        # -- Crear inscripción --
        enrollment = Enrollment(
            id_user_platform=enrollment_data.id_user_platform,
            id_course=enrollment_data.id_course,
            id_congress=enrollment_data.id_congress,
            enrollment_date=datetime.utcnow(),
            status=enrollment_data.status,
            payment_order_url=enrollment_data.payment_order_url,
        )
        db.add(enrollment)
        db.commit()
        db.refresh(enrollment)

        return {
            "message": "Inscripción creada exitosamente.",
            "enrollment_id": enrollment.id,
            "data": EnrollmentController._serialize_enrollment(enrollment),
        }

    # ------------------------------------------------------------------
    # Leer inscripción por ID
    # ------------------------------------------------------------------

    @staticmethod
    def get_enrollment_by_id(enrollment_id: int, db: Session) -> Dict[str, Any]:
        """Obtiene una inscripción con detalles del usuario y recurso inscrito."""
        result = EnrollmentRepository.get_enrollment_with_details(enrollment_id, db)
        if not result:
            raise ValueError(f"Inscripción con ID {enrollment_id} no encontrada.")

        enrollment, first_name, first_last_name, email, course_title, course_category_id, congress_title = result

        return {
            **EnrollmentController._serialize_enrollment(enrollment),
            "user_name": f"{first_name} {first_last_name}",
            "user_email": email,
            "course_title": course_title,
            "course_category_id": course_category_id,
            "congress_title": congress_title,
        }

    # ------------------------------------------------------------------
    # Actualizar / anular
    # ------------------------------------------------------------------

    @staticmethod
    def update_enrollment(
        enrollment_id: int,
        enrollment_data: EnrollmentUpdate,
        db: Session,
    ) -> Dict[str, Any]:
        """Actualiza estado y/o URL de pago de una inscripción."""
        enrollment = EnrollmentRepository.get_enrollment_by_id(enrollment_id, db)
        if not enrollment:
            raise ValueError(f"Inscripción con ID {enrollment_id} no encontrada.")

        if enrollment_data.status is not None:
            enrollment.status = enrollment_data.status
        if enrollment_data.payment_order_url is not None:
            enrollment.payment_order_url = enrollment_data.payment_order_url

        db.add(enrollment)
        db.commit()
        db.refresh(enrollment)

        return {
            "message": "Inscripción actualizada exitosamente.",
            "enrollment_id": enrollment.id,
            "data": EnrollmentController._serialize_enrollment(enrollment),
        }

    @staticmethod
    def delete_enrollment(enrollment_id: int, db: Session) -> Dict[str, str]:
        """Anula una inscripción (soft delete → estado ANULADO)."""
        enrollment = EnrollmentRepository.get_enrollment_by_id(enrollment_id, db)
        if not enrollment:
            raise ValueError(f"Inscripción con ID {enrollment_id} no encontrada.")

        enrollment.status = EnrollmentStatus.ANULADO
        db.add(enrollment)
        db.commit()

        return {"message": f"Inscripción {enrollment_id} anulada exitosamente."}

    # ------------------------------------------------------------------
    # Inscripciones por usuario
    # ------------------------------------------------------------------

    @staticmethod
    def get_enrollments_by_user(
        user_id: int,
        db: Session,
        status: Optional[EnrollmentStatus] = None,
    ) -> List[Dict[str, Any]]:
        """Devuelve inscripciones de un usuario con detalles del curso o congreso."""
        results = EnrollmentRepository.get_enrollments_with_details_by_user(user_id, db)

        enrollments = []
        for (
            enrollment,
            course_title,
            course_category_id,
            category_name,
            category_description,
            category_svgurl,
            course_image,
            congress_title,
        ) in results:
            if status is not None and enrollment.status != status:
                continue
            enrollments.append({
                "id": enrollment.id,
                "id_course": enrollment.id_course,
                "id_congress": enrollment.id_congress,
                "enrollment_date": enrollment.enrollment_date.isoformat(),
                "status": enrollment.status.value,
                "payment_order_url": enrollment.payment_order_url,
                # Datos de curso (None si es inscripción a congreso)
                "course_title": course_title,
                "course_category_id": course_category_id,
                "course_category_name": category_name,
                "course_category_description": category_description,
                "course_category_svgurl": category_svgurl,
                "course_image": course_image,
                # Datos de congreso (None si es inscripción a curso)
                "congress_title": congress_title,
            })

        return enrollments

    # ------------------------------------------------------------------
    # Inscripciones por curso
    # ------------------------------------------------------------------

    @staticmethod
    def get_enrollments_by_course(
        course_id: int,
        db: Session,
        page: int = 1,
        page_size: int = 10,
        status: Optional[EnrollmentStatus] = None,
        search_term: Optional[str] = None,
        base_path: str = "/enrollments/course/",
    ) -> Dict[str, Any]:
        """Devuelve inscripciones de un curso paginadas con datos del usuario."""
        results, total = EnrollmentRepository.get_enrollments_with_details_by_course_paginated(
            db, course_id, page, page_size, status, search_term
        )

        items = []
        for enrollment, first_name, first_last_name, email, cellphone in results:
            items.append({
                "id": enrollment.id,
                "id_user_platform": enrollment.id_user_platform,
                "enrollment_date": enrollment.enrollment_date.isoformat(),
                "status": enrollment.status.value,
                "payment_order_url": enrollment.payment_order_url,
                "user_name": f"{first_name} {first_last_name}",
                "user_email": email,
                "user_cellphone": cellphone,
            })

        pagination = PaginationHelper.build_pagination_response(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            base_path=base_path,
            items_key="courses",
        )
        return {"course_id": course_id, "items": items, "pagination": pagination}

    # ------------------------------------------------------------------
    # Inscripciones por congreso
    # ------------------------------------------------------------------

    @staticmethod
    def get_enrollments_by_congress(
        congress_id: int,
        db: Session,
        page: int = 1,
        page_size: int = 10,
        status: Optional[EnrollmentStatus] = None,
        search_term: Optional[str] = None,
        base_path: str = "/enrollments/congress/",
    ) -> Dict[str, Any]:
        """Devuelve inscripciones de un congreso paginadas con datos del usuario."""
        results, total = EnrollmentRepository.get_enrollments_with_details_by_congress_paginated(
            db, congress_id, page, page_size, status, search_term
        )

        items = []
        for enrollment, first_name, first_last_name, email, cellphone in results:
            items.append({
                "id": enrollment.id,
                "id_user_platform": enrollment.id_user_platform,
                "enrollment_date": enrollment.enrollment_date.isoformat(),
                "status": enrollment.status.value,
                "payment_order_url": enrollment.payment_order_url,
                "user_name": f"{first_name} {first_last_name}",
                "user_email": email,
                "user_cellphone": cellphone,
            })

        pagination = PaginationHelper.build_pagination_response(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            base_path=base_path,
            items_key="congresses",
        )
        return {"congress_id": congress_id, "items": items, "pagination": pagination}

    # ------------------------------------------------------------------
    # Paginación general
    # ------------------------------------------------------------------

    @staticmethod
    def get_enrollments_paginated(
        db: Session,
        page: int = 1,
        page_size: int = 10,
        status: Optional[EnrollmentStatus] = None,
        user_id: Optional[int] = None,
        course_id: Optional[int] = None,
        congress_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Listado paginado de inscripciones con filtros opcionales."""
        enrollments, total = EnrollmentRepository.get_enrollments_paginated(
            db, page, page_size, status, user_id, course_id, congress_id
        )

        items = [EnrollmentController._serialize_enrollment(e) for e in enrollments]

        pagination = PaginationHelper.create_pagination_metadata(
            total_items=total,
            page=page,
            page_size=page_size,
        )
        return {"items": items, "pagination": pagination}

    # ------------------------------------------------------------------
    # Estadísticas
    # ------------------------------------------------------------------

    @staticmethod
    def get_course_enrollment_stats(course_id: int, db: Session) -> Dict[str, Any]:
        """Estadísticas de inscripciones de un curso agrupadas por estado."""
        course = CourseRepository.get_course_with_relations(course_id, db)
        if not course:
            raise ValueError(f"Curso con ID {course_id} no encontrado.")

        stats: Dict[str, Any] = {
            "course_id": course_id,
            "course_title": course.title,
            "total_inscriptions": 0,
            "by_status": {},
        }
        for s in EnrollmentStatus:
            count = EnrollmentRepository.count_enrollments_by_course_and_status(course_id, s, db)
            stats["by_status"][s.value] = count
            stats["total_inscriptions"] += count

        return stats

    @staticmethod
    def get_congress_enrollment_stats(congress_id: int, db: Session) -> Dict[str, Any]:
        """Estadísticas de inscripciones de un congreso agrupadas por estado."""
        congress_repository = CongressRepository()
        congress = congress_repository.get_congress_with_relations(db, congress_id)
        if not congress:
            raise ValueError(f"Congreso con ID {congress_id} no encontrado.")

        stats: Dict[str, Any] = {
            "congress_id": congress_id,
            "congress_title": congress.nombre,
            "total_inscriptions": 0,
            "by_status": {},
        }
        for s in EnrollmentStatus:
            count = EnrollmentRepository.count_enrollments_by_congress_and_status(congress_id, s, db)
            stats["by_status"][s.value] = count
            stats["total_inscriptions"] += count

        return stats
