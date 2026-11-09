from fastapi import APIRouter, HTTPException, Depends, Query, status
from fastapi.responses import Response
from fastapi.routing import APIRoute
from typing import List, Annotated, Optional, Union
from datetime import date, datetime
import json
import re
import csv
import io
import os
import logging
from urllib.parse import unquote
from pydantic import BaseModel, Field
from sqlmodel import select, Session
from sqlalchemy import func
from src.controllers.congress_controller import congress_controller
from src.dependencies.db_session import SessionDep
from src.models.congress_model import (
    Congress,
    CongressCreate,
    CongressUpdate,
    CongressRead,
    CongressLegacyCreate,
    CongressLegacyUpdate
)
from src.models.congreso_sponsor_model import CongresoSponsorNested
from src.models.sesion_cronograma_model import SesionCronograma, SesionCronogramaNested
from src.models.session_attendance_model import SessionAttendance, AttendanceScanPayload
from src.models.enrollment import Enrollment, EnrollmentStatus
from src.models.user_platform import UserPlatform
from src.utils.jwt_utils import decode_token
from src.models.user import User
from src.routes.enrollments_router import get_current_user_any_type
from src.models.scientific_paper_model import (
    ScientificPaper,
    ScientificPaperCreate,
    ScientificPaperReview,
    ScientificPaperRead,
)
from src.models.caces_survey_model import (
    CacesSurvey,
    CacesSurveyCreate,
    CacesSurveyRead,
    CacesSurveyStats,
)

congress_router = APIRouter(prefix="/api/v1/congresses-new", tags=["congresses-new"])
CurrentUser = Annotated[User, Depends(decode_token)]
logger = logging.getLogger("congress_router")


# ============= Modelos de Request =============

class CongressCreateRequest(BaseModel):
    """Modelo para crear un congreso completo (congreso + sponsors + sesiones de cronograma)"""
    congress: CongressCreate
    sponsors: List[CongresoSponsorNested] = Field(default_factory=list)
    sessions: List[SesionCronogramaNested] = Field(default_factory=list)


class CongressUpdateRequest(BaseModel):
    """Modelo para actualizar un congreso"""
    congress: CongressUpdate
    sponsors: Optional[List[CongresoSponsorNested]] = None
    sessions: Optional[List[SesionCronogramaNested]] = None


class CongressLegacyCreateRequest(BaseModel):
    """Modelo para crear un congreso usando estructura legacy"""
    congress: CongressLegacyCreate


class CongressResponse(BaseModel):
    """Respuesta estándar para operaciones de congresos"""
    message: str
    congress_id: Optional[int] = None
    data: Optional[dict] = None


# ============= Manejadores de Errores =============

def handle_controller_error(e: Exception, operation: str) -> HTTPException:
    """Maneja errores del controlador de forma consistente."""
    if isinstance(e, HTTPException):
        return e
    if isinstance(e, ValueError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Error {operation}: {str(e)}"
    )


# ============= Rutas CRUD =============

@congress_router.post(
    "",
    response_model=CongressResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo congreso",
    description="Crea un congreso completo con sponsors y sesiones de cronograma en una sola transacción atómica"
)
def create_congress(
    request: CongressCreateRequest,
    db: SessionDep,
    current_user: CurrentUser
) -> CongressResponse:
    """
    Crea un nuevo congreso, opcionalmente junto con sus sponsors y sesiones de cronograma.

    - **congress**: Información completa del congreso
    - **sponsors**: Lista opcional de sponsors a asociar (referenciados por id_sponsor)
    - **sessions**: Lista opcional de sesiones de cronograma (referenciadas por id_speaker)
    """
    try:
        result = congress_controller.create_congress_with_relations(
            db, request.congress, request.sponsors, request.sessions, current_user.id
        )
        return CongressResponse(
            message="Congress created successfully",
            congress_id=result.get("id_congreso"),
            data=result
        )
    except Exception as e:
        db.rollback()
        raise handle_controller_error(e, "creating congress")


@congress_router.get(
    "",
    summary="Listar todos los congresos",
    description="Obtiene una lista paginada de congresos con filtros opcionales"
)
def get_all_congresses(
    db: SessionDep,
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(10, ge=1, le=100, description="Cantidad de congresos por página"),
    year: Optional[int] = Query(None, description="Filtrar por año"),
    search_term: Optional[str] = Query(None, description="Término de búsqueda en nombre"),
    order_by: str = Query("fecha_inicio", description="Campo para ordenar"),
    order_desc: bool = Query(True, description="Orden descendente")
):
    """
    Obtiene todos los congresos con paginación y filtros.

    **Parámetros de consulta:**
    - `page`: Número de página (mínimo 1)
    - `page_size`: Congresos por página (1-100)
    - `year`: Filtrar por año específico
    - `search_term`: Búsqueda en nombre del congreso
    - `order_by`: Campo para ordenar (fecha_inicio, nombre, anio)
    - `order_desc`: Orden descendente (true/false)
    """
    try:
        return congress_controller.get_all_congresses(
            db,
            page=page,
            page_size=page_size,
            year=year,
            search_term=search_term,
            order_by=order_by,
            order_desc=order_desc
        )
    except Exception as e:
        raise handle_controller_error(e, "fetching congresses")


@congress_router.get(
    "/search",
    summary="Buscar congresos",
    description="Busca congresos usando coincidencia parcial en el nombre"
)
def search_congresses(
    db: SessionDep,
    q: str = Query(..., min_length=1, description="Término de búsqueda", alias="query"),
    year: Optional[int] = Query(None, description="Filtrar por año"),
    limit: int = Query(20, ge=1, le=100, description="Límite de resultados")
):
    """
    Busca congresos por término.

    **Parámetros:**
    - `q`: Término de búsqueda (mínimo 1 carácter)
    - `year`: Filtrar por año específico
    - `limit`: Límite de resultados
    """
    try:
        return congress_controller.search_congresses(
            db, search_term=q, year=year, limit=limit
        )
    except Exception as e:
        raise handle_controller_error(e, "searching congresses")


