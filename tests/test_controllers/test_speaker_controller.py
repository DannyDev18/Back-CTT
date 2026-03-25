"""
Tests unitarios para el SpeakerController

Estos tests verifican que los métodos del controller de speakers
funcionen correctamente.
"""
import pytest
from src.controllers.speaker_controller import speaker_controller
from src.models.speaker_model import SpeakerCreate, SpeakerUpdate


class TestSpeakerController:
    """Suite de tests para SpeakerController"""

    def test_create_speaker_success(self, session, sample_speaker_data):
        """
        Test: Crear un speaker exitosamente

        Verifica que el speaker se crea y se guarda correctamente en la BD
        """
        # Act
        created_speaker = speaker_controller.create_speaker(
            session, sample_speaker_data, current_user_id=1
        )

        # Assert
        assert created_speaker is not None
        assert created_speaker["id_speaker"] is not None
        assert created_speaker["nombres_completos"] == "Dr. Juan Carlos Martínez"
        assert created_speaker["pais"] == "Colombia"
        assert created_speaker["tipo_speaker"] == "keynote"

    def test_get_speaker_by_id_found(self, session, sample_speaker):
        """
        Test: Buscar speaker por ID cuando existe

        Verifica que retorna el speaker correcto cuando existe
        """
        # Act
        found_speaker = speaker_controller.get_speaker_by_id(
            session, sample_speaker.id_speaker
        )

        # Assert
        assert found_speaker is not None
        assert found_speaker["id_speaker"] == sample_speaker.id_speaker
        assert found_speaker["nombres_completos"] == sample_speaker.nombres_completos

    def test_get_speaker_by_id_not_found(self, session):
        """
        Test: Buscar speaker por ID cuando no existe

        Verifica que retorna None cuando el speaker no existe
        """
        # Act
        found_speaker = speaker_controller.get_speaker_by_id(session, 99999)

        # Assert
        assert found_speaker is None

    def test_get_speakers_by_congress(self, session, sample_speaker, sample_congress_new):
        """
        Test: Obtener speakers por congreso

        Verifica que retorna los speakers del congreso correcto
        """
        # Act
        speakers = speaker_controller.get_speakers_by_congress(
            session, sample_congress_new.id_congreso
        )

        # Assert
        assert speakers is not None
        assert len(speakers) >= 1
        assert all(s["id_congreso"] == sample_congress_new.id_congreso for s in speakers)

    def test_get_all_speakers_pagination(self, session, sample_speaker):
        """
        Test: Obtener todos los speakers con paginación

        Verifica que la paginación funciona correctamente
        """
        # Act
        result = speaker_controller.get_all_speakers(
            session, page=1, page_size=10
        )

        # Assert
        assert result is not None
        assert "speakers" in result
        assert "total" in result
        assert "page" in result
        assert result["page"] == 1
        assert len(result["speakers"]) >= 1

    def test_search_speakers(self, session, sample_speaker):
        """
        Test: Buscar speakers por término

        Verifica que la búsqueda funciona
        """
        # Act
        results = speaker_controller.search_speakers(
            session, search_term="González", limit=10
        )

        # Assert
        assert results is not None
        # Debería encontrar nuestro speaker de prueba

    def test_get_speakers_by_type(self, session, sample_speaker):
        """
        Test: Obtener speakers por tipo

        Verifica el filtrado por tipo de speaker
        """
        # Act
        results = speaker_controller.get_speakers_by_type(session, "keynote")

        # Assert
        assert results is not None
        assert all(s["tipo_speaker"] == "keynote" for s in results)

    def test_get_speakers_by_country(self, session, sample_speaker):
        """
        Test: Obtener speakers por país

        Verifica el filtrado por país
        """
        # Act
        results = speaker_controller.get_speakers_by_country(session, "Ecuador")

        # Assert
        assert results is not None
        assert all(s["pais"] == "Ecuador" for s in results)

    def test_get_speakers_by_institution(self, session, sample_speaker):
        """
        Test: Obtener speakers por institución

        Verifica el filtrado por institución
        """
        # Act
        results = speaker_controller.get_speakers_by_institution(
            session, "Universidad de Prueba"
        )

        # Assert
        assert results is not None

    def test_update_speaker_success(self, session, sample_speaker):
        """
        Test: Actualizar speaker exitosamente

        Verifica que la actualización funciona correctamente
        """
        # Arrange
        update_data = SpeakerUpdate(
            titulo_academico="Doctor en Teología Sistemática"
        )

        # Act
        updated_speaker = speaker_controller.update_speaker(
            session, sample_speaker.id_speaker, update_data, current_user_id=1
        )

        # Assert
        assert updated_speaker is not None
        assert updated_speaker["titulo_academico"] == "Doctor en Teología Sistemática"
        assert updated_speaker["nombres_completos"] == sample_speaker.nombres_completos  # No cambiado

    def test_delete_speaker_success(self, session, sample_speaker):
        """
        Test: Eliminar speaker exitosamente

        Verifica que la eliminación funciona correctamente
        """
        # Act
        result = speaker_controller.delete_speaker(
            session, sample_speaker.id_speaker, current_user_id=1
        )

        # Assert
        assert result is not None
        assert "message" in result

        # Verificar que no se puede encontrar después de eliminar
        deleted_speaker = speaker_controller.get_speaker_by_id(
            session, sample_speaker.id_speaker
        )
        assert deleted_speaker is None

    def test_check_speaker_exists_in_congress_exists(self, session, sample_speaker, sample_congress_new):
        """
        Test: Verificar si speaker existe en congreso cuando sí existe

        Verifica que retorna exists=True para speakers existentes
        """
        # Act
        result = speaker_controller.check_speaker_exists_in_congress(
            session, sample_speaker.nombres_completos, sample_congress_new.id_congreso
        )

        # Assert
        assert result is not None
        assert result["exists"] is True

    def test_check_speaker_exists_in_congress_not_exists(self, session, sample_congress_new):
        """
        Test: Verificar si speaker existe en congreso cuando no existe

        Verifica que retorna exists=False para speakers no existentes
        """
        # Act
        result = speaker_controller.check_speaker_exists_in_congress(
            session, "Speaker Inexistente", sample_congress_new.id_congreso
        )

        # Assert
        assert result is not None
        assert result["exists"] is False

    def test_get_frequent_speakers(self, session, sample_speaker):
        """
        Test: Obtener speakers frecuentes

        Verifica que la función de speakers frecuentes funciona
        """
        # Act
        result = speaker_controller.get_frequent_speakers(
            session, min_congresses=1, limit=10
        )

        # Assert
        assert result is not None
        assert "data" in result
        assert "frequent_speakers" in result["data"]

    def test_get_countries_with_speakers(self, session, sample_speaker):
        """
        Test: Obtener países con speakers

        Verifica que retorna los países correctos
        """
        # Act
        result = speaker_controller.get_countries_with_speakers(session)

        # Assert
        assert result is not None
        assert "data" in result
        assert "countries" in result["data"]
        assert "Ecuador" in result["data"]["countries"]

    def test_get_institutions_with_speakers(self, session, sample_speaker):
        """
        Test: Obtener instituciones con speakers

        Verifica que retorna las instituciones correctas
        """
        # Act
        result = speaker_controller.get_institutions_with_speakers(session)

        # Assert
        assert result is not None
        assert "data" in result
        assert "institutions" in result["data"]

    def test_get_speaker_statistics_by_congress(self, session, sample_speaker, sample_congress_new):
        """
        Test: Obtener estadísticas de speakers por congreso

        Verifica que las estadísticas se generan correctamente
        """
        # Act
        result = speaker_controller.get_speaker_statistics_by_congress(
            session, sample_congress_new.id_congreso
        )

        # Assert
        assert result is not None
        assert "data" in result
        assert "message" in result

    def test_get_speaker_summary(self, session, sample_speaker):
        """
        Test: Obtener resumen general de speakers

        Verifica que el resumen se genera correctamente
        """
        # Act
        result = speaker_controller.get_speaker_summary(session)

        # Assert
        assert result is not None
        assert "data" in result
        assert "message" in result

    def test_bulk_import_speakers_success(self, session, sample_congress_new):
        """
        Test: Importar speakers en lote exitosamente

        Verifica que la importación masiva funciona
        """
        # Arrange
        speakers_data = [
            SpeakerCreate(
                id_congreso=sample_congress_new.id_congreso,
                nombres_completos="Dr. Pedro García",
                titulo_academico="Doctor en Historia",
                institucion="Universidad A",
                pais="Argentina",
                tipo_speaker="panel"
            ),
            SpeakerCreate(
                id_congreso=sample_congress_new.id_congreso,
                nombres_completos="Dra. Ana López",
                titulo_academico="Doctora en Filosofía",
                institucion="Universidad B",
                pais="Chile",
                tipo_speaker="conferencia"
            )
        ]

        # Act
        result = speaker_controller.bulk_import_speakers(
            session, sample_congress_new.id_congreso, speakers_data, current_user_id=1
        )

        # Assert
        assert result is not None
        assert "data" in result
        assert result["data"]["count"] == 2

    def test_bulk_import_speakers_duplicate_names_should_fail(self, session, sample_congress_new):
        """
        Test: Importar speakers en lote con nombres duplicados

        Verifica que falla cuando hay nombres duplicados en el lote
        """
        # Arrange - Nombres duplicados en el lote
        speakers_data = [
            SpeakerCreate(
                id_congreso=sample_congress_new.id_congreso,
                nombres_completos="Dr. Speaker Duplicado",
                titulo_academico="Doctor",
                institucion="Universidad A",
                pais="País A",
                tipo_speaker="conferencia"
            ),
            SpeakerCreate(
                id_congreso=sample_congress_new.id_congreso,
                nombres_completos="Dr. Speaker Duplicado",  # Nombre duplicado
                titulo_academico="Doctor",
                institucion="Universidad B",
                pais="País B",
                tipo_speaker="panel"
            )
        ]

        # Act & Assert
        with pytest.raises(Exception):
            speaker_controller.bulk_import_speakers(
                session, sample_congress_new.id_congreso, speakers_data, current_user_id=1
            )

    def test_create_speaker_duplicate_name_in_congress_should_fail(self, session, sample_speaker_data):
        """
        Test: Intentar crear speaker con nombre duplicado en el mismo congreso

        Verifica que no se puede crear un speaker con nombre ya existente en el congreso
        """
        # Arrange - Crear primer speaker
        speaker_controller.create_speaker(session, sample_speaker_data, current_user_id=1)

        # Act & Assert - Intentar crear otro con el mismo nombre
        with pytest.raises(Exception):
            speaker_controller.create_speaker(session, sample_speaker_data, current_user_id=1)

    def test_create_speaker_nonexistent_congress_should_fail(self, session):
        """
        Test: Intentar crear speaker para congreso inexistente

        Verifica que falla cuando el congreso no existe
        """
        # Arrange
        invalid_speaker_data = SpeakerCreate(
            id_congreso=99999,  # Congreso inexistente
            nombres_completos="Dr. Speaker Inválido",
            titulo_academico="Doctor",
            institucion="Universidad Test",
            pais="País Test",
            tipo_speaker="keynote"
        )

        # Act & Assert
        with pytest.raises(Exception):
            speaker_controller.create_speaker(session, invalid_speaker_data, current_user_id=1)

    def test_update_speaker_not_found(self, session):
        """
        Test: Intentar actualizar speaker inexistente

        Verifica que lanza excepción cuando el speaker no existe
        """
        # Arrange
        update_data = SpeakerUpdate(titulo_academico="Nuevo título")

        # Act & Assert
        with pytest.raises(Exception):
            speaker_controller.update_speaker(
                session, 99999, update_data, current_user_id=1
            )

    def test_delete_speaker_not_found(self, session):
        """
        Test: Intentar eliminar speaker inexistente

        Verifica que lanza excepción cuando el speaker no existe
        """
        # Act & Assert
        with pytest.raises(Exception):
            speaker_controller.delete_speaker(session, 99999, current_user_id=1)