"""
Tests unitarios para CongressController

Verifican que los métodos del controller funcionen correctamente
usando una base de datos en memoria y datos de prueba.
"""
import pytest
from datetime import date, time

from src.controllers.congress_controller import CongressController
from sqlmodel import select
from src.models.congress import (
    CongressRequirement,
    CongressContent,
    CongressStatus,
    CongressCreate,
    CongressRequirementCreate,
    CongressContentCreate,
    CongressContentTopicRead,
    CongressUpdate,
    CongressRequirementUpdate,
)


class TestCongressControllerCreate:
    """Tests de creación de congresos"""

    def test_create_congress_with_requirements(
        self,
        session,
        sample_congress_data,
        sample_congress_requirements_data,
        sample_congress_contents_data,
        sample_category,
    ):
        """
        Test: Crear un congreso completo con requisitos y contenidos.
        Verifica que el congreso, requisito y contenidos existen en BD.
        """
        result = CongressController.create_congress_with_requirements(
            congress_data=sample_congress_data,
            requirements_data=sample_congress_requirements_data,
            contents_data=sample_congress_contents_data,
            db=session,
            current_user_id=1,
        )

        assert result is not None
        assert isinstance(result, dict)
        assert result["id"] is not None
        assert result["title"] == "Congreso de Inteligencia Artificial"

        congress_id = result["id"]

        # Verificar requisito creado
        requirement = session.exec(
            select(CongressRequirement).where(CongressRequirement.congress_id == congress_id)
        ).first()
        assert requirement is not None
        assert requirement.in_person_hours + requirement.autonomous_hours == 32  # 24 + 8
        assert requirement.min_quota == 30
        assert requirement.max_quota == 200

        # Verificar contenidos creados
        contents = session.exec(
            select(CongressContent).where(CongressContent.congress_id == congress_id)
        ).all()
        assert len(contents) == 2
        assert contents[0].title == "Fundamentos de IA"

        # Verificar topics en JSON
        import json
        topics = json.loads(contents[0].topics)
        assert len(topics) == 2

    def test_create_congress_invalid_category(
        self,
        session,
        sample_congress_requirements_data,
        sample_congress_contents_data,
    ):
        """
        Test: Crear un congreso con category_id inexistente lanza HTTPException.
        """
        from fastapi import HTTPException

        bad_data = CongressCreate(
            title="Congreso Sin Categoría",
            description="Test",
            place="Auditorio",
            congress_image="img.jpg",
            congress_image_detail="img_detail.jpg",
            category_id=99999,
            objectives=[],
            organizers=[],
            materials=[],
            target_audience=[],
        )
        with pytest.raises(HTTPException) as exc_info:
            CongressController.create_congress_with_requirements(
                congress_data=bad_data,
                requirements_data=sample_congress_requirements_data,
                contents_data=sample_congress_contents_data,
                db=session,
                current_user_id=1,
            )
        assert exc_info.value.status_code == 404

    def test_create_congress_json_fields_serialized(
        self,
        session,
        sample_congress_data,
        sample_congress_requirements_data,
        sample_congress_contents_data,
    ):
        """
        Test: Los campos JSON (objectives, organizers, etc.) se serializan correctamente.
        """
        result = CongressController.create_congress_with_requirements(
            congress_data=sample_congress_data,
            requirements_data=sample_congress_requirements_data,
            contents_data=sample_congress_contents_data,
            db=session,
            current_user_id=1,
        )

        assert isinstance(result["objectives"], list)
        assert isinstance(result["organizers"], list)
        assert isinstance(result["materials"], list)
        assert isinstance(result["target_audience"], list)
        assert "Explorar avances en IA" in result["objectives"]


