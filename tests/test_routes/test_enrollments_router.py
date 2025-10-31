"""
Tests para el router de inscripciones (enrollments)
"""
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from src.routes.enrollments_router import enrollments_router
from src.models.enrollment import EnrollmentStatus
from src.models.user import User


@pytest.fixture
def enrollment_client(session, sample_user_platform):
    """Cliente de prueba con el router de inscripciones"""
    from src.dependencies.db_session import get_db
    from src.routes.enrollments_router import (
        get_current_platform_user,
        get_current_user_any_type,
    )
    
    test_app = FastAPI()
    
    def override_get_db():
        try:
            yield session
        finally:
            pass
    
    def override_get_current_user():
        return sample_user_platform

    async def override_get_current_user_any_type():
        return sample_user_platform, "platform"
    
    test_app.dependency_overrides[get_db] = override_get_db
    test_app.dependency_overrides[get_current_platform_user] = override_get_current_user
    test_app.dependency_overrides[get_current_user_any_type] = override_get_current_user_any_type
    test_app.include_router(enrollments_router)
    
    with TestClient(test_app) as client:
        yield client


@pytest.fixture
def enrollment_client_other_user(session):
    """Cliente de prueba con otro usuario diferente"""
    from src.dependencies.db_session import get_db
    from src.routes.enrollments_router import (
        get_current_platform_user,
        get_current_user_any_type,
    )
    from src.models.user_platform import UserPlatform, UserPlatformType
    
    # Crear otro usuario
    other_user = UserPlatform(
        identification="9876543210",
        first_name="Otro",
        first_last_name="Usuario",
        cellphone="0123456789",
        email="otro@example.com",
        type=UserPlatformType.ESTUDIANTE,
        password="password"
    )
    session.add(other_user)
    session.commit()
    session.refresh(other_user)
    
    test_app = FastAPI()
    
    def override_get_db():
        try:
            yield session
        finally:
            pass
    
    def override_get_current_user():
        return other_user

    async def override_get_current_user_any_type():
        return other_user, "platform"
    
    test_app.dependency_overrides[get_db] = override_get_db
    test_app.dependency_overrides[get_current_platform_user] = override_get_current_user
    test_app.dependency_overrides[get_current_user_any_type] = override_get_current_user_any_type
    test_app.include_router(enrollments_router)
    
    with TestClient(test_app) as client:
        yield client


@pytest.fixture
def sample_admin_user(session):
    """Crea y retorna un usuario administrador de prueba"""
    admin_user = User(
        name="Admin",
        last_name="User",
        email="admin@example.com",
        password="hashed_password_123"
    )
    session.add(admin_user)
    session.commit()
    session.refresh(admin_user)
    return admin_user


@pytest.fixture
def enrollment_admin_client(session, sample_admin_user):
    """Cliente de prueba autenticado como administrador"""
    from src.dependencies.db_session import get_db
    from src.routes.enrollments_router import (
        get_current_admin_user,
        get_current_user_any_type,
    )

    test_app = FastAPI()

    def override_get_db():
        try:
            yield session
        finally:
            pass

    async def override_get_current_admin_user():
        return sample_admin_user

    async def override_get_current_user_any_type():
        return sample_admin_user, "admin"

    test_app.dependency_overrides[get_db] = override_get_db
    test_app.dependency_overrides[get_current_admin_user] = override_get_current_admin_user
    test_app.dependency_overrides[get_current_user_any_type] = override_get_current_user_any_type
    test_app.include_router(enrollments_router)

    with TestClient(test_app) as client:
        yield client