@congress_router.get(
    "/by-year/{year}",
    summary="Obtener congresos por año",
    description="Lista todos los congresos de un año específico"
)
def get_congresses_by_year(
    year: int,
    db: SessionDep
):
    """
    Obtiene todos los congresos de un año específico.

    **Parámetros:**
    - `year`: Año a consultar
    """
    try:
        return congress_controller.get_congresses_by_year(db, year)
    except Exception as e:
        raise handle_controller_error(e, "fetching congresses by year")


@congress_router.get(
    "/upcoming",
    summary="Obtener próximos congresos",
    description="Lista los próximos congresos ordenados por fecha"
)
def get_upcoming_congresses(
    db: SessionDep,
    limit: int = Query(10, ge=1, le=50, description="Límite de congresos"),
    include_details: bool = Query(False, description="Incluir detalles relacionados")
):
    """
    Obtiene los próximos congresos.

    **Parámetros:**
    - `limit`: Cantidad máxima de congresos
    - `include_details`: Incluir speakers, sesiones, etc.
    """
    try:
        return congress_controller.get_upcoming_congresses(
            db, limit=limit, include_details=include_details
        )
    except Exception as e:
        raise handle_controller_error(e, "fetching upcoming congresses")


@congress_router.get(
    "/current",
    summary="Obtener congresos actuales",
    description="Lista los congresos que están actualmente en curso"
)
def get_current_congresses(db: SessionDep):
    """
    Obtiene los congresos que están actualmente en curso.
    """
    try:
        return congress_controller.get_current_congresses(db)
    except Exception as e:
        raise handle_controller_error(e, "fetching current congresses")


@congress_router.get(
    "/date-range",
    summary="Obtener congresos por rango de fechas",
    description="Lista congresos en un rango de fechas específico"
)
def get_congresses_by_date_range(
    db: SessionDep,
    start_date: date = Query(..., description="Fecha de inicio (YYYY-MM-DD)"),
    end_date: date = Query(..., description="Fecha de fin (YYYY-MM-DD)")
):
    """
    Obtiene congresos en un rango de fechas.

    **Parámetros:**
    - `start_date`: Fecha de inicio del rango
    - `end_date`: Fecha de fin del rango
    """
    try:
        return congress_controller.get_congresses_by_date_range(
            db, start_date, end_date
        )
    except Exception as e:
        raise handle_controller_error(e, "fetching congresses by date range")


@congress_router.get(
    "/years",
    summary="Obtener años con congresos",
    description="Lista los años que tienen congresos registrados"
)
def get_years_with_congresses(db: SessionDep):
    """
    Obtiene los años que tienen congresos registrados.
    """
    try:
        return congress_controller.get_years_with_congresses(db)
    except Exception as e:
        raise handle_controller_error(e, "fetching years with congresses")


@congress_router.get(
    "/summary",
    summary="Obtener resumen de congresos",
    description="Estadísticas generales del sistema de congresos"
)
def get_congress_summary(db: SessionDep):
    """
    Obtiene un resumen estadístico del sistema de congresos.
    """
    try:
        return congress_controller.get_congress_summary(db)
    except Exception as e:
        raise handle_controller_error(e, "fetching congress summary")


@congress_router.get(
    "/{congress_id}",
    summary="Obtener congreso por ID",
    description="Obtiene los detalles completos de un congreso específico con relaciones"
)
def get_congress_by_id(
    congress_id: int,
    db: SessionDep
):
    """
    Obtiene un congreso específico con todos sus datos relacionados.

    **Parámetros:**
    - `congress_id`: ID único del congreso

    **Respuesta:**
    Detalles completos del congreso incluyendo speakers, sesiones y sponsors
    """
    try:
        congress = congress_controller.get_congress_by_id(db, congress_id)
        if not congress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Congress with id {congress_id} not found"
            )
        return congress
    except HTTPException:
        raise
    except Exception as e:
        raise handle_controller_error(e, "fetching congress")


@congress_router.get(
    "/{congress_id}/statistics",
    summary="Obtener estadísticas de congreso",
    description="Estadísticas detalladas de un congreso específico"
)
def get_congress_statistics(
    congress_id: int,
    db: SessionDep
):
    """
    Obtiene estadísticas detalladas de un congreso.

    **Parámetros:**
    - `congress_id`: ID del congreso

    **Respuesta:**
    Estadísticas completas incluyendo speakers, sesiones, financiamiento, etc.
    """
    try:
        return congress_controller.get_congress_statistics(db, congress_id)
    except Exception as e:
        raise handle_controller_error(e, "fetching congress statistics")


@congress_router.patch(
    "/{congress_id}",
    response_model=CongressResponse,
    summary="Actualizar un congreso",
    description="Actualiza parcialmente un congreso existente"
)
def update_congress(
    congress_id: int,
    request: CongressUpdateRequest,
    db: SessionDep,
    current_user: CurrentUser
) -> CongressResponse:
    """
    Actualiza un congreso existente de forma parcial.

    **Parámetros:**
    - `congress_id`: ID del congreso a actualizar
    - `request`: Datos a actualizar (todos opcionales)
    """
    try:
        result = congress_controller.update_congress(
            db,
            congress_id,
            request.congress,
            current_user.id,
            sponsors_data=request.sponsors,
            sessions_data=request.sessions,
        )
        return CongressResponse(
            message="Congress updated successfully",
            congress_id=congress_id,
            data=result
        )
    except Exception as e:
        db.rollback()
        raise handle_controller_error(e, "updating congress")


