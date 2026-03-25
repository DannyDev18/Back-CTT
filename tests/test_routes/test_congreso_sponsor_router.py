"""
Tests de integración para los endpoints de Congreso Sponsor

Estos tests verifican que los endpoints del router de sponsorships (relaciones congreso-sponsor)
funcionen correctamente.
"""
import pytest
from decimal import Decimal


class TestCongresoSponsorEndpoints:
    """Suite de tests para los endpoints de sponsorships"""

    @pytest.fixture
    def sponsorship_creation_data(self, sample_congress_new, sample_sponsor):
        """Datos para crear un sponsorship"""
        return {
            "sponsorship": {
                "id_congreso": sample_congress_new.id_congreso,
                "id_sponsor": sample_sponsor.id_sponsor,
                "categoria": "oro",
                "aporte": 5000.0,
                "beneficios": "Logo prominente, stand premium",
                "fecha_confirmacion": "2024-08-01"
            }
        }

    @pytest.fixture
    def auth_token(self, client):
        """Token de autenticación para tests"""
        # Registrar usuario de prueba
        user_data = {
            "name": "Test",
            "last_name": "User",
            "email": "testsponsorship@example.com",
            "password": "password123"
        }
        client.post("/api/v1/auth/register", json=user_data)

        # Login y obtener token
        login_response = client.post("/api/v1/auth/token", data={
            "username": user_data["email"],
            "password": user_data["password"]
        })
        return login_response.json()["access_token"]

    def test_create_sponsorship_success(self, client, sponsorship_creation_data, auth_token):
        """
        Test: POST /api/v1/sponsorships con datos válidos

        Verifica que crea un sponsorship exitosamente
        """
        # Act
        response = client.post(
            "/api/v1/sponsorships",
            json=sponsorship_creation_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Sponsorship created successfully"
        assert "data" in data

    def test_create_sponsorship_without_auth(self, client, sponsorship_creation_data):
        """
        Test: POST /api/v1/sponsorships sin autenticación

        Verifica que retorna 401 sin token
        """
        # Act
        response = client.post("/api/v1/sponsorships", json=sponsorship_creation_data)

        # Assert
        assert response.status_code == 401

    def test_create_sponsorship_missing_fields(self, client, auth_token, sample_congress_new, sample_sponsor):
        """
        Test: POST /api/v1/sponsorships con campos faltantes

        Verifica que retorna error de validación 422
        """
        # Act
        response = client.post(
            "/api/v1/sponsorships",
            json={
                "sponsorship": {
                    "id_congreso": sample_congress_new.id_congreso,
                    "categoria": "oro"
                    # Faltan campos requeridos
                }
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Assert
        assert response.status_code == 422

    def test_get_all_sponsorships(self, client, sample_congreso_sponsor):
        """
        Test: GET /api/v1/sponsorships

        Verifica que retorna lista paginada de sponsorships
        """
        # Act
        response = client.get("/api/v1/sponsorships?page=1&page_size=10")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "sponsorships" in data
        assert "total" in data
        assert "page" in data
        assert data["page"] == 1

    def test_get_all_sponsorships_with_filters(self, client, sample_congreso_sponsor):
        """
        Test: GET /api/v1/sponsorships con filtros

        Verifica que los filtros funcionen correctamente
        """
        # Act
        response = client.get(
            f"/api/v1/sponsorships?congress_id={sample_congreso_sponsor.id_congreso}&categoria=plata&min_aporte=1000&max_aporte=10000"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "sponsorships" in data

    def test_get_sponsorship_by_ids_found(self, client, sample_congreso_sponsor):
        """
        Test: GET /api/v1/sponsorships/{congress_id}/{sponsor_id} cuando existe

        Verifica que retorna el sponsorship correcto
        """
        # Act
        response = client.get(
            f"/api/v1/sponsorships/{sample_congreso_sponsor.id_congreso}/{sample_congreso_sponsor.id_sponsor}"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id_congreso"] == sample_congreso_sponsor.id_congreso
        assert data["id_sponsor"] == sample_congreso_sponsor.id_sponsor

    def test_get_sponsorship_by_ids_not_found(self, client):
        """
        Test: GET /api/v1/sponsorships/{congress_id}/{sponsor_id} cuando no existe

        Verifica que retorna 404
        """
        # Act
        response = client.get("/api/v1/sponsorships/99999/99999")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_get_sponsorship_with_details(self, client, sample_congreso_sponsor):
        """
        Test: GET /api/v1/sponsorships/{congress_id}/{sponsor_id} con información adicional

        Verifica que incluye datos de congreso y sponsor cuando se solicita
        """
        # Act
        response = client.get(
            f"/api/v1/sponsorships/{sample_congreso_sponsor.id_congreso}/{sample_congreso_sponsor.id_sponsor}?include_congress=true&include_sponsor=true"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id_congreso"] == sample_congreso_sponsor.id_congreso
        assert data["id_sponsor"] == sample_congreso_sponsor.id_sponsor

    def test_get_sponsorships_by_congress(self, client, sample_congreso_sponsor):
        """
        Test: GET /api/v1/sponsorships/by-congress/{congress_id}

        Verifica que retorna sponsorships del congreso especificado
        """
        # Act
        response = client.get(f"/api/v1/sponsorships/by-congress/{sample_congreso_sponsor.id_congreso}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Todos los sponsorships deben ser del congreso especificado
        if data:
            assert all(s["id_congreso"] == sample_congreso_sponsor.id_congreso for s in data)

    def test_get_sponsorships_by_congress_with_sponsor_info(self, client, sample_congreso_sponsor):
        """
        Test: GET /api/v1/sponsorships/by-congress/{congress_id} con información de sponsor

        Verifica que incluye información del sponsor cuando se solicita
        """
        # Act
        response = client.get(
            f"/api/v1/sponsorships/by-congress/{sample_congreso_sponsor.id_congreso}?include_sponsor=true"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_sponsorships_by_sponsor(self, client, sample_congreso_sponsor):
        """
        Test: GET /api/v1/sponsorships/by-sponsor/{sponsor_id}

        Verifica que retorna sponsorships del sponsor especificado
        """
        # Act
        response = client.get(f"/api/v1/sponsorships/by-sponsor/{sample_congreso_sponsor.id_sponsor}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Todos los sponsorships deben ser del sponsor especificado
        if data:
            assert all(s["id_sponsor"] == sample_congreso_sponsor.id_sponsor for s in data)

    def test_get_sponsorships_by_sponsor_with_congress_info(self, client, sample_congreso_sponsor):
        """
        Test: GET /api/v1/sponsorships/by-sponsor/{sponsor_id} con información de congreso

        Verifica que incluye información del congreso cuando se solicita
        """
        # Act
        response = client.get(
            f"/api/v1/sponsorships/by-sponsor/{sample_congreso_sponsor.id_sponsor}?include_congress=true"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_sponsorships_by_category(self, client, sample_congreso_sponsor):
        """
        Test: GET /api/v1/sponsorships/by-category/{categoria}

        Verifica el filtrado por categoría
        """
        # Act
        response = client.get("/api/v1/sponsorships/by-category/plata")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Todos los sponsorships deben ser de la categoría especificada
        if data:
            assert all(s["categoria"] == "plata" for s in data)

    def test_get_sponsorships_by_category_with_congress_filter(self, client, sample_congreso_sponsor):
        """
        Test: GET /api/v1/sponsorships/by-category/{categoria} con filtro de congreso

        Verifica que el filtro de congreso funciona en el filtrado por categoría
        """
        # Act
        response = client.get(
            f"/api/v1/sponsorships/by-category/plata?congress_id={sample_congreso_sponsor.id_congreso}"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_top_contributors_by_congress(self, client, sample_congreso_sponsor):
        """
        Test: GET /api/v1/sponsorships/top-contributors/{congress_id}

        Verifica que retorna top contributors del congreso
        """
        # Act
        response = client.get(
            f"/api/v1/sponsorships/top-contributors/{sample_congreso_sponsor.id_congreso}?limit=5"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "top_contributors" in data["data"]

    def test_get_sponsorship_statistics_by_congress(self, client, sample_congreso_sponsor):
        """
        Test: GET /api/v1/sponsorships/statistics/{congress_id}

        Verifica que retorna estadísticas de sponsorships del congreso
        """
        # Act
        response = client.get(f"/api/v1/sponsorships/statistics/{sample_congreso_sponsor.id_congreso}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "message" in data

    def test_get_congress_funding_summary(self, client, sample_congreso_sponsor):
        """
        Test: GET /api/v1/sponsorships/funding-summary

        Verifica que retorna resumen de financiamiento
        """
        # Act
        response = client.get("/api/v1/sponsorships/funding-summary")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "funding_summary" in data["data"]

    def test_get_congress_funding_summary_with_year_filter(self, client, sample_congreso_sponsor):
        """
        Test: GET /api/v1/sponsorships/funding-summary con filtro de año

        Verifica que el filtro por año funciona
        """
        # Act
        response = client.get("/api/v1/sponsorships/funding-summary?year=2024")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_get_sponsor_loyalty_analysis(self, client, sample_congreso_sponsor):
        """
        Test: GET /api/v1/sponsorships/loyalty-analysis

        Verifica que retorna análisis de lealtad de sponsors
        """
        # Act
        response = client.get("/api/v1/sponsorships/loyalty-analysis?min_sponsorships=2")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "loyal_sponsors" in data["data"]

    def test_get_category_trends(self, client, sample_congreso_sponsor):
        """
        Test: GET /api/v1/sponsorships/category-trends

        Verifica que retorna tendencias por categoría
        """
        # Act
        response = client.get("/api/v1/sponsorships/category-trends")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "trends" in data["data"]

    def test_get_category_trends_with_years_filter(self, client, sample_congreso_sponsor):
        """
        Test: GET /api/v1/sponsorships/category-trends con filtro de años

        Verifica que el filtro de años funciona
        """
        # Act
        response = client.get("/api/v1/sponsorships/category-trends?years=2023&years=2024")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_get_sponsorship_summary(self, client, sample_congreso_sponsor):
        """
        Test: GET /api/v1/sponsorships/summary

        Verifica que retorna resumen de sponsorships
        """
        # Act
        response = client.get("/api/v1/sponsorships/summary")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "message" in data

    def test_update_sponsorship_success(self, client, sample_congreso_sponsor, auth_token):
        """
        Test: PATCH /api/v1/sponsorships/{congress_id}/{sponsor_id} con datos válidos

        Verifica que actualiza el sponsorship exitosamente
        """
        # Arrange
        update_data = {
            "sponsorship": {
                "aporte": 4000.0,
                "beneficios": "Beneficios actualizados"
            }
        }

        # Act
        response = client.patch(
            f"/api/v1/sponsorships/{sample_congreso_sponsor.id_congreso}/{sample_congreso_sponsor.id_sponsor}",
            json=update_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Sponsorship updated successfully"

    def test_update_sponsorship_without_auth(self, client, sample_congreso_sponsor):
        """
        Test: PATCH /api/v1/sponsorships/{congress_id}/{sponsor_id} sin autenticación

        Verifica que retorna 401 sin token
        """
        # Act
        response = client.patch(
            f"/api/v1/sponsorships/{sample_congreso_sponsor.id_congreso}/{sample_congreso_sponsor.id_sponsor}",
            json={"sponsorship": {"aporte": 3000.0}}
        )

        # Assert
        assert response.status_code == 401

    def test_update_sponsorship_not_found(self, client, auth_token):
        """
        Test: PATCH /api/v1/sponsorships/{congress_id}/{sponsor_id} cuando no existe

        Verifica que retorna error apropiado
        """
        # Act
        response = client.patch(
            "/api/v1/sponsorships/99999/99999",
            json={"sponsorship": {"aporte": 3000.0}},
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Assert
        assert response.status_code in [400, 404]

    def test_delete_sponsorship_success(self, client, sample_congreso_sponsor, auth_token):
        """
        Test: DELETE /api/v1/sponsorships/{congress_id}/{sponsor_id}

        Verifica que elimina el sponsorship exitosamente
        """
        # Act
        response = client.delete(
            f"/api/v1/sponsorships/{sample_congreso_sponsor.id_congreso}/{sample_congreso_sponsor.id_sponsor}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Sponsorship deleted successfully"

    def test_delete_sponsorship_without_auth(self, client, sample_congreso_sponsor):
        """
        Test: DELETE /api/v1/sponsorships/{congress_id}/{sponsor_id} sin autenticación

        Verifica que retorna 401 sin token
        """
        # Act
        response = client.delete(
            f"/api/v1/sponsorships/{sample_congreso_sponsor.id_congreso}/{sample_congreso_sponsor.id_sponsor}"
        )

        # Assert
        assert response.status_code == 401

    def test_check_sponsorship_exists_true(self, client, sample_congreso_sponsor):
        """
        Test: GET /api/v1/sponsorships/check-exists/{congress_id}/{sponsor_id} cuando existe

        Verifica la verificación de existencia cuando existe
        """
        # Act
        response = client.get(
            f"/api/v1/sponsorships/check-exists/{sample_congreso_sponsor.id_congreso}/{sample_congreso_sponsor.id_sponsor}"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["exists"] is True

    def test_check_sponsorship_exists_false(self, client):
        """
        Test: GET /api/v1/sponsorships/check-exists/{congress_id}/{sponsor_id} cuando no existe

        Verifica la verificación cuando no existe
        """
        # Act
        response = client.get("/api/v1/sponsorships/check-exists/99999/99999")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["exists"] is False

    def test_bulk_create_sponsorships_success(self, client, sample_congress_new, auth_token, session):
        """
        Test: POST /api/v1/sponsorships/bulk-create/{congress_id}

        Verifica la creación de sponsorships en lote
        """
        # Arrange - Crear sponsors adicionales
        from src.models.sponsor_model import Sponsor

        # Use the session fixture to create additional sponsors
        sponsor1 = Sponsor(
                nombre="Sponsor Lote Test 1",
                logo_url="https://example.com/sponsor1test_logo.png",
                sitio_web="https://sponsor1test.com",
                descripcion="Primer sponsor para lote"
            )
        sponsor2 = Sponsor(
            nombre="Sponsor Lote Test 2",
            logo_url="https://example.com/sponsor2test_logo.png",
            sitio_web="https://sponsor2test.com",
            descripcion="Segundo sponsor para lote"
        )
        session.add_all([sponsor1, sponsor2])
        session.commit()
        session.refresh(sponsor1)
        session.refresh(sponsor2)

        bulk_data = {
            "sponsorships": [
                {
                    "id_congreso": sample_congress_new.id_congreso,
                    "id_sponsor": sponsor1.id_sponsor,
                    "categoria": "oro",
                    "aporte": 5000.0
                },
                {
                    "id_congreso": sample_congress_new.id_congreso,
                    "id_sponsor": sponsor2.id_sponsor,
                    "categoria": "plata",
                    "aporte": 3000.0
                }
            ]
        }

        # Act
        response = client.post(
            f"/api/v1/sponsorships/bulk-create/{sample_congress_new.id_congreso}",
            json=bulk_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert "Successfully created" in data["message"]
        assert "2 sponsorships" in data["message"]

    def test_bulk_create_sponsorships_without_auth(self, client, sample_congress_new):
        """
        Test: POST /api/v1/sponsorships/bulk-create/{congress_id} sin autenticación

        Verifica que retorna 401 sin token
        """
        # Arrange
        bulk_data = {
            "sponsorships": [
                {
                    "id_congreso": sample_congress_new.id_congreso,
                    "id_sponsor": 1,
                    "categoria": "oro",
                    "aporte": 5000.0
                }
            ]
        }

        # Act
        response = client.post(
            f"/api/v1/sponsorships/bulk-create/{sample_congress_new.id_congreso}",
            json=bulk_data
        )

        # Assert
        assert response.status_code == 401

    def test_bulk_create_sponsorships_empty_list(self, client, sample_congress_new, auth_token):
        """
        Test: POST /api/v1/sponsorships/bulk-create/{congress_id} con lista vacía

        Verifica que retorna error de validación
        """
        # Arrange
        bulk_data = {
            "sponsorships": []  # Lista vacía
        }

        # Act
        response = client.post(
            f"/api/v1/sponsorships/bulk-create/{sample_congress_new.id_congreso}",
            json=bulk_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Assert
        assert response.status_code == 422

    def test_bulk_create_sponsorships_too_many(self, client, sample_congress_new, auth_token):
        """
        Test: POST /api/v1/sponsorships/bulk-create/{congress_id} con demasiados elementos

        Verifica que respeta el límite máximo
        """
        # Arrange - Crear más de 50 sponsorships
        sponsorships_list = []
        for i in range(51):
            sponsorships_list.append({
                "id_congreso": sample_congress_new.id_congreso,
                "id_sponsor": i + 1000,  # IDs altos para evitar conflictos
                "categoria": "oro",
                "aporte": 1000.0
            })

        bulk_data = {"sponsorships": sponsorships_list}

        # Act
        response = client.post(
            f"/api/v1/sponsorships/bulk-create/{sample_congress_new.id_congreso}",
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
        response = client.get("/api/v1/sponsorships?page=1&page_size=150")

        # Assert
        assert response.status_code == 422  # page_size máximo es 100

    def test_top_contributors_limit_validation(self, client, sample_congress_new):
        """
        Test: Verificar límites en top contributors

        Verifica que se respetan los límites en top contributors
        """
        # Act
        response = client.get(f"/api/v1/sponsorships/top-contributors/{sample_congress_new.id_congreso}?limit=100")

        # Assert
        assert response.status_code == 422  # limit máximo es 50

    def test_loyalty_analysis_min_sponsorships_validation(self, client):
        """
        Test: Verificar validación de min_sponsorships

        Verifica que se respeta el mínimo de sponsorships
        """
        # Act
        response = client.get("/api/v1/sponsorships/loyalty-analysis?min_sponsorships=1")

        # Assert
        assert response.status_code == 422  # min_sponsorships mínimo es 2

    def test_invalid_decimal_values(self, client):
        """
        Test: Valores inválidos para campos decimales

        Verifica que se manejan correctamente los valores decimales inválidos
        """
        # Act
        response = client.get("/api/v1/sponsorships?min_aporte=invalid&max_aporte=also_invalid")

        # Assert
        assert response.status_code == 422

    def test_negative_aporte_values(self, client):
        """
        Test: Valores negativos para aportes

        Verifica que se validan correctamente los valores negativos
        """
        # Act
        response = client.get("/api/v1/sponsorships?min_aporte=-100&max_aporte=-50")

        # Assert
        # Debería permitir la consulta pero no encontrará resultados con valores negativos
        assert response.status_code == 200