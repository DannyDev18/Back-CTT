"""
Tests de integración para los endpoints de Speaker

Estos tests verifican que los endpoints del router de speakers
funcionen correctamente.
"""
import pytest
from urllib.parse import quote


class TestSpeakerEndpoints:
    """Suite de tests para los endpoints de speakers"""

    @pytest.fixture
    def speaker_creation_data(self, sample_congress_new):
        """Datos para crear un speaker"""
        return {
            "speaker": {
                "id_congreso": sample_congress_new.id_congreso,
                "nombres_completos": "Dr. María Isabel Rodríguez",
                "titulo_academico": "Doctora en Teología Sistemática",
                "institucion": "Universidad Nacional de Colombia",
                "pais": "Colombia",
                "foto_url": "https://example.com/speaker.jpg",
                "tipo_speaker": "keynote"
            }
        }

    @pytest.fixture
    def auth_token(self, client):
        """Token de autenticación para tests"""
        # Registrar usuario de prueba
        user_data = {
            "name": "Test",
            "last_name": "User",
            "email": "testspeaker@example.com",
            "password": "password123"
        }
        client.post("/api/v1/auth/register", json=user_data)

        # Login y obtener token
        login_response = client.post("/api/v1/auth/token", data={
            "username": user_data["email"],
            "password": user_data["password"]
        })
        return login_response.json()["access_token"]

    def test_create_speaker_success(self, client, speaker_creation_data, auth_token):
        """
        Test: POST /api/v1/speakers con datos válidos

        Verifica que crea un speaker exitosamente
        """
        # Act
        response = client.post(
            "/api/v1/speakers",
            json=speaker_creation_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Speaker created successfully"
        assert "speaker_id" in data
        assert "data" in data

    def test_create_speaker_without_auth(self, client, speaker_creation_data):
        """
        Test: POST /api/v1/speakers sin autenticación

        Verifica que retorna 401 sin token
        """
        # Act
        response = client.post("/api/v1/speakers", json=speaker_creation_data)

        # Assert
        assert response.status_code == 401

    def test_create_speaker_missing_fields(self, client, auth_token, sample_congress_new):
        """
        Test: POST /api/v1/speakers con campos faltantes

        Verifica que retorna error de validación 422
        """
        # Act
        response = client.post(
            "/api/v1/speakers",
            json={
                "speaker": {
                    "id_congreso": sample_congress_new.id_congreso,
                    "nombres_completos": "Speaker Incompleto"
                    # Faltan campos requeridos
                }
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Assert
        assert response.status_code == 422

    def test_get_all_speakers(self, client, sample_speaker):
        """
        Test: GET /api/v1/speakers

        Verifica que retorna lista paginada de speakers
        """
        # Act
        response = client.get("/api/v1/speakers?page=1&page_size=10")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "speakers" in data
        assert "total" in data
        assert "page" in data
        assert data["page"] == 1

    def test_get_all_speakers_with_filters(self, client, sample_speaker):
        """
        Test: GET /api/v1/speakers con filtros

        Verifica que los filtros funcionen correctamente
        """
        # Act
        response = client.get(
            f"/api/v1/speakers?congress_id={sample_speaker.id_congreso}&tipo_speaker=ponente"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "speakers" in data

    def test_get_speaker_by_id_found(self, client, sample_speaker):
        """
        Test: GET /api/v1/speakers/{id} cuando existe

        Verifica que retorna el speaker correcto
        """
        # Act
        response = client.get(f"/api/v1/speakers/{sample_speaker.id_speaker}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id_speaker"] == sample_speaker.id_speaker
        assert data["nombres_completos"] == sample_speaker.nombres_completos

    def test_get_speaker_by_id_not_found(self, client):
        """
        Test: GET /api/v1/speakers/{id} cuando no existe

        Verifica que retorna 404
        """
        # Act
        response = client.get("/api/v1/speakers/99999")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_get_speaker_with_sessions_and_congress(self, client, sample_speaker):
        """
        Test: GET /api/v1/speakers/{id} con información adicional

        Verifica que incluye datos de sesiones y congreso cuando se solicita
        """
        # Act
        response = client.get(
            f"/api/v1/speakers/{sample_speaker.id_speaker}?include_sessions=true&include_congress=true"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id_speaker"] == sample_speaker.id_speaker

    def test_search_speakers(self, client, sample_speaker):
        """
        Test: GET /api/v1/speakers/search

        Verifica que la búsqueda por nombre funciona
        """
        # Act
        response = client.get("/api/v1/speakers/search?query=González")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_search_speakers_with_congress_filter(self, client, sample_speaker):
        """
        Test: GET /api/v1/speakers/search con filtro de congreso

        Verifica que la búsqueda con filtro de congreso funciona
        """
        # Act
        response = client.get(
            f"/api/v1/speakers/search?query=Test&congress_id={sample_speaker.id_congreso}"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_search_speakers_empty_query(self, client):
        """
        Test: Búsqueda con query vacío

        Verifica que retorna error de validación
        """
        # Act
        response = client.get("/api/v1/speakers/search?query=")

        # Assert
        assert response.status_code == 422  # min_length=1

    def test_get_speakers_by_congress(self, client, sample_speaker):
        """
        Test: GET /api/v1/speakers/by-congress/{congress_id}

        Verifica que retorna speakers del congreso especificado
        """
        # Act
        response = client.get(f"/api/v1/speakers/by-congress/{sample_speaker.id_congreso}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Todos los speakers deben ser del congreso especificado
        if data:
            assert all(s["id_congreso"] == sample_speaker.id_congreso for s in data)

    def test_get_speakers_by_congress_with_sessions(self, client, sample_speaker):
        """
        Test: GET /api/v1/speakers/by-congress/{congress_id} con sesiones

        Verifica que incluye información de sesiones cuando se solicita
        """
        # Act
        response = client.get(
            f"/api/v1/speakers/by-congress/{sample_speaker.id_congreso}?include_sessions=true"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_speakers_by_type(self, client, sample_speaker):
        """
        Test: GET /api/v1/speakers/by-type/{tipo_speaker}

        Verifica el filtrado por tipo de speaker
        """
        # Act
        response = client.get("/api/v1/speakers/by-type/ponente")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Todos los speakers deben ser del tipo especificado
        if data:
            assert all(s["tipo_speaker"] == "ponente" for s in data)

    def test_get_speakers_by_type_with_congress_filter(self, client, sample_speaker):
        """
        Test: GET /api/v1/speakers/by-type/{tipo_speaker} con filtro de congreso

        Verifica que el filtro de congreso funciona en el filtrado por tipo
        """
        # Act
        response = client.get(
            f"/api/v1/speakers/by-type/ponente?congress_id={sample_speaker.id_congreso}"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_speakers_by_country(self, client, sample_speaker):
        """
        Test: GET /api/v1/speakers/by-country/{pais}

        Verifica el filtrado por país
        """
        # Act
        response = client.get("/api/v1/speakers/by-country/Ecuador")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Todos los speakers deben ser del país especificado
        if data:
            assert all(s["pais"] == "Ecuador" for s in data)

    def test_get_speakers_by_country_with_congress_filter(self, client, sample_speaker):
        """
        Test: GET /api/v1/speakers/by-country/{pais} con filtro de congreso

        Verifica que el filtro de congreso funciona en el filtrado por país
        """
        # Act
        response = client.get(
            f"/api/v1/speakers/by-country/Ecuador?congress_id={sample_speaker.id_congreso}"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_speakers_by_institution(self, client, sample_speaker):
        """
        Test: GET /api/v1/speakers/by-institution

        Verifica el filtrado por institución
        """
        # Act
        response = client.get("/api/v1/speakers/by-institution?institucion=Universidad")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_speakers_by_institution_exact_match(self, client, sample_speaker):
        """
        Test: GET /api/v1/speakers/by-institution con match exacto

        Verifica que la búsqueda exacta funciona
        """
        # Act
        response = client.get(
            f"/api/v1/speakers/by-institution?institucion={sample_speaker.institucion}&exact_match=true"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_frequent_speakers(self, client, sample_speaker):
        """
        Test: GET /api/v1/speakers/frequent

        Verifica que retorna speakers frecuentes
        """
        # Act
        response = client.get("/api/v1/speakers/frequent?min_congresses=2&limit=10")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "frequent_speakers" in data["data"]

    def test_get_countries_with_speakers(self, client, sample_speaker):
        """
        Test: GET /api/v1/speakers/countries

        Verifica que retorna países con speakers
        """
        # Act
        response = client.get("/api/v1/speakers/countries")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "countries" in data["data"]

    def test_get_countries_with_speakers_congress_filter(self, client, sample_speaker):
        """
        Test: GET /api/v1/speakers/countries con filtro de congreso

        Verifica que el filtro de congreso funciona
        """
        # Act
        response = client.get(f"/api/v1/speakers/countries?congress_id={sample_speaker.id_congreso}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_get_institutions_with_speakers(self, client, sample_speaker):
        """
        Test: GET /api/v1/speakers/institutions

        Verifica que retorna instituciones con speakers
        """
        # Act
        response = client.get("/api/v1/speakers/institutions")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "institutions" in data["data"]

    def test_get_institutions_with_speakers_congress_filter(self, client, sample_speaker):
        """
        Test: GET /api/v1/speakers/institutions con filtro de congreso

        Verifica que el filtro de congreso funciona
        """
        # Act
        response = client.get(
            f"/api/v1/speakers/institutions?congress_id={sample_speaker.id_congreso}"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_get_speaker_summary(self, client, sample_speaker):
        """
        Test: GET /api/v1/speakers/summary

        Verifica que retorna resumen de speakers
        """
        # Act
        response = client.get("/api/v1/speakers/summary")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "message" in data

    def test_get_speaker_statistics_by_congress(self, client, sample_speaker):
        """
        Test: GET /api/v1/speakers/{congress_id}/statistics

        Verifica que retorna estadísticas de speakers por congreso
        """
        # Act
        response = client.get(f"/api/v1/speakers/{sample_speaker.id_congreso}/statistics")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "message" in data

    def test_update_speaker_success(self, client, sample_speaker, auth_token):
        """
        Test: PATCH /api/v1/speakers/{id} con datos válidos

        Verifica que actualiza el speaker exitosamente
        """
        # Arrange
        update_data = {
            "speaker": {
                "titulo_academico": "Doctor en Teología Bíblica"
            }
        }

        # Act
        response = client.patch(
            f"/api/v1/speakers/{sample_speaker.id_speaker}",
            json=update_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Speaker updated successfully"

    def test_update_speaker_without_auth(self, client, sample_speaker):
        """
        Test: PATCH /api/v1/speakers/{id} sin autenticación

        Verifica que retorna 401 sin token
        """
        # Act
        response = client.patch(
            f"/api/v1/speakers/{sample_speaker.id_speaker}",
            json={"speaker": {"titulo_academico": "Nuevo título"}}
        )

        # Assert
        assert response.status_code == 401

    def test_update_speaker_not_found(self, client, auth_token):
        """
        Test: PATCH /api/v1/speakers/{id} cuando no existe

        Verifica que retorna error apropiado
        """
        # Act
        response = client.patch(
            "/api/v1/speakers/99999",
            json={"speaker": {"titulo_academico": "Nuevo"}},
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Assert
        assert response.status_code in [400, 404]

    def test_delete_speaker_success(self, client, sample_speaker, auth_token):
        """
        Test: DELETE /api/v1/speakers/{id}

        Verifica que elimina el speaker exitosamente
        """
        # Act
        response = client.delete(
            f"/api/v1/speakers/{sample_speaker.id_speaker}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Speaker deleted successfully"

    def test_delete_speaker_without_auth(self, client, sample_speaker):
        """
        Test: DELETE /api/v1/speakers/{id} sin autenticación

        Verifica que retorna 401 sin token
        """
        # Act
        response = client.delete(f"/api/v1/speakers/{sample_speaker.id_speaker}")

        # Assert
        assert response.status_code == 401

    def test_check_speaker_exists_in_congress_exists(self, client, sample_speaker):
        """
        Test: GET /api/v1/speakers/check-exists/{congress_id}/{nombres_completos} cuando existe

        Verifica la verificación de existencia cuando existe
        """
        # Encode the name for URL
        encoded_name = quote(sample_speaker.nombres_completos)

        # Act
        response = client.get(
            f"/api/v1/speakers/check-exists/{sample_speaker.id_congreso}/{encoded_name}"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["exists"] is True

    def test_check_speaker_exists_in_congress_not_exists(self, client, sample_congress_new):
        """
        Test: GET /api/v1/speakers/check-exists/{congress_id}/{nombres_completos} cuando no existe

        Verifica la verificación cuando no existe
        """
        # Act
        response = client.get(
            f"/api/v1/speakers/check-exists/{sample_congress_new.id_congreso}/Speaker%20Inexistente"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["exists"] is False

    def test_check_speaker_exists_with_exclusion(self, client, sample_speaker):
        """
        Test: GET /api/v1/speakers/check-exists con exclusión

        Verifica que funciona la exclusión para actualizaciones
        """
        # Encode the name for URL
        encoded_name = quote(sample_speaker.nombres_completos)

        # Act
        response = client.get(
            f"/api/v1/speakers/check-exists/{sample_speaker.id_congreso}/{encoded_name}?exclude_speaker_id={sample_speaker.id_speaker}"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["exists"] is False  # Debería estar disponible porque se excluye

    def test_bulk_import_speakers_success(self, client, sample_congress_new, auth_token):
        """
        Test: POST /api/v1/speakers/bulk-import/{congress_id}

        Verifica la creación de speakers en lote
        """
        # Arrange
        bulk_data = {
            "speakers": [
                {
                    "id_congreso": sample_congress_new.id_congreso,
                    "nombres_completos": "Dr. Speaker Lote 1",
                    "titulo_academico": "Doctor en Historia",
                    "institucion": "Universidad A",
                    "pais": "Argentina",
                    "foto_url": "https://example.com/speaker1.jpg",
                    "tipo_speaker": "conferencia"
                },
                {
                    "id_congreso": sample_congress_new.id_congreso,
                    "nombres_completos": "Dra. Speaker Lote 2",
                    "titulo_academico": "Doctora en Filosofía",
                    "institucion": "Universidad B",
                    "pais": "Chile",
                    "foto_url": "https://example.com/speaker2.jpg",
                    "tipo_speaker": "panel"
                }
            ]
        }

        # Act
        response = client.post(
            f"/api/v1/speakers/bulk-import/{sample_congress_new.id_congreso}",
            json=bulk_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert "Successfully imported" in data["message"]
        assert "2 speakers" in data["message"]

    def test_bulk_import_speakers_without_auth(self, client, sample_congress_new):
        """
        Test: POST /api/v1/speakers/bulk-import/{congress_id} sin autenticación

        Verifica que retorna 401 sin token
        """
        # Arrange
        bulk_data = {
            "speakers": [
                {
                    "id_congreso": sample_congress_new.id_congreso,
                    "nombres_completos": "Dr. Test Speaker",
                    "titulo_academico": "Doctor",
                    "institucion": "Test University",
                    "pais": "Test Country",
                    "tipo_speaker": "ponente"
                }
            ]
        }

        # Act
        response = client.post(
            f"/api/v1/speakers/bulk-import/{sample_congress_new.id_congreso}",
            json=bulk_data
        )

        # Assert
        assert response.status_code == 401

    def test_bulk_import_speakers_empty_list(self, client, sample_congress_new, auth_token):
        """
        Test: POST /api/v1/speakers/bulk-import/{congress_id} con lista vacía

        Verifica que retorna error de validación
        """
        # Arrange
        bulk_data = {
            "speakers": []  # Lista vacía
        }

        # Act
        response = client.post(
            f"/api/v1/speakers/bulk-import/{sample_congress_new.id_congreso}",
            json=bulk_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Assert
        assert response.status_code == 422

    def test_bulk_import_speakers_too_many(self, client, sample_congress_new, auth_token):
        """
        Test: POST /api/v1/speakers/bulk-import/{congress_id} con demasiados elementos

        Verifica que respeta el límite máximo
        """
        # Arrange - Crear más de 50 speakers
        speakers_list = []
        for i in range(51):
            speakers_list.append({
                "id_congreso": sample_congress_new.id_congreso,
                "nombres_completos": f"Dr. Speaker Lote {i}",
                "titulo_academico": "Doctor",
                "institucion": f"Universidad {i}",
                "pais": "País Test",
                "tipo_speaker": "ponente"
            })

        bulk_data = {"speakers": speakers_list}

        # Act
        response = client.post(
            f"/api/v1/speakers/bulk-import/{sample_congress_new.id_congreso}",
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
        response = client.get("/api/v1/speakers?page=1&page_size=150")

        # Assert
        assert response.status_code == 422  # page_size máximo es 100

    def test_search_speakers_limit_validation(self, client):
        """
        Test: Verificar límites en búsqueda

        Verifica que se respetan los límites en la búsqueda
        """
        # Act
        response = client.get("/api/v1/speakers/search?query=test&limit=150")

        # Assert
        assert response.status_code == 422  # limit máximo es 100

    def test_frequent_speakers_limit_validation(self, client):
        """
        Test: Verificar límites en speakers frecuentes

        Verifica que se respetan los límites en speakers frecuentes
        """
        # Act
        response = client.get("/api/v1/speakers/frequent?min_congresses=2&limit=150")

        # Assert
        assert response.status_code == 422  # limit máximo es 100

    def test_frequent_speakers_min_congresses_validation(self, client):
        """
        Test: Verificar validación de min_congresses

        Verifica que se respeta el mínimo de congresos
        """
        # Act
        response = client.get("/api/v1/speakers/frequent?min_congresses=1&limit=10")

        # Assert
        assert response.status_code == 422  # min_congresses mínimo es 2