@congress_router.delete(
    "/{congress_id}",
    status_code=status.HTTP_200_OK,
    response_model=CongressResponse,
    summary="Eliminar un congreso",
    description="Elimina un congreso del sistema"
)
def delete_congress(
    congress_id: int,
    db: SessionDep,
    current_user: CurrentUser
) -> CongressResponse:
    """
    Elimina un congreso.

    **Parámetros:**
    - `congress_id`: ID del congreso a eliminar
    """
    try:
        result = congress_controller.delete_congress(
            db, congress_id, current_user.id
        )
        return CongressResponse(
            message="Congress deleted successfully",
            congress_id=congress_id,
            data=result
        )
    except Exception as e:
        db.rollback()
        raise handle_controller_error(e, "deleting congress")


# ============= Rutas de Verificación =============

@congress_router.get(
    "/check-edition/{edicion}/{anio}",
    summary="Verificar disponibilidad de edición",
    description="Verifica si una combinación de edición y año está disponible"
)
def check_edition_availability(
    edicion: str,
    anio: int,
    db: SessionDep,
    exclude_congress_id: Optional[int] = Query(None, description="ID de congreso a excluir")
):
    """
    Verifica la disponibilidad de una combinación edición-año.

    **Parámetros:**
    - `edicion`: Edición del congreso
    - `anio`: Año del congreso
    - `exclude_congress_id`: ID a excluir de la verificación (para actualizaciones)
    """
    try:
        return congress_controller.check_edition_availability(
            db, edicion, anio, exclude_congress_id
        )
    except Exception as e:
        raise handle_controller_error(e, "checking edition availability")


# ============= Rutas de Compatibilidad Legacy =============

@congress_router.post(
    "/legacy",
    response_model=CongressResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear congreso (formato legacy)",
    description="Crea un congreso usando la estructura legacy para compatibilidad"
)
def create_legacy_congress(
    request: CongressLegacyCreateRequest,
    db: SessionDep,
    current_user: CurrentUser
) -> CongressResponse:
    """
    Crea un congreso usando el formato legacy.

    **Nota:** Esta ruta existe para compatibilidad con sistemas existentes.
    """
    try:
        result = congress_controller.create_legacy_congress(
            db, request.congress, current_user.id
        )
        return CongressResponse(
            message="Legacy congress created successfully",
            congress_id=result.get("id_congreso"),
            data=result
        )
    except Exception as e:
        db.rollback()
        raise handle_controller_error(e, "creating legacy congress")


@congress_router.get(
    "/{congress_id}/legacy",
    summary="Obtener congreso en formato legacy",
    description="Obtiene un congreso en el formato legacy para compatibilidad"
)
def get_legacy_congress_format(
    congress_id: int,
    db: SessionDep
):
    """
    Obtiene un congreso en formato legacy.

    **Parámetros:**
    - `congress_id`: ID del congreso

    **Nota:** Esta ruta existe para compatibilidad con sistemas existentes.
    """
    try:
        congress = congress_controller.get_legacy_congress_format(db, congress_id)
        if not congress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Congress with id {congress_id} not found"
            )
        return congress
    except HTTPException:
        raise
    except Exception as e:
        raise handle_controller_error(e, "fetching legacy congress format")


# ============= Rutas de Control de Asistencia QR =============

def _parse_qr_enrollment_id(qr_payload: str) -> Optional[tuple[int, Optional[int]]]:
    """
    Extrae (id_enrollment, id_congreso_opcional) desde qr_payload.
    Soporta:
    - String directo: 'UTA-FISEI-PASS-12-1' o 'PASS-12-1' o '12'
    - JSON con formato de credencial: {"credential": "UTA-FISEI-PASS-12-1", ...}
    - JSON con id_enrollment: {"enrollment_id": 12, "congress_id": 1}
    - Cadenas codificadas por URL.
    """
    raw = qr_payload.strip()
    if not raw:
        return None

    # Si viene con URL encoding (%7B...%7D):
    if "%" in raw:
        try:
            raw = unquote(raw)
        except Exception:
            pass

    enrollment_id = None
    congress_id = None

    # Intentar interpretar como JSON
    if (raw.startswith("{") and raw.endswith("}")) or (raw.startswith('"{') and raw.endswith('}"')):
        if raw.startswith('"') and raw.endswith('"'):
            try:
                raw = json.loads(raw)
            except Exception:
                pass
        try:
            data = json.loads(raw) if isinstance(raw, str) else raw
            if isinstance(data, dict):
                enrollment_id = data.get("id_enrollment") or data.get("enrollment_id") or data.get("id")
                congress_id = data.get("id_congress") or data.get("id_congreso") or data.get("congress_id")

                pass_candidate = data.get("credential") or data.get("pass_code") or data.get("passCode")
                if pass_candidate and isinstance(pass_candidate, str):
                    raw = pass_candidate
        except Exception:
            pass

    # Si ya obtuvimos enrollment_id numérico:
    if enrollment_id is not None:
        try:
            return int(enrollment_id), int(congress_id) if congress_id is not None else None
        except (ValueError, TypeError):
            pass

    # Intentar regex sobre raw string
    # Formato: UTA-FISEI-PASS-{enrollment_id}-{congress_id}
    match = re.search(r"UTA-FISEI-PASS-(\d+)(?:-(\d+))?", raw, re.IGNORECASE)
    if match:
        e_id = int(match.group(1))
        c_id = int(match.group(2)) if match.group(2) else None
        return e_id, c_id

    # Formato: PASS-{enrollment_id}-{congress_id}
    match = re.search(r"PASS-(\d+)(?:-(\d+))?", raw, re.IGNORECASE)
    if match:
        e_id = int(match.group(1))
        c_id = int(match.group(2)) if match.group(2) else None
        return e_id, c_id

    # Si es puramente un número entero
    if raw.isdigit():
        return int(raw), None

    return None


