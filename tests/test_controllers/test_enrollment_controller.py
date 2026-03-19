import pytest
from sqlmodel import Session
from src.models.enrollment import Enrollment, EnrollmentCreate, EnrollmentUpdate, EnrollmentStatus
from src.models.user_platform import UserPlatform
from src.models.course import Course
from src.controllers.enrollment_controller import EnrollmentController
from datetime import datetime


class TestEnrollmentController:
    """Tests para el controlador de inscripciones (cursos y congresos)"""

    # ------------------------------------------------------------------
    # Crear inscripción — curso
    # ------------------------------------------------------------------

    def test_create_course_enrollment_success(self, db: Session, sample_user_platform, sample_course):
        """Crear inscripción a un curso exitosamente"""
        enrollment_data = EnrollmentCreate(
            id_user_platform=sample_user_platform.id,
            id_course=sample_course.id,
            status=EnrollmentStatus.INTERESADO
        )

        result = EnrollmentController.create_enrollment(enrollment_data, db)

        assert result["message"] == "Inscripción creada exitosamente."
        assert result["enrollment_id"] is not None
        assert result["data"]["status"] == EnrollmentStatus.INTERESADO.value
        assert result["data"]["id_user_platform"] == sample_user_platform.id
        assert result["data"]["id_course"] == sample_course.id
        assert result["data"]["id_congress"] is None

    def test_create_course_enrollment_duplicate(self, db: Session, sample_user_platform, sample_course):
        """No permitir inscripción duplicada al mismo curso"""
        enrollment_data = EnrollmentCreate(
            id_user_platform=sample_user_platform.id,
            id_course=sample_course.id
        )

        EnrollmentController.create_enrollment(enrollment_data, db)

        with pytest.raises(ValueError, match="ya está inscrito"):
            EnrollmentController.create_enrollment(enrollment_data, db)

    def test_create_enrollment_invalid_course(self, db: Session, sample_user_platform):
        """Error al inscribirse en curso inexistente"""
        enrollment_data = EnrollmentCreate(
            id_user_platform=sample_user_platform.id,
            id_course=99999
        )

        with pytest.raises(ValueError, match="Curso con ID .* no encontrado"):
            EnrollmentController.create_enrollment(enrollment_data, db)

    def test_create_enrollment_invalid_user(self, db: Session, sample_course):
        """Error al inscribir usuario inexistente"""
        enrollment_data = EnrollmentCreate(
            id_user_platform=99999,
            id_course=sample_course.id
        )

        with pytest.raises(ValueError, match="Usuario con ID .* no encontrado"):
            EnrollmentController.create_enrollment(enrollment_data, db)

    # ------------------------------------------------------------------
    # Crear inscripción — congreso
    # ------------------------------------------------------------------

    def test_create_congress_enrollment_success(self, db: Session, sample_user_platform, sample_congress):
        """Crear inscripción a un congreso exitosamente"""
        enrollment_data = EnrollmentCreate(
            id_user_platform=sample_user_platform.id,
            id_congress=sample_congress.id,
            status=EnrollmentStatus.INTERESADO
        )

        result = EnrollmentController.create_enrollment(enrollment_data, db)

        assert result["message"] == "Inscripción creada exitosamente."
        assert result["enrollment_id"] is not None
        assert result["data"]["id_congress"] == sample_congress.id
        assert result["data"]["id_course"] is None

    def test_create_congress_enrollment_duplicate(self, db: Session, sample_user_platform, sample_congress):
        """No permitir inscripción duplicada al mismo congreso"""
        enrollment_data = EnrollmentCreate(
            id_user_platform=sample_user_platform.id,
            id_congress=sample_congress.id
        )

        EnrollmentController.create_enrollment(enrollment_data, db)

        with pytest.raises(ValueError, match="ya está inscrito"):
            EnrollmentController.create_enrollment(enrollment_data, db)

    def test_create_enrollment_invalid_congress(self, db: Session, sample_user_platform):
        """Error al inscribirse en congreso inexistente"""
        enrollment_data = EnrollmentCreate(
            id_user_platform=sample_user_platform.id,
            id_congress=99999
        )

        with pytest.raises(ValueError, match="Congreso con ID .* no encontrado"):
            EnrollmentController.create_enrollment(enrollment_data, db)

    # ------------------------------------------------------------------
    # Validación XOR (Pydantic — antes de llegar al controlador)
    # ------------------------------------------------------------------

    def test_create_enrollment_both_set_raises_error(self, sample_course, sample_congress, sample_user_platform):
        """No se puede especificar id_course e id_congress al mismo tiempo"""
        with pytest.raises(ValueError, match="al mismo tiempo"):
            EnrollmentCreate(
                id_user_platform=sample_user_platform.id,
                id_course=sample_course.id,
                id_congress=sample_congress.id
            )

    def test_create_enrollment_neither_set_raises_error(self, sample_user_platform):
        """Debe especificarse al menos uno: id_course o id_congress"""
        with pytest.raises(ValueError, match="id_course o id_congress"):
            EnrollmentCreate(
                id_user_platform=sample_user_platform.id
            )

    # ------------------------------------------------------------------
    # Leer por ID
    # ------------------------------------------------------------------

    def test_get_enrollment_by_id_course(self, db: Session, sample_enrollment):
        """Obtener inscripción a curso por ID incluye campos de curso"""
        result = EnrollmentController.get_enrollment_by_id(sample_enrollment.id, db)

        assert result["id"] == sample_enrollment.id
        assert result["id_user_platform"] == sample_enrollment.id_user_platform
        assert result["id_course"] == sample_enrollment.id_course
        assert result["id_congress"] is None
        assert "user_name" in result
        assert "course_title" in result
        assert "congress_title" in result

    def test_get_congress_enrollment_by_id(self, db: Session, sample_congress_enrollment):
        """Obtener inscripción a congreso por ID incluye congress_title"""
        result = EnrollmentController.get_enrollment_by_id(sample_congress_enrollment.id, db)

        assert result["id_congress"] == sample_congress_enrollment.id_congress
        assert result["id_course"] is None
        assert result["congress_title"] is not None
        assert "user_name" in result

    def test_get_enrollment_by_id_not_found(self, db: Session):
        """Error al obtener inscripción inexistente"""
        with pytest.raises(ValueError, match="Inscripción con ID .* no encontrada"):
            EnrollmentController.get_enrollment_by_id(99999, db)

    # ------------------------------------------------------------------
    # Actualizar / anular
    # ------------------------------------------------------------------

    def test_update_enrollment_status(self, db: Session, sample_enrollment):
        """Actualizar estado de inscripción"""
        update_data = EnrollmentUpdate(status=EnrollmentStatus.PAGADO)

        result = EnrollmentController.update_enrollment(sample_enrollment.id, update_data, db)

        assert result["message"] == "Inscripción actualizada exitosamente."
        assert result["data"]["status"] == EnrollmentStatus.PAGADO.value

    def test_update_enrollment_payment_url(self, db: Session, sample_enrollment):
        """Actualizar URL de pago"""
        update_data = EnrollmentUpdate(payment_order_url="https://payment.example.com/order123")

        result = EnrollmentController.update_enrollment(sample_enrollment.id, update_data, db)

        assert result["data"]["payment_order_url"] == "https://payment.example.com/order123"

    def test_update_enrollment_not_found(self, db: Session):
        """Error al actualizar inscripción inexistente"""
        update_data = EnrollmentUpdate(status=EnrollmentStatus.PAGADO)

        with pytest.raises(ValueError, match="Inscripción con ID .* no encontrada"):
            EnrollmentController.update_enrollment(99999, update_data, db)

    def test_delete_enrollment(self, db: Session, sample_enrollment):
        """Anular inscripción cambia estado a ANULADO"""
        result = EnrollmentController.delete_enrollment(sample_enrollment.id, db)

        assert "anulada exitosamente" in result["message"]

        enrollment = db.get(Enrollment, sample_enrollment.id)
        assert enrollment.status == EnrollmentStatus.ANULADO

    def test_delete_enrollment_not_found(self, db: Session):
        """Error al anular inscripción inexistente"""
        with pytest.raises(ValueError, match="Inscripción con ID .* no encontrada"):
            EnrollmentController.delete_enrollment(99999, db)

    # ------------------------------------------------------------------
    # Inscripciones por usuario
    # ------------------------------------------------------------------

    def test_get_enrollments_by_user(self, db: Session, sample_user_platform, sample_course, sample_congress):
        """Devuelve inscripciones mixtas (curso y congreso) con todos los campos"""
        enrollment_course = Enrollment(
            id_user_platform=sample_user_platform.id,
            id_course=sample_course.id,
            enrollment_date=datetime.utcnow(),
            status=EnrollmentStatus.INTERESADO
        )
        enrollment_congress = Enrollment(
            id_user_platform=sample_user_platform.id,
            id_congress=sample_congress.id,
            enrollment_date=datetime.utcnow(),
            status=EnrollmentStatus.INTERESADO
        )
        db.add(enrollment_course)
        db.add(enrollment_congress)
        db.commit()

        enrollments = EnrollmentController.get_enrollments_by_user(sample_user_platform.id, db)

        assert len(enrollments) >= 2
        for e in enrollments:
            assert "course_title" in e
            assert "congress_title" in e
            assert "id_course" in e
            assert "id_congress" in e

    def test_get_enrollments_by_user_with_status_filter(
        self, db: Session, sample_user_platform, sample_course, sample_congress
    ):
        """Filtrar inscripciones de usuario por estado"""
        # Curso → INTERESADO, Congreso → PAGADO (diferentes recursos, no hay duplicado)
        enrollment_course = Enrollment(
            id_user_platform=sample_user_platform.id,
            id_course=sample_course.id,
            enrollment_date=datetime.utcnow(),
            status=EnrollmentStatus.INTERESADO
        )
        enrollment_congress = Enrollment(
            id_user_platform=sample_user_platform.id,
            id_congress=sample_congress.id,
            enrollment_date=datetime.utcnow(),
            status=EnrollmentStatus.PAGADO
        )
        db.add(enrollment_course)
        db.add(enrollment_congress)
        db.commit()

        enrollments = EnrollmentController.get_enrollments_by_user(
            sample_user_platform.id, db, EnrollmentStatus.PAGADO
        )

        assert len(enrollments) >= 1
        assert all(e["status"] == EnrollmentStatus.PAGADO.value for e in enrollments)

    # ------------------------------------------------------------------
    # Inscripciones por curso / congreso
    # ------------------------------------------------------------------

    def test_get_enrollments_by_course(self, db: Session, sample_user_platform, sample_course):
        """Devuelve inscripciones de un curso con datos del usuario"""
        enrollment = Enrollment(
            id_user_platform=sample_user_platform.id,
            id_course=sample_course.id,
            enrollment_date=datetime.utcnow(),
            status=EnrollmentStatus.INTERESADO
        )
        db.add(enrollment)
        db.commit()

        result = EnrollmentController.get_enrollments_by_course(sample_course.id, db)

        assert result["course_id"] == sample_course.id
        assert "items" in result
        assert "pagination" in result
        assert len(result["items"]) >= 1
        for item in result["items"]:
            assert "user_name" in item
            assert "user_email" in item

    def test_get_enrollments_by_congress(self, db: Session, sample_user_platform, sample_congress):
        """Devuelve inscripciones de un congreso con datos del usuario"""
        enrollment = Enrollment(
            id_user_platform=sample_user_platform.id,
            id_congress=sample_congress.id,
            enrollment_date=datetime.utcnow(),
            status=EnrollmentStatus.INTERESADO
        )
        db.add(enrollment)
        db.commit()

        result = EnrollmentController.get_enrollments_by_congress(sample_congress.id, db)

        assert result["congress_id"] == sample_congress.id
        assert "items" in result
        assert "pagination" in result
        assert len(result["items"]) >= 1
        for item in result["items"]:
            assert "user_name" in item
            assert "user_email" in item

    # ------------------------------------------------------------------
    # Paginación general
    # ------------------------------------------------------------------

    def test_get_enrollments_paginated(self, db: Session, sample_user_platform, sample_course, sample_congress):
        """Obtener inscripciones paginadas con estructura correcta"""
        # Una inscripción a curso y una a congreso (no genera duplicados)
        db.add(Enrollment(
            id_user_platform=sample_user_platform.id,
            id_course=sample_course.id,
            enrollment_date=datetime.utcnow(),
            status=EnrollmentStatus.INTERESADO
        ))
        db.add(Enrollment(
            id_user_platform=sample_user_platform.id,
            id_congress=sample_congress.id,
            enrollment_date=datetime.utcnow(),
            status=EnrollmentStatus.INTERESADO
        ))
        db.commit()

        result = EnrollmentController.get_enrollments_paginated(db, page=1, page_size=10)

        assert "items" in result
        assert "pagination" in result
        assert len(result["items"]) >= 2
        for item in result["items"]:
            assert "id_course" in item
            assert "id_congress" in item

    # ------------------------------------------------------------------
    # Estadísticas
    # ------------------------------------------------------------------

    def test_get_course_enrollment_stats(self, db: Session, sample_user_platform, sample_course):
        """Estadísticas de inscripciones de un curso agrupadas por estado"""
        db.add(Enrollment(
            id_user_platform=sample_user_platform.id,
            id_course=sample_course.id,
            enrollment_date=datetime.utcnow(),
            status=EnrollmentStatus.INTERESADO
        ))
        db.commit()

        stats = EnrollmentController.get_course_enrollment_stats(sample_course.id, db)

        assert stats["course_id"] == sample_course.id
        assert "total_inscriptions" in stats
        assert "by_status" in stats
        assert stats["by_status"][EnrollmentStatus.INTERESADO.value] >= 1

    def test_get_congress_enrollment_stats(self, db: Session, sample_user_platform, sample_congress):
        """Estadísticas de inscripciones de un congreso agrupadas por estado"""
        db.add(Enrollment(
            id_user_platform=sample_user_platform.id,
            id_congress=sample_congress.id,
            enrollment_date=datetime.utcnow(),
            status=EnrollmentStatus.PAGADO
        ))
        db.commit()

        stats = EnrollmentController.get_congress_enrollment_stats(sample_congress.id, db)

        assert stats["congress_id"] == sample_congress.id
        assert "congress_title" in stats
        assert "total_inscriptions" in stats
        assert "by_status" in stats
        assert stats["by_status"][EnrollmentStatus.PAGADO.value] >= 1

    def test_get_course_enrollment_stats_invalid_course(self, db: Session):
        """Error al obtener estadísticas de curso inexistente"""
        with pytest.raises(ValueError, match="Curso con ID .* no encontrado"):
            EnrollmentController.get_course_enrollment_stats(99999, db)

    def test_get_congress_enrollment_stats_invalid_congress(self, db: Session):
        """Error al obtener estadísticas de congreso inexistente"""
        with pytest.raises(ValueError, match="Congreso con ID .* no encontrado"):
            EnrollmentController.get_congress_enrollment_stats(99999, db)