class TestEnrollmentRouter:
    """Tests para los endpoints de inscripciones"""
    
    def test_create_enrollment_success(self, enrollment_client, session, sample_user_platform, sample_course):
        """Test: Crear inscripción exitosamente"""
        enrollment_data = {
            "id_user_platform": sample_user_platform.id,
            "id_course": sample_course.id,
            "status": EnrollmentStatus.INTERESADO.value
        }
        
        response = enrollment_client.post("/api/v1/enrollments/", json=enrollment_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Inscripción creada exitosamente"
        assert data["enrollment_id"] is not None
    
    def test_create_enrollment_forbidden(self, enrollment_client, session, sample_user_platform, sample_course):
        """Test: No permitir inscribir a otro usuario"""
        enrollment_data = {
            "id_user_platform": 99999,  # ID diferente al usuario autenticado
            "id_course": sample_course.id
        }
        
        response = enrollment_client.post("/api/v1/enrollments/", json=enrollment_data)
        
        assert response.status_code == 403
        assert "permiso" in response.json()["detail"].lower()
    
    def test_create_enrollment_invalid_course(self, enrollment_client, session, sample_user_platform):
        """Test: Error al inscribirse en curso inexistente"""
        enrollment_data = {
            "id_user_platform": sample_user_platform.id,
            "id_course": 99999
        }
        
        response = enrollment_client.post("/api/v1/enrollments/", json=enrollment_data)
        
        assert response.status_code == 400
        assert "no encontrado" in response.json()["detail"].lower()
    
    def test_get_enrollment_success(self, enrollment_client, session, sample_enrollment, sample_user_platform):
        """Test: Obtener inscripción por ID"""
        response = enrollment_client.get(f"/api/v1/enrollments/{sample_enrollment.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_enrollment.id
        assert "user_name" in data
        assert "course_title" in data
    
    def test_get_enrollment_forbidden(self, enrollment_client_other_user, session, sample_enrollment):
        """Test: No permitir ver inscripción de otro usuario"""
        response = enrollment_client_other_user.get(f"/api/v1/enrollments/{sample_enrollment.id}")
        
        assert response.status_code == 403
    
    def test_get_enrollment_not_found(self, enrollment_client, sample_user_platform):
        """Test: Error al obtener inscripción inexistente"""
        response = enrollment_client.get("/api/v1/enrollments/99999")
        
        assert response.status_code == 404
    
    def test_update_enrollment_success(self, enrollment_client, session, sample_enrollment, sample_user_platform):
        """Test: Usuario de plataforma actualiza payment_order_url de su inscripción"""
        update_data = {
            "payment_order_url": "https://payment.example.com/order123"
        }
        
        response = enrollment_client.put(
            f"/api/v1/enrollments/{sample_enrollment.id}",
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["payment_order_url"] == "https://payment.example.com/order123"
    
    def test_update_enrollment_platform_cannot_change_status(self, enrollment_client, session, sample_enrollment, sample_user_platform):
        """Test: Usuario de plataforma NO puede cambiar el status"""
        update_data = {
            "status": EnrollmentStatus.PAGADO.value
        }
        
        response = enrollment_client.put(
            f"/api/v1/enrollments/{sample_enrollment.id}",
            json=update_data
        )
        
        assert response.status_code == 403
        assert "no pueden cambiar el estado" in response.json()["detail"].lower()
    
    def test_update_enrollment_admin_can_change_status(self, enrollment_admin_client, session, sample_enrollment, sample_admin_user):
        """Test: Admin puede cambiar el status y payment_order_url"""
        update_data = {
            "status": EnrollmentStatus.PAGADO.value,
            "payment_order_url": "https://payment.example.com/order456"
        }
        
        response = enrollment_admin_client.put(
            f"/api/v1/enrollments/{sample_enrollment.id}",
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == EnrollmentStatus.PAGADO.value
        assert data["data"]["payment_order_url"] == "https://payment.example.com/order456"
    
    def test_delete_enrollment_success(self, enrollment_admin_client, session, sample_enrollment, sample_admin_user):
        """Test: Anular inscripción exitosamente"""
        response = enrollment_admin_client.delete(f"/api/v1/enrollments/{sample_enrollment.id}")

        assert response.status_code == 200
        assert "anulada exitosamente" in response.json()["message"]
        
        # Verificar que el estado cambió
        from src.models.enrollment import Enrollment
        enrollment = session.get(Enrollment, sample_enrollment.id)
        assert enrollment.status == EnrollmentStatus.ANULADO
    
    def test_get_user_enrollments(self, enrollment_client, session, sample_user_platform, sample_enrollment):
        """Test: Obtener inscripciones de un usuario"""
        response = enrollment_client.get(f"/api/v1/enrollments/user/{sample_user_platform.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "enrollments" in data
        assert len(data["enrollments"]) >= 1
        assert data["user_id"] == sample_user_platform.id
    
    def test_get_user_enrollments_forbidden(self, enrollment_client, sample_user_platform):
        """Test: No permitir ver inscripciones de otro usuario"""
        response = enrollment_client.get("/api/v1/enrollments/user/99999")
        
        assert response.status_code == 403
    
    def test_get_course_enrollments(self, enrollment_admin_client, session, sample_course, sample_enrollment, sample_admin_user):
        """Test: Obtener inscripciones de un curso"""
        response = enrollment_admin_client.get(f"/api/v1/enrollments/course/{sample_course.id}")

        assert response.status_code == 200
        data = response.json()
        assert "enrollments" in data
        assert data["course_id"] == sample_course.id
    
    def test_list_enrollments_paginated(self, enrollment_client, session, sample_user_platform, sample_enrollment):
        """Test: Listar inscripciones paginadas"""
        response = enrollment_client.get("/api/v1/enrollments/?page=1&page_size=10")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "pagination" in data
        assert len(data["items"]) <= 10
    
    def test_list_enrollments_with_filters(self, enrollment_client, session, sample_user_platform, sample_course, sample_enrollment):
        """Test: Listar inscripciones con filtros"""
        response = enrollment_client.get(
            f"/api/v1/enrollments/?status={EnrollmentStatus.INTERESADO.value}&course_id={sample_course.id}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
    
    def test_get_course_stats(self, enrollment_admin_client, session, sample_course, sample_enrollment, sample_admin_user):
        """Test: Obtener estadísticas de curso"""
        response = enrollment_admin_client.get(f"/api/v1/enrollments/stats/course/{sample_course.id}")

        assert response.status_code == 200
        data = response.json()
        assert "course_id" in data
        assert "total_inscriptions" in data
        assert "by_status" in data
        assert data["course_id"] == sample_course.id
    
    def test_get_course_stats_invalid_course(self, enrollment_admin_client, sample_admin_user):
        """Test: Error al obtener estadísticas de curso inexistente"""
        response = enrollment_admin_client.get("/api/v1/enrollments/stats/course/99999")

        assert response.status_code == 404
