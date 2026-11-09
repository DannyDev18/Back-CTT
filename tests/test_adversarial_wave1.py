"""
Adversarial Verification Suite for Wave 1 Backend Implementations
Empirically stress-testing and challenging:
1. Capacity limit boundary conditions (cupo_maximo=1, immediate cancellation slot reclamation, all active statuses)
2. QR session attendance check-in duplicate prevention (rapid consecutive attacks, 409 status, DB count=1, DB-level UniqueConstraint)
3. Password security (wrong password rejection, bcrypt salting non-determinism, minimum length enforcement)
4. Identification immutability (adversarial payloads trying to mutate cédula/identification, cross-user boundary defense)
"""
import json
from datetime import datetime, date, time
import pytest
import bcrypt
from fastapi.testclient import TestClient
from fastapi import FastAPI, status
from sqlmodel import Session, select, SQLModel, func
from sqlalchemy.exc import IntegrityError

from src.dependencies.db_session import get_db
from src.routes.enrollments_router import (
    enrollments_router,
    get_current_platform_user,
    get_current_user_any_type,
)
from src.routes.congress_router import congress_router
from src.routes.users_platform_router import (
    users_platform_router,
    get_optional_current_user_any_type,
)
from src.models.enrollment import Enrollment, EnrollmentStatus, EnrollmentCreate
from src.models.user_platform import UserPlatform, UserPlatformType
from src.models.session_attendance_model import SessionAttendance
from src.models.sesion_cronograma_model import SesionCronograma
from src.models.congress_model import Congress
from src.models.speaker_model import Speaker
from src.controllers.enrollment_controller import EnrollmentController


@pytest.fixture(autouse=True)
def ensure_tables_exist(session: Session):
    """Garantiza que todas las tablas existan en SQLite en memoria."""
    SQLModel.metadata.create_all(session.bind)
    yield