class TestCongressControllerRead:
    """Tests de lectura y listado de congresos"""

    def test_get_all_congresses_empty(self, session):
        """
        Test: get_all_congresses devuelve paginación vacía cuando no hay datos.
        """
        result = CongressController.get_all_congresses(db=session)

        assert isinstance(result, dict)
        assert result["total"] == 0
        assert result["page"] == 1
        assert result["page_size"] == 10
        assert isinstance(result["congresses"], list)
        assert len(result["congresses"]) == 0

    def test_get_all_congresses_with_data(
        self,
        session,
        sample_congress_data,
        sample_congress_requirements_data,
        sample_congress_contents_data,
        sample_category,
    ):
        """
        Test: get_all_congresses devuelve lista paginada con datos correctos.
        """
        CongressController.create_congress_with_requirements(
            congress_data=sample_congress_data,
            requirements_data=sample_congress_requirements_data,
            contents_data=sample_congress_contents_data,
            db=session,
            current_user_id=1,
        )

        second = CongressCreate(
            title="Segundo Congreso de Robótica",
            description="Robótica aplicada",
            place="Aula Magna",
            congress_image="robotics.jpg",
            congress_image_detail="robotics_detail.jpg",
            category_id=sample_category.id,
            objectives=["Innovar en robótica"],
            organizers=["FISEI"],
            materials=["Robots"],
            target_audience=["Estudiantes"],
        )
        CongressController.create_congress_with_requirements(
            congress_data=second,
            requirements_data=sample_congress_requirements_data,
            contents_data=sample_congress_contents_data,
            db=session,
            current_user_id=1,
        )

        result = CongressController.get_all_congresses(db=session)

        assert result["total"] >= 2
        assert isinstance(result["congresses"], list)
        assert len(result["congresses"]) >= 2
        titles = [c["title"] for c in result["congresses"]]
        assert "Congreso de Inteligencia Artificial" in titles

    def test_get_all_congresses_pagination(
        self,
        session,
        sample_congress_data,
        sample_congress_requirements_data,
        sample_congress_contents_data,
        sample_category,
    ):
        """
        Test: La paginación devuelve el subconjunto correcto de resultados.
        """
        for i in range(5):
            data = CongressCreate(
                title=f"Congreso #{i}",
                description="Test",
                place="Auditorio",
                congress_image="img.jpg",
                congress_image_detail="img_detail.jpg",
                category_id=sample_category.id,
                objectives=[],
                organizers=[],
                materials=[],
                target_audience=[],
            )
            CongressController.create_congress_with_requirements(
                congress_data=data,
                requirements_data=sample_congress_requirements_data,
                contents_data=[],
                db=session,
                current_user_id=1,
            )

        page1 = CongressController.get_all_congresses(db=session, page=1, page_size=2)
        page2 = CongressController.get_all_congresses(db=session, page=2, page_size=2)

        assert len(page1["congresses"]) == 2
        assert len(page2["congresses"]) == 2
        assert page1["total"] == 5
        assert page1["congresses"][0]["id"] != page2["congresses"][0]["id"]

    def test_get_congress_by_id_found(
        self,
        session,
        sample_congress_data,
        sample_congress_requirements_data,
        sample_congress_contents_data,
    ):
        """
        Test: get_congress_by_id devuelve el congreso correcto cuando existe.
        """
        created = CongressController.create_congress_with_requirements(
            congress_data=sample_congress_data,
            requirements_data=sample_congress_requirements_data,
            contents_data=sample_congress_contents_data,
            db=session,
            current_user_id=1,
        )

        congress = CongressController.get_congress_by_id(created["id"], db=session)

        assert congress is not None
        assert congress["id"] == created["id"]
        assert congress["title"] == "Congreso de Inteligencia Artificial"
        assert congress["requirement"] is not None
        assert "congressSchedule" in congress["requirement"]
        assert len(congress["contents"]) == 2

    def test_get_congress_by_id_not_found(self, session):
        """
        Test: get_congress_by_id devuelve None cuando el ID no existe.
        """
        result = CongressController.get_congress_by_id(99999, db=session)
        assert result is None

    def test_get_congresses_by_category(
        self,
        session,
        sample_congress_data,
        sample_congress_requirements_data,
        sample_congress_contents_data,
        sample_category,
    ):
        """
        Test: get_congresses_by_category filtra correctamente por categoría.
        """
        CongressController.create_congress_with_requirements(
            congress_data=sample_congress_data,
            requirements_data=sample_congress_requirements_data,
            contents_data=sample_congress_contents_data,
            db=session,
            current_user_id=1,
        )

        congresses = CongressController.get_congresses_by_category(sample_category.id, db=session)

        assert isinstance(congresses, list)
        assert len(congresses) >= 1
        assert all(c["category_id"] == sample_category.id for c in congresses)

    def test_get_congresses_by_category_not_found(self, session):
        """
        Test: get_congresses_by_category lanza HTTPException cuando la categoría no existe.
        """
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            CongressController.get_congresses_by_category(99999, db=session)
        assert exc_info.value.status_code == 404

    def test_search_congresses_by_title(
        self,
        session,
        sample_congress_data,
        sample_congress_requirements_data,
        sample_congress_contents_data,
        sample_category,
    ):
        """
        Test: search_congresses_by_title devuelve coincidencias parciales case-insensitive.
        """
        CongressController.create_congress_with_requirements(
            congress_data=sample_congress_data,
            requirements_data=sample_congress_requirements_data,
            contents_data=sample_congress_contents_data,
            db=session,
            current_user_id=1,
        )
        second = CongressCreate(
            title="Congreso de Robótica Avanzada",
            description="Test",
            place="Auditorio",
            congress_image="r.jpg",
            congress_image_detail="r_detail.jpg",
            category_id=sample_category.id,
            objectives=[],
            organizers=[],
            materials=[],
            target_audience=[],
        )
        CongressController.create_congress_with_requirements(
            congress_data=second,
            requirements_data=sample_congress_requirements_data,
            contents_data=[],
            db=session,
            current_user_id=1,
        )

        results_ia = CongressController.search_congresses_by_title("inteligencia", db=session)
        results_all = CongressController.search_congresses_by_title("Congreso", db=session)
        results_none = CongressController.search_congresses_by_title("Blockchain", db=session)

        assert len(results_ia) == 1
        assert "Inteligencia Artificial" in results_ia[0]["title"]
        assert len(results_all) >= 2
        assert len(results_none) == 0

    def test_get_congress_requirement_fields(
        self,
        session,
        sample_congress_data,
        sample_congress_requirements_data,
        sample_congress_contents_data,
    ):
        """
        Test: El requisito del congreso incluye todos los campos esperados.
        """
        created = CongressController.create_congress_with_requirements(
            congress_data=sample_congress_data,
            requirements_data=sample_congress_requirements_data,
            contents_data=sample_congress_contents_data,
            db=session,
            current_user_id=1,
        )
        congress = CongressController.get_congress_by_id(created["id"], db=session)
        req = congress["requirement"]

        assert "registration" in req
        assert "congressSchedule" in req
        assert "location" in req
        assert "quota" in req
        assert "hours" in req
        assert "prices" in req
        assert req["hours"]["total"] == 32  # 24 + 8


