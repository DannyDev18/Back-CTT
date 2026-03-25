"""
Tests unitarios para el CongresoSponsorController

Estos tests verifican que los métodos del controller de sponsorships
(relaciones congreso-sponsor) funcionen correctamente.
"""
import pytest
from decimal import Decimal
from src.controllers.congreso_sponsor_controller import congreso_sponsor_controller
from src.models.congreso_sponsor_model import CongresoSponsorCreate, CongresoSponsorUpdate


class TestCongresoSponsorController:
    """Suite de tests para CongresoSponsorController"""

    def test_create_sponsorship_success(self, session, sample_congreso_sponsor_data):
        """
        Test: Crear un sponsorship exitosamente

        Verifica que el sponsorship se crea y se guarda correctamente en la BD
        """
        # Act
        created_sponsorship = congreso_sponsor_controller.create_sponsorship(
            session, sample_congreso_sponsor_data, current_user_id=1
        )

        # Assert
        assert created_sponsorship is not None
        assert created_sponsorship["id_congreso"] == sample_congreso_sponsor_data.id_congreso
        assert created_sponsorship["id_sponsor"] == sample_congreso_sponsor_data.id_sponsor
        assert created_sponsorship["categoria"] == "oro"
        assert created_sponsorship["aporte"] == 5000.0

    def test_get_sponsorship_found(self, session, sample_congreso_sponsor):
        """
        Test: Buscar sponsorship por IDs cuando existe

        Verifica que retorna el sponsorship correcto cuando existe
        """
        # Act
        found_sponsorship = congreso_sponsor_controller.get_sponsorship(
            session,
            sample_congreso_sponsor.id_congreso,
            sample_congreso_sponsor.id_sponsor
        )

        # Assert
        assert found_sponsorship is not None
        assert found_sponsorship["id_congreso"] == sample_congreso_sponsor.id_congreso
        assert found_sponsorship["id_sponsor"] == sample_congreso_sponsor.id_sponsor

    def test_get_sponsorship_not_found(self, session):
        """
        Test: Buscar sponsorship por IDs cuando no existe

        Verifica que retorna None cuando el sponsorship no existe
        """
        # Act
        found_sponsorship = congreso_sponsor_controller.get_sponsorship(
            session, 99999, 99999
        )

        # Assert
        assert found_sponsorship is None

    def test_get_sponsorships_by_congress(self, session, sample_congreso_sponsor, sample_congress_new):
        """
        Test: Obtener sponsorships por congreso

        Verifica que retorna los sponsorships del congreso correcto
        """
        # Act
        sponsorships = congreso_sponsor_controller.get_sponsorships_by_congress(
            session, sample_congress_new.id_congreso
        )

        # Assert
        assert sponsorships is not None
        assert len(sponsorships) >= 1
        assert all(s["id_congreso"] == sample_congress_new.id_congreso for s in sponsorships)

    def test_get_sponsorships_by_sponsor(self, session, sample_congreso_sponsor, sample_sponsor):
        """
        Test: Obtener sponsorships por sponsor

        Verifica que retorna los sponsorships del sponsor correcto
        """
        # Act
        sponsorships = congreso_sponsor_controller.get_sponsorships_by_sponsor(
            session, sample_sponsor.id_sponsor
        )

        # Assert
        assert sponsorships is not None
        assert len(sponsorships) >= 1
        assert all(s["id_sponsor"] == sample_sponsor.id_sponsor for s in sponsorships)

    def test_get_all_sponsorships_pagination(self, session, sample_congreso_sponsor):
        """
        Test: Obtener todos los sponsorships con paginación

        Verifica que la paginación funciona correctamente
        """
        # Act
        result = congreso_sponsor_controller.get_all_sponsorships(
            session, page=1, page_size=10
        )

        # Assert
        assert result is not None
        assert "sponsorships" in result
        assert "total" in result
        assert "page" in result
        assert result["page"] == 1
        assert len(result["sponsorships"]) >= 1

    def test_get_sponsorships_by_category(self, session, sample_congreso_sponsor):
        """
        Test: Obtener sponsorships por categoría

        Verifica el filtrado por categoría
        """
        # Act
        sponsorships = congreso_sponsor_controller.get_sponsorships_by_category(
            session, "plata"
        )

        # Assert
        assert sponsorships is not None
        assert all(s["categoria"] == "plata" for s in sponsorships)

    def test_update_sponsorship_success(self, session, sample_congreso_sponsor):
        """
        Test: Actualizar sponsorship exitosamente

        Verifica que la actualización funciona correctamente
        """
        # Arrange
        update_data = CongresoSponsorUpdate(
            aporte=Decimal("4000.00")
        )

        # Act
        updated_sponsorship = congreso_sponsor_controller.update_sponsorship(
            session,
            sample_congreso_sponsor.id_congreso,
            sample_congreso_sponsor.id_sponsor,
            update_data,
            current_user_id=1
        )

        # Assert
        assert updated_sponsorship is not None
        assert updated_sponsorship["aporte"] == 4000.0
        assert updated_sponsorship["categoria"] == sample_congreso_sponsor.categoria  # No cambiado

    def test_delete_sponsorship_success(self, session, sample_congreso_sponsor):
        """
        Test: Eliminar sponsorship exitosamente

        Verifica que la eliminación funciona correctamente
        """
        # Act
        result = congreso_sponsor_controller.delete_sponsorship(
            session,
            sample_congreso_sponsor.id_congreso,
            sample_congreso_sponsor.id_sponsor,
            current_user_id=1
        )

        # Assert
        assert result is not None
        assert "message" in result

        # Verificar que no se puede encontrar después de eliminar
        deleted_sponsorship = congreso_sponsor_controller.get_sponsorship(
            session,
            sample_congreso_sponsor.id_congreso,
            sample_congreso_sponsor.id_sponsor
        )
        assert deleted_sponsorship is None

    def test_check_sponsorship_exists_true(self, session, sample_congreso_sponsor):
        """
        Test: Verificar si sponsorship existe cuando sí existe

        Verifica que retorna exists=True para sponsorships existentes
        """
        # Act
        result = congreso_sponsor_controller.check_sponsorship_exists(
            session,
            sample_congreso_sponsor.id_congreso,
            sample_congreso_sponsor.id_sponsor
        )

        # Assert
        assert result is not None
        assert result["exists"] is True

    def test_check_sponsorship_exists_false(self, session):
        """
        Test: Verificar si sponsorship existe cuando no existe

        Verifica que retorna exists=False para sponsorships no existentes
        """
        # Act
        result = congreso_sponsor_controller.check_sponsorship_exists(
            session, 99999, 99999
        )

        # Assert
        assert result is not None
        assert result["exists"] is False

    def test_get_top_contributors_by_congress(self, session, sample_congreso_sponsor, sample_congress_new):
        """
        Test: Obtener top contribuyentes por congreso

        Verifica que la función de top contributors funciona
        """
        # Act
        result = congreso_sponsor_controller.get_top_contributors_by_congress(
            session, sample_congress_new.id_congreso, limit=5
        )

        # Assert
        assert result is not None
        assert "data" in result
        assert "top_contributors" in result["data"]

    def test_get_sponsorship_statistics_by_congress(self, session, sample_congreso_sponsor, sample_congress_new):
        """
        Test: Obtener estadísticas de sponsorship por congreso

        Verifica que las estadísticas se generan correctamente
        """
        # Act
        result = congreso_sponsor_controller.get_sponsorship_statistics_by_congress(
            session, sample_congress_new.id_congreso
        )

        # Assert
        assert result is not None
        assert "data" in result
        assert "message" in result

    def test_get_congress_funding_summary(self, session, sample_congreso_sponsor):
        """
        Test: Obtener resumen de financiamiento

        Verifica que el resumen de financiamiento se genera correctamente
        """
        # Act
        result = congreso_sponsor_controller.get_congress_funding_summary(session)

        # Assert
        assert result is not None
        assert "data" in result
        assert "funding_summary" in result["data"]

    def test_get_sponsor_loyalty_analysis(self, session, sample_congreso_sponsor):
        """
        Test: Análisis de lealtad de sponsors

        Verifica que el análisis de lealtad funciona
        """
        # Act
        result = congreso_sponsor_controller.get_sponsor_loyalty_analysis(
            session, min_sponsorships=1
        )

        # Assert
        assert result is not None
        assert "data" in result
        assert "loyal_sponsors" in result["data"]

    def test_get_category_trends(self, session, sample_congreso_sponsor):
        """
        Test: Análisis de tendencias por categoría

        Verifica que el análisis de tendencias funciona
        """
        # Act
        result = congreso_sponsor_controller.get_category_trends(session)

        # Assert
        assert result is not None
        assert "data" in result
        assert "trends" in result["data"]

    def test_get_sponsorship_summary(self, session, sample_congreso_sponsor):
        """
        Test: Obtener resumen general de sponsorships

        Verifica que el resumen se genera correctamente
        """
        # Act
        result = congreso_sponsor_controller.get_sponsorship_summary(session)

        # Assert
        assert result is not None
        assert "data" in result
        assert "message" in result

    def test_bulk_create_sponsorships_success(self, session, sample_congress_new):
        """
        Test: Crear sponsorships en lote exitosamente

        Verifica que la creación masiva funciona
        """
        # Arrange - Crear sponsors adicionales
        from src.models.sponsor_model import Sponsor
        sponsor1 = Sponsor(
            nombre="Sponsor Lote 1",
            logo_url="https://example.com/sponsor1_logo.png",
            sitio_web="https://sponsor1.com",
            descripcion="Primer sponsor del lote"
        )
        sponsor2 = Sponsor(
            nombre="Sponsor Lote 2",
            logo_url="https://example.com/sponsor2_logo.png",
            sitio_web="https://sponsor2.com",
            descripcion="Segundo sponsor del lote"
        )
        session.add_all([sponsor1, sponsor2])
        session.commit()
        session.refresh(sponsor1)
        session.refresh(sponsor2)

        sponsorships_data = [
            CongresoSponsorCreate(
                id_congreso=sample_congress_new.id_congreso,
                id_sponsor=sponsor1.id_sponsor,
                categoria="oro",
                aporte=Decimal("5000.00")
            ),
            CongresoSponsorCreate(
                id_congreso=sample_congress_new.id_congreso,
                id_sponsor=sponsor2.id_sponsor,
                categoria="plata",
                aporte=Decimal("3000.00")
            )
        ]

        # Act
        result = congreso_sponsor_controller.bulk_create_sponsorships(
            session, sample_congress_new.id_congreso, sponsorships_data, current_user_id=1
        )

        # Assert
        assert result is not None
        assert "data" in result
        assert result["data"]["count"] == 2

    def test_bulk_create_sponsorships_duplicate_sponsors_should_fail(self, session, sample_congress_new, sample_sponsor):
        """
        Test: Crear sponsorships en lote con sponsors duplicados

        Verifica que falla cuando hay sponsors duplicados en el lote
        """
        # Arrange - Sponsors duplicados en el lote
        sponsorships_data = [
            CongresoSponsorCreate(
                id_congreso=sample_congress_new.id_congreso,
                id_sponsor=sample_sponsor.id_sponsor,
                categoria="oro",
                aporte=Decimal("5000.00")
            ),
            CongresoSponsorCreate(
                id_congreso=sample_congress_new.id_congreso,
                id_sponsor=sample_sponsor.id_sponsor,  # Duplicado
                categoria="plata",
                aporte=Decimal("3000.00")
            )
        ]

        # Act & Assert
        with pytest.raises(Exception):
            congreso_sponsor_controller.bulk_create_sponsorships(
                session, sample_congress_new.id_congreso, sponsorships_data, current_user_id=1
            )

    def test_create_sponsorship_duplicate_should_fail(self, session, sample_congreso_sponsor_data):
        """
        Test: Intentar crear sponsorship duplicado

        Verifica que no se puede crear un sponsorship duplicado
        """
        # Arrange - Crear primer sponsorship
        congreso_sponsor_controller.create_sponsorship(
            session, sample_congreso_sponsor_data, current_user_id=1
        )

        # Act & Assert - Intentar crear duplicado
        with pytest.raises(Exception):
            congreso_sponsor_controller.create_sponsorship(
                session, sample_congreso_sponsor_data, current_user_id=1
            )

    def test_create_sponsorship_nonexistent_congress_should_fail(self, session, sample_sponsor):
        """
        Test: Intentar crear sponsorship para congreso inexistente

        Verifica que falla cuando el congreso no existe
        """
        # Arrange
        invalid_sponsorship_data = CongresoSponsorCreate(
            id_congreso=99999,  # Congreso inexistente
            id_sponsor=sample_sponsor.id_sponsor,
            categoria="oro",
            aporte=Decimal("5000.00")
        )

        # Act & Assert
        with pytest.raises(Exception):
            congreso_sponsor_controller.create_sponsorship(
                session, invalid_sponsorship_data, current_user_id=1
            )

    def test_create_sponsorship_nonexistent_sponsor_should_fail(self, session, sample_congress_new):
        """
        Test: Intentar crear sponsorship para sponsor inexistente

        Verifica que falla cuando el sponsor no existe
        """
        # Arrange
        invalid_sponsorship_data = CongresoSponsorCreate(
            id_congreso=sample_congress_new.id_congreso,
            id_sponsor=99999,  # Sponsor inexistente
            categoria="oro",
            aporte=Decimal("5000.00")
        )

        # Act & Assert
        with pytest.raises(Exception):
            congreso_sponsor_controller.create_sponsorship(
                session, invalid_sponsorship_data, current_user_id=1
            )

    def test_update_sponsorship_not_found(self, session):
        """
        Test: Intentar actualizar sponsorship inexistente

        Verifica que lanza excepción cuando el sponsorship no existe
        """
        # Arrange
        update_data = CongresoSponsorUpdate(aporte=Decimal("4000.00"))

        # Act & Assert
        with pytest.raises(Exception):
            congreso_sponsor_controller.update_sponsorship(
                session, 99999, 99999, update_data, current_user_id=1
            )

    def test_delete_sponsorship_not_found(self, session):
        """
        Test: Intentar eliminar sponsorship inexistente

        Verifica que lanza excepción cuando el sponsorship no existe
        """
        # Act & Assert
        with pytest.raises(Exception):
            congreso_sponsor_controller.delete_sponsorship(
                session, 99999, 99999, current_user_id=1
            )

    def test_get_all_sponsorships_with_filters(self, session, sample_congreso_sponsor):
        """
        Test: Obtener sponsorships con múltiples filtros

        Verifica que los filtros funcionan correctamente
        """
        # Act
        result = congreso_sponsor_controller.get_all_sponsorships(
            session,
            page=1,
            page_size=10,
            categoria="plata",
            min_aporte=Decimal("1000.00"),
            max_aporte=Decimal("5000.00")
        )

        # Assert
        assert result is not None
        assert "sponsorships" in result
        for sponsorship in result["sponsorships"]:
            assert sponsorship["categoria"] == "plata"
            assert 1000.0 <= sponsorship["aporte"] <= 5000.0