"""
Tests de integración para los endpoints de Sponsor

Estos tests verifican que los endpoints del router de sponsors
funcionen correctamente.
"""
import pytest


class TestSponsorEndpoints:
    """Suite de tests para los endpoints de sponsors"""

    @pytest.fixture
    def sponsor_creation_data(self):
        """Datos para crear un sponsor"""
        return {
            "sponsor": {
                "nombre": "Sponsor Tecnológico Internacional",
                "sitio_web": "https://sponsortech.com",
                "descripcion": "Empresa líder en tecnología educativa",
                "logo_url": "https://sponsortech.com/logo.jpg"
            }
        }

    @pytest.fixture
    def auth_token(self, client):
        """Token de autenticación para tests"""
        # Registrar usuario de prueba
        user_data = {
            "name": "Test",
            "last_name": "User",
            "email": "testsponsor@example.com",
            "password": "password123"
        }
        client.post("/api/v1/auth/register", json=user_data)

        # Login y obtener token
        login_response = client.post("/api/v1/auth/token", data={
            "username": user_data["email"],
            "password": user_data["password"]
        })
        return login_response.json()["access_token"]

    def test_create_sponsor_success(self, client, sponsor_creation_data, auth_token):
        """
        Test: POST /api/v1/sponsors con datos válidos

        Verifica que crea un sponsor exitosamente
        """
        # Act
        response = client.post(
            "/api/v1/sponsors",
            json=sponsor_creation_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Sponsor created successfully"
        assert "sponsor_id" in data
        assert "data" in data

    def test_create_sponsor_without_auth(self, client, sponsor_creation_data):
        """
        Test: POST /api/v1/sponsors sin autenticación

        Verifica que retorna 401 sin token
        """
        # Act
        response = client.post("/api/v1/sponsors", json=sponsor_creation_data)

        # Assert
        assert response.status_code == 401

    def test_create_sponsor_missing_fields(self, client, auth_token):
        """
        Test: POST /api/v1/sponsors con campos faltantes

        Verifica que retorna error de validación 422
        """
        # Act
        response = client.post(
            "/api/v1/sponsors",
            json={
                "sponsor": {
                    "nombre": "Sponsor Incompleto"
                    # Faltan campos requeridos
                }
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Assert
        assert response.status_code == 422

    def test_get_all_sponsors(self, client, sample_sponsor):
        """
        Test: GET /api/v1/sponsors

        Verifica que retorna lista paginada de sponsors
        """
        # Act
        response = client.get("/api/v1/sponsors?page=1&page_size=10")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "sponsors" in data
        assert "total" in data
        assert "page" in data
        assert data["page"] == 1

    def test_get_all_sponsors_with_filters(self, client, sample_sponsor):
        """
        Test: GET /api/v1/sponsors con filtros

        Verifica que los filtros funcionen correctamente
        """
        # Act
        response = client.get("/api/v1/sponsors?search_term=Prueba&page=1&page_size=5")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "sponsors" in data

    def test_get_sponsor_by_id_found(self, client, sample_sponsor):
        """
        Test: GET /api/v1/sponsors/{id} cuando existe

        Verifica que retorna el sponsor correcto
        """
        # Act
        response = client.get(f"/api/v1/sponsors/{sample_sponsor.id_sponsor}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id_sponsor"] == sample_sponsor.id_sponsor
        assert data["nombre"] == sample_sponsor.nombre

    def test_get_sponsor_by_id_not_found(self, client):
        """
        Test: GET /api/v1/sponsors/{id} cuando no existe

        Verifica que retorna 404
        """
        # Act
        response = client.get("/api/v1/sponsors/99999")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_get_sponsor_by_id_with_congresses(self, client, sample_sponsor):
        """
        Test: GET /api/v1/sponsors/{id} con información de congresos

        Verifica que incluye datos de congresos cuando se solicita
        """
        # Act
        response = client.get(f"/api/v1/sponsors/{sample_sponsor.id_sponsor}?include_congresses=true")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id_sponsor"] == sample_sponsor.id_sponsor

    def test_search_sponsors_by_name(self, client, sample_sponsor):
        """
        Test: GET /api/v1/sponsors/search

        Verifica que la búsqueda por nombre funciona
        """
        # Act
        response = client.get("/api/v1/sponsors/search?query=Prueba")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_search_sponsors_empty_query(self, client):
        """
        Test: Búsqueda con query vacío

        Verifica que retorna error de validación
        """
        # Act
        response = client.get("/api/v1/sponsors/search?query=")

        # Assert
        assert response.status_code == 422  # min_length=1

    def test_get_sponsors_by_domain(self, client):
        """
        Test: GET /api/v1/sponsors/by-domain/{domain}

        Verifica el filtrado por dominio
        """
        # Act
        response = client.get("/api/v1/sponsors/by-domain/example.com")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_top_sponsors_by_contribution(self, client, sample_sponsor):
        """
        Test: GET /api/v1/sponsors/top-contributors

        Verifica que retorna top sponsors por contribución
        """
        # Act
        response = client.get("/api/v1/sponsors/top-contributors?limit=5")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "top_sponsors" in data["data"]

    def test_get_top_sponsors_with_year_filter(self, client, sample_sponsor):
        """
        Test: GET /api/v1/sponsors/top-contributors con filtro de año

        Verifica que el filtro por año funciona
        """
        # Act
        response = client.get("/api/v1/sponsors/top-contributors?limit=3&year=2024")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_get_inactive_sponsors(self, client, sample_sponsor):
        """
        Test: GET /api/v1/sponsors/inactive

        Verifica que retorna sponsors sin actividad reciente
        """
        # Act
        response = client.get("/api/v1/sponsors/inactive?years_threshold=2")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "inactive_sponsors" in data["data"]

    def test_get_sponsor_summary(self, client, sample_sponsor):
        """
        Test: GET /api/v1/sponsors/summary

        Verifica que retorna resumen de sponsors
        """
        # Act
        response = client.get("/api/v1/sponsors/summary")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "message" in data

    def test_get_sponsor_statistics(self, client, sample_sponsor):
        """
        Test: GET /api/v1/sponsors/{id}/statistics

        Verifica que retorna estadísticas del sponsor
        """
        # Act
        response = client.get(f"/api/v1/sponsors/{sample_sponsor.id_sponsor}/statistics")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "message" in data

    def test_update_sponsor_success(self, client, sample_sponsor, auth_token):
        """
        Test: PATCH /api/v1/sponsors/{id} con datos válidos

        Verifica que actualiza el sponsor exitosamente
        """
        # Arrange
        update_data = {
            "sponsor": {
                "descripcion": "Nueva descripción actualizada"
            }
        }

        # Act
        response = client.patch(
            f"/api/v1/sponsors/{sample_sponsor.id_sponsor}",
            json=update_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Sponsor updated successfully"

    def test_update_sponsor_without_auth(self, client, sample_sponsor):
        """
        Test: PATCH /api/v1/sponsors/{id} sin autenticación

        Verifica que retorna 401 sin token
        """
        # Act
        response = client.patch(
            f"/api/v1/sponsors/{sample_sponsor.id_sponsor}",
            json={"sponsor": {"descripcion": "Nueva"}}
        )

        # Assert
        assert response.status_code == 401

    def test_update_sponsor_not_found(self, client, auth_token):
        """
        Test: PATCH /api/v1/sponsors/{id} cuando no existe

        Verifica que retorna error apropiado
        """
        # Act
        response = client.patch(
            "/api/v1/sponsors/99999",
            json={"sponsor": {"descripcion": "Nueva"}},
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Assert
        assert response.status_code in [400, 404]

    def test_delete_sponsor_success(self, client, sample_sponsor, auth_token):
        """
        Test: DELETE /api/v1/sponsors/{id}

        Verifica que elimina el sponsor exitosamente
        """
        # Act
        response = client.delete(
            f"/api/v1/sponsors/{sample_sponsor.id_sponsor}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Sponsor deleted successfully"

    def test_delete_sponsor_without_auth(self, client, sample_sponsor):
        """
        Test: DELETE /api/v1/sponsors/{id} sin autenticación

        Verifica que retorna 401 sin token
        """
        # Act
        response = client.delete(f"/api/v1/sponsors/{sample_sponsor.id_sponsor}")

        # Assert
        assert response.status_code == 401

    def test_check_name_availability_available(self, client):
        """
        Test: GET /api/v1/sponsors/check-name/{nombre} disponible

        Verifica la verificación de disponibilidad cuando está disponible
        """
        # Act
        response = client.get("/api/v1/sponsors/check-name/Sponsor Inexistente")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["available"] is True

    def test_check_name_availability_not_available(self, client, sample_sponsor):
        """
        Test: GET /api/v1/sponsors/check-name/{nombre} no disponible

        Verifica la verificación cuando no está disponible
        """
        # Act
        response = client.get(f"/api/v1/sponsors/check-name/{sample_sponsor.nombre}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["available"] is False

    def test_check_name_availability_with_exclusion(self, client, sample_sponsor):
        """
        Test: GET /api/v1/sponsors/check-name con exclusión

        Verifica que funciona la exclusión para actualizaciones
        """
        # Act
        response = client.get(
            f"/api/v1/sponsors/check-name/{sample_sponsor.nombre}?exclude_sponsor_id={sample_sponsor.id_sponsor}"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["available"] is True  # Debería estar disponible porque se excluye

    def test_bulk_import_sponsors_success(self, client, auth_token):
        """
        Test: POST /api/v1/sponsors/bulk-import

        Verifica la creación de sponsors en lote
        """
        # Arrange
        bulk_data = {
            "sponsors": [
                {
                    "nombre": "Sponsor Lote 1",
                    "logo_url": "https://example.com/logo1.jpg",
                    "sitio_web": "https://sponsor1.com",
                    "descripcion": "Primer sponsor del lote"
                },
                {
                    "nombre": "Sponsor Lote 2",
                    "logo_url": "https://example.com/logo2.jpg",
                    "sitio_web": "https://sponsor2.com",
                    "descripcion": "Segundo sponsor del lote"
                }
            ]
        }

        # Act
        response = client.post(
            "/api/v1/sponsors/bulk-import",
            json=bulk_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert "Successfully imported" in data["message"]
        assert "2 sponsors" in data["message"]

    def test_bulk_import_sponsors_without_auth(self, client):
        """
        Test: POST /api/v1/sponsors/bulk-import sin autenticación

        Verifica que retorna 401 sin token
        """
        # Arrange
        bulk_data = {
            "sponsors": [
                {
                    "nombre": "Sponsor Test",
                    "sitio_web": "https://test.com",
                    "descripcion": "Test sponsor"
                }
            ]
        }

        # Act
        response = client.post("/api/v1/sponsors/bulk-import", json=bulk_data)

        # Assert
        assert response.status_code == 401

    def test_bulk_import_sponsors_empty_list(self, client, auth_token):
        """
        Test: POST /api/v1/sponsors/bulk-import con lista vacía

        Verifica que retorna error de validación
        """
        # Arrange
        bulk_data = {
            "sponsors": []  # Lista vacía
        }

        # Act
        response = client.post(
            "/api/v1/sponsors/bulk-import",
            json=bulk_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Assert
        assert response.status_code == 422

    def test_bulk_import_sponsors_too_many(self, client, auth_token):
        """
        Test: POST /api/v1/sponsors/bulk-import con demasiados elementos

        Verifica que respeta el límite máximo
        """
        # Arrange - Crear más de 50 sponsors
        sponsors_list = []
        for i in range(51):
            sponsors_list.append({
                "nombre": f"Sponsor Lote {i}",
                "sitio_web": f"https://sponsor{i}.com",
                "descripcion": f"Sponsor número {i}"
            })

        bulk_data = {"sponsors": sponsors_list}

        # Act
        response = client.post(
            "/api/v1/sponsors/bulk-import",
            json=bulk_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Assert
        assert response.status_code == 422

    def test_pagination_limits(self, client):
        """
        Test: Verificar límites de paginación

        Verifica que se respetan los límites de paginación
        """
        # Act
        response = client.get("/api/v1/sponsors?page=1&page_size=150")

        # Assert
        assert response.status_code == 422  # page_size máximo es 100

    def test_search_sponsors_limit_validation(self, client):
        """
        Test: Verificar límites en búsqueda

        Verifica que se respetan los límites en la búsqueda
        """
        # Act
        response = client.get("/api/v1/sponsors/search?query=test&limit=150")

        # Assert
        assert response.status_code == 422  # limit máximo es 100

    def test_top_contributors_limit_validation(self, client):
        """
        Test: Verificar límites en top contributors

        Verifica que se respetan los límites en top contributors
        """
        # Act
        response = client.get("/api/v1/sponsors/top-contributors?limit=100")

        # Assert
        assert response.status_code == 422  # limit máximo es 50

    def test_inactive_sponsors_years_validation(self, client):
        """
        Test: Verificar validación de años en sponsors inactivos

        Verifica que se respetan los límites de años
        """
        # Act
        response = client.get("/api/v1/sponsors/inactive?years_threshold=15")

        # Assert
        assert response.status_code == 422  # years_threshold máximo es 10