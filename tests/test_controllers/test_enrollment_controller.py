import pytest
from sqlmodel import Session, select
from src.models.enrollment import Enrollment, EnrollmentCreate, EnrollmentUpdate, EnrollmentStatus
from src.models.user_platform import UserPlatform
from src.models.course import Course
from src.controllers.enrollment_controller import EnrollmentController
from datetime import datetime

class TestEnrollmentController:
    """Tests para el controlador de inscripciones"""
    
    def test_create_enrollment_success(self, db: Session, sample_user_platform, sample_course):
        """Test: Crear inscripción exitosamente"""
        enrollment_data = EnrollmentCreate(
            id_user_platform=sample_user_platform.id,
            id_course=sample_course.id,
            status=EnrollmentStatus.INTERESADO
        )
        
        result = EnrollmentController.create_enrollment(enrollment_data, db)
        
        assert result["message"] == "Inscripción creada exitosamente"
        assert result["enrollment_id"] is not None
        assert result["data"]["status"] == EnrollmentStatus.INTERESADO.value
        assert result["data"]["id_user_platform"] == sample_user_platform.id
        assert result["data"]["id_course"] == sample_course.id
    
    def test_create_enrollment_duplicate(self, db: Session, sample_user_platform, sample_course):
        """Test: No permitir inscripción duplicada"""
        enrollment_data = EnrollmentCreate(
            id_user_platform=sample_user_platform.id,
            id_course=sample_course.id
        )
        
        # Primera inscripción
        EnrollmentController.create_enrollment(enrollment_data, db)
        
        # Intentar segunda inscripción
        with pytest.raises(ValueError, match="ya está inscrito"):
            EnrollmentController.create_enrollment(enrollment_data, db)
    
    def test_create_enrollment_invalid_course(self, db: Session, sample_user_platform):
        """Test: Error al inscribirse en curso inexistente"""
        enrollment_data = EnrollmentCreate(
            id_user_platform=sample_user_platform.id,
            id_course=99999  # ID inexistente
        )
        
        with pytest.raises(ValueError, match="Curso con ID .* no encontrado"):
            EnrollmentController.create_enrollment(enrollment_data, db)
    
    def test_create_enrollment_invalid_user(self, db: Session, sample_course):
        """Test: Error al inscribir usuario inexistente"""
        enrollment_data = EnrollmentCreate(
            id_user_platform=99999,  # ID inexistente
            id_course=sample_course.id
        )
        
        with pytest.raises(ValueError, match="Usuario con ID .* no encontrado"):
            EnrollmentController.create_enrollment(enrollment_data, db)
    
    def test_get_enrollment_by_id(self, db: Session, sample_enrollment):
        """Test: Obtener inscripción por ID"""
        result = EnrollmentController.get_enrollment_by_id(sample_enrollment.id, db)
        
        assert result["id"] == sample_enrollment.id
        assert result["id_user_platform"] == sample_enrollment.id_user_platform
        assert result["id_course"] == sample_enrollment.id_course
        assert "user_name" in result
        assert "course_title" in result
    
    def test_get_enrollment_by_id_not_found(self, db: Session):
        """Test: Error al obtener inscripción inexistente"""
        with pytest.raises(ValueError, match="Inscripción con ID .* no encontrada"):
            EnrollmentController.get_enrollment_by_id(99999, db)
    
    def test_update_enrollment_status(self, db: Session, sample_enrollment):
        """Test: Actualizar estado de inscripción"""
        update_data = EnrollmentUpdate(status=EnrollmentStatus.PAGADO)
        
        result = EnrollmentController.update_enrollment(sample_enrollment.id, update_data, db)
        
        assert result["message"] == "Inscripción actualizada exitosamente"
        assert result["data"]["status"] == EnrollmentStatus.PAGADO.value
    
    def test_update_enrollment_payment_url(self, db: Session, sample_enrollment):
        """Test: Actualizar URL de pago"""
        update_data = EnrollmentUpdate(payment_order_url="https://payment.example.com/order123")
        
        result = EnrollmentController.update_enrollment(sample_enrollment.id, update_data, db)
        
        assert result["data"]["payment_order_url"] == "https://payment.example.com/order123"
    
    def test_update_enrollment_not_found(self, db: Session):
        """Test: Error al actualizar inscripción inexistente"""
        update_data = EnrollmentUpdate(status=EnrollmentStatus.PAGADO)
        
        with pytest.raises(ValueError, match="Inscripción con ID .* no encontrada"):
            EnrollmentController.update_enrollment(99999, update_data, db)
    
    def test_delete_enrollment(self, db: Session, sample_enrollment):
        """Test: Anular inscripción"""
        result = EnrollmentController.delete_enrollment(sample_enrollment.id, db)
        
        assert "anulada exitosamente" in result["message"]
        
        # Verificar que el estado cambió a ANULADO
        enrollment = db.get(Enrollment, sample_enrollment.id)
        assert enrollment.status == EnrollmentStatus.ANULADO
    
    def test_delete_enrollment_not_found(self, db: Session):
        """Test: Error al anular inscripción inexistente"""
        with pytest.raises(ValueError, match="Inscripción con ID .* no encontrada"):
            EnrollmentController.delete_enrollment(99999, db)
    
    def test_get_enrollments_by_user(self, db: Session, sample_user_platform, sample_course):
        """Test: Obtener inscripciones de un usuario"""
        # Crear múltiples inscripciones
        for _ in range(3):
            enrollment = Enrollment(
                id_user_platform=sample_user_platform.id,
                id_course=sample_course.id,
                enrollment_date=datetime.utcnow(),
                status=EnrollmentStatus.INTERESADO
            )
            db.add(enrollment)
        db.commit()
        
        enrollments = EnrollmentController.get_enrollments_by_user(sample_user_platform.id, db)
        
        assert len(enrollments) >= 3
        for enrollment in enrollments:
            assert "course_title" in enrollment
            assert "course_category" in enrollment
    
    def test_get_enrollments_by_user_with_status_filter(self, db: Session, sample_user_platform, sample_course):
        """Test: Filtrar inscripciones de usuario por estado"""
        # Crear inscripciones con diferentes estados
        enrollment1 = Enrollment(
            id_user_platform=sample_user_platform.id,
            id_course=sample_course.id,
            status=EnrollmentStatus.INTERESADO
        )
        enrollment2 = Enrollment(
            id_user_platform=sample_user_platform.id,
            id_course=sample_course.id,
            status=EnrollmentStatus.PAGADO
        )
        db.add(enrollment1)
        db.add(enrollment2)
        db.commit()
        
        # Filtrar por PAGADO
        enrollments = EnrollmentController.get_enrollments_by_user(
            sample_user_platform.id, db, EnrollmentStatus.PAGADO
        )
        
        assert all(e["status"] == EnrollmentStatus.PAGADO.value for e in enrollments)
    
    def test_get_enrollments_by_course(self, db: Session, sample_user_platform, sample_course):
        """Test: Obtener inscripciones de un curso"""
        # Crear inscripción
        enrollment = Enrollment(
            id_user_platform=sample_user_platform.id,
            id_course=sample_course.id,
            status=EnrollmentStatus.INTERESADO
        )
        db.add(enrollment)
        db.commit()
        
        enrollments = EnrollmentController.get_enrollments_by_course(sample_course.id, db)
        
        assert len(enrollments) >= 1
        for enrollment in enrollments:
            assert "user_name" in enrollment
            assert "user_email" in enrollment
    
    def test_get_enrollments_paginated(self, db: Session, sample_user_platform, sample_course):
        """Test: Obtener inscripciones paginadas"""
        # Crear múltiples inscripciones
        for _ in range(15):
            enrollment = Enrollment(
                id_user_platform=sample_user_platform.id,
                id_course=sample_course.id,
                status=EnrollmentStatus.INTERESADO
            )
            db.add(enrollment)
        db.commit()
        
        result = EnrollmentController.get_enrollments_paginated(db, page=1, page_size=10)
        
        assert "items" in result
        assert "pagination" in result
        assert len(result["items"]) <= 10
        assert result["pagination"]["total_items"] >= 15
    
    def test_get_course_enrollment_stats(self, db: Session, sample_user_platform, sample_course):
        """Test: Obtener estadísticas de inscripciones por curso"""
        # Crear inscripciones con diferentes estados
        for status in [EnrollmentStatus.INTERESADO, EnrollmentStatus.PAGADO, EnrollmentStatus.PAGADO]:
            enrollment = Enrollment(
                id_user_platform=sample_user_platform.id,
                id_course=sample_course.id,
                status=status
            )
            db.add(enrollment)
        db.commit()
        
        stats = EnrollmentController.get_course_enrollment_stats(sample_course.id, db)
        
        assert stats["course_id"] == sample_course.id
        assert "total_inscriptions" in stats
        assert "by_status" in stats
        assert stats["by_status"][EnrollmentStatus.INTERESADO.value] >= 1
        assert stats["by_status"][EnrollmentStatus.PAGADO.value] >= 2
    
    def test_get_course_enrollment_stats_invalid_course(self, db: Session):
        """Test: Error al obtener estadísticas de curso inexistente"""
        with pytest.raises(ValueError, match="Curso con ID .* no encontrado"):
            EnrollmentController.get_course_enrollment_stats(99999, db)
