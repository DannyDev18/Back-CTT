"""
Tests de integración para los endpoints de Congress Categories

Estos tests verifican que los endpoints de la API de categorías de congresos funcionen correctamente,
incluyendo validaciones, respuestas HTTP correctas y manejo de errores.
"""
import pytest
from src.models.congress_category import CongressCategoryStatus
from src.utils.jwt_utils import encode_token


class TestCongressCategoriesEndpoints:
    """Suite de tests para los endpoints de congress-categories"""

    @pytest.fixture
    def sample_user(self, session):
        """Crea un usuario de prueba"""
        from src.models.user import User

        user = User(
            name="Admin",
            last_name="Test",
            email="admin@test.com",
            password="hashed_password"
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    @pytest.fixture
    def auth_token(self, sample_user):
        """Token de autenticación para tests que requieren auth"""
        token = encode_token({
            "user_id": sample_user.id,
            "username": sample_user.name,
            "email": sample_user.email
        })
        return token

    @pytest.fixture
    def auth_headers(self, auth_token):
        """Headers con autenticación"""
        return {"Authorization": f"Bearer {auth_token}"}

    @pytest.fixture
    def sample_congress_category_payload(self):
        """Payload de ejemplo para crear una categoría de congreso"""
        return {
            "name": "Tecnología",
            "description": "Congresos de tecnología e innovación",
            "svgurl": "https://example.com/icons/technology.svg",
            "status": "activo"
        }

    @pytest.fixture
    def congress_categories_client(self, session):
        """Cliente de prueba con el router de categorías de congresos incluido"""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from src.routes.congress_categories_router import congress_categories_router
        from src.dependencies.db_session import get_db

        test_app = FastAPI()

        def override_get_db():
            try:
                yield session
            finally:
                pass

        test_app.dependency_overrides[get_db] = override_get_db
        test_app.include_router(congress_categories_router)

        with TestClient(test_app) as test_client:
            yield test_client

    # ==================== POST /api/v1/congress-categories ====================

    def test_create_congress_category_success(
        self,
        congress_categories_client,
        sample_congress_category_payload,
        auth_headers
    ):
        """
        Test: POST /api/v1/congress-categories - Crear categoría exitosamente

        Verifica que se puede crear una categoría de congreso con datos válidos
        """
        # Act
        response = congress_categories_client.post(
            "/api/v1/congress-categories/",
            json=sample_congress_category_payload,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Tecnología"
        assert data["description"] == "Congresos de tecnología e innovación"
        assert data["status"] == "activo"
        assert "id" in data

    def test_create_congress_category_without_auth(
        self,
        congress_categories_client,
        sample_congress_category_payload
    ):
        """
        Test: POST /api/v1/congress-categories - Sin autenticación

        Verifica que no se puede crear sin token
        """
        # Act
        response = congress_categories_client.post(
            "/api/v1/congress-categories/",
            json=sample_congress_category_payload
        )

        # Assert
        assert response.status_code == 401

    def test_create_congress_category_duplicate_name(
        self,
        congress_categories_client,
        sample_congress_category_payload,
        auth_headers
    ):
        """
        Test: POST /api/v1/congress-categories - Nombre duplicado

        Verifica que no se puede crear categoría con nombre existente
        """
        # Arrange: Crear primera categoría
        congress_categories_client.post(
            "/api/v1/congress-categories/",
            json=sample_congress_category_payload,
            headers=auth_headers
        )

        # Act: Intentar crear con mismo nombre
        response = congress_categories_client.post(
            "/api/v1/congress-categories/",
            json=sample_congress_category_payload,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 400
        assert "Ya existe" in response.json()["detail"]

    def test_create_congress_category_invalid_data(
        self,
        congress_categories_client,
        auth_headers
    ):
        """
        Test: POST /api/v1/congress-categories - Datos inválidos

        Verifica validación de campos obligatorios
        """
        # Act: Enviar payload sin nombre
        invalid_payload = {
            "description": "Solo descripción"
        }
        response = congress_categories_client.post(
            "/api/v1/congress-categories/",
            json=invalid_payload,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 422  # Validation error

    def test_create_congress_category_minimal_data(
        self,
        congress_categories_client,
        auth_headers
    ):
        """
        Test: POST /api/v1/congress-categories - Datos mínimos requeridos

        Verifica que se puede crear con solo el nombre
        """
        # Act
        minimal_payload = {
            "name": "Categoría Mínima"
        }
        response = congress_categories_client.post(
            "/api/v1/congress-categories/",
            json=minimal_payload,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Categoría Mínima"
        assert data["description"] is None
        assert data["svgurl"] is None

    # ==================== GET /api/v1/congress-categories/enabled ====================

    def test_get_enabled_congress_categories(
        self,
        congress_categories_client,
        auth_headers
    ):
        """
        Test: GET /api/v1/congress-categories/enabled - Solo activas

        Verifica que retorna solo categorías activas (público)
        """
        # Arrange: Crear categorías
        congress_categories_client.post(
            "/api/v1/congress-categories/",
            json={"name": "Activa 1", "status": "activo"},
            headers=auth_headers
        )
        congress_categories_client.post(
            "/api/v1/congress-categories/",
            json={"name": "Activa 2", "status": "activo"},
            headers=auth_headers
        )
        congress_categories_client.post(
            "/api/v1/congress-categories/",
            json={"name": "Inactiva", "status": "inactivo"},
            headers=auth_headers
        )

        # Act: Sin auth (endpoint público)
        response = congress_categories_client.get("/api/v1/congress-categories/enabled")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        for category in data:
            assert category["status"] == "activo"

    # ==================== GET /api/v1/congress-categories ====================

    def test_get_all_congress_categories_empty(self, congress_categories_client, auth_headers):
        """
        Test: GET /api/v1/congress-categories - Lista vacía

        Verifica respuesta cuando no hay categorías
        """
        # Act
        response = congress_categories_client.get("/api/v1/congress-categories/", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0

    def test_get_all_congress_categories_with_data(
        self,
        congress_categories_client,
        sample_congress_category_payload,
        auth_headers
    ):
        """
        Test: GET /api/v1/congress-categories - Con datos

        Verifica que retorna todas las categorías
        """
        # Arrange: Crear categorías
        congress_categories_client.post(
            "/api/v1/congress-categories/",
            json=sample_congress_category_payload,
            headers=auth_headers
        )

        second_category = {
            "name": "Ciencia",
            "description": "Congresos de ciencia",
            "status": "activo"
        }
        congress_categories_client.post(
            "/api/v1/congress-categories/",
            json=second_category,
            headers=auth_headers
        )

        # Act
        response = congress_categories_client.get("/api/v1/congress-categories/", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    def test_get_all_congress_categories_pagination(
        self,
        congress_categories_client,
        auth_headers
    ):
        """
        Test: GET /api/v1/congress-categories - Paginación

        Verifica que la paginación funciona correctamente
        """
        # Arrange: Crear 5 categorías
        for i in range(1, 6):
            congress_categories_client.post(
                "/api/v1/congress-categories/",
                json={"name": f"Categoría {i}"},
                headers=auth_headers
            )

        # Act: Primera página (3 items)
        response_page1 = congress_categories_client.get(
            "/api/v1/congress-categories/?page=1&page_size=3",
            headers=auth_headers
        )

        # Assert: Primera página
        assert response_page1.status_code == 200
        data_page1 = response_page1.json()
        assert data_page1["total"] == 5
        assert len(data_page1["items"]) == 3
        assert data_page1["page"] == 1

        # Act: Segunda página
        response_page2 = congress_categories_client.get(
            "/api/v1/congress-categories/?page=2&page_size=3",
            headers=auth_headers
        )

        # Assert: Segunda página
        data_page2 = response_page2.json()
        assert len(data_page2["items"]) == 2  # Solo quedan 2

    def test_get_all_congress_categories_filter_by_status(
        self,
        congress_categories_client,
        auth_headers
    ):
        """
        Test: GET /api/v1/congress-categories - Filtro por estado

        Verifica que se pueden filtrar categorías por estado
        """
        # Arrange: Crear categorías activas e inactivas
        congress_categories_client.post(
            "/api/v1/congress-categories/",
            json={"name": "Activa", "status": "activo"},
            headers=auth_headers
        )
        congress_categories_client.post(
            "/api/v1/congress-categories/",
            json={"name": "Inactiva", "status": "inactivo"},
            headers=auth_headers
        )

        # Act: Filtrar solo activas
        response = congress_categories_client.get(
            "/api/v1/congress-categories/?status_filter=activo",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "Activa"

    # ==================== GET /api/v1/congress-categories/{category_id} ====================

    def test_get_congress_category_by_id_success(
        self,
        congress_categories_client,
        sample_congress_category_payload,
        auth_headers
    ):
        """
        Test: GET /api/v1/congress-categories/{id} - Categoría existente
        """
        # Arrange: Crear categoría
        create_response = congress_categories_client.post(
            "/api/v1/congress-categories/",
            json=sample_congress_category_payload,
            headers=auth_headers
        )
        category_id = create_response.json()["id"]

        # Act
        response = congress_categories_client.get(f"/api/v1/congress-categories/{category_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == category_id
        assert data["name"] == "Tecnología"

    def test_get_congress_category_by_id_not_found(self, congress_categories_client):
        """
        Test: GET /api/v1/congress-categories/{id} - Categoría no existe
        """
        # Act
        response = congress_categories_client.get("/api/v1/congress-categories/9999")

        # Assert
        assert response.status_code == 404

    # ==================== GET /api/v1/congress-categories/by-name/{name} ====================

    def test_get_congress_category_by_name_success(
        self,
        congress_categories_client,
        sample_congress_category_payload,
        auth_headers
    ):
        """
        Test: GET /api/v1/congress-categories/by-name/{name} - Categoría existente
        """
        # Arrange
        congress_categories_client.post(
            "/api/v1/congress-categories/",
            json=sample_congress_category_payload,
            headers=auth_headers
        )

        # Act
        response = congress_categories_client.get("/api/v1/congress-categories/by-name/Tecnología")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Tecnología"

    def test_get_congress_category_by_name_not_found(self, congress_categories_client):
        """
        Test: GET /api/v1/congress-categories/by-name/{name} - No existe
        """
        # Act
        response = congress_categories_client.get("/api/v1/congress-categories/by-name/NoExiste")

        # Assert
        assert response.status_code == 404

    # ==================== PUT /api/v1/congress-categories/{category_id} ====================

    def test_update_congress_category_success(
        self,
        congress_categories_client,
        sample_congress_category_payload,
        auth_headers
    ):
        """
        Test: PUT /api/v1/congress-categories/{id} - Actualizar exitosamente
        """
        # Arrange: Crear categoría
        create_response = congress_categories_client.post(
            "/api/v1/congress-categories/",
            json=sample_congress_category_payload,
            headers=auth_headers
        )
        category_id = create_response.json()["id"]

        # Act: Actualizar
        update_payload = {
            "name": "Tecnología Avanzada",
            "description": "Congresos de tecnología de punta"
        }
        response = congress_categories_client.put(
            f"/api/v1/congress-categories/{category_id}",
            json=update_payload,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Tecnología Avanzada"
        assert data["description"] == "Congresos de tecnología de punta"

    def test_update_congress_category_not_found(
        self,
        congress_categories_client,
        auth_headers
    ):
        """
        Test: PUT /api/v1/congress-categories/{id} - Categoría no existe
        """
        # Act
        update_payload = {"name": "Nuevo Nombre"}
        response = congress_categories_client.put(
            "/api/v1/congress-categories/9999",
            json=update_payload,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 404

    def test_update_congress_category_without_auth(
        self,
        congress_categories_client,
        sample_congress_category_payload,
        auth_headers
    ):
        """
        Test: PUT /api/v1/congress-categories/{id} - Sin autenticación
        """
        # Arrange: Crear categoría
        create_response = congress_categories_client.post(
            "/api/v1/congress-categories/",
            json=sample_congress_category_payload,
            headers=auth_headers
        )
        category_id = create_response.json()["id"]

        # Act: Intentar actualizar sin auth
        response = congress_categories_client.put(
            f"/api/v1/congress-categories/{category_id}",
            json={"name": "Nuevo Nombre"}
        )

        # Assert
        assert response.status_code == 401

    # ==================== DELETE /api/v1/congress-categories/{category_id} ====================

    def test_delete_congress_category_success(
        self,
        congress_categories_client,
        sample_congress_category_payload,
        auth_headers
    ):
        """
        Test: DELETE /api/v1/congress-categories/{id} - Eliminar exitosamente

        Verifica soft delete (marca como inactiva)
        """
        # Arrange: Crear categoría
        create_response = congress_categories_client.post(
            "/api/v1/congress-categories/",
            json=sample_congress_category_payload,
            headers=auth_headers
        )
        category_id = create_response.json()["id"]

        # Act
        response = congress_categories_client.delete(
            f"/api/v1/congress-categories/{category_id}",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 204

        # Verificar que está inactiva
        get_response = congress_categories_client.get(f"/api/v1/congress-categories/{category_id}")
        if get_response.status_code == 200:
            data = get_response.json()
            assert data["status"] == "inactivo"

    def test_delete_congress_category_not_found(
        self,
        congress_categories_client,
        auth_headers
    ):
        """
        Test: DELETE /api/v1/congress-categories/{id} - Categoría no existe
        """
        # Act
        response = congress_categories_client.delete(
            "/api/v1/congress-categories/9999",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 404

    def test_delete_congress_category_without_auth(
        self,
        congress_categories_client,
        sample_congress_category_payload,
        auth_headers
    ):
        """
        Test: DELETE /api/v1/congress-categories/{id} - Sin autenticación
        """
        # Arrange: Crear categoría
        create_response = congress_categories_client.post(
            "/api/v1/congress-categories/",
            json=sample_congress_category_payload,
            headers=auth_headers
        )
        category_id = create_response.json()["id"]

        # Act: Intentar eliminar sin auth
        response = congress_categories_client.delete(
            f"/api/v1/congress-categories/{category_id}"
        )

        # Assert
        assert response.status_code == 401
