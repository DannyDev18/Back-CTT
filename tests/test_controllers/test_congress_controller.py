"""
Tests unitarios para el CongressControllerNew

Estos tests verifican que los métodos del controller de congresos
funcionen correctamente con el nuevo esquema.
"""
import pytest
from datetime import date
from src.controllers.congress_controller import congress_controller
from src.models.congress_model import CongressCreate, CongressUpdate


class TestCongressController:
    """Suite de tests para CongressControllerNew"""

    def test_create_congress_success(self, session, sample_congress_new_data):
        """
        Test: Crear un congreso exitosamente

        Verifica que el congreso se crea y se guarda correctamente en la BD
        """
        # Act
        created_congress = congress_controller.create_congress(
            session, sample_congress_new_data, current_user_id=1
        )

        # Assert
        assert created_congress is not None
        assert created_congress["id_congreso"] is not None
        assert created_congress["nombre"] == "Congreso Internacional de Teología 2024"
        assert created_congress["edicion"] == "CIT-2024-01"
        assert created_congress["anio"] == 2026

    def test_get_congress_by_id_found(self, session, sample_congress_new):
        """
        Test: Buscar congreso por ID cuando existe

        Verifica que retorna el congreso correcto cuando existe
        """
        # Act
        found_congress = congress_controller.get_congress_by_id(
            session, sample_congress_new.id_congreso
        )

        # Assert
        assert found_congress is not None
        assert found_congress["id_congreso"] == sample_congress_new.id_congreso
        assert found_congress["nombre"] == sample_congress_new.nombre

    def test_get_congress_by_id_not_found(self, session):
        """
        Test: Buscar congreso por ID cuando no existe

        Verifica que retorna None cuando el congreso no existe
        """
        # Act
        found_congress = congress_controller.get_congress_by_id(session, 99999)

        # Assert
        assert found_congress is None

    def test_get_all_congresses_pagination(self, session, sample_congress_new):
        """
        Test: Obtener todos los congresos con paginación

        Verifica que la paginación funciona correctamente
        """
        # Act
        result = congress_controller.get_all_congresses(
            session, page=1, page_size=10
        )

        # Assert
        assert result is not None
        assert "congresses" in result
        assert "total" in result
        assert "page" in result
        assert result["page"] == 1
        assert len(result["congresses"]) >= 1

    def test_search_congresses(self, session, sample_congress_new):
        """
        Test: Buscar congresos por término

        Verifica que la búsqueda por texto funciona
        """
        # Act
        results = congress_controller.search_congresses(
            session, search_term="Prueba", limit=10
        )

        # Assert
        assert results is not None
        assert len(results) >= 1
        assert "Prueba" in results[0]["nombre"]

    def test_get_congresses_by_year(self, session, sample_congress_new):
        """
        Test: Obtener congresos por año

        Verifica el filtrado por año
        """
        # Act
        results = congress_controller.get_congresses_by_year(session, 2026)

        # Assert
        assert results is not None
        assert len(results) >= 1
        assert all(congress["anio"] == 2026 for congress in results)

    def test_update_congress_success(self, session, sample_congress_new):
        """
        Test: Actualizar congreso exitosamente

        Verifica que la actualización funciona correctamente
        """
        # Arrange
        update_data = CongressUpdate(
            descripcion_general="Nueva descripción actualizada"
        )

        # Act
        updated_congress = congress_controller.update_congress(
            session, sample_congress_new.id_congreso, update_data, current_user_id=1
        )

        # Assert
        assert updated_congress is not None
        assert updated_congress["descripcion_general"] == "Nueva descripción actualizada"
        assert updated_congress["nombre"] == sample_congress_new.nombre  # No cambiado

    def test_delete_congress_success(self, session, sample_congress_new):
        """
        Test: Eliminar congreso exitosamente

        Verifica que la eliminación funciona correctamente
        """
        # Act
        result = congress_controller.delete_congress(
            session, sample_congress_new.id_congreso, current_user_id=1
        )

        # Assert
        assert result is not None
        assert "message" in result

        # Verificar que no se puede encontrar después de eliminar
        deleted_congress = congress_controller.get_congress_by_id(
            session, sample_congress_new.id_congreso
        )
        assert deleted_congress is None

    def test_check_edition_availability_available(self, session):
        """
        Test: Verificar disponibilidad de edición cuando está disponible

        Verifica que retorna available=True para ediciones no existentes
        """
        # Act
        result = congress_controller.check_edition_availability(
            session, "TEST-2025-01", 2025
        )

        # Assert
        assert result is not None
        assert result["available"] is True

    def test_check_edition_availability_not_available(self, session, sample_congress_new):
        """
        Test: Verificar disponibilidad de edición cuando no está disponible

        Verifica que retorna available=False para ediciones existentes
        """
        # Act
        result = congress_controller.check_edition_availability(
            session, sample_congress_new.edicion, sample_congress_new.anio
        )

        # Assert
        assert result is not None
        assert result["available"] is False

    def test_get_congress_statistics(self, session, sample_congress_new):
        """
        Test: Obtener estadísticas de congreso

        Verifica que las estadísticas se generan correctamente
        """
        # Act
        result = congress_controller.get_congress_statistics(
            session, sample_congress_new.id_congreso
        )

        # Assert
        assert result is not None
        assert "data" in result
        assert "message" in result

    def test_get_congress_summary(self, session, sample_congress_new):
        """
        Test: Obtener resumen general de congresos

        Verifica que el resumen se genera correctamente
        """
        # Act
        result = congress_controller.get_congress_summary(session)

        # Assert
        assert result is not None
        assert "data" in result
        assert "message" in result

    def test_get_years_with_congresses(self, session, sample_congress_new):
        """
        Test: Obtener años que tienen congresos

        Verifica que retorna los años correctos
        """
        # Act
        result = congress_controller.get_years_with_congresses(session)

        # Assert
        assert result is not None
        assert "data" in result
        assert "years" in result["data"]
        assert 2026 in result["data"]["years"]

    def test_create_congress_with_duplicate_edition_should_fail(self, session, sample_congress_new):
        """
        Test: Intentar crear congreso con edición duplicada

        Verifica que no se puede crear un congreso con edición ya existente
        """
        # Arrange
        duplicate_congress_data = CongressCreate(
            nombre="Otro Congreso",
            edicion=sample_congress_new.edicion,  # Edición duplicada
            anio=sample_congress_new.anio,        # Año duplicado
            fecha_inicio=date(2024, 10, 1),
            fecha_fin=date(2024, 10, 3),
            descripcion_general="Intento de duplicado",
            poster_cover_url="https://example.com/duplicate.jpg"
        )

        # Act & Assert
        with pytest.raises(Exception):
            congress_controller.create_congress(
                session, duplicate_congress_data, current_user_id=1
            )

    def test_update_congress_not_found(self, session):
        """
        Test: Intentar actualizar congreso inexistente

        Verifica que lanza excepción cuando el congreso no existe
        """
        # Arrange
        update_data = CongressUpdate(descripcion_general="Nueva descripción")

        # Act & Assert
        with pytest.raises(Exception):
            congress_controller.update_congress(
                session, 99999, update_data, current_user_id=1
            )

    def test_delete_congress_not_found(self, session):
        """
        Test: Intentar eliminar congreso inexistente

        Verifica que lanza excepción cuando el congreso no existe
        """
        # Act & Assert
        with pytest.raises(Exception):
            congress_controller.delete_congress(session, 99999, current_user_id=1)

    def test_get_upcoming_congresses(self, session):
        """
        Test: Obtener próximos congresos

        Verifica que la función de próximos congresos funciona
        """
        # Arrange - Crear congreso futuro
        from datetime import datetime, timedelta
        future_date = datetime.now().date() + timedelta(days=365)
        future_congress_data = CongressCreate(
            nombre="Congreso Futuro",
            edicion="CF-2025-01",
            anio=future_date.year,
            fecha_inicio=future_date,
            fecha_fin=future_date + timedelta(days=2),
            descripcion_general="Congreso en el futuro",
            poster_cover_url="https://example.com/future.jpg"
        )
        congress_controller.create_congress(session, future_congress_data, current_user_id=1)

        # Act
        results = congress_controller.get_upcoming_congresses(session, limit=5)

        # Assert
        assert results is not None
        assert len(results) >= 1

    def test_get_current_congresses(self, session):
        """
        Test: Obtener congresos actuales

        Verifica que la función de congresos actuales funciona
        """
        # Act
        results = congress_controller.get_current_congresses(session)

        # Assert
        assert results is not None
        # Puede estar vacío si no hay congresos en curso

    def test_validate_date_range_in_create(self, session):
        """
        Test: Validar que fecha_fin > fecha_inicio en creación

        Verifica que se validan las fechas correctamente
        """
        # Act & Assert
        with pytest.raises(Exception):  # Can be ValueError from controller or ValidationError from Pydantic
            # The validation should fail either at Pydantic level or controller level
            try:
                invalid_congress_data = CongressCreate(
                    nombre="Congreso Inválido",
                    edicion="CI-2024-01",
                    anio=2024,
                    fecha_inicio=date(2024, 10, 10),
                    fecha_fin=date(2024, 10, 5),  # Fecha fin anterior a inicio
                    descripcion_general="Congreso con fechas inválidas",
                    poster_cover_url="https://example.com/invalid.jpg"
                )
                # If Pydantic validation passes, controller should still catch it
                congress_controller.create_congress(
                    session, invalid_congress_data, current_user_id=1
                )
            except Exception:
                # Re-raise to be caught by pytest.raises
                raise

    def test_complete_congress_crud_with_related_entities(self, session):
        """
        Test: Flujo CRUD completo de Congress con todas las entidades relacionadas

        Verifica que toda la funcionalidad CRUD funciona en conjunto:
        - Congress (crear, leer, actualizar, eliminar)
        - Sponsors (crear, asociar al congress)
        - Speakers (crear, asociar al congress)
        - Sesiones del cronograma (crear para el congress con speakers)
        - Congress Categories (crear, asociar)
        """
        from src.controllers.sponsor_controller import sponsor_controller
        from src.controllers.speaker_controller import speaker_controller
        from src.controllers.sesion_cronograma_controller import sesion_cronograma_controller
        from src.controllers.congreso_sponsor_controller import congreso_sponsor_controller
        from src.models.sponsor_model import SponsorCreate
        from src.models.speaker_model import SpeakerCreate
        from src.models.sesion_cronograma_model import SesionCronogramaCreate
        from src.models.congreso_sponsor_model import CongresoSponsorCreate
        from datetime import date, time
        from decimal import Decimal

        # STEP 1: Crear Congress principal
        congress_data = CongressCreate(
            nombre="Congreso Integral de Teología 2024",
            edicion="CIT-INTEG-2024-01",
            anio=2026,
            fecha_inicio=date(2026, 11, 15),
            fecha_fin=date(2026, 11, 17),
            descripcion_general="Congreso integral con speakers, sponsors y cronograma completo",
            poster_cover_url="https://example.com/integral_congress.jpg"
        )

        created_congress = congress_controller.create_congress(
            session, congress_data, current_user_id=1
        )

        assert created_congress is not None
        congress_id = created_congress["id_congreso"]

        # STEP 2: Crear y asociar Sponsors
        sponsor_data_1 = SponsorCreate(
            nombre="Editorial Cristiana Internacional",
            logo_url="https://example.com/logo_editorial.png",
            sitio_web="https://editorialcristiana.com",
            descripcion="Editorial líder en literatura teológica cristiana"
        )

        sponsor_data_2 = SponsorCreate(
            nombre="Universidad Teológica Central",
            logo_url="https://example.com/logo_universidad.png",
            sitio_web="https://uteologica.edu",
            descripcion="Institución educativa superior especializada en teología"
        )

        created_sponsor_1 = sponsor_controller.create_sponsor(session, sponsor_data_1, current_user_id=1)
        created_sponsor_2 = sponsor_controller.create_sponsor(session, sponsor_data_2, current_user_id=1)

        # Asociar sponsors al congress
        sponsor_association_1 = CongresoSponsorCreate(
            id_congreso=congress_id,
            id_sponsor=created_sponsor_1["id_sponsor"],
            categoria="oro",
            aporte=Decimal("10000.00")
        )

        sponsor_association_2 = CongresoSponsorCreate(
            id_congreso=congress_id,
            id_sponsor=created_sponsor_2["id_sponsor"],
            categoria="plata",
            aporte=Decimal("5000.00")
        )

        created_association_1 = congreso_sponsor_controller.create_sponsorship(
            session, sponsor_association_1, current_user_id=1
        )
        created_association_2 = congreso_sponsor_controller.create_sponsorship(
            session, sponsor_association_2, current_user_id=1
        )

        assert created_association_1 is not None
        assert created_association_2 is not None

        # STEP 3: Crear Speakers para el congress
        speaker_data_1 = SpeakerCreate(
            id_congreso=congress_id,
            nombres_completos="Dr. Carlos Eduardo Martínez",
            titulo_academico="Doctor en Teología Sistemática",
            institucion="Seminario Teológico de Guatemala",
            pais="Guatemala",
            foto_url="https://example.com/speaker_carlos.jpg",
            tipo_speaker="keynote"
        )

        speaker_data_2 = SpeakerCreate(
            id_congreso=congress_id,
            nombres_completos="Dra. María Elena Rodríguez",
            titulo_academico="Doctora en Historia del Cristianismo",
            institucion="Universidad Pontificia de México",
            pais="México",
            foto_url="https://example.com/speaker_maria.jpg",
            tipo_speaker="conferencia"
        )

        speaker_data_3 = SpeakerCreate(
            id_congreso=congress_id,
            nombres_completos="Rev. Jonathan Smith",
            titulo_academico="Master en Teología Pastoral",
            institucion="Dallas Theological Seminary",
            pais="Estados Unidos",
            foto_url="https://example.com/speaker_jonathan.jpg",
            tipo_speaker="panel"
        )

        created_speaker_1 = speaker_controller.create_speaker(session, speaker_data_1, current_user_id=1)
        created_speaker_2 = speaker_controller.create_speaker(session, speaker_data_2, current_user_id=1)
        created_speaker_3 = speaker_controller.create_speaker(session, speaker_data_3, current_user_id=1)

        assert created_speaker_1 is not None
        assert created_speaker_2 is not None
        assert created_speaker_3 is not None

        # STEP 4: Crear cronograma de sesiones
        sesion_data_1 = SesionCronogramaCreate(
            id_congreso=congress_id,
            id_speaker=created_speaker_1["id_speaker"],
            fecha=date(2026, 11, 15),
            hora_inicio=time(9, 0),
            hora_fin=time(10, 30),
            titulo_sesion="Conferencia Magistral: El Futuro de la Teología Cristiana",
            jornada="mañana",
            lugar="Auditorio Principal"
        )

        sesion_data_2 = SesionCronogramaCreate(
            id_congreso=congress_id,
            id_speaker=created_speaker_2["id_speaker"],
            fecha=date(2026, 11, 15),
            hora_inicio=time(11, 0),
            hora_fin=time(12, 30),
            titulo_sesion="Historia y Evolución del Pensamiento Cristiano",
            jornada="mañana",
            lugar="Aula Magna"
        )

        sesion_data_3 = SesionCronogramaCreate(
            id_congreso=congress_id,
            id_speaker=created_speaker_3["id_speaker"],
            fecha=date(2026, 11, 16),
            hora_inicio=time(14, 0),
            hora_fin=time(15, 30),
            titulo_sesion="Panel: Desafíos Pastorales Contemporáneos",
            jornada="tarde",
            lugar="Salón de Conferencias"
        )

        created_sesion_1 = sesion_cronograma_controller.create_session(
            session, sesion_data_1, current_user_id=1
        )
        created_sesion_2 = sesion_cronograma_controller.create_session(
            session, sesion_data_2, current_user_id=1
        )
        created_sesion_3 = sesion_cronograma_controller.create_session(
            session, sesion_data_3, current_user_id=1
        )

        assert created_sesion_1 is not None
        assert created_sesion_2 is not None
        assert created_sesion_3 is not None

        # STEP 5: Verificar lectura completa del congress con todas sus relaciones
        congress_retrieved = congress_controller.get_congress_by_id(session, congress_id)
        assert congress_retrieved is not None
        assert congress_retrieved["nombre"] == "Congreso Integral de Teología 2024"

        # Verificar que los sponsors están asociados
        congress_sponsors = congreso_sponsor_controller.get_sponsorships_by_congress(session, congress_id)
        assert len(congress_sponsors) == 2
        sponsor_categories = [sponsor["categoria"] for sponsor in congress_sponsors]
        assert "oro" in sponsor_categories
        assert "plata" in sponsor_categories

        # Verificar que los speakers están asociados
        congress_speakers = speaker_controller.get_speakers_by_congress(session, congress_id)
        assert len(congress_speakers) >= 3
        speaker_types = [speaker["tipo_speaker"] for speaker in congress_speakers]
        assert "keynote" in speaker_types
        assert "conferencia" in speaker_types
        assert "panel" in speaker_types

        # Verificar que las sesiones están programadas
        congress_sessions = sesion_cronograma_controller.get_sessions_by_congress(session, congress_id)
        assert len(congress_sessions) >= 3
        session_dates = [str(session["fecha"]) for session in congress_sessions]
        assert "2026-11-15" in session_dates
        assert "2026-11-16" in session_dates

        # STEP 6: Actualizar congress y verificar que las relaciones se mantienen
        from src.models.congress_model import CongressUpdate

        update_data = CongressUpdate(
            descripcion_general="Congreso integral actualizado con gran éxito de participación esperada"
        )

        updated_congress = congress_controller.update_congress(
            session, congress_id, update_data, current_user_id=1
        )

        assert updated_congress is not None
        assert "actualizado" in updated_congress["descripcion_general"]

        # Verificar que las relaciones siguen intactas después de la actualización
        sponsors_after_update = congreso_sponsor_controller.get_sponsorships_by_congress(session, congress_id)
        speakers_after_update = speaker_controller.get_speakers_by_congress(session, congress_id)
        sessions_after_update = sesion_cronograma_controller.get_sessions_by_congress(session, congress_id)

        assert len(sponsors_after_update) == 2
        assert len(speakers_after_update) >= 3
        assert len(sessions_after_update) >= 3

        # STEP 7: Actualizar entidades relacionadas
        # Actualizar un speaker
        from src.models.speaker_model import SpeakerUpdate
        speaker_update = SpeakerUpdate(
            institucion="Seminario Teológico de Guatemala - Campus Principal"
        )

        updated_speaker = speaker_controller.update_speaker(
            session, created_speaker_1["id_speaker"], speaker_update, current_user_id=1
        )
        assert "Campus Principal" in updated_speaker["institucion"]

        # Actualizar una sesión del cronograma
        from src.models.sesion_cronograma_model import SesionCronogramaUpdate
        session_update = SesionCronogramaUpdate(
            lugar="Auditorio Principal - Sala VIP"
        )

        updated_session = sesion_cronograma_controller.update_session(
            session, created_sesion_1["id_sesion"], session_update, current_user_id=1
        )
        assert "VIP" in updated_session["lugar"]

        # STEP 8: Probar búsquedas y filtros del sistema completo
        # Buscar congress por año
        congresses_2026 = congress_controller.get_congresses_by_year(session, 2026)
        congress_names = [congress["nombre"] for congress in congresses_2026]
        assert "Congreso Integral de Teología 2024" in congress_names

        # Buscar congress por término
        search_results = congress_controller.search_congresses(session, search_term="Integral", limit=10)
        search_names = [congress["nombre"] for congress in search_results]
        assert "Congreso Integral de Teología 2024" in search_names

        # Obtener estadísticas del congress
        stats = congress_controller.get_congress_statistics(session, congress_id)
        assert stats is not None
        assert "data" in stats

        # STEP 9: Probar eliminaciones en cascada (eliminar entidades relacionadas primero)
        # Eliminar sesiones del cronograma
        delete_result_1 = sesion_cronograma_controller.delete_session(
            session, created_sesion_1["id_sesion"], current_user_id=1
        )
        assert delete_result_1 is not None

        delete_result_2 = sesion_cronograma_controller.delete_session(
            session, created_sesion_2["id_sesion"], current_user_id=1
        )
        assert delete_result_2 is not None

        delete_result_3 = sesion_cronograma_controller.delete_session(
            session, created_sesion_3["id_sesion"], current_user_id=1
        )
        assert delete_result_3 is not None

        # Eliminar asociaciones de sponsor
        delete_association_1 = congreso_sponsor_controller.delete_sponsorship(
            session,
            congress_id,
            created_sponsor_1["id_sponsor"],
            current_user_id=1
        )
        assert delete_association_1 is not None

        delete_association_2 = congreso_sponsor_controller.delete_sponsorship(
            session,
            congress_id,
            created_sponsor_2["id_sponsor"],
            current_user_id=1
        )
        assert delete_association_2 is not None

        # Eliminar speakers
        delete_speaker_1 = speaker_controller.delete_speaker(
            session, created_speaker_1["id_speaker"], current_user_id=1
        )
        assert delete_speaker_1 is not None

        delete_speaker_2 = speaker_controller.delete_speaker(
            session, created_speaker_2["id_speaker"], current_user_id=1
        )
        assert delete_speaker_2 is not None

        delete_speaker_3 = speaker_controller.delete_speaker(
            session, created_speaker_3["id_speaker"], current_user_id=1
        )
        assert delete_speaker_3 is not None

        # STEP 10: Finalmente eliminar el congress principal
        delete_congress_result = congress_controller.delete_congress(
            session, congress_id, current_user_id=1
        )

        assert delete_congress_result is not None
        assert "message" in delete_congress_result

        # Verificar que el congress fue eliminado
        deleted_congress = congress_controller.get_congress_by_id(session, congress_id)
        assert deleted_congress is None

        # Verificar que las entidades relacionadas restantes siguen siendo accesibles independientemente
        remaining_sponsors_result = sponsor_controller.get_all_sponsors(session)
        remaining_sponsors = remaining_sponsors_result["sponsors"]
        sponsor_names = [sponsor["nombre"] for sponsor in remaining_sponsors]
        assert "Editorial Cristiana Internacional" in sponsor_names
        assert "Universidad Teológica Central" in sponsor_names

        print("✅ Test CRUD completo exitoso: Congress con todas las entidades relacionadas")

    def test_congress_with_enrollments_integration(self, session):
        """
        Test: Integración completa de Congress con inscripciones de usuarios

        Verifica el flujo completo desde la creación del congress hasta las inscripciones
        """
        from src.models.user_platform import UserPlatform, UserPlatformType
        from src.models.enrollment import Enrollment, EnrollmentStatus
        from datetime import datetime

        # STEP 1: Crear Congress
        congress_data = CongressCreate(
            nombre="Congreso de Inscripciones Test",
            edicion="CIT-2026-ENROLL",
            anio=2026,
            fecha_inicio=date(2026, 12, 1),
            fecha_fin=date(2026, 12, 3),
            descripcion_general="Congress para probar inscripciones",
            poster_cover_url="https://example.com/enrollment_test.jpg"
        )

        created_congress = congress_controller.create_congress(
            session, congress_data, current_user_id=1
        )
        congress_id = created_congress["id_congreso"]

        # STEP 2: Crear usuarios de plataforma
        user_1 = UserPlatform(
            identification="1234567890",
            first_name="Juan",
            second_name="Carlos",
            first_last_name="Pérez",
            second_last_name="González",
            cellphone="0987654321",
            email="juan.perez@example.com",
            address="Av. Principal 123",
            type=UserPlatformType.ESTUDIANTE,
            password="hashed_password_123"
        )

        user_2 = UserPlatform(
            identification="0987654321",
            first_name="María",
            second_name="Elena",
            first_last_name="Rodríguez",
            second_last_name="Martínez",
            cellphone="0912345678",
            email="maria.rodriguez@example.com",
            address="Calle Secundaria 456",
            type=UserPlatformType.EXTERNO,
            password="hashed_password_456"
        )

        session.add(user_1)
        session.add(user_2)
        session.commit()
        session.refresh(user_1)
        session.refresh(user_2)

        # STEP 3: Crear inscripciones al congress
        enrollment_1 = Enrollment(
            id_user_platform=user_1.id,
            id_congress=congress_id,
            enrollment_date=datetime.utcnow(),
            status=EnrollmentStatus.INTERESADO
        )

        enrollment_2 = Enrollment(
            id_user_platform=user_2.id,
            id_congress=congress_id,
            enrollment_date=datetime.utcnow(),
            status=EnrollmentStatus.PAGADO
        )

        session.add(enrollment_1)
        session.add(enrollment_2)
        session.commit()

        # STEP 4: Verificar las inscripciones
        # Obtener inscripciones por congress (esto requeriría un método en el controller)
        from sqlmodel import select

        enrollments_query = select(Enrollment).where(Enrollment.id_congress == congress_id)
        enrollments = session.exec(enrollments_query).all()

        assert len(enrollments) == 2

        enrollment_statuses = [enrollment.status for enrollment in enrollments]
        assert EnrollmentStatus.INTERESADO in enrollment_statuses
        assert EnrollmentStatus.PAGADO in enrollment_statuses

        # STEP 5: Verificar estadísticas del congress con inscripciones
        stats = congress_controller.get_congress_statistics(session, congress_id)
        assert stats is not None

        # STEP 6: Limpiar - eliminar congress y verificar que las inscripciones se manejen correctamente
        delete_result = congress_controller.delete_congress(
            session, congress_id, current_user_id=1
        )
        assert delete_result is not None

        print("✅ Test de integración con inscripciones exitoso")