"""
Tests unitarios para el SesionCronogramaController

Estos tests verifican que los métodos del controller de sesiones del cronograma
funcionen correctamente.
"""
import pytest
from datetime import date, time
from src.controllers.sesion_cronograma_controller import sesion_cronograma_controller
from src.models.sesion_cronograma_model import SesionCronogramaCreate, SesionCronogramaUpdate


class TestSesionCronogramaController:
    """Suite de tests para SesionCronogramaController"""

    def test_create_session_success(self, session, sample_sesion_cronograma_data):
        """
        Test: Crear una sesión exitosamente

        Verifica que la sesión se crea y se guarda correctamente en la BD
        """
        # Act
        created_session = sesion_cronograma_controller.create_session(
            session, sample_sesion_cronograma_data, current_user_id=1
        )

        # Assert
        assert created_session is not None
        assert created_session["id_sesion"] is not None
        assert created_session["titulo_sesion"] == "Teología Sistemática en el Siglo XXI"
        assert created_session["jornada"] == "mañana"
        assert created_session["lugar"] == "Auditorio Principal"

    def test_get_session_by_id_found(self, session, sample_sesion_cronograma):
        """
        Test: Buscar sesión por ID cuando existe

        Verifica que retorna la sesión correcta cuando existe
        """
        # Act
        found_session = sesion_cronograma_controller.get_session_by_id(
            session, sample_sesion_cronograma.id_sesion
        )

        # Assert
        assert found_session is not None
        assert found_session["id_sesion"] == sample_sesion_cronograma.id_sesion
        assert found_session["titulo_sesion"] == sample_sesion_cronograma.titulo_sesion

    def test_get_session_by_id_not_found(self, session):
        """
        Test: Buscar sesión por ID cuando no existe

        Verifica que retorna None cuando la sesión no existe
        """
        # Act
        found_session = sesion_cronograma_controller.get_session_by_id(session, 99999)

        # Assert
        assert found_session is None

    def test_get_sessions_by_congress(self, session, sample_sesion_cronograma, sample_congress_new):
        """
        Test: Obtener sesiones por congreso

        Verifica que retorna las sesiones del congreso correcto
        """
        # Act
        sessions = sesion_cronograma_controller.get_sessions_by_congress(
            session, sample_congress_new.id_congreso
        )

        # Assert
        assert sessions is not None
        assert len(sessions) >= 1
        assert all(s["id_congreso"] == sample_congress_new.id_congreso for s in sessions)

    def test_get_sessions_by_speaker(self, session, sample_sesion_cronograma, sample_speaker):
        """
        Test: Obtener sesiones por speaker

        Verifica que retorna las sesiones del speaker correcto
        """
        # Act
        sessions = sesion_cronograma_controller.get_sessions_by_speaker(
            session, sample_speaker.id_speaker
        )

        # Assert
        assert sessions is not None
        assert len(sessions) >= 1
        assert all(s["id_speaker"] == sample_speaker.id_speaker for s in sessions)

    def test_get_sessions_by_date(self, session, sample_sesion_cronograma):
        """
        Test: Obtener sesiones por fecha

        Verifica el filtrado por fecha
        """
        # Act
        sessions = sesion_cronograma_controller.get_sessions_by_date(
            session, sample_sesion_cronograma.fecha
        )

        # Assert
        assert sessions is not None
        assert len(sessions) >= 1
        assert all(s["fecha"] == sample_sesion_cronograma.fecha.isoformat() for s in sessions)

    def test_get_all_sessions_pagination(self, session, sample_sesion_cronograma):
        """
        Test: Obtener todas las sesiones con paginación

        Verifica que la paginación funciona correctamente
        """
        # Act
        result = sesion_cronograma_controller.get_all_sessions(
            session, page=1, page_size=10
        )

        # Assert
        assert result is not None
        assert "sessions" in result
        assert "total" in result
        assert "page" in result
        assert result["page"] == 1
        assert len(result["sessions"]) >= 1

    def test_search_sessions(self, session, sample_sesion_cronograma):
        """
        Test: Buscar sesiones por término

        Verifica que la búsqueda funciona
        """
        # Act
        results = sesion_cronograma_controller.search_sessions(
            session, search_term="Prueba", limit=10
        )

        # Assert
        assert results is not None
        # Debería encontrar nuestra sesión de prueba

    def test_get_sessions_by_date_range(self, session, sample_sesion_cronograma):
        """
        Test: Obtener sesiones por rango de fechas

        Verifica el filtrado por rango de fechas
        """
        # Act
        sessions = sesion_cronograma_controller.get_sessions_by_date_range(
            session,
            start_date=date(2026, 9, 14),
            end_date=date(2026, 9, 16)
        )

        # Assert
        assert sessions is not None
        assert len(sessions) >= 1

    def test_get_sessions_by_jornada(self, session, sample_sesion_cronograma):
        """
        Test: Obtener sesiones por jornada

        Verifica el filtrado por jornada
        """
        # Act
        sessions = sesion_cronograma_controller.get_sessions_by_jornada(
            session, "mañana"
        )

        # Assert
        assert sessions is not None
        assert all(s["jornada"] == "mañana" for s in sessions)

    def test_update_session_success(self, session, sample_sesion_cronograma):
        """
        Test: Actualizar sesión exitosamente

        Verifica que la actualización funciona correctamente
        """
        # Arrange
        update_data = SesionCronogramaUpdate(
            lugar="Nuevo Auditorio"
        )

        # Act
        updated_session = sesion_cronograma_controller.update_session(
            session, sample_sesion_cronograma.id_sesion, update_data, current_user_id=1
        )

        # Assert
        assert updated_session is not None
        assert updated_session["lugar"] == "Nuevo Auditorio"
        assert updated_session["titulo_sesion"] == sample_sesion_cronograma.titulo_sesion  # No cambiado

    def test_delete_session_success(self, session, sample_sesion_cronograma):
        """
        Test: Eliminar sesión exitosamente

        Verifica que la eliminación funciona correctamente
        """
        # Act
        result = sesion_cronograma_controller.delete_session(
            session, sample_sesion_cronograma.id_sesion, current_user_id=1
        )

        # Assert
        assert result is not None
        assert "message" in result

        # Verificar que no se puede encontrar después de eliminar
        deleted_session = sesion_cronograma_controller.get_session_by_id(
            session, sample_sesion_cronograma.id_sesion
        )
        assert deleted_session is None

    def test_check_time_conflicts_no_conflict(self, session, sample_speaker):
        """
        Test: Verificar conflictos de horario cuando no hay conflictos

        Verifica que retorna has_conflicts=False cuando no hay conflictos
        """
        # Act
        result = sesion_cronograma_controller.check_time_conflicts(
            session,
            sample_speaker.id_speaker,
            date(2024, 12, 1),  # Fecha diferente sin conflictos
            time(14, 0),
            time(15, 30)
        )

        # Assert
        assert result is not None
        assert result["has_conflicts"] is False

    def test_check_time_conflicts_with_conflict(self, session, sample_sesion_cronograma, sample_speaker):
        """
        Test: Verificar conflictos de horario cuando hay conflictos

        Verifica que retorna has_conflicts=True cuando hay conflictos
        """
        # Act - Usar misma fecha y horario que solapan
        result = sesion_cronograma_controller.check_time_conflicts(
            session,
            sample_speaker.id_speaker,
            sample_sesion_cronograma.fecha,
            time(10, 30),  # Solapa con la sesión existente (10:00-11:30)
            time(12, 0)
        )

        # Assert
        assert result is not None
        assert result["has_conflicts"] is True
        assert "conflicts" in result

    def test_get_daily_schedule(self, session, sample_sesion_cronograma, sample_congress_new):
        """
        Test: Obtener cronograma diario

        Verifica que el cronograma diario se genera correctamente
        """
        # Act
        result = sesion_cronograma_controller.get_daily_schedule(
            session,
            sample_congress_new.id_congreso,
            sample_sesion_cronograma.fecha
        )

        # Assert
        assert result is not None
        assert "data" in result
        assert "message" in result

    def test_get_congress_schedule_summary(self, session, sample_sesion_cronograma, sample_congress_new):
        """
        Test: Obtener resumen del cronograma del congreso

        Verifica que las estadísticas del cronograma se generan correctamente
        """
        # Act
        result = sesion_cronograma_controller.get_congress_schedule_summary(
            session, sample_congress_new.id_congreso
        )

        # Assert
        assert result is not None
        assert "data" in result
        assert "message" in result

    def test_get_session_summary(self, session, sample_sesion_cronograma):
        """
        Test: Obtener resumen general de sesiones

        Verifica que el resumen se genera correctamente
        """
        # Act
        result = sesion_cronograma_controller.get_session_summary(session)

        # Assert
        assert result is not None
        assert "data" in result
        assert "message" in result

    def test_create_session_time_conflict_should_fail(self, session, sample_sesion_cronograma_data):
        """
        Test: Intentar crear sesión con conflicto de horario

        Verifica que falla cuando hay conflictos de horario
        """
        # Arrange - Crear primera sesión
        sesion_cronograma_controller.create_session(
            session, sample_sesion_cronograma_data, current_user_id=1
        )

        # Act & Assert - Intentar crear otra con conflicto de horario
        conflicting_session_data = SesionCronogramaCreate(
            id_congreso=sample_sesion_cronograma_data.id_congreso,
            id_speaker=sample_sesion_cronograma_data.id_speaker,
            fecha=sample_sesion_cronograma_data.fecha,  # Misma fecha
            hora_inicio=time(9, 30),  # Solapa con 9:00-10:30
            hora_fin=time(11, 0),
            titulo_sesion="Sesión Conflictiva",
            jornada="mañana",
            lugar="Otro Auditorio"
        )

        with pytest.raises(Exception):
            sesion_cronograma_controller.create_session(
                session, conflicting_session_data, current_user_id=1
            )

    def test_create_session_nonexistent_congress_should_fail(self, session, sample_speaker):
        """
        Test: Intentar crear sesión para congreso inexistente

        Verifica que falla cuando el congreso no existe
        """
        # Arrange
        invalid_session_data = SesionCronogramaCreate(
            id_congreso=99999,  # Congreso inexistente
            id_speaker=sample_speaker.id_speaker,
            fecha=date(2026, 12, 1),
            hora_inicio=time(9, 0),
            hora_fin=time(10, 30),
            titulo_sesion="Sesión Inválida",
            jornada="mañana",
            lugar="Aula Test"
        )

        # Act & Assert
        with pytest.raises(Exception):
            sesion_cronograma_controller.create_session(
                session, invalid_session_data, current_user_id=1
            )

    def test_create_session_nonexistent_speaker_should_fail(self, session, sample_congress_new):
        """
        Test: Intentar crear sesión para speaker inexistente

        Verifica que falla cuando el speaker no existe
        """
        # Arrange
        invalid_session_data = SesionCronogramaCreate(
            id_congreso=sample_congress_new.id_congreso,
            id_speaker=99999,  # Speaker inexistente
            fecha=date(2026, 12, 1),
            hora_inicio=time(9, 0),
            hora_fin=time(10, 30),
            titulo_sesion="Sesión Inválida",
            jornada="mañana",
            lugar="Aula Test"
        )

        # Act & Assert
        with pytest.raises(Exception):
            sesion_cronograma_controller.create_session(
                session, invalid_session_data, current_user_id=1
            )

    def test_create_session_speaker_not_in_congress_should_fail(self, session, sample_congress_new):
        """
        Test: Intentar crear sesión con speaker de otro congreso

        Verifica que falla cuando el speaker no pertenece al congreso
        """
        # Arrange - Crear otro congreso y speaker
        from src.models.congress_model import Congress
        other_congress = Congress(
            nombre="Otro Congreso",
            edicion="OC-2024-01",
            anio=2024,
            fecha_inicio=date(2024, 11, 1),
            fecha_fin=date(2024, 11, 3),
            descripcion_general="Otro congreso de prueba",
            poster_cover_url="https://example.com/other.jpg"
        )
        session.add(other_congress)
        session.commit()
        session.refresh(other_congress)

        from src.models.speaker_model import Speaker
        other_speaker = Speaker(
            id_congreso=other_congress.id_congreso,
            nombres_completos="Dr. Otro Speaker",
            titulo_academico="Doctor",
            institucion="Otra Universidad",
            pais="Otro País",
            foto_url="https://example.com/foto_otro_speaker.jpg",
            tipo_speaker="keynote"
        )
        session.add(other_speaker)
        session.commit()
        session.refresh(other_speaker)

        # Arrange - Sesión inválida (speaker de otro congreso)
        invalid_session_data = SesionCronogramaCreate(
            id_congreso=sample_congress_new.id_congreso,
            id_speaker=other_speaker.id_speaker,  # Speaker de otro congreso
            fecha=date(2026, 12, 1),
            hora_inicio=time(9, 0),
            hora_fin=time(10, 30),
            titulo_sesion="Sesión Inválida",
            jornada="mañana",
            lugar="Aula Test"
        )

        # Act & Assert
        with pytest.raises(Exception):
            sesion_cronograma_controller.create_session(
                session, invalid_session_data, current_user_id=1
            )

    def test_update_session_not_found(self, session):
        """
        Test: Intentar actualizar sesión inexistente

        Verifica que lanza excepción cuando la sesión no existe
        """
        # Arrange
        update_data = SesionCronogramaUpdate(lugar="Nuevo lugar")

        # Act & Assert
        with pytest.raises(Exception):
            sesion_cronograma_controller.update_session(
                session, 99999, update_data, current_user_id=1
            )

    def test_delete_session_not_found(self, session):
        """
        Test: Intentar eliminar sesión inexistente

        Verifica que lanza excepción cuando la sesión no existe
        """
        # Act & Assert
        with pytest.raises(Exception):
            sesion_cronograma_controller.delete_session(session, 99999, current_user_id=1)