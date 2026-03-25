"""
Tests para el router de inscripciones (enrollments)
"""
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from src.routes.enrollments_router import enrollments_router
from src.models.enrollment import EnrollmentStatus
from src.models.user import User


# ============= Fixtures de clientes de prueba =============

@pytest.fixture
def enrollment_client(session, sample_user_platform):
    """Cliente autenticado como usuario de plataforma (sample_user_platform)"""
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
    """Cliente autenticado como un usuario diferente (para tests de permisos)"""
    from src.dependencies.db_session import get_db
    from src.routes.enrollments_router import (
        get_current_platform_user,
        get_current_user_any_type,
    )
    from src.models.user_platform import UserPlatform, UserPlatformType

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
    """Usuario administrador de prueba"""
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
    """Cliente autenticado como administrador"""
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


# ============= Tests =============

class TestEnrollmentRouter:
    """Tests para los endpoints de inscripciones"""

    # ------------------------------------------------------------------
    # POST / — crear inscripción
    # ------------------------------------------------------------------

    def test_create_course_enrollment_success(
        self, enrollment_client, session, sample_user_platform, sample_course
    ):
        """Crear inscripción a curso exitosamente"""
        payload = {
            "id_user_platform": sample_user_platform.id,
            "id_course": sample_course.id,
            "status": EnrollmentStatus.INTERESADO.value
        }

        response = enrollment_client.post("/api/v1/enrollments/", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Inscripción creada exitosamente."
        assert data["enrollment_id"] is not None
        assert data["data"]["id_course"] == sample_course.id
        assert data["data"]["id_congress"] is None

    def test_create_congress_enrollment_success(
        self, enrollment_client, session, sample_user_platform, sample_congress
    ):
        """Crear inscripción a congreso exitosamente"""
        payload = {
            "id_user_platform": sample_user_platform.id,
            "id_congress": sample_congress.id_congreso,
            "status": EnrollmentStatus.INTERESADO.value
        }

        response = enrollment_client.post("/api/v1/enrollments/", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Inscripción creada exitosamente."
        assert data["data"]["id_congress"] == sample_congress.id_congreso
        assert data["data"]["id_course"] is None

    def test_create_enrollment_validation_error_both(
        self, enrollment_client, sample_user_platform, sample_course, sample_congress
    ):
        """422 si se envían id_course e id_congress simultáneamente"""
        payload = {
            "id_user_platform": sample_user_platform.id,
            "id_course": sample_course.id,
            "id_congress": sample_congress.id_congreso
        }

        response = enrollment_client.post("/api/v1/enrollments/", json=payload)

        assert response.status_code == 422

    def test_create_enrollment_validation_error_neither(
        self, enrollment_client, sample_user_platform
    ):
        """422 si no se envía ni id_course ni id_congress"""
        payload = {"id_user_platform": sample_user_platform.id}

        response = enrollment_client.post("/api/v1/enrollments/", json=payload)

        assert response.status_code == 422

    def test_create_enrollment_forbidden(
        self, enrollment_client, session, sample_user_platform, sample_course
    ):
        """403 al intentar inscribir a otro usuario"""
        payload = {
            "id_user_platform": 99999,
            "id_course": sample_course.id
        }

        response = enrollment_client.post("/api/v1/enrollments/", json=payload)

        assert response.status_code == 403
        assert "permiso" in response.json()["detail"].lower()

    def test_create_enrollment_invalid_course(
        self, enrollment_client, session, sample_user_platform
    ):
        """400 al inscribirse en curso inexistente"""
        payload = {
            "id_user_platform": sample_user_platform.id,
            "id_course": 99999
        }

        response = enrollment_client.post("/api/v1/enrollments/", json=payload)

        assert response.status_code == 400
        assert "no encontrado" in response.json()["detail"].lower()

    # ------------------------------------------------------------------
    # GET /{id}
    # ------------------------------------------------------------------

    def test_get_course_enrollment_success(
        self, enrollment_client, session, sample_enrollment, sample_user_platform
    ):
        """Obtener inscripción a curso por ID"""
        response = enrollment_client.get(f"/api/v1/enrollments/{sample_enrollment.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_enrollment.id
        assert "user_name" in data
        assert "course_title" in data
        assert "congress_title" in data
        assert data["id_congress"] is None

    def test_get_congress_enrollment_success(
        self, enrollment_client, session, sample_congress_enrollment, sample_user_platform
    ):
        """Obtener inscripción a congreso por ID"""
        response = enrollment_client.get(
            f"/api/v1/enrollments/{sample_congress_enrollment.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id_congress"] == sample_congress_enrollment.id_congress
        assert data["id_course"] is None
        assert "congress_title" in data

    def test_get_enrollment_forbidden(
        self, enrollment_client_other_user, session, sample_enrollment
    ):
        """403 al intentar ver inscripción de otro usuario"""
        response = enrollment_client_other_user.get(
            f"/api/v1/enrollments/{sample_enrollment.id}"
        )

        assert response.status_code == 403

    def test_get_enrollment_not_found(self, enrollment_client, sample_user_platform):
        """404 al obtener inscripción inexistente"""
        response = enrollment_client.get("/api/v1/enrollments/99999")

        assert response.status_code == 404

    # ------------------------------------------------------------------
    # PUT /{id}
    # ------------------------------------------------------------------

    def test_update_enrollment_success(
        self, enrollment_client, session, sample_enrollment, sample_user_platform
    ):
        """Usuario de plataforma actualiza payment_order_url de su inscripción"""
        update_data = {"payment_order_url": "https://payment.example.com/order123"}

        response = enrollment_client.put(
            f"/api/v1/enrollments/{sample_enrollment.id}",
            json=update_data
        )

        assert response.status_code == 200
        assert response.json()["data"]["payment_order_url"] == "https://payment.example.com/order123"

    def test_update_enrollment_platform_cannot_change_status(
        self, enrollment_client, session, sample_enrollment, sample_user_platform
    ):
        """Usuario de plataforma NO puede cambiar el status"""
        response = enrollment_client.put(
            f"/api/v1/enrollments/{sample_enrollment.id}",
            json={"status": EnrollmentStatus.PAGADO.value}
        )

        assert response.status_code == 403
        assert "no pueden cambiar el estado" in response.json()["detail"].lower()

    def test_update_enrollment_admin_can_change_status(
        self, enrollment_admin_client, session, sample_enrollment, sample_admin_user
    ):
        """Admin puede cambiar status y payment_order_url"""
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

    # ------------------------------------------------------------------
    # DELETE /{id}
    # ------------------------------------------------------------------

    def test_delete_enrollment_success(
        self, enrollment_admin_client, session, sample_enrollment, sample_admin_user
    ):
        """Admin puede anular una inscripción"""
        response = enrollment_admin_client.delete(
            f"/api/v1/enrollments/{sample_enrollment.id}"
        )

        assert response.status_code == 200
        assert "anulada exitosamente" in response.json()["message"]

        from src.models.enrollment import Enrollment
        enrollment = session.get(Enrollment, sample_enrollment.id)
        assert enrollment.status == EnrollmentStatus.ANULADO

    # ------------------------------------------------------------------
    # GET /user/{id}
    # ------------------------------------------------------------------

    def test_get_user_enrollments(
        self, enrollment_client, session, sample_user_platform, sample_enrollment
    ):
        """Listar inscripciones de un usuario"""
        response = enrollment_client.get(
            f"/api/v1/enrollments/user/{sample_user_platform.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert "enrollments" in data
        assert data["user_id"] == sample_user_platform.id
        assert len(data["enrollments"]) >= 1

    def test_get_user_enrollments_forbidden(self, enrollment_client, sample_user_platform):
        """403 al intentar ver inscripciones de otro usuario"""
        response = enrollment_client.get("/api/v1/enrollments/user/99999")

        assert response.status_code == 403

    # ------------------------------------------------------------------
    # GET /course/{id} y /congress/{id}
    # ------------------------------------------------------------------

    def test_get_course_enrollments(
        self, enrollment_admin_client, session, sample_course, sample_enrollment, sample_admin_user
    ):
        """Admin obtiene lista paginada de inscritos en un curso"""
        response = enrollment_admin_client.get(
            f"/api/v1/enrollments/course/{sample_course.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "pagination" in data
        assert data["course_id"] == sample_course.id

    def test_get_congress_enrollments(
        self,
        enrollment_admin_client,
        session,
        sample_congress,
        sample_congress_enrollment,
        sample_admin_user,
    ):
        """Admin obtiene lista paginada de inscritos en un congreso"""
        response = enrollment_admin_client.get(
            f"/api/v1/enrollments/congress/{sample_congress.id_congreso}"
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "pagination" in data
        assert data["congress_id"] == sample_congress.id_congreso
        assert len(data["items"]) >= 1

    # ------------------------------------------------------------------
    # GET / — paginación general
    # ------------------------------------------------------------------

    def test_list_enrollments_paginated(
        self, enrollment_client, session, sample_user_platform, sample_enrollment
    ):
        """Listar inscripciones paginadas"""
        response = enrollment_client.get("/api/v1/enrollments/?page=1&page_size=10")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "pagination" in data
        assert len(data["items"]) <= 10

    def test_list_enrollments_filter_by_course(
        self, enrollment_client, session, sample_user_platform, sample_course, sample_enrollment
    ):
        """Filtrar inscripciones por curso y estado"""
        response = enrollment_client.get(
            f"/api/v1/enrollments/?status={EnrollmentStatus.INTERESADO.value}"
            f"&course_id={sample_course.id}"
        )

        assert response.status_code == 200
        assert "items" in response.json()

    def test_list_enrollments_filter_by_congress(
        self,
        enrollment_client,
        session,
        sample_user_platform,
        sample_congress,
        sample_congress_enrollment,
    ):
        """Filtrar inscripciones por congreso"""
        response = enrollment_client.get(
            f"/api/v1/enrollments/?congress_id={sample_congress.id_congreso}"
        )

        assert response.status_code == 200
        assert "items" in response.json()

    # ------------------------------------------------------------------
    # GET /stats/course/{id} y /stats/congress/{id}
    # ------------------------------------------------------------------

    def test_get_course_stats(
        self, enrollment_admin_client, session, sample_course, sample_enrollment, sample_admin_user
    ):
        """Admin obtiene estadísticas de inscripciones por curso"""
        response = enrollment_admin_client.get(
            f"/api/v1/enrollments/stats/course/{sample_course.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["course_id"] == sample_course.id
        assert "total_inscriptions" in data
        assert "by_status" in data

    def test_get_congress_stats(
        self,
        enrollment_admin_client,
        session,
        sample_congress,
        sample_congress_enrollment,
        sample_admin_user,
    ):
        """Admin obtiene estadísticas de inscripciones por congreso"""
        response = enrollment_admin_client.get(
            f"/api/v1/enrollments/stats/congress/{sample_congress.id_congreso}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["congress_id"] == sample_congress.id_congreso
        assert "total_inscriptions" in data
        assert "by_status" in data

    def test_get_course_stats_invalid_course(
        self, enrollment_admin_client, sample_admin_user
    ):
        """404 al obtener estadísticas de curso inexistente"""
        response = enrollment_admin_client.get("/api/v1/enrollments/stats/course/99999")

        assert response.status_code == 404

    def test_get_congress_stats_invalid_congress(
        self, enrollment_admin_client, sample_admin_user
    ):
        """404 al obtener estadísticas de congreso inexistente"""
        response = enrollment_admin_client.get("/api/v1/enrollments/stats/congress/99999")

        assert response.status_code == 404
