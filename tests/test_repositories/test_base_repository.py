"""
Tests de regresión para BaseRepository (A7, A8).

A7: create/update/delete/bulk_create no deben hacer commit por su cuenta —
la transacción es responsabilidad exclusiva de quien los llama (el
controller), para poder componer varias escrituras en una sola operación
atómica (como create_congress_with_relations) sin un commit intermedio
inesperado.

A8: handle_repository_errors no debe destruir tipos de excepción que un
llamador necesite inspeccionar (HTTPException, ValueError).
"""
import pytest
from fastapi import HTTPException

from src.repositories.sponsor_repository import sponsor_repository
from src.repositories.base_repository import RepositoryError, handle_repository_errors
from src.models.sponsor_model import SponsorCreate


class TestBaseRepositoryNoImplicitCommit:
    def test_create_does_not_commit_without_caller_commit(self, session):
        """
        Test de regresión (A7): repository.create() solo debe hacer flush,
        no commit. Si el llamador nunca commitea (p.ej. porque la validación
        posterior falla y se hace rollback), el registro no debe persistir.
        """
        sponsor_data = SponsorCreate(
            nombre="Sponsor Sin Commit",
            sitio_web="https://example.com",
            descripcion="No debe persistir tras un rollback"
        )

        created = sponsor_repository.create(session, obj_in=sponsor_data)
        assert created.id_sponsor is not None  # flush() ya asignó el id

        # Simula que el controller decide abortar la operación
        session.rollback()

        from sqlmodel import select
        from src.models.sponsor_model import Sponsor
        remaining = session.exec(
            select(Sponsor).where(Sponsor.nombre == "Sponsor Sin Commit")
        ).all()
        assert remaining == []

    def test_create_persists_when_caller_commits(self, session):
        """El flujo normal (controller hace commit) sigue funcionando."""
        sponsor_data = SponsorCreate(
            nombre="Sponsor Con Commit",
            sitio_web="https://example.com",
            descripcion="Debe persistir tras el commit del caller"
        )

        created = sponsor_repository.create(session, obj_in=sponsor_data)
        session.commit()

        from sqlmodel import select
        from src.models.sponsor_model import Sponsor
        found = session.exec(
            select(Sponsor).where(Sponsor.id_sponsor == created.id_sponsor)
        ).first()
        assert found is not None
        assert found.nombre == "Sponsor Con Commit"


class TestHandleRepositoryErrors:
    def test_lets_http_exception_pass_through_unmodified(self):
        """Test de regresión (A8): una HTTPException no debe envolverse en RepositoryError."""

        @handle_repository_errors
        def raises_http_exception():
            raise HTTPException(status_code=404, detail="not found")

        with pytest.raises(HTTPException) as exc_info:
            raises_http_exception()
        assert exc_info.value.status_code == 404

    def test_lets_value_error_pass_through_unmodified(self):
        """Test de regresión (A8): un ValueError no debe envolverse en RepositoryError."""

        @handle_repository_errors
        def raises_value_error():
            raise ValueError("bad input")

        with pytest.raises(ValueError, match="bad input"):
            raises_value_error()

    def test_wraps_unexpected_exception_with_chained_cause(self):
        """Un error inesperado se envuelve en RepositoryError, pero conserva la causa original (`from e`)."""

        @handle_repository_errors
        def raises_unexpected():
            raise RuntimeError("db exploded")

        with pytest.raises(RepositoryError) as exc_info:
            raises_unexpected()

        assert isinstance(exc_info.value.__cause__, RuntimeError)
        assert "db exploded" in str(exc_info.value.__cause__)
