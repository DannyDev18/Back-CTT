"""
Tests de integración para los endpoints de Categories

Estos tests verifican que los endpoints de la API de categorías funcionen correctamente,
incluyendo validaciones, respuestas HTTP correctas y manejo de errores.
"""
import pytest
from src.models.category import CategoryStatus
from src.utils.jwt_utils import encode_token


class TestCategoriesEndpoints:
    """Suite de tests para los endpoints de categories"""

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
    def sample_category_payload(self):
        """Payload de ejemplo para crear una categoría"""
        return {
            "name": "Programación",
            "description": "Cursos de programación y desarrollo de software",
            "svgurl": "https://example.com/icons/programming.svg",
            "status": "activo"
        }

    @pytest.fixture
    def categories_client(self, session):
        """Cliente de prueba con el router de categorías incluido"""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from src.routes.categories_router import categories_router
        from src.dependencies.db_session import get_db
        
        test_app = FastAPI()
        
        def override_get_db():
            try:
                yield session
            finally:
                pass
        
        test_app.dependency_overrides[get_db] = override_get_db
        test_app.include_router(categories_router)
        
        with TestClient(test_app) as test_client:
            yield test_client

    # ==================== POST /api/v1/categories ====================

    def test_create_category_success(
        self,
        categories_client,
        sample_category_payload,
        auth_headers
    ):
        """
        Test: POST /api/v1/categories - Crear categoría exitosamente
        
        Verifica que se puede crear una categoría con datos válidos
        """
        # Act
        response = categories_client.post(
            "/api/v1/categories/",
            json=sample_category_payload,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Programación"
        assert data["description"] == "Cursos de programación y desarrollo de software"
        assert data["status"] == "activo"
        assert "id" in data

    def test_create_category_without_auth(
        self,
        categories_client,
        sample_category_payload
    ):
        """
        Test: POST /api/v1/categories - Sin autenticación
        
        Verifica que no se puede crear sin token
        """
        # Act
        response = categories_client.post(
            "/api/v1/categories/",
            json=sample_category_payload
        )
        
        # Assert
        assert response.status_code == 401

    def test_create_category_duplicate_name(
        self,
        categories_client,
        sample_category_payload,
        auth_headers
    ):
        """
        Test: POST /api/v1/categories - Nombre duplicado
        
        Verifica que no se puede crear categoría con nombre existente
        """
        # Arrange: Crear primera categoría
        categories_client.post(
            "/api/v1/categories/",
            json=sample_category_payload,
            headers=auth_headers
        )
        
        # Act: Intentar crear con mismo nombre
        response = categories_client.post(
            "/api/v1/categories/",
            json=sample_category_payload,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 400
        assert "Ya existe" in response.json()["detail"]

    def test_create_category_invalid_data(
        self,
        categories_client,
        auth_headers
    ):
        """
        Test: POST /api/v1/categories - Datos inválidos
        
        Verifica validación de campos obligatorios
        """
        # Act: Enviar payload sin nombre
        invalid_payload = {
            "description": "Solo descripción"
        }
        response = categories_client.post(
            "/api/v1/categories/",
            json=invalid_payload,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 422  # Validation error

    def test_create_category_minimal_data(
        self,
        categories_client,
        auth_headers
    ):
        """
        Test: POST /api/v1/categories - Datos mínimos requeridos
        
        Verifica que se puede crear con solo el nombre
        """
        # Act
        minimal_payload = {
            "name": "Categoría Mínima"
        }
        response = categories_client.post(
            "/api/v1/categories/",
            json=minimal_payload,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Categoría Mínima"
        assert data["description"] is None
        assert data["svgurl"] is None

    # ==================== GET /api/v1/categories/enabled ====================

    def test_get_enabled_categories(
        self,
        categories_client,
        auth_headers
    ):
        """
        Test: GET /api/v1/categories/enabled - Solo activas
        
        Verifica que retorna solo categorías activas (público)
        """
        # Arrange: Crear categorías
        categories_client.post(
            "/api/v1/categories/",
            json={"name": "Activa 1", "status": "activo"},
            headers=auth_headers
        )
        categories_client.post(
            "/api/v1/categories/",
            json={"name": "Activa 2", "status": "activo"},
            headers=auth_headers
        )
        categories_client.post(
            "/api/v1/categories/",
            json={"name": "Inactiva", "status": "inactivo"},
            headers=auth_headers
        )
        
        # Act: Sin auth (endpoint público)
        response = categories_client.get("/api/v1/categories/enabled")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        for category in data:
            assert category["status"] == "activo"

    # ==================== GET /api/v1/categories ====================

    def test_get_all_categories_empty(self, categories_client, auth_headers):
        """
        Test: GET /api/v1/categories - Lista vacía
        
        Verifica respuesta cuando no hay categorías
        """
        # Act
        response = categories_client.get("/api/v1/categories/", headers=auth_headers)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0

    def test_get_all_categories_with_data(
        self,
        categories_client,
        sample_category_payload,
        auth_headers
    ):
        """
        Test: GET /api/v1/categories - Con datos
        
        Verifica que retorna todas las categorías
        """
        # Arrange: Crear categorías
        categories_client.post(
            "/api/v1/categories/",
            json=sample_category_payload,
            headers=auth_headers
        )
        
        second_category = {
            "name": "Electrónica",
            "description": "Cursos de electrónica",
            "status": "activo"
        }
        categories_client.post(
            "/api/v1/categories/",
            json=second_category,
            headers=auth_headers
        )
        
        # Act
        response = categories_client.get("/api/v1/categories/", headers=auth_headers)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    def test_get_all_categories_pagination(
        self,
        categories_client,
        auth_headers
    ):
        """
        Test: GET /api/v1/categories - Paginación
        
        Verifica que la paginación funciona correctamente
        """
        # Arrange: Crear 5 categorías
        for i in range(1, 6):
            categories_client.post(
                "/api/v1/categories/",
                json={"name": f"Categoría {i}"},
                headers=auth_headers
            )
        
        # Act: Primera página (3 items)
        response_page1 = categories_client.get(
            "/api/v1/categories/?page=1&page_size=3",
            headers=auth_headers
        )
        
        # Assert: Primera página
        assert response_page1.status_code == 200
        data_page1 = response_page1.json()
        assert data_page1["total"] == 5
        assert len(data_page1["items"]) == 3
        assert data_page1["page"] == 1
        
        # Act: Segunda página
        response_page2 = categories_client.get(
            "/api/v1/categories/?page=2&page_size=3",
            headers=auth_headers
        )
        
        # Assert: Segunda página
        data_page2 = response_page2.json()
        assert len(data_page2["items"]) == 2  # Solo quedan 2

    def test_get_all_categories_filter_by_status(
        self,
        categories_client,
        auth_headers
    ):
        """
        Test: GET /api/v1/categories - Filtro por estado
        
        Verifica que se pueden filtrar categorías por estado
        """
        # Arrange: Crear categorías activas e inactivas
        categories_client.post(
            "/api/v1/categories/",
            json={"name": "Activa", "status": "activo"},
            headers=auth_headers
        )
        categories_client.post(
            "/api/v1/categories/",
            json={"name": "Inactiva", "status": "inactivo"},
            headers=auth_headers
        )
        
        # Act: Filtrar solo activas
        response = categories_client.get(
            "/api/v1/categories/?status_filter=activo",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "Activa"

    # ==================== GET /api/v1/categories/{category_id} ====================

    def test_get_category_by_id_success(
        self,
        categories_client,
        sample_category_payload,
        auth_headers
    ):
        """
        Test: GET /api/v1/categories/{id} - Categoría existente
        """
        # Arrange: Crear categoría
        create_response = categories_client.post(
            "/api/v1/categories/",
            json=sample_category_payload,
            headers=auth_headers
        )
        category_id = create_response.json()["id"]
        
        # Act
        response = categories_client.get(f"/api/v1/categories/{category_id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == category_id
        assert data["name"] == "Programación"

    def test_get_category_by_id_not_found(self, categories_client):
        """
        Test: GET /api/v1/categories/{id} - Categoría no existe
        """
        # Act
        response = categories_client.get("/api/v1/categories/9999")
        
        # Assert
        assert response.status_code == 404

    # ==================== GET /api/v1/categories/by-name/{name} ====================

    def test_get_category_by_name_success(
        self,
        categories_client,
        sample_category_payload,
        auth_headers
    ):
        """
        Test: GET /api/v1/categories/by-name/{name} - Categoría existente
        """
        # Arrange
        categories_client.post(
            "/api/v1/categories/",
            json=sample_category_payload,
            headers=auth_headers
        )
        
        # Act
        response = categories_client.get("/api/v1/categories/by-name/Programación")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Programación"

    def test_get_category_by_name_not_found(self, categories_client):
        """
        Test: GET /api/v1/categories/by-name/{name} - No existe
        """
        # Act
        response = categories_client.get("/api/v1/categories/by-name/NoExiste")
        
        # Assert
        assert response.status_code == 404

    # ==================== PUT /api/v1/categories/{category_id} ====================

    def test_update_category_success(
        self,
        categories_client,
        sample_category_payload,
        auth_headers
    ):
        """
        Test: PUT /api/v1/categories/{id} - Actualizar exitosamente
        """
        # Arrange: Crear categoría
        create_response = categories_client.post(
            "/api/v1/categories/",
            json=sample_category_payload,
            headers=auth_headers
        )
        category_id = create_response.json()["id"]
        
        # Act: Actualizar
        update_payload = {
            "name": "Programación Avanzada",
            "description": "Cursos avanzados"
        }
        response = categories_client.put(
            f"/api/v1/categories/{category_id}",
            json=update_payload,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Programación Avanzada"
        assert data["description"] == "Cursos avanzados"

    def test_update_category_not_found(
        self,
        categories_client,
        auth_headers
    ):
        """
        Test: PUT /api/v1/categories/{id} - Categoría no existe
        """
        # Act
        update_payload = {"name": "Nuevo Nombre"}
        response = categories_client.put(
            "/api/v1/categories/9999",
            json=update_payload,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 404

    def test_update_category_without_auth(
        self,
        categories_client,
        sample_category_payload,
        auth_headers
    ):
        """
        Test: PUT /api/v1/categories/{id} - Sin autenticación
        """
        # Arrange: Crear categoría
        create_response = categories_client.post(
            "/api/v1/categories/",
            json=sample_category_payload,
            headers=auth_headers
        )
        category_id = create_response.json()["id"]
        
        # Act: Intentar actualizar sin auth
        response = categories_client.put(
            f"/api/v1/categories/{category_id}",
            json={"name": "Nuevo Nombre"}
        )
        
        # Assert
        assert response.status_code == 401

    # ==================== DELETE /api/v1/categories/{category_id} ====================

    def test_delete_category_success(
        self,
        categories_client,
        sample_category_payload,
        auth_headers
    ):
        """
        Test: DELETE /api/v1/categories/{id} - Eliminar exitosamente
        
        Verifica soft delete (marca como inactiva)
        """
        # Arrange: Crear categoría
        create_response = categories_client.post(
            "/api/v1/categories/",
            json=sample_category_payload,
            headers=auth_headers
        )
        category_id = create_response.json()["id"]
        
        # Act
        response = categories_client.delete(
            f"/api/v1/categories/{category_id}",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 204
        
        # Verificar que está inactiva
        get_response = categories_client.get(f"/api/v1/categories/{category_id}")
        if get_response.status_code == 200:
            data = get_response.json()
            assert data["status"] == "inactivo"

    def test_delete_category_not_found(
        self,
        categories_client,
        auth_headers
    ):
        """
        Test: DELETE /api/v1/categories/{id} - Categoría no existe
        """
        # Act
        response = categories_client.delete(
            "/api/v1/categories/9999",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 404

    def test_delete_category_without_auth(
        self,
        categories_client,
        sample_category_payload,
        auth_headers
    ):
        """
        Test: DELETE /api/v1/categories/{id} - Sin autenticación
        """
        # Arrange: Crear categoría
        create_response = categories_client.post(
            "/api/v1/categories/",
            json=sample_category_payload,
            headers=auth_headers
        )
        category_id = create_response.json()["id"]
        
        # Act: Intentar eliminar sin auth
        response = categories_client.delete(
            f"/api/v1/categories/{category_id}"
        )
        
        # Assert
        assert response.status_code == 401
