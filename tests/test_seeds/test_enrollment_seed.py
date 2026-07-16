"""
Tests de regresión para el seed de inscripciones (enrollment_seed).

Cubre el bug A6 detectado durante la verificación en vivo del backend:
con pocos usuarios de plataforma y un congreso futuro, `random.randint`
recibía un rango vacío y crasheaba el arranque de la API (los seeds
corren en el lifespan de FastAPI).
"""
from datetime import date, timedelta

import pytest

from src.utils.seeds import enrollment_seed


@pytest.fixture
def few_users(session):
    """Solo 2 usuarios de plataforma: dispara len(users)//2 < 10."""
    from src.models.user_platform import UserPlatform, UserPlatformType

    users = []
    for i in range(2):
        user = UserPlatform(
            identification=f"100000000{i}",
            first_name=f"Usuario{i}",
            first_last_name="Prueba",
            cellphone="0987654321",
            email=f"seed.user{i}@example.com",
            type=UserPlatformType.ESTUDIANTE,
            password="hashed_password_123"
        )
        session.add(user)
        users.append(user)
    session.commit()
    for user in users:
        session.refresh(user)
    return users


@pytest.fixture
def future_congress(session):
    """Congreso con fecha_inicio en el futuro (dispara la rama 'congress futuro')."""
    from src.models.congress_model import Congress

    future_date = date.today() + timedelta(days=180)
    congress = Congress(
        nombre="Congreso Futuro Seed Test",
        edicion="SEED-FUT",
        anio=future_date.year,
        fecha_inicio=future_date,
        fecha_fin=future_date + timedelta(days=2),
        descripcion_general="Congreso de prueba para el seed",
        poster_cover_url="https://example.com/p.jpg"
    )
    session.add(congress)
    session.commit()
    session.refresh(congress)
    return congress


class TestEnrollmentSeed:
    def test_seed_enrollments_with_few_users_and_future_congress_does_not_crash(
        self, session, few_users, future_congress, monkeypatch
    ):
        """
        Test de regresión (A6): antes, random.randint(10, min(150, len(users)//2))
        con 2 usuarios (len(users)//2 == 1) lanzaba
        ValueError: empty range for randrange(). Debe correr sin excepción.
        """
        monkeypatch.setattr(enrollment_seed, "engine", session.get_bind())

        # No debe lanzar ValueError
        enrollment_seed.seed_enrollments()

        from sqlmodel import select
        from src.models.enrollment import Enrollment

        enrollments = session.exec(
            select(Enrollment).where(Enrollment.id_congress == future_congress.id_congreso)
        ).all()
        assert len(enrollments) > 0
        assert len(enrollments) <= len(few_users)
