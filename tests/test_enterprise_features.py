"""
Tests de integración para funcionalidades Enterprise (Wave 1 Core + Wave 2 Stubs):
1. Control estricto de aforo y cupos (cupo_maximo)
2. Registro y escaneo de asistencia QR a sesiones (session_attendance) con detección de duplicados (409 Conflict)
3. Gestión de perfil de usuario (inmutabilidad de cédula) y actualización segura de contraseña con bcrypt
4. Descarga de Comprobante / RIDE Oficial UTA en PDF (RUC 1860000880001)
5. Exportación de nómina de estudiantes en CSV formato Moodle LMS
"""
import io
import csv
from datetime import datetime, date, time
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI, status
from sqlmodel import Session, select, SQLModel

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
    """Garantiza que todas las tablas registradas en SQLModel existan en SQLite en memoria."""
    SQLModel.metadata.create_all(session.bind)
    yield


@pytest.fixture
def student_user_1(session: Session) -> UserPlatform:
    """Primer usuario de plataforma con contraseña hasheada correctamente con bcrypt."""
    user = UserPlatform(
        identification="1801111111",
        first_name="Carlos",
        second_name="Andres",
        first_last_name="Mora",
        second_last_name="Sanchez",
        cellphone="0991111111",
        email="carlos.mora@example.com",
        type=UserPlatformType.ESTUDIANTE,
        password=UserPlatform.hash_password("Secret123!"),
        address="Campus Huachi, Ambato",
        billing_identification="1801111111",
        billing_name="Carlos Mora",
        billing_address="Campus Huachi, Ambato",
        billing_phone="0991111111",
        billing_email="carlos.mora@example.com",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def student_user_2(session: Session) -> UserPlatform:
    """Segundo usuario de plataforma para pruebas de aforo y multiusuario."""
    user = UserPlatform(
        identification="1802222222",
        first_name="Maria",
        second_name="Fernanda",
        first_last_name="Perez",
        second_last_name="Castro",
        cellphone="0992222222",
        email="maria.perez@example.com",
        type=UserPlatformType.ESTUDIANTE,
        password=UserPlatform.hash_password("Secret123!"),
        address="Av. Cevallos 456, Ambato",
        billing_identification="1802222222",
        billing_name="Maria Perez",
        billing_address="Av. Cevallos 456, Ambato",
        billing_phone="0992222222",
        billing_email="maria.perez@example.com",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def student_user_3(session: Session) -> UserPlatform:
    """Tercer usuario de plataforma para pruebas de límite de aforo."""
    user = UserPlatform(
        identification="1803333333",
        first_name="Juan",
        second_name="Pablo",
        first_last_name="Torres",
        second_last_name="Ramos",
        cellphone="0993333333",
        email="juan.torres@example.com",
        type=UserPlatformType.EXTERNO,
        password=UserPlatform.hash_password("Secret123!"),
        address="Av. Los Guaytambos 789, Ambato",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def create_user_client(session: Session, user: UserPlatform) -> TestClient:
    """Crea un TestClient autenticado para un usuario de plataforma específico."""
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
def enterprise_client(session: Session, student_user_1: UserPlatform) -> TestClient:
    """Cliente de pruebas predeterminado autenticado como student_user_1."""
    return create_user_client(session, student_user_1)


@pytest.fixture
def enterprise_congress(session: Session) -> Congress:
    """Congreso de prueba con cupo_maximo = 2 y tarifas oficiales FISEI."""
    congress = Congress(
        nombre="Congreso Internacional de Ciberseguridad e IA 2026",
        edicion="CIIA-2026",
        anio=2026,
        fecha_inicio=date(2026, 11, 10),
        fecha_fin=date(2026, 11, 12),
        descripcion_general="Congreso tecnológico oficial de la FISEI-UTA",
        poster_cover_url="https://example.com/poster.jpg",
        lugar_sede="Auditorio Central FISEI",
        cupo_maximo=2,
        costo_estudiante_uta=20.0,
        costo_profesional=50.0,
        costo_ponente=80.0,
    )
    session.add(congress)
    session.commit()
    session.refresh(congress)
    return congress


@pytest.fixture
def enterprise_speaker(session: Session, enterprise_congress: Congress) -> Speaker:
    """Ponente magistral asociado al congreso."""
    speaker = Speaker(
        id_congreso=enterprise_congress.id_congreso,
        nombres_completos="Dr. Roberto Alan Turing",
        titulo_academico="PhD en Inteligencia Artificial",
        institucion="MIT / FISEI Visiting Scholar",
        pais="Ecuador",
        foto_url="https://example.com/speaker.jpg",
        tipo_speaker="magistral",
    )
    session.add(speaker)
    session.commit()
    session.refresh(speaker)
    return speaker


@pytest.fixture
def enterprise_session(
    session: Session, enterprise_congress: Congress, enterprise_speaker: Speaker
) -> SesionCronograma:
    """Sesión del cronograma asociada al congreso y ponente."""
    cronograma_session = SesionCronograma(
        id_congreso=enterprise_congress.id_congreso,
        id_speaker=enterprise_speaker.id_speaker,
        fecha=date(2026, 11, 10),
        hora_inicio=time(9, 0),
        hora_fin=time(11, 0),
        titulo_sesion="Keynote Apertura: Ciberseguridad Cuántica",
        jornada="mañana",
        lugar="Auditorio Central FISEI",
    )
    session.add(cronograma_session)
    session.commit()
    session.refresh(cronograma_session)
    return cronograma_session


def send_attendance_scan(client: TestClient, congress_id: int, payload: dict):
    """Envía el scan probando tanto `/api/v1/congresses` como `/api/v1/congresses-new`."""
    resp = client.post(f"/api/v1/congresses/{congress_id}/attendance/scan", json=payload)
    if resp.status_code == 404:
        resp = client.post(f"/api/v1/congresses-new/{congress_id}/attendance/scan", json=payload)
    return resp


def get_attendance_list(client: TestClient, congress_id: int, session_id: int):
    """Obtiene la lista de asistencias probando ambos prefijos."""
    resp = client.get(f"/api/v1/congresses/{congress_id}/attendance/session/{session_id}")
    if resp.status_code == 404:
        resp = client.get(f"/api/v1/congresses-new/{congress_id}/attendance/session/{session_id}")
    return resp


# ==============================================================================
# 1. TESTS DE CONTROL DE AFORO (cupo_maximo)
# ==============================================================================

class TestCapacityControl:
    """Pruebas de validación y control de cupo máximo en congresos."""

    def test_congress_enrollment_allowed_under_capacity(
        self, session: Session, student_user_1: UserPlatform, enterprise_congress: Congress
    ):
        """Verifica que la inscripción es exitosa cuando hay cupos disponibles."""
        enterprise_congress.cupo_maximo = 50
        session.add(enterprise_congress)
        session.commit()

        client_1 = create_user_client(session, student_user_1)
        response = client_1.post(
            "/api/v1/enrollments",
            json={
                "id_user_platform": student_user_1.id,
                "id_congress": enterprise_congress.id_congreso,
                "status": "Interesado",
                "tariff_type": "Estudiante UTA",
                "amount": 20.0,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Inscripción creada exitosamente."
        assert data["data"]["tariff_type"] == "Estudiante UTA"

    def test_congress_enrollment_blocked_when_capacity_reached(
        self,
        session: Session,
        student_user_1: UserPlatform,
        student_user_2: UserPlatform,
        student_user_3: UserPlatform,
        enterprise_congress: Congress,
    ):
        """
        Verifica que se rechaza con HTTP 400 al alcanzar el cupo_maximo exacto (2 cupos):
        - Estudiante 1 se inscribe (1/2 cupos).
        - Estudiante 2 se inscribe (2/2 cupos - CONVOCATORIA LLENA).
        - Estudiante 3 intenta inscribirse -> Rechazado con HTTP 400.
        """
        enterprise_congress.cupo_maximo = 2
        session.add(enterprise_congress)
        session.commit()

        # Inscribir primer participante (cupo 1/2) autenticado como student_user_1
        client_1 = create_user_client(session, student_user_1)
        resp1 = client_1.post(
            "/api/v1/enrollments",
            json={
                "id_user_platform": student_user_1.id,
                "id_congress": enterprise_congress.id_congreso,
                "status": "Pagado",
            },
        )
        assert resp1.status_code == 201

        # Inscribir segundo participante (cupo 2/2) autenticado como student_user_2
        client_2 = create_user_client(session, student_user_2)
        resp2 = client_2.post(
            "/api/v1/enrollments",
            json={
                "id_user_platform": student_user_2.id,
                "id_congress": enterprise_congress.id_congreso,
                "status": "Generada la orden",
            },
        )
        assert resp2.status_code == 201

        # Intentar inscribir tercer participante autenticado como student_user_3 -> 400 Bad Request
        client_3 = create_user_client(session, student_user_3)
        resp3 = client_3.post(
            "/api/v1/enrollments",
            json={
                "id_user_platform": student_user_3.id,
                "id_congress": enterprise_congress.id_congreso,
                "status": "Interesado",
            },
        )
        assert resp3.status_code == 400
        error_detail = resp3.json()["detail"]
        assert "cupo máximo" in error_detail.lower() or "cerrada" in error_detail.lower()

    def test_direct_controller_call_raises_value_error_on_capacity(
        self,
        session: Session,
        student_user_1: UserPlatform,
        student_user_2: UserPlatform,
        student_user_3: UserPlatform,
        enterprise_congress: Congress,
    ):
        """Verifica que el controlador invoque ValueError directamente si se intenta superar el cupo."""
        enterprise_congress.cupo_maximo = 2
        session.add(enterprise_congress)
        session.commit()

        # Inscribir 2 participantes
        EnrollmentController.create_enrollment(
            EnrollmentCreate(
                id_congress=enterprise_congress.id_congreso,
                id_user_platform=student_user_1.id,
                status=EnrollmentStatus.PAGADO,
            ),
            session,
        )
        EnrollmentController.create_enrollment(
            EnrollmentCreate(
                id_congress=enterprise_congress.id_congreso,
                id_user_platform=student_user_2.id,
                status=EnrollmentStatus.PAGADO,
            ),
            session,
        )

        # 3er intento lanza ValueError
        with pytest.raises(ValueError) as excinfo:
            EnrollmentController.create_enrollment(
                EnrollmentCreate(
                    id_congress=enterprise_congress.id_congreso,
                    id_user_platform=student_user_3.id,
                    status=EnrollmentStatus.INTERESADO,
                ),
                session,
            )
        assert "cupo máximo" in str(excinfo.value).lower()

    def test_canceled_enrollments_do_not_count_towards_capacity(
        self,
        session: Session,
        student_user_1: UserPlatform,
        student_user_2: UserPlatform,
        enterprise_congress: Congress,
    ):
        """Verifica que inscripciones en estado Anulado liberan cupo para nuevos participantes."""
        enterprise_congress.cupo_maximo = 1
        session.add(enterprise_congress)
        session.commit()

        # Inscripción anulada
        enr = Enrollment(
            id_user_platform=student_user_1.id,
            id_congress=enterprise_congress.id_congreso,
            enrollment_date=datetime.utcnow(),
            status=EnrollmentStatus.ANULADO,
        )
        session.add(enr)
        session.commit()

        # Segundo usuario intenta inscribirse: debe permitirse porque el primero está anulado
        client_2 = create_user_client(session, student_user_2)
        resp = client_2.post(
            "/api/v1/enrollments",
            json={
                "id_user_platform": student_user_2.id,
                "id_congress": enterprise_congress.id_congreso,
                "status": "Pagado",
            },
        )
        assert resp.status_code == 201


# ==============================================================================
# 2. TESTS DE ASISTENCIA QR A SESIONES (session_attendance)
# ==============================================================================

class TestSessionAttendanceQR:
    """Pruebas de escaneo de QR, validación de pago y detección de duplicados (409 Conflict)."""

    def test_scan_attendance_success_and_total_count(
        self,
        session: Session,
        student_user_1: UserPlatform,
        enterprise_congress: Congress,
        enterprise_session: SesionCronograma,
    ):
        """Verifica el registro exitoso del primer escaneo QR y cálculo de total de asistencias."""
        enrollment = Enrollment(
            id_user_platform=student_user_1.id,
            id_congress=enterprise_congress.id_congreso,
            enrollment_date=datetime.utcnow(),
            status=EnrollmentStatus.PAGADO,
            tariff_type="Estudiante UTA",
            amount=20.0,
        )
        session.add(enrollment)
        session.commit()
        session.refresh(enrollment)

        client = create_user_client(session, student_user_1)
        qr_string = f"UTA-FISEI-PASS-{enrollment.id}-{enterprise_congress.id_congreso}"

        response = send_attendance_scan(
            client,
            enterprise_congress.id_congreso,
            {
                "qr_payload": qr_string,
                "id_sesion": enterprise_session.id_sesion,
                "notes": "Escaneo de entrada en puerta norte",
            },
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["status"] == "OK"
        assert "Carlos" in data["attendee_name"]
        assert data["total_sessions_attended"] == 1
        assert data["tariff_type"] == "Estudiante UTA"

        # Verificar en base de datos
        attendance_rec = session.exec(
            select(SessionAttendance).where(
                SessionAttendance.id_enrollment == enrollment.id,
                SessionAttendance.id_sesion == enterprise_session.id_sesion,
            )
        ).first()
        assert attendance_rec is not None
        assert attendance_rec.notes == "Escaneo de entrada en puerta norte"

    def test_scan_attendance_duplicate_rejected_with_409(
        self,
        session: Session,
        student_user_1: UserPlatform,
        enterprise_congress: Congress,
        enterprise_session: SesionCronograma,
    ):
        """Verifica que un segundo escaneo para la misma sesión retorna HTTP 409 Conflict."""
        enrollment = Enrollment(
            id_user_platform=student_user_1.id,
            id_congress=enterprise_congress.id_congreso,
            enrollment_date=datetime.utcnow(),
            status=EnrollmentStatus.PAGADO,
        )
        session.add(enrollment)
        session.commit()
        session.refresh(enrollment)

        client = create_user_client(session, student_user_1)
        qr_string = f"UTA-FISEI-PASS-{enrollment.id}-{enterprise_congress.id_congreso}"
        payload = {
            "qr_payload": qr_string,
            "id_sesion": enterprise_session.id_sesion,
        }

        # Primer escaneo
        resp1 = send_attendance_scan(client, enterprise_congress.id_congreso, payload)
        assert resp1.status_code == 200

        # Segundo escaneo idéntico
        resp2 = send_attendance_scan(client, enterprise_congress.id_congreso, payload)
        assert resp2.status_code == 409
        assert "ya registró asistencia" in resp2.json()["detail"].lower()

    def test_scan_attendance_rejected_for_unpaid_enrollment(
        self,
        session: Session,
        student_user_1: UserPlatform,
        enterprise_congress: Congress,
        enterprise_session: SesionCronograma,
    ):
        """Verifica que se rechaza con HTTP 400 si la inscripción no está pagada/facturada."""
        unpaid_enrollment = Enrollment(
            id_user_platform=student_user_1.id,
            id_congress=enterprise_congress.id_congreso,
            enrollment_date=datetime.utcnow(),
            status=EnrollmentStatus.INTERESADO,
        )
        session.add(unpaid_enrollment)
        session.commit()
        session.refresh(unpaid_enrollment)

        client = create_user_client(session, student_user_1)
        qr_string = f"UTA-FISEI-PASS-{unpaid_enrollment.id}-{enterprise_congress.id_congreso}"

        response = send_attendance_scan(
            client,
            enterprise_congress.id_congreso,
            {
                "qr_payload": qr_string,
                "id_sesion": enterprise_session.id_sesion,
            },
        )
        assert response.status_code == 400
        detail = response.json()["detail"].lower()
        assert "pago" in detail or "pagada" in detail or "interesado" in detail

    def test_scan_attendance_supports_json_payload(
        self,
        session: Session,
        student_user_1: UserPlatform,
        enterprise_congress: Congress,
        enterprise_session: SesionCronograma,
    ):
        """Verifica que el escáner soporte también payloads serializados en formato JSON."""
        enrollment = Enrollment(
            id_user_platform=student_user_1.id,
            id_congress=enterprise_congress.id_congreso,
            enrollment_date=datetime.utcnow(),
            status=EnrollmentStatus.FACTURADO,
        )
        session.add(enrollment)
        session.commit()
        session.refresh(enrollment)

        client = create_user_client(session, student_user_1)
        json_qr = (
            f'{{"id_enrollment": {enrollment.id}, "id_congress": {enterprise_congress.id_congreso}}}'
        )

        response = send_attendance_scan(
            client,
            enterprise_congress.id_congreso,
            {
                "qr_payload": json_qr,
                "id_sesion": enterprise_session.id_sesion,
            },
        )
        assert response.status_code == 200
        assert response.json()["status"] == "OK"

    def test_list_session_attendance(
        self,
        session: Session,
        student_user_1: UserPlatform,
        enterprise_congress: Congress,
        enterprise_session: SesionCronograma,
    ):
        """Verifica el endpoint para consultar en vivo los asistentes a una sesión."""
        enrollment = Enrollment(
            id_user_platform=student_user_1.id,
            id_congress=enterprise_congress.id_congreso,
            enrollment_date=datetime.utcnow(),
            status=EnrollmentStatus.PAGADO,
        )
        session.add(enrollment)
        session.commit()
        session.refresh(enrollment)

        client = create_user_client(session, student_user_1)
        send_attendance_scan(
            client,
            enterprise_congress.id_congreso,
            {
                "qr_payload": f"UTA-FISEI-PASS-{enrollment.id}-{enterprise_congress.id_congreso}",
                "id_sesion": enterprise_session.id_sesion,
            },
        )

        response = get_attendance_list(
            client, enterprise_congress.id_congreso, enterprise_session.id_sesion
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_attendees"] >= 1
        attendee = data["data"][0]
        assert attendee["id_enrollment"] == enrollment.id
        assert attendee["identification"] == student_user_1.identification


# ==============================================================================
# 3. TESTS DE PERFIL Y SEGURIDAD / CONTRASEÑA (users_platform)
# ==============================================================================

class TestUserProfileAndSecurity:
    """Pruebas de actualización de perfil, inmutabilidad de la cédula y cambio de clave con bcrypt."""

    def test_update_profile_success(
        self, session: Session, student_user_1: UserPlatform
    ):
        """Verifica la actualización de campos personales y de contacto."""
        client = create_user_client(session, student_user_1)
        response = client.put(
            f"/api/v1/users/{student_user_1.id}/profile",
            json={
                "first_name": "Carlos Actualizado",
                "last_name": "Mora Sanchez",
                "phone": "0998887766",
                "address": "Campus Huachi FISEI Bloque 2",
            },
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["first_name"] == "Carlos Actualizado"
        assert data["phone"] == "0998887766"
        assert data["address"] == "Campus Huachi FISEI Bloque 2"

        # Verificar en base de datos
        session.refresh(student_user_1)
        assert student_user_1.first_name == "Carlos Actualizado"
        assert student_user_1.cellphone == "0998887766"

    def test_update_profile_cannot_change_identification(
        self, session: Session, student_user_1: UserPlatform
    ):
        """Regla de seguridad: La identificación (cédula/RUC) es estrictamente inmutable."""
        client = create_user_client(session, student_user_1)
        original_cedula = student_user_1.identification

        response = client.put(
            f"/api/v1/users/{student_user_1.id}/profile",
            json={
                "first_name": "Nombre Modificado",
                "identification": "9999999999",  # Intento de alterar la cédula
            },
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["identification"] == original_cedula
        assert data["identification"] != "9999999999"

        session.refresh(student_user_1)
        assert student_user_1.identification == original_cedula

    def test_update_password_wrong_current_password_rejected(
        self, session: Session, student_user_1: UserPlatform
    ):
        """Verifica que una contraseña actual incorrecta es rechazada con HTTP 400."""
        client = create_user_client(session, student_user_1)
        response = client.put(
            f"/api/v1/users/{student_user_1.id}/password",
            json={
                "current_password": "contrasena_incorrecta",
                "new_password": "nueva_password_segura_123",
            },
        )
        assert response.status_code == 400
        assert "Contraseña actual incorrecta" in response.json()["detail"]

        # La clave original sigue activa
        session.refresh(student_user_1)
        assert student_user_1.verify_password("Secret123!") is True

    def test_update_password_success_verifies_with_bcrypt(
        self, session: Session, student_user_1: UserPlatform
    ):
        """Verifica que el cambio exitoso de contraseña hashea con bcrypt y valida inmediatamente."""
        client = create_user_client(session, student_user_1)
        response = client.put(
            f"/api/v1/users/{student_user_1.id}/password",
            json={
                "current_password": "Secret123!",
                "new_password": "mi_nueva_super_clave_2026",
            },
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Contraseña actualizada exitosamente"

        # Refrescar y validar que la contraseña vieja ya no coincide y la nueva sí
        session.refresh(student_user_1)
        assert not student_user_1.verify_password("Secret123!")
        assert student_user_1.verify_password("mi_nueva_super_clave_2026")

    def test_get_user_profile(self, session: Session, student_user_1: UserPlatform):
        """Verifica que GET /api/v1/users/{user_id}/profile devuelve datos personales y de facturación SRI."""
        client = create_user_client(session, student_user_1)
        response = client.get(f"/api/v1/users/{student_user_1.id}/profile")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == student_user_1.id
        assert data["identification"] == student_user_1.identification
        assert "billing_identification" in data

    def test_update_password_forbidden_for_other_user(
        self, session: Session, student_user_1: UserPlatform, student_user_2: UserPlatform
    ):
        """Verifica que un usuario no puede modificar la contraseña de otro usuario (HTTP 403 Forbidden)."""
        client_2 = create_user_client(session, student_user_2)
        response = client_2.put(
            f"/api/v1/users/{student_user_1.id}/password",
            json={
                "current_password": "CualquierClave!",
                "new_password": "HackedPassword123!",
            },
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN



# ==============================================================================
# 4. TESTS DE GENERACIÓN DE RIDE PDF OFICIAL (Wave 2 Future-Proof)
# ==============================================================================

class TestRidePdfGeneration:
    """Verificación del comprobante / RIDE oficial en PDF con RUC institucional."""

    def test_ride_pdf_download_generates_valid_pdf_with_institutional_ruc(
        self,
        session: Session,
        student_user_1: UserPlatform,
        enterprise_congress: Congress,
    ):
        """
        Prueba la descarga del RIDE PDF oficial:
        - Endpoint: GET /api/v1/enrollments/{enrollment_id}/ride/download
        - Si el endpoint está en desarrollo en Wave 2, se documenta como xfail controlado.
        - Cuando está disponible: responde 200, Content-Type application/pdf, header %PDF y RUC 1860000880001.
        """
        enrollment = Enrollment(
            id_congress=enterprise_congress.id_congreso,
            id_user_platform=student_user_1.id,
            status=EnrollmentStatus.PAGADO,
            tariff_type="Estudiante UTA",
            amount=20.0,
            enrollment_date=datetime.utcnow(),
        )
        session.add(enrollment)
        session.commit()
        session.refresh(enrollment)

        client = create_user_client(session, student_user_1)
        res = client.get(f"/api/v1/enrollments/{enrollment.id}/ride/download")

        if res.status_code == status.HTTP_404_NOT_FOUND:
            pytest.xfail("Wave 2 implementation in progress: RIDE PDF download endpoint pending")

        assert res.status_code == status.HTTP_200_OK
        assert "application/pdf" in res.headers.get("content-type", "").lower()
        assert res.content.startswith(b"%PDF"), "El archivo no inicia con el encabezado estándar %PDF"
        assert b"1860000880001" in res.content, "El PDF del RIDE no contiene el RUC institucional 1860000880001"


# ==============================================================================
# 5. TESTS DE EXPORTADOR MOODLE LMS EN CSV (Wave 2 Future-Proof)
# ==============================================================================

class TestMoodleCsvExport:
    """Verificación de la exportación de nómina de alumnos a Moodle."""

    def test_moodle_csv_export_format_and_headers(
        self,
        session: Session,
        student_user_1: UserPlatform,
        enterprise_congress: Congress,
    ):
        """
        Prueba la exportación de inscritos a Moodle:
        - Endpoint: GET /api/v1/congresses/{congress_id}/export/moodle-csv
        - Si el endpoint está en desarrollo en Wave 2, se documenta como xfail controlado.
        - Cuando está disponible: responde 200, CSV con headers username,firstname,lastname,email.
        """
        enrollment = Enrollment(
            id_congress=enterprise_congress.id_congreso,
            id_user_platform=student_user_1.id,
            status=EnrollmentStatus.PAGADO,
            tariff_type="Estudiante UTA",
            enrollment_date=datetime.utcnow(),
        )
        session.add(enrollment)
        session.commit()
        session.refresh(enrollment)

        client = create_user_client(session, student_user_1)
        res = client.get(f"/api/v1/congresses/{enterprise_congress.id_congreso}/export/moodle-csv")
        if res.status_code == 404:
            res = client.get(f"/api/v1/congresses-new/{enterprise_congress.id_congreso}/export/moodle-csv")

        if res.status_code == status.HTTP_404_NOT_FOUND:
            pytest.xfail("Wave 2 implementation in progress: Moodle CSV export endpoint pending")

        assert res.status_code == status.HTTP_200_OK
        content_type = res.headers.get("content-type", "").lower()
        assert "csv" in content_type or "text/" in content_type

        csv_reader = csv.reader(io.StringIO(res.text))
        rows = list(csv_reader)
        assert len(rows) >= 2, "El archivo CSV debe contener al menos el encabezado y 1 estudiante"

        header = [col.strip().lower() for col in rows[0]]
        for expected_col in ["username", "firstname", "lastname", "email"]:
            assert expected_col in header, f"Falta la columna '{expected_col}' en el CSV de Moodle"

        user_emails = [r[header.index("email")].strip() for r in rows[1:] if len(r) > header.index("email")]
        assert student_user_1.email in user_emails