@pytest.fixture
def student_user_1(session: Session) -> UserPlatform:
    user = UserPlatform(
        identification="1801111111",
        first_name="AdversarialOne",
        second_name="Alpha",
        first_last_name="Tester",
        second_last_name="One",
        cellphone="0991111111",
        email="adv1@example.com",
        type=UserPlatformType.ESTUDIANTE,
        password=UserPlatform.hash_password("Secret123!"),
        address="Av. Huachi 100, Ambato",
        billing_identification="1801111111",
        billing_name="Adversarial One",
        billing_address="Av. Huachi 100, Ambato",
        billing_phone="0991111111",
        billing_email="adv1@example.com",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def student_user_2(session: Session) -> UserPlatform:
    user = UserPlatform(
        identification="1802222222",
        first_name="AdversarialTwo",
        second_name="Beta",
        first_last_name="Tester",
        second_last_name="Two",
        cellphone="0992222222",
        email="adv2@example.com",
        type=UserPlatformType.ESTUDIANTE,
        password=UserPlatform.hash_password("Secret123!"),
        address="Av. Huachi 200, Ambato",
        billing_identification="1802222222",
        billing_name="Adversarial Two",
        billing_address="Av. Huachi 200, Ambato",
        billing_phone="0992222222",
        billing_email="adv2@example.com",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def student_user_3(session: Session) -> UserPlatform:
    user = UserPlatform(
        identification="1803333333",
        first_name="AdversarialThree",
        second_name="Gamma",
        first_last_name="Tester",
        second_last_name="Three",
        cellphone="0993333333",
        email="adv3@example.com",
        type=UserPlatformType.EXTERNO,
        password=UserPlatform.hash_password("Secret123!"),
        address="Av. Huachi 300, Ambato",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def create_user_client(session: Session, user: UserPlatform) -> TestClient:
    app = FastAPI()

    def override_get_db():
        try:
            yield session
        finally:
            pass

    def override_get_current_platform_user():
        return user

    async def override_get_current_user_any_type():
        return user, "platform"

    def override_get_optional_current_user_any_type():
        return user, "platform"

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_platform_user] = override_get_current_platform_user
    app.dependency_overrides[get_current_user_any_type] = override_get_current_user_any_type
    app.dependency_overrides[get_optional_current_user_any_type] = override_get_optional_current_user_any_type

    app.include_router(enrollments_router)
    app.include_router(congress_router)
    app.include_router(users_platform_router)

    return TestClient(app)


@pytest.fixture
def single_capacity_congress(session: Session) -> Congress:
    """Congreso con cupo_maximo exactamente 1 para pruebas de frontera."""
    congress = Congress(
        nombre="Congreso de Aforo Mínimo",
        edicion="AFORO-1",
        anio=2026,
        fecha_inicio=date(2026, 12, 1),
        fecha_fin=date(2026, 12, 3),
        descripcion_general="Congreso con límite de capacidad estricto de 1 participante",
        poster_cover_url="https://example.com/poster1.jpg",
        lugar_sede="Auditorio Central FISEI",
        cupo_maximo=1,
        costo_estudiante_uta=20.0,
        costo_profesional=50.0,
        costo_ponente=80.0,
    )
    session.add(congress)
    session.commit()
    session.refresh(congress)
    return congress


@pytest.fixture
def multi_capacity_congress(session: Session) -> Congress:
    """Congreso con cupo_maximo = 4 para probar todos los estados activos."""
    congress = Congress(
        nombre="Congreso Multi Estado",
        edicion="MULTI-4",
        anio=2026,
        fecha_inicio=date(2026, 12, 5),
        fecha_fin=date(2026, 12, 7),
        descripcion_general="Congreso con capacidad de 4 cupos",
        poster_cover_url="https://example.com/poster4.jpg",
        lugar_sede="Auditorio Central FISEI",
        cupo_maximo=4,
        costo_estudiante_uta=20.0,
        costo_profesional=50.0,
        costo_ponente=80.0,
    )
    session.add(congress)
    session.commit()
    session.refresh(congress)
    return congress


@pytest.fixture
def sample_session_cronograma(session: Session, single_capacity_congress: Congress) -> SesionCronograma:
    speaker = Speaker(
        id_congreso=single_capacity_congress.id_congreso,
        nombres_completos="Speaker Stress Test",
        titulo_academico="PhD",
        institucion="UTA",
        pais="Ecuador",
        foto_url="https://example.com/speaker.jpg",
        tipo_speaker="magistral",
    )
    session.add(speaker)
    session.commit()
    session.refresh(speaker)

    sesion = SesionCronograma(
        id_congreso=single_capacity_congress.id_congreso,
        id_speaker=speaker.id_speaker,
        fecha=date(2026, 12, 1),
        hora_inicio=time(9, 0),
        hora_fin=time(11, 0),
        titulo_sesion="Sesión Adversarial de Ciberseguridad",
        jornada="mañana",
        lugar="Auditorio 1",
    )
    session.add(sesion)
    session.commit()
    session.refresh(sesion)
    return sesion


# ==============================================================================
# CHALLENGE 1: CAPACITY LIMIT & CANCELLATION BOUNDARY
# ==============================================================================

class TestAdversarialCapacityLimit:

    def test_boundary_cupo_maximo_exact_1(
        self, session: Session, single_capacity_congress: Congress,
        student_user_1: UserPlatform, student_user_2: UserPlatform, student_user_3: UserPlatform
    ):
        """
        Desafío: cupo_maximo = 1.
        - La 1ra inscripción debe pasar (201).
        - La 2da inscripción debe ser rechazada inmediatamente (400) con mensaje exacto.
        - La 3ra inscripción también debe ser rechazada (400).
        - Verificar que el recuento de inscripciones activas en la BD es exactamente 1.
        """
        client1 = create_user_client(session, student_user_1)
        client2 = create_user_client(session, student_user_2)
        client3 = create_user_client(session, student_user_3)

        # 1ra inscripción: Debe tener éxito
        res1 = client1.post("/api/v1/enrollments", json={
            "id_user_platform": student_user_1.id,
            "id_congress": single_capacity_congress.id_congreso,
            "status": "Interesado",
            "tariff_type": "ESTUDIANTE_UTA",
            "amount": 20.0,
        })
        assert res1.status_code == status.HTTP_201_CREATED, res1.text
        enrollment_1_id = res1.json()["data"]["id"]

        # Recuento activo en BD debe ser 1
        active_count = session.exec(
            select(func.count(Enrollment.id)).where(
                Enrollment.id_congress == single_capacity_congress.id_congreso,
                Enrollment.status.in_([
                    EnrollmentStatus.PAGADO,
                    EnrollmentStatus.FACTURADO,
                    EnrollmentStatus.INTERESADO,
                    EnrollmentStatus.ORDEN_GENERADA,
                ]),
            )
        ).one()
        assert active_count == 1

        # 2da inscripción: Debe bloquearse inmediatamente
        res2 = client2.post("/api/v1/enrollments", json={
            "id_user_platform": student_user_2.id,
            "id_congress": single_capacity_congress.id_congreso,
            "status": "Interesado",
            "tariff_type": "ESTUDIANTE_UTA",
            "amount": 20.0,
        })
        assert res2.status_code == status.HTTP_400_BAD_REQUEST
        assert "cupo máximo (1 participantes) ha sido alcanzado" in res2.json()["detail"]

        # 3ra inscripción: También bloqueada
        res3 = client3.post("/api/v1/enrollments", json={
            "id_user_platform": student_user_3.id,
            "id_congress": single_capacity_congress.id_congreso,
            "status": "Interesado",
            "tariff_type": "PROFESIONAL",
            "amount": 50.0,
        })
        assert res3.status_code == status.HTTP_400_BAD_REQUEST
        assert "cupo máximo" in res3.json()["detail"]

        # Verificar que la BD sigue teniendo EXACTAMENTE 1 inscripción activa
        active_count_after = session.exec(
            select(func.count(Enrollment.id)).where(
                Enrollment.id_congress == single_capacity_congress.id_congreso,
                Enrollment.status.in_([
                    EnrollmentStatus.PAGADO,
                    EnrollmentStatus.FACTURADO,
                    EnrollmentStatus.INTERESADO,
                    EnrollmentStatus.ORDEN_GENERADA,
                ]),
            )
        ).one()
        assert active_count_after == 1

    def test_cancellation_frees_slot_immediately(
        self, session: Session, single_capacity_congress: Congress,
        student_user_1: UserPlatform, student_user_2: UserPlatform, student_user_3: UserPlatform
    ):
        """
        Desafío: Liberación inmediata de cupo al anular inscripción.
        - Estudiante 1 llena el cupo (1/1).
        - Estudiante 2 es rechazado (400).
        - La inscripción del Estudiante 1 se cambia a ANULADO.
        - Inmediatamente el Estudiante 2 intenta inscribirse -> DEBE triunfar con 201.
        - Ahora que el cupo volvió a llenarse con Estudiante 2, Estudiante 3 debe ser rechazado (400).
        """
        client1 = create_user_client(session, student_user_1)
        client2 = create_user_client(session, student_user_2)
        client3 = create_user_client(session, student_user_3)

        # Llenar cupo
        res1 = client1.post("/api/v1/enrollments", json={
            "id_user_platform": student_user_1.id,
            "id_congress": single_capacity_congress.id_congreso,
            "status": "Interesado",
            "tariff_type": "ESTUDIANTE_UTA",
            "amount": 20.0,
        })
        assert res1.status_code == status.HTTP_201_CREATED
        e1_id = res1.json()["data"]["id"]

        # Estudiante 2 bloqueado
        res2_blocked = client2.post("/api/v1/enrollments", json={
            "id_user_platform": student_user_2.id,
            "id_congress": single_capacity_congress.id_congreso,
            "status": "Interesado",
            "tariff_type": "ESTUDIANTE_UTA",
            "amount": 20.0,
        })
        assert res2_blocked.status_code == status.HTTP_400_BAD_REQUEST

        # Anular inscripción 1
        enrollment_1 = session.get(Enrollment, e1_id)
        enrollment_1.status = EnrollmentStatus.ANULADO
        session.add(enrollment_1)
        session.commit()
        session.refresh(enrollment_1)

        # Reintento de Estudiante 2: Cupo liberado, DEBE pasar
        res2_retry = client2.post("/api/v1/enrollments", json={
            "id_user_platform": student_user_2.id,
            "id_congress": single_capacity_congress.id_congreso,
            "status": "Interesado",
            "tariff_type": "ESTUDIANTE_UTA",
            "amount": 20.0,
        })
        assert res2_retry.status_code == status.HTTP_201_CREATED, res2_retry.text

        # Ahora el cupo vuelve a estar 1/1 ocupado por Estudiante 2.
        # Estudiante 3 debe ser rechazado
        res3 = client3.post("/api/v1/enrollments", json={
            "id_user_platform": student_user_3.id,
            "id_congress": single_capacity_congress.id_congreso,
            "status": "Interesado",
            "tariff_type": "PROFESIONAL",
            "amount": 50.0,
        })
        assert res3.status_code == status.HTTP_400_BAD_REQUEST
        assert "cupo máximo" in res3.json()["detail"]

    def test_all_active_statuses_consume_capacity(
        self, session: Session, multi_capacity_congress: Congress, student_user_1: UserPlatform
    ):
        """
        Desafío: Comprobar que PAGADO, FACTURADO, INTERESADO y ORDEN_GENERADA
        consumen cupo efectivamente hasta agotar el límite de 4.
        """
        # Crear 4 usuarios sintéticos
        users = []
        for i in range(10, 14):
            u = UserPlatform(
                identification=f"18000000{i}",
                first_name=f"User{i}",
                first_last_name="Test",
                cellphone="0990000000",
                email=f"user{i}@test.com",
                type=UserPlatformType.ESTUDIANTE,
                password=UserPlatform.hash_password("Pass123!"),
            )
            session.add(u)
            users.append(u)
        session.commit()

        statuses = [
            EnrollmentStatus.PAGADO,
            EnrollmentStatus.FACTURADO,
            EnrollmentStatus.INTERESADO,
            EnrollmentStatus.ORDEN_GENERADA,
        ]

        # Insertar 4 inscripciones con los 4 estados activos
        for u, st in zip(users, statuses):
            e = Enrollment(
                id_user_platform=u.id,
                id_congress=multi_capacity_congress.id_congreso,
                status=st,
                tariff_type="GENERAL",
                amount=20.0,
            )
            session.add(e)
        session.commit()

        # El 5to usuario (student_user_1) intenta inscribirse -> Debe ser bloqueado
        client = create_user_client(session, student_user_1)
        res = client.post("/api/v1/enrollments", json={
            "id_user_platform": student_user_1.id,
            "id_congress": multi_capacity_congress.id_congreso,
            "status": "Interesado",
            "tariff_type": "GENERAL",
            "amount": 20.0,
        })
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert "cupo máximo (4 participantes) ha sido alcanzado" in res.json()["detail"]


# ==============================================================================
# CHALLENGE 2: QR CHECK-IN RAPID DUPLICATE & INTEGRITY PREVENTION
# ==============================================================================

class TestAdversarialQRDuplicateCheckin:

    def test_rapid_consecutive_duplicate_scans_exact_409_and_single_db_row(
        self, session: Session, single_capacity_congress: Congress,
        sample_session_cronograma: SesionCronograma, student_user_1: UserPlatform
    ):
        """
        Desafío de estrés:
        1. Primer escaneo válido -> HTTP 200 OK.
        2. Bucle de 12 escaneos rápidos y consecutivos con formatos alternativos (JSON, URI, raw).
        3. CADA reintento debe responder exactamente con HTTP 409 Conflict.
        4. El mensaje debe contener el timestamp original de registro.
        5. La base de datos debe contener ESTRICTAMENTE 1 sola fila en session_attendance.
        """
        # Crear inscripción PAGADA
        enrollment = Enrollment(
            id_user_platform=student_user_1.id,
            id_congress=single_capacity_congress.id_congreso,
            status=EnrollmentStatus.PAGADO,
            tariff_type="ESTUDIANTE_UTA",
            amount=20.0,
        )
        session.add(enrollment)
        session.commit()
        session.refresh(enrollment)

        client = create_user_client(session, student_user_1)
        cid = single_capacity_congress.id_congreso
        sid = sample_session_cronograma.id_sesion
        eid = enrollment.id

        # 1er Escaneo: Éxito
        res_initial = client.post(
            f"/api/v1/congresses/{cid}/attendance/scan",
            json={
                "qr_payload": f"UTA-FISEI-PASS-{eid}-{cid}",
                "id_sesion": sid,
            }
        )
        assert res_initial.status_code == status.HTTP_200_OK, res_initial.text
        data = res_initial.json()
        assert data["status"] == "OK"
        assert data["total_sessions_attended"] == 1

        # Verificar BD tras primer escaneo: Exactamente 1 fila
        initial_db_rows = session.exec(
            select(SessionAttendance).where(
                SessionAttendance.id_enrollment == eid,
                SessionAttendance.id_sesion == sid,
            )
        ).all()
        assert len(initial_db_rows) == 1
        initial_record = initial_db_rows[0]
        recorded_time_iso = initial_record.check_in_time.isoformat()

        # 2. Ráfaga de formatos alternativos de QR en intentos duplicados
        duplicate_payloads = [
            f"UTA-FISEI-PASS-{eid}-{cid}",
            f"PASS-{eid}-{cid}",
            f"{eid}",
            json.dumps({"credential": f"UTA-FISEI-PASS-{eid}-{cid}"}),
            json.dumps({"id_enrollment": eid, "id_congress": cid}),
            json.dumps({"enrollment_id": eid, "congress_id": cid}),
            f"UTA-FISEI-PASS-{eid}",
            f"PASS-{eid}",
            json.dumps({"pass_code": f"UTA-FISEI-PASS-{eid}-{cid}"}),
            json.dumps({"id": eid}),
            f"UTA-FISEI-PASS-{eid}-{cid}",
            f"{eid}",
        ]

        for idx, pl in enumerate(duplicate_payloads):
            res_dup = client.post(
                f"/api/v1/congresses/{cid}/attendance/scan",
                json={
                    "qr_payload": pl,
                    "id_sesion": sid,
                }
            )
            # Debe ser estrictamente 409 Conflict
            assert res_dup.status_code == status.HTTP_409_CONFLICT, (
                f"Intento {idx} con payload '{pl}' retornó {res_dup.status_code}: {res_dup.text}"
            )
            detail = res_dup.json()["detail"]
            assert "ya registró asistencia" in detail
            # El timestamp debe coincidir con el registro original
            assert recorded_time_iso[:19] in detail

        # 3. Verificación final de integridad en la BD: Debe continuar habiendo ESTRICTAMENTE 1 fila
        final_db_rows = session.exec(
            select(SessionAttendance).where(
                SessionAttendance.id_enrollment == eid,
                SessionAttendance.id_sesion == sid,
            )
        ).all()
        assert len(final_db_rows) == 1, f"Esperado 1 registro, encontrados {len(final_db_rows)}"

    def test_database_level_unique_constraint_enforcement(
        self, session: Session, single_capacity_congress: Congress,
        sample_session_cronograma: SesionCronograma, student_user_1: UserPlatform
    ):
        """
        Desafío a nivel DDL/Base de Datos:
        Intentar forzar una inserción duplicada en session_attendance directamente
        en la sesión de base de datos debe disparar una violación de UniqueConstraint (IntegrityError).
        """
        enrollment = Enrollment(
            id_user_platform=student_user_1.id,
            id_congress=single_capacity_congress.id_congreso,
            status=EnrollmentStatus.PAGADO,
        )
        session.add(enrollment)
        session.commit()
        session.refresh(enrollment)

        sid = sample_session_cronograma.id_sesion
        eid = enrollment.id

        # Insertar 1er registro
        rec1 = SessionAttendance(id_enrollment=eid, id_sesion=sid)
        session.add(rec1)
        session.commit()

        # Intentar insertar 2do registro idéntico directamente en la base de datos
        rec2 = SessionAttendance(id_enrollment=eid, id_sesion=sid)
        session.add(rec2)
        with pytest.raises(IntegrityError):
            session.commit()

        session.rollback()

    def test_multi_session_attendance_isolation(
        self, session: Session, single_capacity_congress: Congress,
        sample_session_cronograma: SesionCronograma, student_user_1: UserPlatform
    ):
        """
        Desafío: Distintas sesiones del mismo congreso deben registrarse de forma aislada.
        - Sesión 1: Asistencia registrada (total = 1).
        - Sesión 2: Asistencia registrada (total = 2).
        - Duplicado en Sesión 1 -> 409 Conflict.
        - Duplicado en Sesión 2 -> 409 Conflict.
        - BD: Exactamente 2 filas en total, 1 por cada sesión.
        """
        # Crear 2da sesión
        sesion2 = SesionCronograma(
            id_congreso=single_capacity_congress.id_congreso,
            id_speaker=sample_session_cronograma.id_speaker,
            fecha=date(2026, 12, 2),
            hora_inicio=time(14, 0),
            hora_fin=time(16, 0),
            titulo_sesion="Sesión Adversarial 2",
            jornada="tarde",
            lugar="Auditorio 2",
        )
        session.add(sesion2)
        session.commit()
        session.refresh(sesion2)

        enrollment = Enrollment(
            id_user_platform=student_user_1.id,
            id_congress=single_capacity_congress.id_congreso,
            status=EnrollmentStatus.PAGADO,
            tariff_type="ESTUDIANTE_UTA",
        )
        session.add(enrollment)
        session.commit()
        session.refresh(enrollment)

        client = create_user_client(session, student_user_1)
        cid = single_capacity_congress.id_congreso
        eid = enrollment.id

        # Sesión 1: 1er check-in
        r1 = client.post(
            f"/api/v1/congresses/{cid}/attendance/scan",
            json={"qr_payload": f"UTA-FISEI-PASS-{eid}-{cid}", "id_sesion": sample_session_cronograma.id_sesion}
        )
        assert r1.status_code == status.HTTP_200_OK
        assert r1.json()["total_sessions_attended"] == 1

        # Sesión 2: 1er check-in
        r2 = client.post(
            f"/api/v1/congresses/{cid}/attendance/scan",
            json={"qr_payload": f"UTA-FISEI-PASS-{eid}-{cid}", "id_sesion": sesion2.id_sesion}
        )
        assert r2.status_code == status.HTTP_200_OK
        assert r2.json()["total_sessions_attended"] == 2

        # Duplicado Sesión 1 -> 409
        r1_dup = client.post(
            f"/api/v1/congresses/{cid}/attendance/scan",
            json={"qr_payload": f"UTA-FISEI-PASS-{eid}-{cid}", "id_sesion": sample_session_cronograma.id_sesion}
        )
        assert r1_dup.status_code == status.HTTP_409_CONFLICT

        # Duplicado Sesión 2 -> 409
        r2_dup = client.post(
            f"/api/v1/congresses/{cid}/attendance/scan",
            json={"qr_payload": f"UTA-FISEI-PASS-{eid}-{cid}", "id_sesion": sesion2.id_sesion}
        )
        assert r2_dup.status_code == status.HTTP_409_CONFLICT

        # Verificar BD: exactamente 2 registros
        total_records = session.exec(
            select(func.count(SessionAttendance.id)).where(
                SessionAttendance.id_enrollment == eid
            )
        ).one()
        assert total_records == 2


# ==============================================================================
# CHALLENGE 3: PASSWORD SECURITY & BCRYPT SALTING
# ==============================================================================

class TestAdversarialPasswordSecurity:

    def test_wrong_password_rejected_and_original_preserved(
        self, session: Session, student_user_1: UserPlatform
    ):
        """
        Desafío: Contraseña incorrecta.
        - Intento de actualizar contraseña suministrando 'WrongPassword999!'.
        - Debe responder HTTP 400 Bad Request ('Contraseña actual incorrecta').
        - La contraseña almacenada en la BD no debe modificarse.
        - La contraseña original ('Secret123!') debe seguir verificándose como válida.
        """
        client = create_user_client(session, student_user_1)
        original_hash = student_user_1.password

        res = client.put(
            f"/api/v1/users/{student_user_1.id}/password",
            json={
                "current_password": "WrongPassword999!",
                "new_password": "NewLegitPassword2026!",
            }
        )
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert "Contraseña actual incorrecta" in res.json()["detail"]

        # Comprobar que en BD no hubo alteración
        refreshed_user = session.get(UserPlatform, student_user_1.id)
        assert refreshed_user.password == original_hash
        assert refreshed_user.verify_password("Secret123!") is True
        assert refreshed_user.verify_password("NewLegitPassword2026!") is False

    def test_short_password_rejected(
        self, session: Session, student_user_1: UserPlatform
    ):
        """
        Desafío: Contraseña menor a 6 caracteres.
        - Debe responder HTTP 400 Bad Request.
        """
        client = create_user_client(session, student_user_1)
        res = client.put(
            f"/api/v1/users/{student_user_1.id}/password",
            json={
                "current_password": "Secret123!",
                "new_password": "short",
            }
        )
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert "al menos 6 caracteres" in res.json()["detail"]

    def test_bcrypt_salting_non_determinism(self):
        """
        Desafío Criptográfico:
        Hashear 3 veces la misma contraseña en texto plano.
        - Los 3 hashes deben ser completamente distintos entre sí (salting aleatorio).
        - Todos deben comenzar con $2b$ o $2a$.
        - Cada hash debe verificar exitosamente la contraseña original.
        - Ninguno debe verificar una contraseña errónea.
        """
        plain = "IdenticalPlainPassword2026!"
        h1 = UserPlatform.hash_password(plain)
        h2 = UserPlatform.hash_password(plain)
        h3 = UserPlatform.hash_password(plain)

        # Hashes distintos por efecto del salt
        assert h1 != h2
        assert h2 != h3
        assert h1 != h3

        # Formato bcrypt
        for h in [h1, h2, h3]:
            assert h.startswith("$2b$") or h.startswith("$2a$")
            assert bcrypt.checkpw(plain.encode("utf-8"), h.encode("utf-8")) is True
            assert bcrypt.checkpw(b"BadPass123", h.encode("utf-8")) is False

    def test_update_password_success_flow(
        self, session: Session, student_user_1: UserPlatform
    ):
        """
        Desafío: Actualización exitosa.
        - Valida contraseña actual, hashea con bcrypt.
        - La anterior deja de funcionar, la nueva valida inmediatamente.
        """
        client = create_user_client(session, student_user_1)
        res = client.put(
            f"/api/v1/users/{student_user_1.id}/password",
            json={
                "current_password": "Secret123!",
                "new_password": "UpgradedPassword2026!",
            }
        )
        assert res.status_code == status.HTTP_200_OK

        refreshed = session.get(UserPlatform, student_user_1.id)
        assert refreshed.verify_password("Secret123!") is False
        assert refreshed.verify_password("UpgradedPassword2026!") is True


# ==============================================================================
# CHALLENGE 4: IDENTIFICATION IMMUTABILITY & AUTHORIZATION DEFENSE
# ==============================================================================

class TestAdversarialIdentificationImmutability:

    def test_identification_strictly_immutable_under_adversarial_profile_payload(
        self, session: Session, student_user_1: UserPlatform
    ):
        """
        Desafío de inmutabilidad de la cédula ecuatoriana:
        Se envía un payload agresivo intentando sobrescribir identification, cedula, ruc, etc.
        - La respuesta debe devolver la cédula original intacta.
        - La base de datos debe conservar la cédula original '1801111111'.
        - Los campos permitidos (first_name, address) sí deben actualizarse.
        """
        client = create_user_client(session, student_user_1)

        adversarial_payload = {
            "first_name": "CarlosModificado",
            "last_name": "MoraActualizado",
            "phone": "0998887766",
            "address": "Campus Huachi Modificado",
            # Intentos de inyección/modificación de identificación
            "identification": "9999999999",
            "cedula": "0000000000",
            "ruc": "1801111111001",
            "id_user_platform": 99999,
        }

        res = client.put(f"/api/v1/users/{student_user_1.id}/profile", json=adversarial_payload)
        assert res.status_code == status.HTTP_200_OK, res.text
        data = res.json()["data"]

        # Cédula devuelta DEBE ser la original
        assert data["identification"] == "1801111111"
        assert data["first_name"] == "CarlosModificado"
        assert data["address"] == "Campus Huachi Modificado"

        # Consulta directa en BD
        db_user = session.get(UserPlatform, student_user_1.id)
        assert db_user.identification == "1801111111"
        assert db_user.first_name == "CarlosModificado"
        assert db_user.address == "Campus Huachi Modificado"

    def test_cross_user_profile_and_password_tampering_forbidden(
        self, session: Session, student_user_1: UserPlatform, student_user_2: UserPlatform
    ):
        """
        Desafío de autorización cruzada:
        El Estudiante 1 intenta actualizar el perfil y la contraseña del Estudiante 2.
        - Ambas acciones deben ser bloqueadas con HTTP 403 Forbidden.
        - El perfil y la contraseña del Estudiante 2 deben permanecer 100% intactos en la BD.
        """
        client1 = create_user_client(session, student_user_1)
        u2_original_pass = student_user_2.password
        u2_original_name = student_user_2.first_name

        # Intento de modificar perfil de otro usuario
        res_profile = client1.put(
            f"/api/v1/users/{student_user_2.id}/profile",
            json={"first_name": "HackedName"}
        )
        assert res_profile.status_code == status.HTTP_403_FORBIDDEN
        assert "No tienes permiso" in res_profile.json()["detail"]

        # Intento de modificar contraseña de otro usuario
        res_pass = client1.put(
            f"/api/v1/users/{student_user_2.id}/password",
            json={
                "current_password": "Secret123!",
                "new_password": "AttackerTakeoverPass2026!",
            }
        )
        assert res_pass.status_code == status.HTTP_403_FORBIDDEN
        assert "No tienes permiso" in res_pass.json()["detail"]

        # Verificación en BD
        db_u2 = session.get(UserPlatform, student_user_2.id)
        assert db_u2.first_name == u2_original_name
        assert db_u2.password == u2_original_pass
        assert db_u2.verify_password("Secret123!") is True