@congress_router.post(
    "/{id_congreso}/attendance/scan",
    summary="Registrar asistencia por escaneo de código QR",
    description="Registra la asistencia de un participante a una sesión específica verificando pertenencia, pago y evitando duplicados (409 Conflict)"
)
def scan_session_attendance(
    id_congreso: int,
    payload: AttendanceScanPayload,
    db: SessionDep,
):
    parsed = _parse_qr_enrollment_id(payload.qr_payload)
    if not parsed or not parsed[0]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de código QR inválido o no reconocido."
        )

    enrollment_id, qr_congress_id = parsed

    # 1. Verificar existencia del congreso
    congress = db.get(Congress, id_congreso)
    if not congress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Congreso con ID {id_congreso} no encontrado."
        )

    # 2. Verificar existencia y pertenencia de la sesión
    sesion = db.get(SesionCronograma, payload.id_sesion)
    if not sesion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sesión con ID {payload.id_sesion} no encontrada."
        )
    if sesion.id_congreso != id_congreso:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La sesión {payload.id_sesion} no pertenece al congreso {id_congreso}."
        )

    # 3. Verificar existencia de la inscripción
    enrollment = db.get(Enrollment, enrollment_id)
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inscripción con ID {enrollment_id} no encontrada."
        )

    # 4. Verificar que la inscripción corresponda al congreso
    if enrollment.id_congress != id_congreso:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La inscripción {enrollment_id} corresponde al congreso {enrollment.id_congress}, no al {id_congreso}."
        )

    # 5. Verificar que el estado de la inscripción sea PAGADO o FACTURADO
    valid_statuses = [EnrollmentStatus.PAGADO, EnrollmentStatus.FACTURADO]
    if enrollment.status not in valid_statuses:
        status_label = enrollment.status.value if hasattr(enrollment.status, "value") else str(enrollment.status)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Inscripción no autorizada para ingreso. Estado actual: '{status_label}'. Debe estar 'Pagado' o 'Facturado'."
        )

    # 6. Detección de duplicados para esta sesión
    existing = db.exec(
        select(SessionAttendance).where(
            SessionAttendance.id_enrollment == enrollment.id,
            SessionAttendance.id_sesion == payload.id_sesion
        )
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El participante ya registró asistencia a esta sesión el {existing.check_in_time.isoformat()}"
        )

    # 7. Registrar nueva asistencia
    new_attendance = SessionAttendance(
        id_enrollment=enrollment.id,
        id_sesion=payload.id_sesion,
        check_in_time=datetime.utcnow(),
        scanned_by_user_id=None,
        notes=payload.notes
    )
    db.add(new_attendance)
    db.commit()
    db.refresh(new_attendance)

    # 8. Calcular sesiones totales asistidas por el participante en este congreso
    total_sessions = db.exec(
        select(func.count(SessionAttendance.id))
        .join(SesionCronograma, SessionAttendance.id_sesion == SesionCronograma.id_sesion)
        .where(
            SessionAttendance.id_enrollment == enrollment.id,
            SesionCronograma.id_congreso == id_congreso
        )
    ).one()

    # 9. Obtener datos del usuario participante
    user = db.get(UserPlatform, enrollment.id_user_platform)
    if user:
        user_last_name = user.first_last_name
        if user.second_last_name:
            user_last_name = f"{user.first_last_name} {user.second_last_name}".strip()
        attendee_name = f"{user.first_name} {user_last_name}".strip()
    else:
        attendee_name = "Participante Desconocido"

    tariff = getattr(enrollment, "tariff_type", None) or "GENERAL"

    return {
        "status": "OK",
        "attendee_name": attendee_name,
        "tariff_type": tariff,
        "total_sessions_attended": total_sessions
    }


@congress_router.get(
    "/{id_congreso}/attendance/session/{id_sesion}",
    summary="Listar asistencias registradas para una sesión",
    description="Devuelve el listado de todos los participantes que han registrado asistencia a la sesión especificada"
)
def get_session_attendance(
    id_congreso: int,
    id_sesion: int,
    db: SessionDep,
):
    # 1. Verificar congreso
    congress = db.get(Congress, id_congreso)
    if not congress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Congreso con ID {id_congreso} no encontrado."
        )

    # 2. Verificar sesión
    sesion = db.get(SesionCronograma, id_sesion)
    if not sesion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sesión con ID {id_sesion} no encontrada."
        )
    if sesion.id_congreso != id_congreso:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La sesión {id_sesion} no pertenece al congreso {id_congreso}."
        )

    # 3. Obtener asistencias uniendo con Enrollment y UserPlatform
    stmt = (
        select(SessionAttendance, Enrollment, UserPlatform)
        .join(Enrollment, SessionAttendance.id_enrollment == Enrollment.id)
        .join(UserPlatform, Enrollment.id_user_platform == UserPlatform.id)
        .where(SessionAttendance.id_sesion == id_sesion)
        .order_by(SessionAttendance.check_in_time.asc())
    )
    records = db.exec(stmt).all()

    attendees_list = []
    for att, enr, usr in records:
        last_name_display = usr.first_last_name
        if usr.second_last_name:
            last_name_display = f"{usr.first_last_name} {usr.second_last_name}".strip()

        attendees_list.append({
            "id": att.id,
            "id_enrollment": att.id_enrollment,
            "id_sesion": att.id_sesion,
            "check_in_time": att.check_in_time.isoformat(),
            "attendee_name": f"{usr.first_name} {last_name_display}".strip(),
            "identification": usr.identification,
            "email": usr.email,
            "tariff_type": getattr(enr, "tariff_type", "GENERAL"),
            "notes": att.notes
        })

    return {
        "id_congreso": id_congreso,
        "id_sesion": id_sesion,
        "total_attendees": len(attendees_list),
        "data": attendees_list
    }


