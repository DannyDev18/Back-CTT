"""
Tests unitarios para el SponsorController

Estos tests verifican que los métodos del controller de sponsors
funcionen correctamente.
"""
import pytest
from src.controllers.sponsor_controller import sponsor_controller
from src.models.sponsor_model import SponsorCreate, SponsorUpdate


class TestSponsorController:
    """Suite de tests para SponsorController"""

    def test_create_sponsor_success(self, session, sample_sponsor_data):
        """
        Test: Crear un sponsor exitosamente

        Verifica que el sponsor se crea y se guarda correctamente en la BD
        """
        # Act
        created_sponsor = sponsor_controller.create_sponsor(
            session, sample_sponsor_data, current_user_id=1
        )

        # Assert
        assert created_sponsor is not None
        assert created_sponsor["id_sponsor"] is not None
        assert created_sponsor["nombre"] == "Editorial Teológica Internacional"
        assert created_sponsor["sitio_web"] == "https://editorialteologica.com"

    def test_get_sponsor_by_id_found(self, session, sample_sponsor):
        """
        Test: Buscar sponsor por ID cuando existe

        Verifica que retorna el sponsor correcto cuando existe
        """
        # Act
        found_sponsor = sponsor_controller.get_sponsor_by_id(
            session, sample_sponsor.id_sponsor
        )

        # Assert
        assert found_sponsor is not None
        assert found_sponsor["id_sponsor"] == sample_sponsor.id_sponsor
        assert found_sponsor["nombre"] == sample_sponsor.nombre

    def test_get_sponsor_by_id_not_found(self, session):
        """
        Test: Buscar sponsor por ID cuando no existe

        Verifica que retorna None cuando el sponsor no existe
        """
        # Act
        found_sponsor = sponsor_controller.get_sponsor_by_id(session, 99999)

        # Assert
        assert found_sponsor is None

    def test_get_all_sponsors_pagination(self, session, sample_sponsor):
        """
        Test: Obtener todos los sponsors con paginación

        Verifica que la paginación funciona correctamente
        """
        # Act
        result = sponsor_controller.get_all_sponsors(
            session, page=1, page_size=10
        )

        # Assert
        assert result is not None
        assert "sponsors" in result
        assert "total" in result
        assert "page" in result
        assert result["page"] == 1
        assert len(result["sponsors"]) >= 1

    def test_search_sponsors_by_name(self, session, sample_sponsor):
        """
        Test: Buscar sponsors por nombre

        Verifica que la búsqueda por nombre funciona
        """
        # Act
        results = sponsor_controller.search_sponsors_by_name(
            session, search_term="Prueba", limit=10
        )

        # Assert
        assert results is not None
        # Debería encontrar al menos nuestro sponsor de prueba

    def test_update_sponsor_success(self, session, sample_sponsor):
        """
        Test: Actualizar sponsor exitosamente

        Verifica que la actualización funciona correctamente
        """
        # Arrange
        update_data = SponsorUpdate(
            descripcion="Nueva descripción actualizada"
        )

        # Act
        updated_sponsor = sponsor_controller.update_sponsor(
            session, sample_sponsor.id_sponsor, update_data, current_user_id=1
        )

        # Assert
        assert updated_sponsor is not None
        assert updated_sponsor["descripcion"] == "Nueva descripción actualizada"
        assert updated_sponsor["nombre"] == sample_sponsor.nombre  # No cambiado

    def test_delete_sponsor_success(self, session, sample_sponsor):
        """
        Test: Eliminar sponsor exitosamente

        Verifica que la eliminación funciona correctamente
        """
        # Act
        result = sponsor_controller.delete_sponsor(
            session, sample_sponsor.id_sponsor, current_user_id=1
        )

        # Assert
        assert result is not None
        assert "message" in result

        # Verificar que no se puede encontrar después de eliminar
        deleted_sponsor = sponsor_controller.get_sponsor_by_id(
            session, sample_sponsor.id_sponsor
        )
        assert deleted_sponsor is None

    def test_check_name_availability_available(self, session):
        """
        Test: Verificar disponibilidad de nombre cuando está disponible

        Verifica que retorna available=True para nombres no existentes
        """
        # Act
        result = sponsor_controller.check_name_availability(
            session, "Sponsor Inexistente"
        )

        # Assert
        assert result is not None
        assert result["available"] is True

    def test_check_name_availability_not_available(self, session, sample_sponsor):
        """
        Test: Verificar disponibilidad de nombre cuando no está disponible

        Verifica que retorna available=False para nombres existentes
        """
        # Act
        result = sponsor_controller.check_name_availability(
            session, sample_sponsor.nombre
        )

        # Assert
        assert result is not None
        assert result["available"] is False

    def test_get_sponsor_statistics(self, session, sample_sponsor):
        """
        Test: Obtener estadísticas de sponsor

        Verifica que las estadísticas se generan correctamente
        """
        # Act
        result = sponsor_controller.get_sponsor_statistics(
            session, sample_sponsor.id_sponsor
        )

        # Assert
        assert result is not None
        assert "data" in result
        assert "message" in result

    def test_get_sponsor_summary(self, session, sample_sponsor):
        """
        Test: Obtener resumen general de sponsors

        Verifica que el resumen se genera correctamente
        """
        # Act
        result = sponsor_controller.get_sponsor_summary(session)

        # Assert
        assert result is not None
        assert "data" in result
        assert "message" in result

    def test_get_top_sponsors_by_contribution(self, session, sample_sponsor):
        """
        Test: Obtener top sponsors por contribución

        Verifica que la función de top contributors funciona
        """
        # Act
        result = sponsor_controller.get_top_sponsors_by_contribution(
            session, limit=5
        )

        # Assert
        assert result is not None
        assert "data" in result
        assert "top_sponsors" in result["data"]

    def test_get_sponsors_without_recent_activity(self, session, sample_sponsor):
        """
        Test: Obtener sponsors sin actividad reciente

        Verifica que la función de sponsors inactivos funciona
        """
        # Act
        result = sponsor_controller.get_sponsors_without_recent_activity(
            session, years_threshold=2
        )

        # Assert
        assert result is not None
        assert "data" in result
        assert "inactive_sponsors" in result["data"]

    def test_get_sponsors_by_website_domain(self, session):
        """
        Test: Obtener sponsors por dominio web

        Verifica el filtrado por dominio
        """
        # Arrange - Crear sponsor con dominio específico
        sponsor_data = SponsorCreate(
            nombre="Sponsor Dominio Test",
            sitio_web="https://testcompany.com",
            descripcion="Sponsor para test de dominio"
        )
        sponsor_controller.create_sponsor(session, sponsor_data, current_user_id=1)

        # Act
        results = sponsor_controller.get_sponsors_by_website_domain(
            session, "testcompany.com"
        )

        # Assert
        assert results is not None
        assert len(results) >= 1

    def test_bulk_import_sponsors_success(self, session):
        """
        Test: Importar sponsors en lote exitosamente

        Verifica que la importación masiva funciona
        """
        # Arrange
        sponsors_data = [
            SponsorCreate(
                nombre="Sponsor Lote 1",
                sitio_web="https://sponsor1.com",
                descripcion="Primer sponsor del lote"
            ),
            SponsorCreate(
                nombre="Sponsor Lote 2",
                sitio_web="https://sponsor2.com",
                descripcion="Segundo sponsor del lote"
            )
        ]

        # Act
        result = sponsor_controller.bulk_import_sponsors(
            session, sponsors_data, current_user_id=1
        )

        # Assert
        assert result is not None
        assert "data" in result
        assert result["data"]["count"] == 2

    def test_bulk_import_sponsors_duplicate_names_should_fail(self, session):
        """
        Test: Importar sponsors en lote con nombres duplicados

        Verifica que falla cuando hay nombres duplicados en el lote
        """
        # Arrange - Nombres duplicados en el lote
        sponsors_data = [
            SponsorCreate(
                nombre="Sponsor Duplicado",
                sitio_web="https://sponsor1.com",
                descripcion="Primer sponsor"
            ),
            SponsorCreate(
                nombre="Sponsor Duplicado",  # Nombre duplicado
                sitio_web="https://sponsor2.com",
                descripcion="Segundo sponsor"
            )
        ]

        # Act & Assert
        with pytest.raises(Exception):
            sponsor_controller.bulk_import_sponsors(
                session, sponsors_data, current_user_id=1
            )

    def test_bulk_import_sponsors_existing_name_should_fail(self, session, sample_sponsor):
        """
        Test: Importar sponsors en lote con nombre ya existente en BD

        Verifica que falla cuando un nombre ya existe en la BD
        """
        # Arrange - Usar nombre existente
        sponsors_data = [
            SponsorCreate(
                nombre=sample_sponsor.nombre,  # Nombre ya existente
                sitio_web="https://sponsor1.com",
                descripcion="Sponsor con nombre existente"
            )
        ]

        # Act & Assert
        with pytest.raises(Exception):
            sponsor_controller.bulk_import_sponsors(
                session, sponsors_data, current_user_id=1
            )

    def test_create_sponsor_duplicate_name_should_fail(self, session, sample_sponsor):
        """
        Test: Intentar crear sponsor con nombre duplicado

        Verifica que no se puede crear un sponsor con nombre ya existente
        """
        # Arrange
        duplicate_sponsor_data = SponsorCreate(
            nombre=sample_sponsor.nombre,  # Nombre duplicado
            sitio_web="https://different-site.com",
            descripcion="Intento de duplicado"
        )

        # Act & Assert
        with pytest.raises(Exception):
            sponsor_controller.create_sponsor(
                session, duplicate_sponsor_data, current_user_id=1
            )

    def test_update_sponsor_not_found(self, session):
        """
        Test: Intentar actualizar sponsor inexistente

        Verifica que lanza excepción cuando el sponsor no existe
        """
        # Arrange
        update_data = SponsorUpdate(descripcion="Nueva descripción")

        # Act & Assert
        with pytest.raises(Exception):
            sponsor_controller.update_sponsor(
                session, 99999, update_data, current_user_id=1
            )

    def test_delete_sponsor_not_found(self, session):
        """
        Test: Intentar eliminar sponsor inexistente

        Verifica que lanza excepción cuando el sponsor no existe
        """
        # Act & Assert
        with pytest.raises(Exception):
            sponsor_controller.delete_sponsor(session, 99999, current_user_id=1)