class TestCongressControllerUpdate:
    """Tests de actualización de congresos"""

    def test_update_congress_title(
        self,
        session,
        sample_congress_data,
        sample_congress_requirements_data,
        sample_congress_contents_data,
    ):
        """
        Test: Actualizar solo el título del congreso funciona correctamente.
        """
        created = CongressController.create_congress_with_requirements(
            congress_data=sample_congress_data,
            requirements_data=sample_congress_requirements_data,
            contents_data=sample_congress_contents_data,
            db=session,
            current_user_id=1,
        )

        updated = CongressController.update_congress_with_requirements(
            congress_id=created["id"],
            db=session,
            congress_data=CongressUpdate(title="Congreso de IA y Big Data"),
        )

        assert updated["title"] == "Congreso de IA y Big Data"
        assert updated["description"] == sample_congress_data.description  # sin cambio

    def test_update_congress_requirements(
        self,
        session,
        sample_congress_data,
        sample_congress_requirements_data,
        sample_congress_contents_data,
    ):
        """
        Test: Actualizar requisitos del congreso se refleja en la BD.
        """
        created = CongressController.create_congress_with_requirements(
            congress_data=sample_congress_data,
            requirements_data=sample_congress_requirements_data,
            contents_data=sample_congress_contents_data,
            db=session,
            current_user_id=1,
        )

        updated = CongressController.update_congress_with_requirements(
            congress_id=created["id"],
            db=session,
            requirements_data=CongressRequirementUpdate(
                min_quota=50,
                max_quota=300,
                in_person_hours=30,
                autonomous_hours=10,
            ),
        )

        req = session.exec(
            select(CongressRequirement).where(CongressRequirement.congress_id == created["id"])
        ).first()
        assert req.min_quota == 50
        assert req.max_quota == 300
        assert req.in_person_hours + req.autonomous_hours == 40

    def test_update_congress_contents_replaced(
        self,
        session,
        sample_congress_data,
        sample_congress_requirements_data,
        sample_congress_contents_data,
    ):
        """
        Test: Al actualizar contenidos, los anteriores son reemplazados completamente.
        """
        created = CongressController.create_congress_with_requirements(
            congress_data=sample_congress_data,
            requirements_data=sample_congress_requirements_data,
            contents_data=sample_congress_contents_data,
            db=session,
            current_user_id=1,
        )

        new_contents = [
            CongressContentCreate(
                unit="Día Único",
                title="Sesión Especial",
                topics=[
                    CongressContentTopicRead(unit="1", title="Keynote final"),
                ],
            )
        ]

        CongressController.update_congress_with_requirements(
            congress_id=created["id"],
            db=session,
            contents_data=new_contents,
        )

        contents = session.exec(
            select(CongressContent).where(CongressContent.congress_id == created["id"])
        ).all()
        assert len(contents) == 1
        assert contents[0].title == "Sesión Especial"

    def test_update_congress_not_found(self, session):
        """
        Test: Actualizar un congreso inexistente lanza ValueError.
        """
        with pytest.raises(ValueError, match="Congress not found"):
            CongressController.update_congress_with_requirements(
                congress_id=99999,
                db=session,
                congress_data=CongressUpdate(title="Nuevo título"),
            )