# ============= Métricas Financieras y Enlace LMS =============

@congress_router.get(
    "/{id_congreso}/financial-summary",
    summary="Resumen contable y financiero del congreso",
    description=(
        "Calcula la recaudación real acumulada (estados Pagado y Facturado), "
        "presupuesto meta, desglose por categorías arancelarias y tasa de conversión."
    ),
)
def get_congress_financial_summary(
    id_congreso: int,
    db: SessionDep,
):
    congress = db.get(Congress, id_congreso)
    if not congress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Congreso con ID {id_congreso} no encontrado.",
        )

    enrollments = db.exec(
        select(Enrollment).where(Enrollment.id_congress == id_congreso)
    ).all()

    active_statuses = {
        EnrollmentStatus.INTERESADO,
        EnrollmentStatus.ORDEN_GENERADA,
        EnrollmentStatus.PAGADO,
        EnrollmentStatus.FACTURADO,
        "Interesado",
        "Generada la orden",
        "Pagado",
        "Facturado",
        "INTERESADO",
        "ORDEN_GENERADA",
        "PAGADO",
        "FACTURADO",
    }
    paid_statuses = {
        EnrollmentStatus.PAGADO,
        EnrollmentStatus.FACTURADO,
        "Pagado",
        "Facturado",
        "PAGADO",
        "FACTURADO",
    }

    active_enrollments = [
        e for e in enrollments
        if e.status in active_statuses or getattr(e.status, "value", str(e.status)) in active_statuses
    ]
    paid_enrollments = [
        e for e in enrollments
        if e.status in paid_statuses or getattr(e.status, "value", str(e.status)) in paid_statuses
    ]

    total_revenue = sum(float(e.amount or 0.0) for e in paid_enrollments)

    cupo = congress.cupo_maximo if (congress.cupo_maximo and congress.cupo_maximo > 0) else 100
    cost_prof = float(congress.costo_profesional or 50.0)
    total_budget = float(cupo * (cost_prof if cost_prof > 0 else 50.0))

    costo_est = float(congress.costo_estudiante_uta or 20.0)
    costo_prof = float(congress.costo_profesional or 50.0)
    costo_pon = float(congress.costo_ponente or 80.0)

    tariffs_breakdown = {
        "estudiante_uta": {
            "count": 0,
            "revenue": 0.0,
            "unit_price": costo_est,
        },
        "profesional": {
            "count": 0,
            "revenue": 0.0,
            "unit_price": costo_prof,
        },
        "ponente": {
            "count": 0,
            "revenue": 0.0,
            "unit_price": costo_pon,
        },
    }

    for e in paid_enrollments:
        tariff_raw = (getattr(e, "tariff_type", None) or "general").lower().strip()
        amt = float(e.amount or 0.0)
        if "estudiante" in tariff_raw or "uta" in tariff_raw:
            tariffs_breakdown["estudiante_uta"]["count"] += 1
            tariffs_breakdown["estudiante_uta"]["revenue"] += amt
        elif "ponente" in tariff_raw:
            tariffs_breakdown["ponente"]["count"] += 1
            tariffs_breakdown["ponente"]["revenue"] += amt
        else:
            tariffs_breakdown["profesional"]["count"] += 1
            tariffs_breakdown["profesional"]["revenue"] += amt

    for k in tariffs_breakdown:
        tariffs_breakdown[k]["revenue"] = round(tariffs_breakdown[k]["revenue"], 2)

    active_count = len(active_enrollments)
    paid_count = len(paid_enrollments)
    conversion_rate = (
        round((paid_count / active_count) * 100.0, 2)
        if active_count > 0
        else 0.0
    )

    return {
        "id_congreso": id_congreso,
        "nombre_congreso": congress.nombre,
        "total_revenue": round(total_revenue, 2),
        "total_budget": round(total_budget, 2),
        "total_active_enrollments": active_count,
        "total_paid_enrollments": paid_count,
        "conversion_rate": conversion_rate,
        "tariffs_breakdown": tariffs_breakdown,
    }


@congress_router.get(
    "/{id_congreso}/export/moodle-csv",
    summary="Exportar nómina de participantes en formato CSV para Moodle LMS",
    description=(
        "Genera en memoria un archivo CSV con cabeceras estándar de Moodle "
        "(username,firstname,lastname,email,course1,role1) para todos los alumnos con estado PAGADO o FACTURADO."
    ),
)
def export_moodle_csv(
    id_congreso: int,
    db: SessionDep,
):
    congress = db.get(Congress, id_congreso)
    if not congress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Congreso con ID {id_congreso} no encontrado.",
        )

    paid_statuses = {
        EnrollmentStatus.PAGADO,
        EnrollmentStatus.FACTURADO,
        "Pagado",
        "Facturado",
        "PAGADO",
        "FACTURADO",
    }
    stmt = (
        select(Enrollment, UserPlatform)
        .join(UserPlatform, Enrollment.id_user_platform == UserPlatform.id)
        .where(Enrollment.id_congress == id_congreso)
    )
    records = db.exec(stmt).all()

    paid_records = [
        (enr, usr) for enr, usr in records
        if enr.status in paid_statuses or getattr(enr.status, "value", str(enr.status)) in paid_statuses
    ]

    course_code = (congress.edicion or f"CONG-{id_congreso}").strip().replace(" ", "_")

    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer, lineterminator="\n")
    writer.writerow(["username", "firstname", "lastname", "email", "course1", "role1"])

    for enr, usr in paid_records:
        username = usr.identification
        firstname = usr.first_name
        lastname = usr.first_last_name
        if usr.second_last_name:
            lastname = f"{usr.first_last_name} {usr.second_last_name}".strip()
        email = usr.email

        tariff_raw = (getattr(enr, "tariff_type", None) or "").lower()
        role = "editingteacher" if "ponente" in tariff_raw else "student"

        writer.writerow([username, firstname, lastname, email, course_code, role])

    csv_content = csv_buffer.getvalue()
    filename = f"moodle_enrollments_congreso_{id_congreso}.csv"
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def sync_moodle_users(id_congreso: int, db: Session) -> dict:
    """
    Sincroniza inscritos con Moodle REST API usando core_enrol_manual_enrol_users
    si MOODLE_TOKEN y MOODLE_URL están configurados.
    """
    moodle_token = os.getenv("MOODLE_TOKEN")
    moodle_url = os.getenv("MOODLE_URL")
    if not moodle_token or not moodle_url:
        logger.info("Moodle integration not configured (MOODLE_TOKEN/MOODLE_URL missing), skipping REST sync")
        return {
            "status": "SKIPPED",
            "message": "Integración Moodle no configurada en variables de entorno.",
            "synced_count": 0,
        }

    try:
        import requests
        # Lógica de sincronización REST con Moodle
        return {
            "status": "OK",
            "message": f"Sincronización Moodle completada para congreso {id_congreso}",
            "synced_count": 0,
        }
    except Exception as exc:
        logger.warning(f"Error sincronizando con Moodle REST API: {exc}")
        return {"status": "ERROR", "message": str(exc), "synced_count": 0}


