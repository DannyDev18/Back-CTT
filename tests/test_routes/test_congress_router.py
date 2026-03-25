"""
Tests de integración para los endpoints de Congress New

Estos tests verifican que los endpoints del router de congresos
funcionen correctamente.
"""
import pytest
from datetime import date


class TestCongressNewEndpoints:
    """Suite de tests para los endpoints de congresos nuevos"""

    @pytest.fixture
    def congress_creation_data(self):
        """Datos para crear un congreso"""
        return {
            "congress": {
                "nombre": "Congreso Internacional de Teología 2024",
                "edicion": "CIT-2024-TEST",
                "anio": 2024,
                "fecha_inicio": "2024-09-15",
                "fecha_fin": "2024-09-17",
                "descripcion_general": "Congreso anual de teología con expertos internacionales.",
                "poster_cover_url": "https://example.com/poster2024.jpg"
            }
        }

    @pytest.fixture
    def auth_token(self, client):
        """Token de autenticación para tests"""
        # Registrar usuario de prueba
        user_data = {
            "name": "Test",
            "last_name": "User",
            "email": "testcongress@example.com",
            "password": "password123"
        }
        client.post("/api/v1/auth/register", json=user_data)

        # Login y obtener token
        login_response = client.post("/api/v1/auth/token", data={
            "username": user_data["email"],
            "password": user_data["password"]
        })
        return login_response.json()["access_token"]

    def test_create_congress_success(self, client, congress_creation_data, auth_token):
        """
        Test: POST /api/v1/congresses-new con datos válidos

        Verifica que crea un congreso exitosamente
        """
        # Act
        response = client.post(
            "/api/v1/congresses-new",
            json=congress_creation_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Congress created successfully"
        assert "congress_id" in data
        assert "data" in data

    def test_create_congress_without_auth(self, client, congress_creation_data):
        """
        Test: POST /api/v1/congresses-new sin autenticación

        Verifica que retorna 401 sin token
        """
        # Act
        response = client.post("/api/v1/congresses-new", json=congress_creation_data)

        # Assert
        assert response.status_code == 401

    def test_create_congress_missing_fields(self, client, auth_token):
        """
        Test: POST /api/v1/congresses-new con campos faltantes

        Verifica que retorna error de validación 422
        """
        # Act
        response = client.post(
            "/api/v1/congresses-new",
            json={
                "congress": {
                    "nombre": "Congreso Incompleto"
                    # Faltan campos requeridos
                }
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Assert
        assert response.status_code == 422

    def test_get_all_congresses(self, client, sample_congress_new):
        """
        Test: GET /api/v1/congresses-new

        Verifica que retorna lista paginada de congresos
        """
        # Act
        response = client.get("/api/v1/congresses-new?page=1&page_size=10")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "congresses" in data
        assert "total" in data
        assert "page" in data
        assert data["page"] == 1

    def test_get_all_congresses_with_filters(self, client, sample_congress_new):
        """
        Test: GET /api/v1/congresses-new con filtros

        Verifica que los filtros funcionen correctamente
        """
        # Act
        response = client.get("/api/v1/congresses-new?year=2024&search_term=Prueba")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "congresses" in data

    def test_get_congress_by_id_found(self, client, sample_congress_new):
        """
        Test: GET /api/v1/congresses-new/{id} cuando existe

        Verifica que retorna el congreso correcto
        """
        # Act
        response = client.get(f"/api/v1/congresses-new/{sample_congress_new.id_congreso}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id_congreso"] == sample_congress_new.id_congreso
        assert data["nombre"] == sample_congress_new.nombre

    def test_get_congress_by_id_not_found(self, client):
        """
        Test: GET /api/v1/congresses-new/{id} cuando no existe

        Verifica que retorna 404
        """
        # Act
        response = client.get("/api/v1/congresses-new/99999")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_search_congresses(self, client, sample_congress_new):
        """
        Test: GET /api/v1/congresses-new/search

        Verifica que la búsqueda funciona
        """
        # Act
        response = client.get("/api/v1/congresses-new/search?query=Prueba")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_upcoming_congresses(self, client):
        """
        Test: GET /api/v1/congresses-new/upcoming

        Verifica que retorna próximos congresos
        """
        # Act
        response = client.get("/api/v1/congresses-new/upcoming?limit=5")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_current_congresses(self, client):
        """
        Test: GET /api/v1/congresses-new/current

        Verifica que retorna congresos actuales
        """
        # Act
        response = client.get("/api/v1/congresses-new/current")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_congresses_by_year(self, client, sample_congress_new):
        """
        Test: GET /api/v1/congresses-new/by-year/{year}

        Verifica el filtrado por año
        """
        # Act
        response = client.get("/api/v1/congresses-new/by-year/2024")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_congress_statistics(self, client, sample_congress_new):
        """
        Test: GET /api/v1/congresses-new/{id}/statistics

        Verifica que retorna estadísticas del congreso
        """
        # Act
        response = client.get(f"/api/v1/congresses-new/{sample_congress_new.id_congreso}/statistics")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "message" in data

    def test_get_years_with_congresses(self, client, sample_congress_new):
        """
        Test: GET /api/v1/congresses-new/years

        Verifica que retorna años con congresos
        """
        # Act
        response = client.get("/api/v1/congresses-new/years")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "years" in data["data"]

    def test_get_congress_summary(self, client, sample_congress_new):
        """
        Test: GET /api/v1/congresses-new/summary

        Verifica que retorna resumen de congresos
        """
        # Act
        response = client.get("/api/v1/congresses-new/summary")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "message" in data

    def test_update_congress_success(self, client, sample_congress_new, auth_token):
        """
        Test: PATCH /api/v1/congresses-new/{id} con datos válidos

        Verifica que actualiza el congreso exitosamente
        """
        # Arrange
        update_data = {
            "congress": {
                "descripcion_general": "Nueva descripción actualizada"
            }
        }

        # Act
        response = client.patch(
            f"/api/v1/congresses-new/{sample_congress_new.id_congreso}",
            json=update_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Congress updated successfully"

    def test_update_congress_without_auth(self, client, sample_congress_new):
        """
        Test: PATCH /api/v1/congresses-new/{id} sin autenticación

        Verifica que retorna 401 sin token
        """
        # Act
        response = client.patch(
            f"/api/v1/congresses-new/{sample_congress_new.id_congreso}",
            json={"congress": {"descripcion_general": "Nueva"}}
        )

        # Assert
        assert response.status_code == 401

    def test_update_congress_not_found(self, client, auth_token):
        """
        Test: PATCH /api/v1/congresses-new/{id} cuando no existe

        Verifica que retorna error apropiado
        """
        # Act
        response = client.patch(
            "/api/v1/congresses-new/99999",
            json={"congress": {"descripcion_general": "Nueva"}},
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Assert
        assert response.status_code in [400, 404]

    def test_delete_congress_success(self, client, sample_congress_new, auth_token):
        """
        Test: DELETE /api/v1/congresses-new/{id}

        Verifica que elimina el congreso exitosamente
        """
        # Act
        response = client.delete(
            f"/api/v1/congresses-new/{sample_congress_new.id_congreso}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Congress deleted successfully"

    def test_delete_congress_without_auth(self, client, sample_congress_new):
        """
        Test: DELETE /api/v1/congresses-new/{id} sin autenticación

        Verifica que retorna 401 sin token
        """
        # Act
        response = client.delete(f"/api/v1/congresses-new/{sample_congress_new.id_congreso}")

        # Assert
        assert response.status_code == 401

    def test_check_edition_availability_available(self, client):
        """
        Test: GET /api/v1/congresses-new/check-edition/{edicion}/{anio} disponible

        Verifica la verificación de disponibilidad cuando está disponible
        """
        # Act
        response = client.get("/api/v1/congresses-new/check-edition/TEST-2025/2025")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["available"] is True

    def test_check_edition_availability_not_available(self, client, sample_congress_new):
        """
        Test: GET /api/v1/congresses-new/check-edition/{edicion}/{anio} no disponible

        Verifica la verificación cuando no está disponible
        """
        # Act
        response = client.get(
            f"/api/v1/congresses-new/check-edition/{sample_congress_new.edicion}/{sample_congress_new.anio}"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["available"] is False

    def test_create_legacy_congress(self, client, auth_token):
        """
        Test: POST /api/v1/congresses-new/legacy

        Verifica la creación de congreso en formato legacy
        """
        # Arrange
        legacy_data = {
            "congress": {
                "title": "Congreso Legacy",
                "description": "Congreso en formato legacy",
                "congress_image": "https://example.com/legacy.jpg"
            }
        }

        # Act
        response = client.post(
            "/api/v1/congresses-new/legacy",
            json=legacy_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Legacy congress created successfully"

    def test_get_legacy_congress_format(self, client, sample_congress_new):
        """
        Test: GET /api/v1/congresses-new/{id}/legacy

        Verifica la obtención de congreso en formato legacy
        """
        # Act
        response = client.get(f"/api/v1/congresses-new/{sample_congress_new.id_congreso}/legacy")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "title" in data

    def test_get_congresses_by_date_range(self, client):
        """
        Test: GET /api/v1/congresses-new/date-range

        Verifica el filtrado por rango de fechas
        """
        # Act
        response = client.get(
            "/api/v1/congresses-new/date-range?start_date=2024-01-01&end_date=2024-12-31"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_invalid_date_format_in_date_range(self, client):
        """
        Test: GET /api/v1/congresses-new/date-range con formato de fecha inválido

        Verifica que retorna error de validación
        """
        # Act
        response = client.get(
            "/api/v1/congresses-new/date-range?start_date=invalid&end_date=2024-12-31"
        )

        # Assert
        assert response.status_code == 422

    def test_pagination_limits(self, client):
        """
        Test: Verificar límites de paginación

        Verifica que se respetan los límites de paginación
        """
        # Act
        response = client.get("/api/v1/congresses-new?page=1&page_size=150")

        # Assert
        assert response.status_code == 422  # page_size máximo es 100

    def test_search_empty_query(self, client):
        """
        Test: Búsqueda con query vacío

        Verifica que retorna error de validación
        """
        # Act
        response = client.get("/api/v1/congresses-new/search?query=")

        # Assert
        assert response.status_code == 422  # min_length=1

    def test_complete_congress_api_workflow_with_all_entities(self, client, auth_token):
        """
        Test: Flujo completo de API para Congress con todas las entidades relacionadas

        Verifica el flujo completo de endpoints desde la creación hasta la eliminación:
        - Crear congress via API
        - Crear y asociar sponsors via API
        - Crear speakers via API
        - Crear sesiones del cronograma via API
        - Verificar todas las relaciones via API
        - Actualizar entidades via API
        - Eliminar everything via API
        """
        # STEP 1: Crear Congress via API
        congress_data = {
            "congress": {
                "nombre": "Congreso API Integral 2024",
                "edicion": "CAI-2024-01",
                "anio": 2024,
                "fecha_inicio": "2024-12-15",
                "fecha_fin": "2024-12-17",
                "descripcion_general": "Congress completo creado via API para pruebas de integración",
                "poster_cover_url": "https://example.com/api_congress.jpg"
            }
        }

        congress_response = client.post(
            "/api/v1/congresses-new",
            json=congress_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert congress_response.status_code == 201
        congress_result = congress_response.json()
        congress_id = congress_result["congress_id"]

        # Verificar que el congress fue creado correctamente
        get_congress_response = client.get(f"/api/v1/congresses-new/{congress_id}")
        assert get_congress_response.status_code == 200
        congress_details = get_congress_response.json()
        assert congress_details["nombre"] == "Congreso API Integral 2024"

        # STEP 2: Crear Sponsors via API
        sponsor_1_data = {
            "sponsor": {
                "nombre": "Sponsor API 1",
                "logo_url": "https://example.com/sponsor1_api.png",
                "sitio_web": "https://sponsor1api.com",
                "descripcion": "Primer sponsor creado via API"
            }
        }

        sponsor_2_data = {
            "sponsor": {
                "nombre": "Sponsor API 2",
                "logo_url": "https://example.com/sponsor2_api.png",
                "sitio_web": "https://sponsor2api.com",
                "descripcion": "Segundo sponsor creado via API"
            }
        }

        sponsor_1_response = client.post(
            "/api/v1/sponsors",
            json=sponsor_1_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        sponsor_2_response = client.post(
            "/api/v1/sponsors",
            json=sponsor_2_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert sponsor_1_response.status_code == 201
        assert sponsor_2_response.status_code == 201

        sponsor_1_id = sponsor_1_response.json()["sponsor_id"]
        sponsor_2_id = sponsor_2_response.json()["sponsor_id"]

        # Asociar sponsors al congress
        sponsor_association_1_data = {
            "sponsorship": {
                "id_congreso": congress_id,
                "id_sponsor": sponsor_1_id,
                "categoria": "oro",
                "aporte": "15000.00"
            }
        }

        sponsor_association_2_data = {
            "sponsorship": {
                "id_congreso": congress_id,
                "id_sponsor": sponsor_2_id,
                "categoria": "plata",
                "aporte": "8000.00"
            }
        }

        association_1_response = client.post(
            "/api/v1/sponsorships",
            json=sponsor_association_1_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        association_2_response = client.post(
            "/api/v1/sponsorships",
            json=sponsor_association_2_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert association_1_response.status_code == 201
        assert association_2_response.status_code == 201

        # Verificar las asociaciones
        congress_sponsors_response = client.get(f"/api/v1/sponsorships/by-congress/{congress_id}")

        assert congress_sponsors_response.status_code == 200
        sponsors_list = congress_sponsors_response.json()
        assert len(sponsors_list) == 2

        sponsor_categories = [sponsor["categoria"] for sponsor in sponsors_list]
        assert "oro" in sponsor_categories
        assert "plata" in sponsor_categories

        # STEP 3: Crear Speakers via API
        speaker_1_data = {
            "speaker": {
                "id_congreso": congress_id,
                "nombres_completos": "Dr. API Speaker Uno",
                "titulo_academico": "Doctor en Teología Digital",
                "institucion": "Universidad API",
                "pais": "Ecuador",
                "foto_url": "https://example.com/speaker1_api.jpg",
                "tipo_speaker": "keynote"
            }
        }

        speaker_2_data = {
            "speaker": {
                "id_congreso": congress_id,
                "nombres_completos": "Dra. API Speaker Dos",
                "titulo_academico": "Doctora en Comunicación Cristiana",
                "institucion": "Instituto API",
                "pais": "Colombia",
                "foto_url": "https://example.com/speaker2_api.jpg",
                "tipo_speaker": "conferencia"
            }
        }

        speaker_1_response = client.post(
            "/api/v1/speakers",
            json=speaker_1_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        speaker_2_response = client.post(
            "/api/v1/speakers",
            json=speaker_2_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert speaker_1_response.status_code == 201
        assert speaker_2_response.status_code == 201

        speaker_1_id = speaker_1_response.json()["speaker_id"]
        speaker_2_id = speaker_2_response.json()["speaker_id"]

        # Verificar speakers del congress
        congress_speakers_response = client.get(f"/api/v1/speakers/by-congress/{congress_id}")
        assert congress_speakers_response.status_code == 200
        speakers_list = congress_speakers_response.json()
        assert len(speakers_list) >= 2

        # STEP 4: Crear Sesiones del Cronograma via API
        session_1_data = {
            "session": {
                "id_congreso": congress_id,
                "id_speaker": speaker_1_id,
                "fecha": "2024-12-15",
                "hora_inicio": "09:00:00",
                "hora_fin": "10:30:00",
                "titulo_sesion": "Conferencia Magistral API",
                "jornada": "mañana",
                "lugar": "Auditorio API Principal"
            }
        }

        session_2_data = {
            "session": {
                "id_congreso": congress_id,
                "id_speaker": speaker_2_id,
                "fecha": "2024-12-15",
                "hora_inicio": "11:00:00",
                "hora_fin": "12:30:00",
                "titulo_sesion": "Sesión de Comunicación Digital",
                "jornada": "mañana",
                "lugar": "Aula API 101"
            }
        }

        session_1_response = client.post(
            "/api/v1/sessions",
            json=session_1_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        session_2_response = client.post(
            "/api/v1/sessions",
            json=session_2_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert session_1_response.status_code == 201
        assert session_2_response.status_code == 201

        session_1_id = session_1_response.json()["session_id"]
        session_2_id = session_2_response.json()["session_id"]

        # Verificar sesiones del congress
        congress_sessions_response = client.get(f"/api/v1/sessions/by-congress/{congress_id}")
        assert congress_sessions_response.status_code == 200
        sessions_list = congress_sessions_response.json()
        assert len(sessions_list) >= 2

        # STEP 5: Verificar estadísticas completas del congress
        stats_response = client.get(f"/api/v1/congresses-new/{congress_id}/statistics")
        assert stats_response.status_code == 200
        stats = stats_response.json()
        assert "data" in stats

        # STEP 6: Actualizar congress y verificar que las relaciones se mantienen
        update_congress_data = {
            "congress": {
                "descripcion_general": "Congress API actualizado con éxito y nuevas características"
            }
        }

        update_response = client.patch(
            f"/api/v1/congresses-new/{congress_id}",
            json=update_congress_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert update_response.status_code == 200

        # Verificar que la actualización fue exitosa
        updated_congress_response = client.get(f"/api/v1/congresses-new/{congress_id}")
        updated_congress = updated_congress_response.json()
        assert "actualizado" in updated_congress["descripcion_general"]

        # Verificar que las relaciones siguen intactas
        sponsors_after_update = client.get(f"/api/v1/sponsorships/by-congress/{congress_id}")
        speakers_after_update = client.get(f"/api/v1/speakers/by-congress/{congress_id}")
        sessions_after_update = client.get(f"/api/v1/sessions/by-congress/{congress_id}")

        assert len(sponsors_after_update.json()) == 2
        assert len(speakers_after_update.json()) >= 2
        assert len(sessions_after_update.json()) >= 2

        # STEP 7: Actualizar entidades relacionadas
        # Actualizar speaker
        update_speaker_data = {
            "speaker": {
                "titulo_academico": "Doctor en Teología Digital Avanzada"
            }
        }

        update_speaker_response = client.patch(
            f"/api/v1/speakers/{speaker_1_id}",
            json=update_speaker_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert update_speaker_response.status_code == 200

        # Actualizar sesión
        update_session_data = {
            "session": {
                "lugar": "Auditorio API Principal - Sala VIP"
            }
        }

        update_session_response = client.patch(
            f"/api/v1/sessions/{session_1_id}",
            json=update_session_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert update_session_response.status_code == 200

        # STEP 8: Probar búsquedas del sistema completo via API
        # Buscar congress por año
        search_by_year_response = client.get("/api/v1/congresses-new/by-year/2024")
        assert search_by_year_response.status_code == 200
        year_results = search_by_year_response.json()
        congress_names_by_year = [congress["nombre"] for congress in year_results]
        assert "Congreso API Integral 2024" in congress_names_by_year

        # Buscar congress por término
        search_response = client.get("/api/v1/congresses-new/search?query=API")
        assert search_response.status_code == 200
        search_results = search_response.json()
        search_names = [congress["nombre"] for congress in search_results]
        assert "Congreso API Integral 2024" in search_names

        # STEP 9: Eliminar entidades en orden correcto (de dependientes hacia principales)
        # Eliminar sesiones
        delete_session_1 = client.delete(
            f"/api/v1/sessions/{session_1_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        delete_session_2 = client.delete(
            f"/api/v1/sessions/{session_2_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert delete_session_1.status_code == 200
        assert delete_session_2.status_code == 200

        # Eliminar asociaciones de sponsors
        delete_association_1 = client.delete(
            f"/api/v1/sponsorships/{congress_id}/{sponsor_1_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        delete_association_2 = client.delete(
            f"/api/v1/sponsorships/{congress_id}/{sponsor_2_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert delete_association_1.status_code == 200
        assert delete_association_2.status_code == 200

        # Eliminar speakers
        delete_speaker_1 = client.delete(
            f"/api/v1/speakers/{speaker_1_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        delete_speaker_2 = client.delete(
            f"/api/v1/speakers/{speaker_2_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert delete_speaker_1.status_code == 200
        assert delete_speaker_2.status_code == 200

        # STEP 10: Finalmente eliminar el congress principal
        delete_congress_response = client.delete(
            f"/api/v1/congresses-new/{congress_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert delete_congress_response.status_code == 200

        # Verificar que el congress fue eliminado
        deleted_congress_response = client.get(f"/api/v1/congresses-new/{congress_id}")
        assert deleted_congress_response.status_code == 404

        # Verificar que los sponsors independientes aún existen
        sponsor_1_check = client.get(f"/api/v1/sponsors/{sponsor_1_id}")
        sponsor_2_check = client.get(f"/api/v1/sponsors/{sponsor_2_id}")

        assert sponsor_1_check.status_code == 200
        assert sponsor_2_check.status_code == 200

        print("✅ Test completo de flujo de API exitoso: Congress con todas las entidades vía endpoints")

    def test_congress_bulk_operations_api(self, client, auth_token):
        """
        Test: Operaciones masivas de Congress via API

        Verifica operaciones masivas y filtros avanzados:
        - Crear múltiples congress
        - Búsquedas con filtros múltiples
        - Operaciones de paginación
        - Resúmenes y estadísticas masivas
        """
        # STEP 1: Crear múltiples congress para pruebas masivas
        congress_data_list = []
        congress_ids = []

        for i in range(5):
            congress_data = {
                "congress": {
                    "nombre": f"Congreso Masivo {i+1}",
                    "edicion": f"CM-2024-0{i+1}",
                    "anio": 2024,
                    "fecha_inicio": f"2024-{11+i%2}-{15+(i*2)}",
                    "fecha_fin": f"2024-{11+i%2}-{17+(i*2)}",
                    "descripcion_general": f"Congreso número {i+1} para pruebas masivas",
                    "poster_cover_url": f"https://example.com/masivo_{i+1}.jpg"
                }
            }

            response = client.post(
                "/api/v1/congresses-new",
                json=congress_data,
                headers={"Authorization": f"Bearer {auth_token}"}
            )

            assert response.status_code == 201
            congress_ids.append(response.json()["congress_id"])

        # STEP 2: Verificar paginación con múltiples congress
        pagination_response = client.get("/api/v1/congresses-new?page=1&page_size=3")
        assert pagination_response.status_code == 200
        pagination_data = pagination_response.json()

        assert "congresses" in pagination_data
        assert "total" in pagination_data
        assert "page" in pagination_data
        assert pagination_data["page"] == 1
        assert len(pagination_data["congresses"]) <= 3

        # STEP 3: Búsquedas con filtros múltiples
        # Búsqueda por año y término
        filtered_search_response = client.get("/api/v1/congresses-new?year=2024&search_term=Masivo")
        assert filtered_search_response.status_code == 200
        filtered_results = filtered_search_response.json()

        masivo_congresses = [congress for congress in filtered_results["congresses"] if "Masivo" in congress["nombre"]]
        assert len(masivo_congresses) >= 5

        # STEP 4: Obtener resumen general con estadísticas
        summary_response = client.get("/api/v1/congresses-new/summary")
        assert summary_response.status_code == 200
        summary_data = summary_response.json()

        assert "data" in summary_data
        assert "message" in summary_data

        # STEP 5: Verificar años disponibles
        years_response = client.get("/api/v1/congresses-new/years")
        assert years_response.status_code == 200
        years_data = years_response.json()

        assert "data" in years_data
        assert "years" in years_data["data"]
        assert 2024 in years_data["data"]["years"]

        # STEP 6: Búsqueda por rango de fechas
        date_range_response = client.get(
            "/api/v1/congresses-new/date-range?start_date=2024-11-01&end_date=2024-12-31"
        )
        assert date_range_response.status_code == 200
        date_range_results = date_range_response.json()

        # Verificar que incluye nuestros congress masivos
        masivo_in_range = [congress for congress in date_range_results if "Masivo" in congress["nombre"]]
        assert len(masivo_in_range) >= 5

        # STEP 7: Limpiar - eliminar todos los congress creados
        for congress_id in congress_ids:
            delete_response = client.delete(
                f"/api/v1/congresses-new/{congress_id}",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            assert delete_response.status_code == 200

        print("✅ Test de operaciones masivas de API exitoso")

    def test_congress_error_handling_and_edge_cases_api(self, client, auth_token):
        """
        Test: Manejo de errores y casos límite en Congress API

        Verifica el comportamiento de la API ante:
        - Datos inválidos
        - IDs no existentes
        - Conflictos de datos
        - Límites de validación
        """
        # STEP 1: Probar creación con datos inválidos
        invalid_congress_data = {
            "congress": {
                "nombre": "",  # Nombre vacío
                "edicion": "INVALID-2024",
                "anio": 2025,
                "fecha_inicio": "2024-12-31",
                "fecha_fin": "2024-12-30",  # Fecha fin antes del inicio
                "descripcion_general": "Congress inválido",
                "poster_cover_url": "invalid-url"
            }
        }

        invalid_response = client.post(
            "/api/v1/congresses-new",
            json=invalid_congress_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert invalid_response.status_code == 422  # Validation error

        # STEP 2: Intentar acceder a congress inexistente
        nonexistent_id = 999999
        nonexistent_response = client.get(f"/api/v1/congresses-new/{nonexistent_id}")
        assert nonexistent_response.status_code == 404

        # STEP 3: Intentar actualizar congress inexistente
        update_nonexistent_response = client.patch(
            f"/api/v1/congresses-new/{nonexistent_id}",
            json={"congress": {"descripcion_general": "Update"}},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert update_nonexistent_response.status_code in [400, 404]

        # STEP 4: Intentar eliminar congress inexistente
        delete_nonexistent_response = client.delete(
            f"/api/v1/congresses-new/{nonexistent_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert delete_nonexistent_response.status_code in [400, 404]

        # STEP 5: Probar límites de paginación
        large_page_size_response = client.get("/api/v1/congresses-new?page=1&page_size=150")
        assert large_page_size_response.status_code == 422  # Page size limit exceeded

        # STEP 6: Búsqueda con query vacío
        empty_search_response = client.get("/api/v1/congresses-new/search?query=")
        assert empty_search_response.status_code == 422

        # STEP 7: Crear congress válido para probar duplicado
        valid_congress_data = {
            "congress": {
                "nombre": "Congreso Para Duplicar",
                "edicion": "CPD-2024-01",
                "anio": 2024,
                "fecha_inicio": "2024-12-20",
                "fecha_fin": "2024-12-22",
                "descripcion_general": "Congress para probar duplicados",
                "poster_cover_url": "https://example.com/duplicate_test.jpg"
            }
        }

        valid_response = client.post(
            "/api/v1/congresses-new",
            json=valid_congress_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert valid_response.status_code == 201
        congress_id = valid_response.json()["congress_id"]

        # Intentar crear duplicado con la misma edición
        duplicate_response = client.post(
            "/api/v1/congresses-new",
            json=valid_congress_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert duplicate_response.status_code in [400, 422, 409]  # Conflict or validation error

        # STEP 8: Verificar disponibilidad de edición
        availability_response = client.get(f"/api/v1/congresses-new/check-edition/CPD-2024-01/2024")
        assert availability_response.status_code == 200
        availability_data = availability_response.json()
        assert availability_data["available"] is False

        # Verificar edición disponible
        available_response = client.get("/api/v1/congresses-new/check-edition/DISPONIBLE-2025/2025")
        assert available_response.status_code == 200
        available_data = available_response.json()
        assert available_data["available"] is True

        # STEP 9: Limpiar congress creado
        cleanup_response = client.delete(
            f"/api/v1/congresses-new/{congress_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert cleanup_response.status_code == 200

        print("✅ Test de manejo de errores y casos límite exitoso")

    def test_congress_with_categories_integration_api(self, client, auth_token):
        """
        Test: Integración de Congress con Categories via API

        Verifica la integración completa con el sistema de categorías:
        - Crear categorías de congress
        - Asociar congress a categorías
        - Filtrar por categorías
        """
        # STEP 1: Crear categoría de congress via API
        category_data = {
            "name": "Teología Sistemática",
            "description": "Categoría para congresos de teología sistemática",
            "svgurl": "https://example.com/teologia.svg",
            "status": "activo"  # Usar minúsculas según el enum
        }

        category_response = client.post(
            "/api/v1/congress-categories",
            json=category_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert category_response.status_code == 201
        category_id = category_response.json()["id"]  # Usar "id" directamente

        # STEP 2: Crear congress asociado a la categoría
        congress_with_category_data = {
            "congress": {
                "nombre": "Congreso de Teología Sistemática 2024",
                "edicion": "CTS-2024-01",
                "anio": 2024,
                "fecha_inicio": "2024-12-25",
                "fecha_fin": "2024-12-27",
                "descripcion_general": "Congress sobre teología sistemática contemporánea",
                "poster_cover_url": "https://example.com/teologia_congress.jpg"
            }
        }

        congress_response = client.post(
            "/api/v1/congresses-new",
            json=congress_with_category_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert congress_response.status_code == 201
        congress_id = congress_response.json()["congress_id"]

        # STEP 3: Verificar que las categorías están funcionando
        categories_list_response = client.get(
            "/api/v1/congress-categories",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert categories_list_response.status_code == 200
        categories_list = categories_list_response.json()

        category_names = [category["name"] for category in categories_list["items"]]
        assert "Teología Sistemática" in category_names

        # STEP 4: Limpiar
        delete_congress_response = client.delete(
            f"/api/v1/congresses-new/{congress_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        delete_category_response = client.delete(
            f"/api/v1/congress-categories/{category_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert delete_congress_response.status_code == 200
        assert delete_category_response.status_code == 204  # 204 No Content es correcto para DELETE

        print("✅ Test de integración con categorías exitoso")