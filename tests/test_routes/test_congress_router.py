"""
Tests de integración y rendimiento para los endpoints de Congresses

Verifican que los endpoints de la API funcionen correctamente,
incluyendo validaciones, respuestas HTTP y manejo de errores.
"""
import pytest
import time as time_module
from datetime import date, time
from src.models.congress import CongressStatus
from src.utils.jwt_utils import encode_token


# ===========================================================
# Fixtures locales
# ===========================================================

@pytest.fixture
def sample_test_user(session):
    """Crea un usuario admin de prueba"""
    from src.models.user import User

    user = User(
        name="Admin",
        last_name="Congress",
        email="admin_congress@test.com",
        password="hashed_password",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def auth_token(session, sample_test_user):
    """Token JWT válido para endpoints protegidos"""
    return encode_token({
        "username": sample_test_user.name,
        "email": sample_test_user.email,
    })


@pytest.fixture
def auth_headers(auth_token):
    """Headers con autenticación Bearer"""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def congress_payload(sample_category):
    """Payload JSON completo para crear un congreso vía API"""
    return {
        "congress": {
            "title": "Congreso API Test",
            "description": "Congreso creado desde los tests de integración",
            "place": "Auditorio FISEI",
            "congress_image": "test.jpg",
            "congress_image_detail": "test_detail.jpg",
            "category_id": sample_category.id,
            "status": "activo",
            "objectives": ["Innovar", "Compartir conocimiento"],
            "organizers": ["FISEI-UTA"],
            "materials": ["Presentaciones digitales"],
            "target_audience": ["Estudiantes", "Profesionales"],
        },
        "requirements": {
            "start_date_registration": "2025-08-01",
            "end_date_registration": "2025-09-15",
            "start_date_congress": "2025-10-08",
            "end_date_congress": "2025-10-10",
            "days": ["Miércoles", "Jueves", "Viernes"],
            "start_time": "08:30:00",
            "end_time": "18:00:00",
            "location": "Auditorio Central FISEI",
            "min_quota": 30,
            "max_quota": 200,
            "in_person_hours": 24,
            "autonomous_hours": 8,
            "modality": "Presencial",
            "certification": "Certificado digital con validación QR",
            "prerequisites": ["Ninguno"],
            "prices": [
                {"amount": 20, "category": "Estudiantes"},
                {"amount": 50, "category": "Público general"},
            ],
        },
        "contents": [
            {
                "unit": "Día 1",
                "title": "Fundamentos de IA",
                "topics": [
                    {"unit": "Sesión 1", "title": "Keynote: El futuro de la IA"},
                    {"unit": "Sesión 2", "title": "Machine Learning práctico"},
                ],
            }
        ],
    }


# ===========================================================
# Tests de integración — CRUD completo
# ===========================================================

class TestCongressEndpoints:
    """Suite de tests de integración para /api/v1/congresses"""

    # ---- GET (listado) ----

    def test_get_all_congresses_empty(self, client):
        """GET /api/v1/congresses sin datos → 200 con lista vacía"""
        response = client.get("/api/v1/congresses")

        assert response.status_code == 200
        data = response.json()
        assert "congresses" in data
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert isinstance(data["congresses"], list)

    def test_get_all_congresses_with_data(
        self, client, session,
        sample_congress_data, sample_congress_requirements_data,
        sample_congress_contents_data, sample_test_user,
    ):
        """GET /api/v1/congresses con datos → lista paginada con congresos"""
        from src.controllers.congress_controller import CongressController

        CongressController.create_congress_with_requirements(
            sample_congress_data,
            sample_congress_requirements_data,
            sample_congress_contents_data,
            session,
            sample_test_user.id,
        )

        response = client.get("/api/v1/congresses")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["congresses"]) >= 1
        assert data["congresses"][0]["title"] is not None

    def test_get_all_congresses_filter_by_status(
        self, client, session,
        sample_congress_data, sample_congress_requirements_data,
        sample_congress_contents_data, sample_test_user,
    ):
        """GET /api/v1/congresses?status=inactivo → solo inactivos"""
        from src.controllers.congress_controller import CongressController

        created = CongressController.create_congress_with_requirements(
            sample_congress_data,
            sample_congress_requirements_data,
            sample_congress_contents_data,
            session,
            sample_test_user.id,
        )
        CongressController.delete_congress(created["id"], db=session)

        response = client.get("/api/v1/congresses?status=inactivo")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert all(c["status"] == "inactivo" for c in data["congresses"])

    def test_get_all_congresses_filter_by_category(
        self, client, session,
        sample_congress_data, sample_congress_requirements_data,
        sample_congress_contents_data, sample_test_user, sample_category,
    ):
        """GET /api/v1/congresses?category_id=<id> → filtra por categoría"""
        from src.controllers.congress_controller import CongressController

        CongressController.create_congress_with_requirements(
            sample_congress_data,
            sample_congress_requirements_data,
            sample_congress_contents_data,
            session,
            sample_test_user.id,
        )

        response = client.get(f"/api/v1/congresses?category_id={sample_category.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    def test_get_all_congresses_invalid_category(self, client):
        """GET /api/v1/congresses?category_id=99999 → 404"""
        response = client.get("/api/v1/congresses?category_id=99999")
        assert response.status_code == 404

    def test_get_all_congresses_pagination_params(
        self, client, session,
        sample_congress_data, sample_congress_requirements_data,
        sample_congress_contents_data, sample_test_user, sample_category,
    ):
        """GET /api/v1/congresses?page=1&page_size=2 → respeta paginación"""
        from src.controllers.congress_controller import CongressController
        from src.models.congress import CongressCreate

        for i in range(4):
            from src.models.congress import CongressCreate
            data = CongressCreate(
                title=f"Congreso Paginación {i}",
                description="test",
                place="Auditorio",
                congress_image="img.jpg",
                congress_image_detail="img_detail.jpg",
                category_id=sample_category.id,
                objectives=[], organizers=[], materials=[], target_audience=[],
            )
            CongressController.create_congress_with_requirements(
                data, sample_congress_requirements_data, [], session, sample_test_user.id,
            )

        response = client.get("/api/v1/congresses?page=1&page_size=2")

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert len(data["congresses"]) == 2
        assert data["total_pages"] >= 2

    # ---- GET (detalle por ID) ----

    def test_get_congress_by_id_found(
        self, client, session,
        sample_congress_data, sample_congress_requirements_data,
        sample_congress_contents_data, sample_test_user,
    ):
        """GET /api/v1/congresses/{id} → 200 con datos completos"""
        from src.controllers.congress_controller import CongressController

        created = CongressController.create_congress_with_requirements(
            sample_congress_data,
            sample_congress_requirements_data,
            sample_congress_contents_data,
            session,
            sample_test_user.id,
        )

        response = client.get(f"/api/v1/congresses/{created['id']}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created["id"]
        assert data["title"] == sample_congress_data.title
        assert data["requirement"] is not None
        assert len(data["contents"]) == 2

    def test_get_congress_by_id_not_found(self, client):
        """GET /api/v1/congresses/99999 → 404"""
        response = client.get("/api/v1/congresses/99999")
        assert response.status_code == 404

    # ---- GET (buscar por título) ----

    def test_search_congresses_found(
        self, client, session,
        sample_congress_data, sample_congress_requirements_data,
        sample_congress_contents_data, sample_test_user,
    ):
        """GET /api/v1/congresses/search?query=inteligencia → resultados parciales"""
        from src.controllers.congress_controller import CongressController

        CongressController.create_congress_with_requirements(
            sample_congress_data,
            sample_congress_requirements_data,
            sample_congress_contents_data,
            session,
            sample_test_user.id,
        )

        response = client.get("/api/v1/congresses/search?query=Inteligencia")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert any("Inteligencia" in c["title"] for c in data["congresses"])

    def test_search_congresses_case_insensitive(
        self, client, session,
        sample_congress_data, sample_congress_requirements_data,
        sample_congress_contents_data, sample_test_user,
    ):
        """GET /api/v1/congresses/search?query=CONGRESO → case-insensitive"""
        from src.controllers.congress_controller import CongressController

        CongressController.create_congress_with_requirements(
            sample_congress_data,
            sample_congress_requirements_data,
            sample_congress_contents_data,
            session,
            sample_test_user.id,
        )

        response = client.get("/api/v1/congresses/search?query=CONGRESO")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    def test_search_congresses_not_found(self, client):
        """GET /api/v1/congresses/search?query=Blockchain → lista vacía"""
        response = client.get("/api/v1/congresses/search?query=Blockchain")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["congresses"]) == 0

    def test_search_congresses_missing_query(self, client):
        """GET /api/v1/congresses/search sin query → 422 validation error"""
        response = client.get("/api/v1/congresses/search")
        assert response.status_code == 422

    def test_search_congresses_empty_query(self, client):
        """GET /api/v1/congresses/search?query= (vacío) → 422 por min_length"""
        response = client.get("/api/v1/congresses/search?query=")
        assert response.status_code == 422

    # ---- GET (por categoría) ----

    def test_get_congresses_by_category(
        self, client, session,
        sample_congress_data, sample_congress_requirements_data,
        sample_congress_contents_data, sample_test_user, sample_category,
    ):
        """GET /api/v1/congresses/category/{id} → congresos de esa categoría"""
        from src.controllers.congress_controller import CongressController

        CongressController.create_congress_with_requirements(
            sample_congress_data,
            sample_congress_requirements_data,
            sample_congress_contents_data,
            session,
            sample_test_user.id,
        )

        response = client.get(f"/api/v1/congresses/category/{sample_category.id}")

        assert response.status_code == 200
        data = response.json()
        assert "congresses" in data
        assert data["total"] >= 1

    def test_get_congresses_by_category_not_found(self, client):
        """GET /api/v1/congresses/category/99999 → 404"""
        response = client.get("/api/v1/congresses/category/99999")
        assert response.status_code == 404

    # ---- POST (crear) ----

    def test_create_congress_without_auth(self, client, congress_payload):
        """POST /api/v1/congresses sin token → 401"""
        response = client.post("/api/v1/congresses", json=congress_payload)
        assert response.status_code == 401

    def test_create_congress_invalid_token(self, client, congress_payload):
        """POST /api/v1/congresses con token inválido → 401"""
        response = client.post(
            "/api/v1/congresses",
            json=congress_payload,
            headers={"Authorization": "Bearer invalidtoken"},
        )
        assert response.status_code == 401

    def test_create_congress_with_auth(self, client, auth_headers, congress_payload):
        """POST /api/v1/congresses con token válido → 201 con congreso creado"""
        response = client.post(
            "/api/v1/congresses",
            json=congress_payload,
            headers=auth_headers,
        )

        if response.status_code != 201:
            print(f"Error: {response.json()}")
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Congress created successfully"
        assert "congress_id" in data
        assert data["congress_id"] is not None

    def test_create_congress_invalid_category(self, client, auth_headers, congress_payload):
        """POST /api/v1/congresses con category_id inexistente → 404"""
        congress_payload["congress"]["category_id"] = 99999
        response = client.post(
            "/api/v1/congresses",
            json=congress_payload,
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_create_congress_missing_required_fields(self, client, auth_headers):
        """POST /api/v1/congresses con payload incompleto → 422"""
        response = client.post(
            "/api/v1/congresses",
            json={"congress": {"title": "Solo título"}},
            headers=auth_headers,
        )
        assert response.status_code == 422

    # ---- PATCH (actualizar) ----

    def test_update_congress_without_auth(self, client):
        """PATCH /api/v1/congresses/{id} sin token → 401"""
        response = client.patch("/api/v1/congresses/1", json={"congress": {"title": "X"}})
        assert response.status_code == 401

    def test_update_congress_with_auth(
        self, client, auth_headers, session,
        sample_congress_data, sample_congress_requirements_data,
        sample_congress_contents_data, sample_test_user,
    ):
        """PATCH /api/v1/congresses/{id} con token → 200 con datos actualizados"""
        from src.controllers.congress_controller import CongressController

        created = CongressController.create_congress_with_requirements(
            sample_congress_data,
            sample_congress_requirements_data,
            sample_congress_contents_data,
            session,
            sample_test_user.id,
        )

        response = client.patch(
            f"/api/v1/congresses/{created['id']}",
            json={"congress": {"title": "Congreso Actualizado PATCH"}},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Congress updated successfully"
        assert data["data"]["title"] == "Congreso Actualizado PATCH"

    def test_update_congress_not_found(self, client, auth_headers):
        """PATCH /api/v1/congresses/99999 → 404"""
        response = client.patch(
            "/api/v1/congresses/99999",
            json={"congress": {"title": "No existe"}},
            headers=auth_headers,
        )
        assert response.status_code == 404

    # ---- DELETE (eliminar) ----

    def test_delete_congress_without_auth(self, client):
        """DELETE /api/v1/congresses/{id} sin token → 401"""
        response = client.delete("/api/v1/congresses/1")
        assert response.status_code == 401

    def test_delete_congress_with_auth(
        self, client, auth_headers, session,
        sample_congress_data, sample_congress_requirements_data,
        sample_congress_contents_data, sample_test_user,
    ):
        """DELETE /api/v1/congresses/{id} con token → 200 soft delete"""
        from src.controllers.congress_controller import CongressController

        created = CongressController.create_congress_with_requirements(
            sample_congress_data,
            sample_congress_requirements_data,
            sample_congress_contents_data,
            session,
            sample_test_user.id,
        )

        response = client.delete(
            f"/api/v1/congresses/{created['id']}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Congress deleted successfully"

    def test_delete_congress_not_found(self, client, auth_headers):
        """DELETE /api/v1/congresses/99999 → 404"""
        response = client.delete("/api/v1/congresses/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_delete_congress_already_deleted(
        self, client, auth_headers, session,
        sample_congress_data, sample_congress_requirements_data,
        sample_congress_contents_data, sample_test_user,
    ):
        """DELETE /api/v1/congresses/{id} dos veces → segunda vez 404"""
        from src.controllers.congress_controller import CongressController

        created = CongressController.create_congress_with_requirements(
            sample_congress_data,
            sample_congress_requirements_data,
            sample_congress_contents_data,
            session,
            sample_test_user.id,
        )
        congress_id = created["id"]

        client.delete(f"/api/v1/congresses/{congress_id}", headers=auth_headers)
        response = client.delete(f"/api/v1/congresses/{congress_id}", headers=auth_headers)

        assert response.status_code == 404

    # ---- Formato de respuesta ----

    def test_response_content_type_is_json(self, client):
        """Todas las respuestas tienen Content-Type application/json"""
        response = client.get("/api/v1/congresses")
        assert response.headers["content-type"] == "application/json"

    def test_paginated_response_structure(self, client):
        """La respuesta paginada incluye todos los campos de metadata esperados"""
        response = client.get("/api/v1/congresses")

        assert response.status_code == 200
        data = response.json()
        required_keys = {"total", "total_pages", "page", "page_size", "has_next", "has_prev", "links", "congresses"}
        assert required_keys.issubset(data.keys())

    def test_congress_detail_structure(
        self, client, session,
        sample_congress_data, sample_congress_requirements_data,
        sample_congress_contents_data, sample_test_user,
    ):
        """GET /{id} devuelve la estructura de detalle completa del congreso"""
        from src.controllers.congress_controller import CongressController

        created = CongressController.create_congress_with_requirements(
            sample_congress_data,
            sample_congress_requirements_data,
            sample_congress_contents_data,
            session,
            sample_test_user.id,
        )

        response = client.get(f"/api/v1/congresses/{created['id']}")
        data = response.json()

        for field in ["id", "title", "description", "place", "status",
                      "objectives", "organizers", "materials", "target_audience",
                      "requirement", "contents"]:
            assert field in data, f"Campo '{field}' faltante en la respuesta"

        req = data["requirement"]
        assert "registration" in req
        assert "congressSchedule" in req
        assert "hours" in req
        assert req["hours"]["total"] == 32


# ===========================================================
# Tests de rendimiento
# ===========================================================

class TestCongressEndpointsPerformance:
    """Tests de rendimiento para /api/v1/congresses"""

    def test_list_endpoint_response_time(self, client):
        """GET /api/v1/congresses responde en menos de 1 segundo"""
        start = time_module.time()
        response = client.get("/api/v1/congresses")
        elapsed = time_module.time() - start

        assert response.status_code == 200
        assert elapsed < 1.0, f"Tiempo de respuesta {elapsed:.3f}s supera el límite de 1s"

    def test_detail_endpoint_response_time(
        self, client, session,
        sample_congress_data, sample_congress_requirements_data,
        sample_congress_contents_data, sample_test_user,
    ):
        """GET /api/v1/congresses/{id} responde en menos de 1 segundo"""
        from src.controllers.congress_controller import CongressController

        created = CongressController.create_congress_with_requirements(
            sample_congress_data,
            sample_congress_requirements_data,
            sample_congress_contents_data,
            session,
            sample_test_user.id,
        )

        start = time_module.time()
        response = client.get(f"/api/v1/congresses/{created['id']}")
        elapsed = time_module.time() - start

        assert response.status_code == 200
        assert elapsed < 1.0, f"Tiempo de respuesta {elapsed:.3f}s supera el límite de 1s"

    def test_search_endpoint_response_time(self, client):
        """GET /api/v1/congresses/search responde en menos de 1 segundo"""
        start = time_module.time()
        response = client.get("/api/v1/congresses/search?query=Congreso")
        elapsed = time_module.time() - start

        assert response.status_code == 200
        assert elapsed < 1.0, f"Tiempo de respuesta {elapsed:.3f}s supera el límite de 1s"

    def test_create_endpoint_response_time(
        self, client, auth_headers, congress_payload,
    ):
        """POST /api/v1/congresses responde en menos de 2 segundos"""
        start = time_module.time()
        response = client.post(
            "/api/v1/congresses",
            json=congress_payload,
            headers=auth_headers,
        )
        elapsed = time_module.time() - start

        assert response.status_code == 201
        assert elapsed < 2.0, f"Tiempo de creación {elapsed:.3f}s supera el límite de 2s"

    def test_sequential_reads_performance(
        self, client, session,
        sample_congress_data, sample_congress_requirements_data,
        sample_congress_contents_data, sample_test_user,
    ):
        """10 peticiones GET consecutivas completan en menos de 5 segundos en total"""
        from src.controllers.congress_controller import CongressController

        CongressController.create_congress_with_requirements(
            sample_congress_data,
            sample_congress_requirements_data,
            sample_congress_contents_data,
            session,
            sample_test_user.id,
        )

        start = time_module.time()
        for _ in range(10):
            res = client.get("/api/v1/congresses")
            assert res.status_code == 200
        total = time_module.time() - start

        assert total < 5.0, f"10 requests tardaron {total:.3f}s, superan el límite de 5s"

    @pytest.mark.skip(reason="Test de carga, ejecutar manualmente cuando sea necesario")
    def test_concurrent_requests(self, client):
        """50 peticiones concurrentes completan con status 200"""
        import concurrent.futures

        def make_request():
            return client.get("/api/v1/congresses")

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(50)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        assert all(r.status_code == 200 for r in results)