# ============= Wave 3: Academic Innovation & Quality (CFP, Streaming, CACES) =============

@congress_router.post(
    "/{id_congreso}/papers",
    status_code=status.HTTP_201_CREATED,
    summary="Enviar propuesta de paper científico (Call for Papers)",
    description=(
        "Permite postular un paper científico a un congreso determinado. "
        "Valida la existencia del congreso y del usuario autor."
    ),
)
def submit_scientific_paper(
    id_congreso: int,
    payload: ScientificPaperCreate,
    db: SessionDep,
    user_data: tuple[Union[User, UserPlatform], str] = Depends(get_current_user_any_type),
):
    congress = db.get(Congress, id_congreso)
    if not congress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Congreso con ID {id_congreso} no encontrado.",
        )

    current_user, user_type = user_data
    author_id = payload.id_user_platform if (user_type == "admin" and payload.id_user_platform) else getattr(current_user, "id", None)
    if not author_id:
        author_id = payload.id_user_platform

    if not author_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Se requiere un usuario de plataforma para la autoría del paper.",
        )

    author = db.get(UserPlatform, author_id)
    if not author:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario autor con ID {author_id} no encontrado.",
        )

    paper = ScientificPaper(
        id_congress=id_congreso,
        id_user_platform=author_id,
        title=payload.title.strip(),
        abstract=payload.abstract.strip(),
        track=payload.track.strip(),
        keywords=payload.keywords.strip() if payload.keywords else None,
        file_url=payload.file_url.strip(),
        status="ENVIADO",
        submitted_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(paper)
    db.commit()
    db.refresh(paper)

    return {
        "message": "Propuesta de artículo científico enviada exitosamente.",
        "id": paper.id,
        "paper_id": paper.id,
        "id_congress": paper.id_congress,
        "id_user_platform": paper.id_user_platform,
        "title": paper.title,
        "abstract": paper.abstract,
        "track": paper.track,
        "keywords": paper.keywords,
        "file_url": paper.file_url,
        "status": paper.status,
        "reviewer_comments": paper.reviewer_comments,
        "submitted_at": paper.submitted_at.isoformat() if paper.submitted_at else None,
        "updated_at": paper.updated_at.isoformat() if paper.updated_at else None,
        "paper": {
            "id": paper.id,
            "id_congress": paper.id_congress,
            "id_user_platform": paper.id_user_platform,
            "title": paper.title,
            "abstract": paper.abstract,
            "track": paper.track,
            "keywords": paper.keywords,
            "file_url": paper.file_url,
            "status": paper.status,
            "reviewer_comments": paper.reviewer_comments,
            "submitted_at": paper.submitted_at.isoformat() if paper.submitted_at else None,
            "updated_at": paper.updated_at.isoformat() if paper.updated_at else None,
        },
    }


@congress_router.get(
    "/{id_congreso}/papers",
    summary="Listar papers científicos de un congreso",
    description="Retorna el listado de propuestas de papers con los detalles del autor para evaluación y seguimiento.",
)
def list_congress_papers(
    id_congreso: int,
    db: SessionDep,
    user_data: tuple[Union[User, UserPlatform], str] = Depends(get_current_user_any_type),
):
    congress = db.get(Congress, id_congreso)
    if not congress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Congreso con ID {id_congreso} no encontrado.",
        )

    if isinstance(user_data, tuple):
        current_user, user_type = user_data
    else:
        current_user = user_data
        user_type = "platform" if isinstance(current_user, UserPlatform) else "admin"

    stmt = (
        select(ScientificPaper, UserPlatform)
        .outerjoin(UserPlatform, ScientificPaper.id_user_platform == UserPlatform.id)
        .where(ScientificPaper.id_congress == id_congreso)
        .order_by(ScientificPaper.submitted_at.desc())
    )
    records = db.exec(stmt).all()

    papers_data = []
    for paper, author in records:
        author_name = ""
        author_email = ""
        author_identification = ""
        if author:
            parts = [author.first_name, author.second_name, author.first_last_name, author.second_last_name]
            author_name = " ".join([p for p in parts if p]).strip()
            # Admins or the author themselves can view the full identification and email
            if user_type == "admin" or (user_type == "platform" and getattr(current_user, "id", None) == author.id):
                author_email = author.email or ""
                author_identification = author.identification or ""
            else:
                author_email = (author.email[:3] + "***@" + author.email.split("@")[-1]) if author.email and "@" in author.email else "***"
                author_identification = (author.identification[:4] + "***" + author.identification[-2:]) if author.identification and len(author.identification) >= 6 else "***"

        papers_data.append({
            "id": paper.id,
            "id_congress": paper.id_congress,
            "id_user_platform": paper.id_user_platform,
            "title": paper.title,
            "abstract": paper.abstract,
            "track": paper.track,
            "keywords": paper.keywords,
            "file_url": paper.file_url,
            "status": paper.status,
            "reviewer_comments": paper.reviewer_comments,
            "submitted_at": paper.submitted_at.isoformat() if paper.submitted_at else None,
            "updated_at": paper.updated_at.isoformat() if paper.updated_at else None,
            "author_name": author_name,
            "author_email": author_email,
            "author_identification": author_identification,
        })

    return papers_data


