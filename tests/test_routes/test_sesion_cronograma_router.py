"""
Tests de integración para los endpoints de Sesion Cronograma

Estos tests verifican que los endpoints del router de sesiones de cronograma
funcionen correctamente.
"""
import pytest
from datetime import date, time


class TestSesionCronogramaEndpoints:
    """Suite de tests para los endpoints de sesiones del cronograma"""

    @pytest.fixture
    def session_creation_data(self, sample_congress_new, sample_speaker):
        """Datos para crear una sesión"""
        return {
            "session": {
                "id_congreso": sample_congress_new.id_congreso,
                "id_speaker": sample_speaker.id_speaker,
                "fecha": "2026-09-15",
                "hora_inicio": "09:00:00",
                "hora_fin": "10:30:00",
                "titulo_sesion": "Nueva Sesión de Cronograma",
                "jornada": "mañana",
                "lugar": "Auditorio Central"
            }
        }

    @pytest.fixture
    def auth_token(self, client):
        """Token de autenticación para tests"""
        # Registrar usuario de prueba
        user_data = {
            "name": "Test",
            "last_name": "User",
            "email": "testsession@example.com",
            "password": "password123"
        }
        client.post("/api/v1/auth/register", json=user_data)

        # Login y obtener token
        login_response = client.post("/api/v1/auth/token", data={
            "username": user_data["email"],
            "password": user_data["password"]
        })
        return login_response.json()["access_token"]

    def test_create_session_success(self, client, session_creation_data, auth_token):
        """
        Test: POST /api/v1/sessions con datos válidos

        Verifica que crea una sesión exitosamente
        """
        # Act
        response = client.post(
            "/api/v1/sessions",
            json=session_creation_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Session created successfully"
        assert "session_id" in data
        assert "data" in data

    def test_create_session_without_auth(self, client, session_creation_data):
        """
        Test: POST /api/v1/sessions sin autenticación

        Verifica que retorna 401 sin token
        """
        # Act
        response = client.post("/api/v1/sessions", json=session_creation_data)

        # Assert
        assert response.status_code == 401

    def test_create_session_missing_fields(self, client, auth_token, sample_congress_new, sample_speaker):
        """
        Test: POST /api/v1/sessions con campos faltantes

        Verifica que retorna error de validación 422
        """
        # Act
        response = client.post(
            "/api/v1/sessions",
            json={
                "session": {
                    "id_congreso": sample_congress_new.id_congreso,
                    "titulo_sesion": "Sesión Incompleta"
                    # Faltan campos requeridos
                }
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Assert
        assert response.status_code == 422

    def test_get_all_sessions(self, client, sample_sesion_cronograma):
        """
        Test: GET /api/v1/sessions

        Verifica que retorna lista paginada de sesiones
        """
        # Act
        response = client.get("/api/v1/sessions?page=1&page_size=10")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert "total" in data
        assert "page" in data
        assert data["page"] == 1

    def test_get_all_sessions_with_filters(self, client, sample_sesion_cronograma):
        """
        Test: GET /api/v1/sessions con filtros

        Verifica que los filtros funcionen correctamente
        """
        # Act
        response = client.get(
            f"/api/v1/sessions?congress_id={sample_sesion_cronograma.id_congreso}&jornada=mañana"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data

    def test_get_session_by_id_found(self, client, sample_sesion_cronograma):
        """
        Test: GET /api/v1/sessions/{id} cuando existe

        Verifica que retorna la sesión correcta
        """
        # Act
        response = client.get(f"/api/v1/sessions/{sample_sesion_cronograma.id_sesion}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id_sesion"] == sample_sesion_cronograma.id_sesion
        assert data["titulo_sesion"] == sample_sesion_cronograma.titulo_sesion

    def test_get_session_by_id_not_found(self, client):
        """
        Test: GET /api/v1/sessions/{id} cuando no existe

        Verifica que retorna 404
        """
        # Act
        response = client.get("/api/v1/sessions/99999")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_get_session_with_speaker_and_congress(self, client, sample_sesion_cronograma):
        """
        Test: GET /api/v1/sessions/{id} con información adicional

        Verifica que incluye datos de speaker y congreso cuando se solicita
        """
        # Act
        response = client.get(
            f"/api/v1/sessions/{sample_sesion_cronograma.id_sesion}?include_speaker=true&include_congress=true"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id_sesion"] == sample_sesion_cronograma.id_sesion

    def test_search_sessions(self, client, sample_sesion_cronograma):
        """
        Test: GET /api/v1/sessions/search

        Verifica que la búsqueda por título funciona
        """
        # Act
        response = client.get("/api/v1/sessions/search?query=Prueba")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_search_sessions_with_congress_filter(self, client, sample_sesion_cronograma):
        """
        Test: GET /api/v1/sessions/search con filtro de congreso

        Verifica que la búsqueda con filtro de congreso funciona
        """
        # Act
        response = client.get(
            f"/api/v1/sessions/search?query=Test&congress_id={sample_sesion_cronograma.id_congreso}"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_search_sessions_empty_query(self, client):
        """
        Test: Búsqueda con query vacío

        Verifica que retorna error de validación
        """
        # Act
        response = client.get("/api/v1/sessions/search?query=")

        # Assert
        assert response.status_code == 422  # min_length=1

    def test_get_sessions_by_congress(self, client, sample_sesion_cronograma):
        """
        Test: GET /api/v1/sessions/by-congress/{congress_id}

        Verifica que retorna sesiones del congreso especificado
        """
        # Act
        response = client.get(f"/api/v1/sessions/by-congress/{sample_sesion_cronograma.id_congreso}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Todas las sesiones deben ser del congreso especificado
        if data:
            assert all(s["id_congreso"] == sample_sesion_cronograma.id_congreso for s in data)

    def test_get_sessions_by_congress_with_details(self, client, sample_sesion_cronograma):
        """
        Test: GET /api/v1/sessions/by-congress/{congress_id} con detalles

        Verifica que incluye información detallada cuando se solicita
        """
        # Act
        response = client.get(
            f"/api/v1/sessions/by-congress/{sample_sesion_cronograma.id_congreso}?include_details=true&order_by_date=true"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_sessions_by_speaker(self, client, sample_sesion_cronograma):
        """
        Test: GET /api/v1/sessions/by-speaker/{speaker_id}

        Verifica que retorna sesiones del speaker especificado
        """
        # Act
        response = client.get(f"/api/v1/sessions/by-speaker/{sample_sesion_cronograma.id_speaker}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Todas las sesiones deben ser del speaker especificado
        if data:
            assert all(s["id_speaker"] == sample_sesion_cronograma.id_speaker for s in data)

    def test_get_sessions_by_speaker_with_details(self, client, sample_sesion_cronograma):
        """
        Test: GET /api/v1/sessions/by-speaker/{speaker_id} con detalles

        Verifica que incluye información del congreso cuando se solicita
        """
        # Act
        response = client.get(
            f"/api/v1/sessions/by-speaker/{sample_sesion_cronograma.id_speaker}?include_details=true"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_sessions_by_date(self, client, sample_sesion_cronograma):
        """
        Test: GET /api/v1/sessions/by-date/{fecha}

        Verifica el filtrado por fecha específica
        """
        # Act
        response = client.get(f"/api/v1/sessions/by-date/{sample_sesion_cronograma.fecha}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Todas las sesiones deben ser de la fecha especificada
        if data:
            assert all(s["fecha"] == sample_sesion_cronograma.fecha.isoformat() for s in data)

    def test_get_sessions_by_date_with_congress_filter(self, client, sample_sesion_cronograma):
        """
        Test: GET /api/v1/sessions/by-date/{fecha} con filtro de congreso

        Verifica que el filtro de congreso funciona en el filtrado por fecha
        """
        # Act
        response = client.get(
            f"/api/v1/sessions/by-date/{sample_sesion_cronograma.fecha}?congress_id={sample_sesion_cronograma.id_congreso}&include_details=true"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_sessions_by_date_range(self, client, sample_sesion_cronograma):
        """
        Test: GET /api/v1/sessions/by-date-range

        Verifica el filtrado por rango de fechas
        """
        # Act
        response = client.get(
            "/api/v1/sessions/by-date-range?start_date=2024-09-14&end_date=2024-09-16"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_sessions_by_date_range_with_filters(self, client, sample_sesion_cronograma):
        """
        Test: GET /api/v1/sessions/by-date-range con filtros adicionales

        Verifica que los filtros adicionales funcionen
        """
        # Act
        response = client.get(
            f"/api/v1/sessions/by-date-range?start_date=2024-09-01&end_date=2024-12-31&congress_id={sample_sesion_cronograma.id_congreso}&include_details=false"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_sessions_by_jornada(self, client, sample_sesion_cronograma):
        """
        Test: GET /api/v1/sessions/by-jornada/{jornada}

        Verifica el filtrado por jornada
        """
        # Act
        response = client.get("/api/v1/sessions/by-jornada/mañana")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Todas las sesiones deben ser de la jornada especificada
        if data:
            assert all(s["jornada"] == "mañana" for s in data)

    def test_get_sessions_by_jornada_with_filters(self, client, sample_sesion_cronograma):
        """
        Test: GET /api/v1/sessions/by-jornada/{jornada} con filtros

        Verifica que los filtros adicionales funcionen
        """
        # Act
        response = client.get(
            f"/api/v1/sessions/by-jornada/mañana?congress_id={sample_sesion_cronograma.id_congreso}&fecha={sample_sesion_cronograma.fecha}"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_daily_schedule(self, client, sample_sesion_cronograma):
        """
        Test: GET /api/v1/sessions/daily-schedule/{congress_id}/{fecha}

        Verifica que retorna cronograma diario organizado
        """
        # Act
        response = client.get(
            f"/api/v1/sessions/daily-schedule/{sample_sesion_cronograma.id_congreso}/{sample_sesion_cronograma.fecha}"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "message" in data

    def test_get_daily_schedule_with_grouping(self, client, sample_sesion_cronograma):
        """
        Test: GET /api/v1/sessions/daily-schedule con agrupación

        Verifica que la agrupación por jornada funciona
        """
        # Act
        response = client.get(
            f"/api/v1/sessions/daily-schedule/{sample_sesion_cronograma.id_congreso}/{sample_sesion_cronograma.fecha}?group_by_jornada=false"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_get_congress_schedule_summary(self, client, sample_sesion_cronograma):
        """
        Test: GET /api/v1/sessions/congress-schedule/{congress_id}

        Verifica que retorna resumen del cronograma del congreso
        """
        # Act
        response = client.get(
            f"/api/v1/sessions/congress-schedule/{sample_sesion_cronograma.id_congreso}"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "message" in data

    def test_get_session_summary(self, client, sample_sesion_cronograma):
        """
        Test: GET /api/v1/sessions/summary

        Verifica que retorna resumen de sesiones
        """
        # Act
        response = client.get("/api/v1/sessions/summary")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "message" in data

    def test_update_session_success(self, client, sample_sesion_cronograma, auth_token):
        """
        Test: PATCH /api/v1/sessions/{id} con datos válidos

        Verifica que actualiza la sesión exitosamente
        """
        # Arrange
        update_data = {
            "session": {
                "lugar": "Nuevo Auditorio Principal"
            }
        }

        # Act
        response = client.patch(
            f"/api/v1/sessions/{sample_sesion_cronograma.id_sesion}",
            json=update_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Session updated successfully"

    def test_update_session_without_auth(self, client, sample_sesion_cronograma):
        """
        Test: PATCH /api/v1/sessions/{id} sin autenticación

        Verifica que retorna 401 sin token
        """
        # Act
        response = client.patch(
            f"/api/v1/sessions/{sample_sesion_cronograma.id_sesion}",
            json={"session": {"lugar": "Nuevo lugar"}}
        )

        # Assert
        assert response.status_code == 401

    def test_update_session_not_found(self, client, auth_token):
        """
        Test: PATCH /api/v1/sessions/{id} cuando no existe

        Verifica que retorna error apropiado
        """
        # Act
        response = client.patch(
            "/api/v1/sessions/99999",
            json={"session": {"lugar": "Nuevo"}},
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Assert
        assert response.status_code in [400, 404]

    def test_delete_session_success(self, client, sample_sesion_cronograma, auth_token):
        """
        Test: DELETE /api/v1/sessions/{id}

        Verifica que elimina la sesión exitosamente
        """
        # Act
        response = client.delete(
            f"/api/v1/sessions/{sample_sesion_cronograma.id_sesion}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Session deleted successfully"

    def test_delete_session_without_auth(self, client, sample_sesion_cronograma):
        """
        Test: DELETE /api/v1/sessions/{id} sin autenticación

        Verifica que retorna 401 sin token
        """
        # Act
        response = client.delete(f"/api/v1/sessions/{sample_sesion_cronograma.id_sesion}")

        # Assert
        assert response.status_code == 401

    def test_check_time_conflicts_no_conflict(self, client, sample_speaker):
        """
        Test: GET /api/v1/sessions/check-conflicts/{speaker_id} sin conflictos

        Verifica la verificación de conflictos cuando no hay conflictos
        """
        # Act
        response = client.get(
            f"/api/v1/sessions/check-conflicts/{sample_speaker.id_speaker}?fecha=2024-12-01&hora_inicio=14:00&hora_fin=15:30"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["has_conflicts"] is False

    def test_check_time_conflicts_with_conflict(self, client, sample_sesion_cronograma):
        """
        Test: GET /api/v1/sessions/check-conflicts/{speaker_id} con conflictos

        Verifica la verificación cuando hay conflictos
        """
        # Act - Usar misma fecha y horario que solapan
        response = client.get(
            f"/api/v1/sessions/check-conflicts/{sample_sesion_cronograma.id_speaker}?fecha={sample_sesion_cronograma.fecha}&hora_inicio=10:30&hora_fin=12:00"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["has_conflicts"] is True
        assert "conflicts" in data

    def test_check_time_conflicts_with_exclusion(self, client, sample_sesion_cronograma):
        """
        Test: GET /api/v1/sessions/check-conflicts con exclusión

        Verifica que funciona la exclusión para actualizaciones
        """
        # Act
        response = client.get(
            f"/api/v1/sessions/check-conflicts/{sample_sesion_cronograma.id_speaker}?fecha={sample_sesion_cronograma.fecha}&hora_inicio=09:30&hora_fin=11:00&exclude_session_id={sample_sesion_cronograma.id_sesion}"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        # No debería haber conflictos porque se excluye la sesión actual
        assert data["has_conflicts"] is False

    def test_check_time_conflicts_invalid_time_format(self, client, sample_speaker):
        """
        Test: GET /api/v1/sessions/check-conflicts con formato de hora inválido

        Verifica que retorna error con formato inválido
        """
        # Act
        response = client.get(
            f"/api/v1/sessions/check-conflicts/{sample_speaker.id_speaker}?fecha=2024-12-01&hora_inicio=25:00&hora_fin=15:30"
        )

        # Assert
        assert response.status_code == 422  # FastAPI returns 422 for validation errors

    def test_pagination_limits(self, client):
        """
        Test: Verificar límites de paginación

        Verifica que se respetan los límites de paginación
        """
        # Act
        response = client.get("/api/v1/sessions?page=1&page_size=150")

        # Assert
        assert response.status_code == 422  # page_size máximo es 100

    def test_search_sessions_limit_validation(self, client):
        """
        Test: Verificar límites en búsqueda

        Verifica que se respetan los límites en la búsqueda
        """
        # Act
        response = client.get("/api/v1/sessions/search?query=test&limit=150")

        # Assert
        assert response.status_code == 422  # limit máximo es 100

    def test_invalid_date_format_in_date_range(self, client):
        """
        Test: GET /api/v1/sessions/by-date-range con formato de fecha inválido

        Verifica que retorna error de validación
        """
        # Act
        response = client.get(
            "/api/v1/sessions/by-date-range?start_date=invalid&end_date=2024-12-31"
        )

        # Assert
        assert response.status_code == 422

    def test_missing_required_parameters_date_range(self, client):
        """
        Test: GET /api/v1/sessions/by-date-range sin parámetros requeridos

        Verifica que retorna error cuando faltan parámetros
        """
        # Act
        response = client.get("/api/v1/sessions/by-date-range")

        # Assert
        assert response.status_code == 422

    def test_time_conflicts_missing_parameters(self, client, sample_speaker):
        """
        Test: GET /api/v1/sessions/check-conflicts sin parámetros requeridos

        Verifica que retorna error cuando faltan parámetros
        """
        # Act
        response = client.get(f"/api/v1/sessions/check-conflicts/{sample_speaker.id_speaker}")

        # Assert
        assert response.status_code == 422  # Faltan parámetros requeridos