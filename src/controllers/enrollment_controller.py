from typing import List, Optional, Dict, Any
from sqlmodel import Session, select
from sqlalchemy import func
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
            "tariff_type": getattr(enrollment, "tariff_type", "GENERAL"),
            "amount": float(enrollment.amount) if getattr(enrollment, "amount", None) is not None else 0.0,
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
        - Que el congreso no haya alcanzado su cupo máximo.
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

        # -- Validar cupo máximo en congresos --
        if not is_course_enrollment:
            if getattr(resource, "cupo_maximo", None) and resource.cupo_maximo > 0:
                active_statuses = [
                    EnrollmentStatus.PAGADO,
                    EnrollmentStatus.FACTURADO,
                    EnrollmentStatus.INTERESADO,
                    EnrollmentStatus.ORDEN_GENERADA,
                ]
                active_count = db.exec(
                    select(func.count(Enrollment.id)).where(
                        Enrollment.id_congress == enrollment_data.id_congress,
                        Enrollment.status.in_(active_statuses),
                    )
                ).one()
                if active_count >= resource.cupo_maximo:
                    raise ValueError(
                        f"El cupo máximo ({resource.cupo_maximo} participantes) ha sido alcanzado. Convocatoria cerrada."
                    )

        # -- Validar vigencia de inscripciones (Legalidad CTT - FISEI) --
        today = datetime.utcnow().date()
        if is_course_enrollment:
            if getattr(resource, "requirement", None) and getattr(resource.requirement, "end_date_registration", None):
                if today > resource.requirement.end_date_registration:
                    raise ValueError(
                        "El periodo de inscripciones para este curso ha finalizado. El temario y detalles continúan disponibles para consulta."
                    )
        else:
            if getattr(resource, "fecha_fin", None):
                if today > resource.fecha_fin:
                    raise ValueError(
                        "El congreso seleccionado ha concluido. La información y memorias se encuentran disponibles para consulta pública."
                    )

        # -- Determinar tarifa institucional y monto según el rol del usuario --
        import json
        user_type_str = str(getattr(user, "type", "Estudiante")).replace("UserPlatformType.", "")
        computed_tariff = enrollment_data.tariff_type or "GENERAL"
        computed_amount = enrollment_data.amount or 0.0

        if computed_amount == 0.0:
            if is_course_enrollment:
                prices = []
                if getattr(resource, "requirement", None) and getattr(resource.requirement, "prices", None):
                    raw_prices = resource.requirement.prices
                    if isinstance(raw_prices, str):
                        try:
                            prices = json.loads(raw_prices)
                        except Exception:
                            prices = []
                    elif isinstance(raw_prices, list):
                        prices = raw_prices

                if user_type_str.lower() in ["estudiante", "estudiante uta"]:
                    computed_tariff = "Estudiante UTA"
                    match = next((p for p in prices if "estudiante" in str(p.get("category", "")).lower()), None)
                    computed_amount = float(match["amount"]) if match else (float(prices[0]["amount"]) if prices else 40.0)
                elif user_type_str.lower() in ["administrativo", "docente", "graduado"]:
                    computed_tariff = "Graduados y Docentes UTA"
                    match = next((p for p in prices if any(k in str(p.get("category", "")).lower() for k in ["graduado", "docente", "administrativo"])), None)
                    computed_amount = float(match["amount"]) if match else (float(prices[1]["amount"]) if len(prices) > 1 else 50.0)
                else:
                    computed_tariff = "Público en general"
                    match = next((p for p in prices if "general" in str(p.get("category", "")).lower()), None)
                    computed_amount = float(match["amount"]) if match else (float(prices[-1]["amount"]) if prices else 60.0)
            else:
                if user_type_str.lower() in ["estudiante", "estudiante uta"]:
                    computed_tariff = "Estudiante UTA"
                    computed_amount = float(getattr(resource, "costo_estudiante_uta", 20.0) or 20.0)
                elif user_type_str.lower() in ["administrativo", "docente", "graduado"]:
                    computed_tariff = "Graduado / Docente UTA"
                    computed_amount = float(getattr(resource, "costo_profesional", 50.0) or 50.0)
                else:
                    computed_tariff = "Público General"
                    computed_amount = float(getattr(resource, "costo_ponente", 80.0) or 80.0)

        # -- Crear inscripción --
        enrollment = Enrollment(
            id_user_platform=enrollment_data.id_user_platform,
            id_course=enrollment_data.id_course,
            id_congress=enrollment_data.id_congress,
            enrollment_date=datetime.utcnow(),
            status=enrollment_data.status,
            payment_order_url=enrollment_data.payment_order_url,
            tariff_type=computed_tariff,
            amount=computed_amount,
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

            effective_title = course_title or congress_title or "Sin título"
            effective_category = category_name or ("Congreso" if enrollment.id_congress else "General")

            enrollments.append({
                "id": enrollment.id,
                "id_course": enrollment.id_course,
                "id_congress": enrollment.id_congress,
                "enrollment_date": enrollment.enrollment_date.isoformat(),
                "status": enrollment.status.value,
                "payment_order_url": enrollment.payment_order_url,
                "tariff_type": getattr(enrollment, "tariff_type", "GENERAL") or "GENERAL",
                "amount": float(getattr(enrollment, "amount", 0.0) or 0.0),
                # Datos de curso o congreso unificados
                "course_title": effective_title,
                "title": effective_title,
                "course_category_id": course_category_id,
                "course_category_name": effective_category,
                "course_category_description": category_description,
                "course_category_svgurl": category_svgurl,
                "course_image": course_image,
                # Datos de congreso
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
        for enrollment, user in results:
            items.append({
                "id": enrollment.id,
                "id_user_platform": enrollment.id_user_platform,
                "enrollment_date": enrollment.enrollment_date.isoformat(),
                "status": enrollment.status.value,
                "payment_order_url": enrollment.payment_order_url,
                "tariff_type": getattr(enrollment, "tariff_type", "GENERAL") or "GENERAL",
                "amount": float(getattr(enrollment, "amount", 0.0) or 0.0),
                "user_name": f"{user.first_name} {user.first_last_name}",
                "user_identification": getattr(user, "identification", ""),
                "user_email": user.email,
                "user_cellphone": user.cellphone,
                "billing_identification": getattr(user, "billing_identification", "") or getattr(user, "identification", ""),
                "billing_name": getattr(user, "billing_name", "") or f"{user.first_name} {user.first_last_name}",
                "billing_address": getattr(user, "billing_address", "") or getattr(user, "address", "") or "",
                "billing_phone": getattr(user, "billing_phone", "") or user.cellphone,
                "billing_email": getattr(user, "billing_email", "") or user.email,
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
        for enrollment, user in results:
            items.append({
                "id": enrollment.id,
                "id_user_platform": enrollment.id_user_platform,
                "enrollment_date": enrollment.enrollment_date.isoformat(),
                "status": enrollment.status.value,
                "payment_order_url": enrollment.payment_order_url,
                "tariff_type": getattr(enrollment, "tariff_type", "GENERAL") or "GENERAL",
                "amount": float(getattr(enrollment, "amount", 0.0) or 0.0),
                "user_name": f"{user.first_name} {user.first_last_name}",
                "user_identification": getattr(user, "identification", ""),
                "user_email": user.email,
                "user_cellphone": user.cellphone,
                "billing_identification": getattr(user, "billing_identification", "") or getattr(user, "identification", ""),
                "billing_name": getattr(user, "billing_name", "") or f"{user.first_name} {user.first_last_name}",
                "billing_address": getattr(user, "billing_address", "") or getattr(user, "address", "") or "",
                "billing_phone": getattr(user, "billing_phone", "") or user.cellphone,
                "billing_email": getattr(user, "billing_email", "") or user.email,
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