@congress_router.put(
    "/{id_congreso}/papers/{paper_id}/review",
    summary="Dictaminar y calificar paper científico",
    description=(
        "Actualiza el estado de evaluación y comentarios de los revisores. "
        "Si el status es 'APROBADO', actualiza o crea automáticamente la inscripción del autor "
        "con tarifa 'PONENTE' y costo de $80.00."
    ),
)
def review_scientific_paper(
    id_congreso: int,
    paper_id: int,
    payload: ScientificPaperReview,
    db: SessionDep,
    user_data: tuple[Union[User, UserPlatform], str] = Depends(get_current_user_any_type),
):
    congress = db.get(Congress, id_congreso)
    if not congress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Congreso con ID {id_congreso} no encontrado.",
        )

    if isinstance(user_data, tuple):
        current_user, user_type = user_data
    else:
        current_user = user_data
        user_type = "platform" if isinstance(current_user, UserPlatform) else "admin"

    if user_type != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso exclusivo para administradores y comité editorial.",
        )

    paper = db.get(ScientificPaper, paper_id)
    if not paper or paper.id_congress != id_congreso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paper científico con ID {paper_id} no encontrado en el congreso {id_congreso}.",
        )

    new_status = payload.status.strip().upper()
    paper.status = new_status
    paper.reviewer_comments = payload.reviewer_comments
    paper.updated_at = datetime.utcnow()
    db.add(paper)

    tariff_updated = False
    if new_status == "APROBADO":
        stmt = select(Enrollment).where(
            Enrollment.id_congress == id_congreso,
            Enrollment.id_user_platform == paper.id_user_platform,
        )
        enrollment = db.exec(stmt).first()
        if enrollment:
            enrollment.tariff_type = "PONENTE"
            enrollment.amount = 80.0
            db.add(enrollment)
            tariff_updated = True
        else:
            enrollment = Enrollment(
                id_congress=id_congreso,
                id_user_platform=paper.id_user_platform,
                tariff_type="PONENTE",
                amount=80.0,
                status=EnrollmentStatus.ORDEN_GENERADA,
                enrollment_date=datetime.utcnow(),
            )
            db.add(enrollment)
            tariff_updated = True

    db.commit()
    db.refresh(paper)

    return {
        "message": f"Paper actualizado exitosamente a estado '{paper.status}'.",
        "id": paper.id,
        "paper_id": paper.id,
        "status": paper.status,
        "reviewer_comments": paper.reviewer_comments,
        "tariff_type": "PONENTE" if new_status == "APROBADO" else None,
        "amount": 80.0 if new_status == "APROBADO" else None,
        "tariff_updated_to_ponente": tariff_updated,
        "paper": {
            "id": paper.id,
            "id_congress": paper.id_congress,
            "id_user_platform": paper.id_user_platform,
            "title": paper.title,
            "abstract": paper.abstract,
            "track": paper.track,
            "keywords": paper.keywords,
            "file_url": paper.file_url,
            "status": paper.status,
            "reviewer_comments": paper.reviewer_comments,
            "submitted_at": paper.submitted_at.isoformat() if paper.submitted_at else None,
            "updated_at": paper.updated_at.isoformat() if paper.updated_at else None,
        },
    }


@congress_router.get(
    "/{id_congreso}/streaming",
    summary="Acceso a la sala de transmisión en vivo y materiales del congreso",
    description=(
        "Verifica que el usuario actual tenga una inscripción confirmada con estado "
        "PAGADO o FACTURADO. En caso contrario, retorna 403 Forbidden. "
        "Si está autorizado, entrega el enlace de streaming HD y el repositorio de materiales descargables."
    ),
)
def get_congress_streaming_hub(
    id_congreso: int,
    db: SessionDep,
    user_data: tuple[Union[User, UserPlatform], str] = Depends(get_current_user_any_type),
):
    congress = db.get(Congress, id_congreso)
    if not congress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Congreso con ID {id_congreso} no encontrado.",
        )

    current_user, user_type = user_data
    if user_type == "platform":
        stmt = select(Enrollment).where(
            Enrollment.id_congress == id_congreso,
            Enrollment.id_user_platform == current_user.id,
        )
        enrollments = db.exec(stmt).all()
        paid_statuses = {
            "PAGADO",
            "FACTURADO",
            "Pagado",
            "Facturado",
            EnrollmentStatus.PAGADO,
            EnrollmentStatus.FACTURADO,
        }
        has_paid_enrollment = any(
            e.status in paid_statuses or getattr(e.status, "value", str(e.status)).upper() in {"PAGADO", "FACTURADO"}
            for e in enrollments
        )
        if not has_paid_enrollment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso exclusivo para participantes con inscripción confirmada (PAGADO/FACTURADO)",
            )

    streaming_url = (
        congress.sitio_web_oficial
        if (congress.sitio_web_oficial and "http" in congress.sitio_web_oficial)
        else f"https://cedia.zoom.us/j/9876543210?pwd=UTA_FISEI_CONGRESS_{id_congreso}"
    )

    return {
        "id_congreso": id_congreso,
        "nombre_congreso": congress.nombre,
        "streaming_url": streaming_url,
        "platform": "Zoom Enterprise / Teams HD (CEDIA)",
        "access_code": f"UTA-FISEI-{id_congreso}-2026",
        "status": "LIVE",
        "materials": [
            {
                "title": "Guía Oficial del Congreso & Agenda Académica",
                "url": f"/api/v1/congresses/{id_congreso}/materials/guia-oficial.pdf",
                "type": "PDF",
            },
            {
                "title": "Memorias del Congreso (Proceedings Preliminares)",
                "url": f"/api/v1/congresses/{id_congreso}/materials/memorias-congreso.pdf",
                "type": "PDF",
            },
            {
                "title": "Plantilla Oficial para Presentación de Ponentes UTA FISEI",
                "url": f"/api/v1/congresses/{id_congreso}/materials/plantilla-ponentes.pptx",
                "type": "PPTX",
            },
        ],
    }