class TestCongressControllerDelete:
    """Tests de eliminación de congresos"""

    def test_delete_congress_soft_delete(
        self,
        session,
        sample_congress_data,
        sample_congress_requirements_data,
        sample_congress_contents_data,
    ):
        """
        Test: delete_congress realiza soft delete (status → INACTIVO).
        """
        created = CongressController.create_congress_with_requirements(
            congress_data=sample_congress_data,
            requirements_data=sample_congress_requirements_data,
            contents_data=sample_congress_contents_data,
            db=session,
            current_user_id=1,
        )
        congress_id = created["id"]

        CongressController.delete_congress(congress_id, db=session)

        deleted = CongressController.get_congress_by_id(congress_id, db=session)
        assert deleted["status"] == CongressStatus.INACTIVO

    def test_delete_congress_not_found(self, session):
        """
        Test: Eliminar un congreso inexistente lanza ValueError.
        """
        with pytest.raises(ValueError, match="Congress not found"):
            CongressController.delete_congress(99999, db=session)

    def test_delete_congress_already_deleted(
        self,
        session,
        sample_congress_data,
        sample_congress_requirements_data,
        sample_congress_contents_data,
    ):
        """
        Test: Eliminar un congreso ya inactivo lanza ValueError.
        """
        created = CongressController.create_congress_with_requirements(
            congress_data=sample_congress_data,
            requirements_data=sample_congress_requirements_data,
            contents_data=sample_congress_contents_data,
            db=session,
            current_user_id=1,
        )

        CongressController.delete_congress(created["id"], db=session)

        with pytest.raises(ValueError, match="already deleted"):
            CongressController.delete_congress(created["id"], db=session)

    def test_deleted_congress_excluded_from_active_list(
        self,
        session,
        sample_congress_data,
        sample_congress_requirements_data,
        sample_congress_contents_data,
    ):
        """
        Test: Los congresos eliminados no aparecen en el listado activo.
        """
        created = CongressController.create_congress_with_requirements(
            congress_data=sample_congress_data,
            requirements_data=sample_congress_requirements_data,
            contents_data=sample_congress_contents_data,
            db=session,
            current_user_id=1,
        )

        CongressController.delete_congress(created["id"], db=session)

        result = CongressController.get_all_congresses(db=session, status=CongressStatus.ACTIVO)
        active_ids = [c["id"] for c in result["congresses"]]
        assert created["id"] not in active_ids

    def test_deleted_congress_appears_in_inactive_list(
        self,
        session,
        sample_congress_data,
        sample_congress_requirements_data,
        sample_congress_contents_data,
    ):
        """
        Test: Los congresos eliminados aparecen en el listado inactivo.
        """
        created = CongressController.create_congress_with_requirements(
            congress_data=sample_congress_data,
            requirements_data=sample_congress_requirements_data,
            contents_data=sample_congress_contents_data,
            db=session,
            current_user_id=1,
        )

        CongressController.delete_congress(created["id"], db=session)

        result = CongressController.get_all_congresses(db=session, status=CongressStatus.INACTIVO)
        inactive_ids = [c["id"] for c in result["congresses"]]
        assert created["id"] in inactive_ids