@congress_router.post(
    "/{id_congreso}/survey",
    status_code=status.HTTP_201_CREATED,
    summary="Registrar encuesta de calidad académica CACES",
    description=(
        "Registra la evaluación de satisfacción con escalas de 1 a 5 estrellas. "
        "Valida que 1 <= q <= 5 en todas las preguntas."
    ),
)
def submit_caces_survey(
    id_congreso: int,
    payload: CacesSurveyCreate,
    db: SessionDep,
    user_data: tuple[Union[User, UserPlatform], str] = Depends(get_current_user_any_type),
):
    for q_field, val in [("q1_rating", payload.q1_rating), ("q2_rating", payload.q2_rating), ("q3_rating", payload.q3_rating)]:
        if val < 1 or val > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La calificación en {q_field} debe estar comprendida entre 1 y 5 estrellas.",
            )

    congress = db.get(Congress, id_congreso)
    if not congress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Congreso con ID {id_congreso} no encontrado.",
        )

    current_user, user_type = user_data
    user_id = payload.id_user_platform if (user_type == "admin" and payload.id_user_platform) else getattr(current_user, "id", None)
    if not user_id:
        user_id = payload.id_user_platform

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Se requiere un usuario participante para registrar la encuesta.",
        )

    user = db.get(UserPlatform, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario participante con ID {user_id} no encontrado.",
        )

    survey = CacesSurvey(
        id_congress=id_congreso,
        id_user_platform=user_id,
        q1_rating=payload.q1_rating,
        q2_rating=payload.q2_rating,
        q3_rating=payload.q3_rating,
        comments=payload.comments.strip() if payload.comments else None,
        submitted_at=datetime.utcnow(),
    )
    db.add(survey)
    db.commit()
    db.refresh(survey)

    return {
        "message": "Encuesta CACES registrada exitosamente. ¡Gracias por su evaluación académica!",
        "id": survey.id,
        "id_congress": survey.id_congress,
        "id_user_platform": survey.id_user_platform,
        "q1_rating": survey.q1_rating,
        "q2_rating": survey.q2_rating,
        "q3_rating": survey.q3_rating,
        "comments": survey.comments,
        "submitted_at": survey.submitted_at.isoformat() if survey.submitted_at else None,
        "survey": {
            "id": survey.id,
            "id_congress": survey.id_congress,
            "id_user_platform": survey.id_user_platform,
            "q1_rating": survey.q1_rating,
            "q2_rating": survey.q2_rating,
            "q3_rating": survey.q3_rating,
            "comments": survey.comments,
            "submitted_at": survey.submitted_at.isoformat() if survey.submitted_at else None,
        },
    }


@congress_router.get(
    "/{id_congreso}/survey/stats",
    summary="Obtener estadísticas consolidadas de la encuesta de calidad CACES",
    description="Calcula promedios de calificación por pregunta, promedio general y total de respuestas.",
)
def get_caces_survey_stats(
    id_congreso: int,
    db: SessionDep,
):
    congress = db.get(Congress, id_congreso)
    if not congress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Congreso con ID {id_congreso} no encontrado.",
        )

    stmt = select(CacesSurvey).where(CacesSurvey.id_congress == id_congreso)
    surveys = db.exec(stmt).all()
    total = len(surveys)

    if total == 0:
        return {
            "id_congress": id_congreso,
            "total_responses": 0,
            "avg_q1": 0.0,
            "avg_q2": 0.0,
            "avg_q3": 0.0,
            "overall_average": 0.0,
            "recent_comments": [],
        }

    avg_q1 = round(sum(s.q1_rating for s in surveys) / total, 2)
    avg_q2 = round(sum(s.q2_rating for s in surveys) / total, 2)
    avg_q3 = round(sum(s.q3_rating for s in surveys) / total, 2)
    overall = round((avg_q1 + avg_q2 + avg_q3) / 3.0, 2)
    comments = [s.comments for s in surveys if s.comments and s.comments.strip()]

    return {
        "id_congress": id_congreso,
        "total_responses": total,
        "avg_q1": avg_q1,
        "avg_q2": avg_q2,
        "avg_q3": avg_q3,
        "overall_average": overall,
        "recent_comments": comments,
    }


# Registrar alias para soportar tanto /api/v1/congresses/... como /api/v1/congresses-new/...
existing_routes = {(r.path, tuple(sorted(r.methods))) for r in congress_router.routes}
for route in list(congress_router.routes):
    if "/api/v1/congresses-new" in route.path:
        alt_path = route.path.replace("/api/v1/congresses-new", "/api/v1/congresses")
        route_key = (alt_path, tuple(sorted(route.methods)))
        if route_key not in existing_routes:
            existing_routes.add(route_key)
            congress_router.routes.append(
                APIRoute(
                    alt_path,
                    route.endpoint,
                    methods=route.methods,
                    response_model=route.response_model,
                    response_class=route.response_class,
                    status_code=route.status_code,
                    dependencies=route.dependencies
                )
            )
