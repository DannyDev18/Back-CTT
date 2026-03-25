from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List, Annotated, Optional
from datetime import date, time
from pydantic import BaseModel, Field
from src.controllers.sesion_cronograma_controller import sesion_cronograma_controller
from src.dependencies.db_session import SessionDep
from src.models.sesion_cronograma_model import (
    SesionCronogramaCreate,
    SesionCronogramaUpdate,
    SesionCronogramaRead
)
from src.utils.jwt_utils import decode_token
from src.models.user import User

sesion_cronograma_router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])
CurrentUser = Annotated[User, Depends(decode_token)]


# ============= Modelos de Request =============

class SesionCronogramaCreateRequest(BaseModel):
    """Modelo para crear una sesión del cronograma"""
    session: SesionCronogramaCreate


class SesionCronogramaUpdateRequest(BaseModel):
    """Modelo para actualizar una sesión del cronograma"""
    session: SesionCronogramaUpdate


class SesionCronogramaResponse(BaseModel):
    """Respuesta estándar para operaciones de sesiones"""
    message: str
    session_id: Optional[int] = None
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

@sesion_cronograma_router.post(
    "",
    response_model=SesionCronogramaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una nueva sesión",
    description="Crea una nueva sesión en el cronograma de un congreso"
)
def create_session(
    request: SesionCronogramaCreateRequest,
    db: SessionDep,
    current_user: CurrentUser
) -> SesionCronogramaResponse:
    """
    Crea una nueva sesión del cronograma.

    - **session**: Información completa de la sesión

    **Validaciones automáticas:**
    - El congreso debe existir
    - El speaker debe existir y pertenecer al congreso
    - No debe haber conflictos de horario con el speaker
    """
    try:
        result = sesion_cronograma_controller.create_session(
            db, request.session, current_user.id
        )
        return SesionCronogramaResponse(
            message="Session created successfully",
            session_id=result.get("id_sesion"),
            data=result
        )
    except Exception as e:
        db.rollback()
        raise handle_controller_error(e, "creating session")


@sesion_cronograma_router.get(
    "",
    summary="Listar todas las sesiones",
    description="Obtiene una lista paginada de sesiones con filtros opcionales"
)
def get_all_sessions(
    db: SessionDep,
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(10, ge=1, le=100, description="Cantidad de sesiones por página"),
    congress_id: Optional[int] = Query(None, description="Filtrar por congreso"),
    speaker_id: Optional[int] = Query(None, description="Filtrar por speaker"),
    fecha: Optional[date] = Query(None, description="Filtrar por fecha (YYYY-MM-DD)"),
    jornada: Optional[str] = Query(None, description="Filtrar por jornada (mañana, tarde, noche)"),
    search_term: Optional[str] = Query(None, description="Término de búsqueda en título"),
    order_by: str = Query("fecha", description="Campo para ordenar"),
    order_desc: bool = Query(False, description="Orden descendente")
):
    """
    Obtiene todas las sesiones con paginación y filtros.

    **Parámetros de consulta:**
    - `page`: Número de página (mínimo 1)
    - `page_size`: Sesiones por página (1-100)
    - `congress_id`: Filtrar por congreso específico
    - `speaker_id`: Filtrar por speaker específico
    - `fecha`: Filtrar por fecha específica
    - `jornada`: Filtrar por jornada (mañana/tarde/noche)
    - `search_term`: Búsqueda en título de sesión
    - `order_by`: Campo para ordenar
    - `order_desc`: Orden descendente
    """
    try:
        return sesion_cronograma_controller.get_all_sessions(
            db,
            page=page,
            page_size=page_size,
            congress_id=congress_id,
            speaker_id=speaker_id,
            fecha=fecha,
            jornada=jornada,
            search_term=search_term,
            order_by=order_by,
            order_desc=order_desc
        )
    except Exception as e:
        raise handle_controller_error(e, "fetching sessions")


@sesion_cronograma_router.get(
    "/search",
    summary="Buscar sesiones",
    description="Busca sesiones usando coincidencia parcial en el título"
)
def search_sessions(
    db: SessionDep,
    q: str = Query(..., min_length=1, description="Término de búsqueda", alias="query"),
    congress_id: Optional[int] = Query(None, description="Filtrar por congreso"),
    limit: int = Query(20, ge=1, le=100, description="Límite de resultados")
):
    """
    Busca sesiones por término.

    **Parámetros:**
    - `q`: Término de búsqueda (mínimo 1 carácter)
    - `congress_id`: Filtrar por congreso específico
    - `limit`: Límite de resultados
    """
    try:
        return sesion_cronograma_controller.search_sessions(
            db, search_term=q, congress_id=congress_id, limit=limit
        )
    except Exception as e:
        raise handle_controller_error(e, "searching sessions")


@sesion_cronograma_router.get(
    "/by-congress/{congress_id}",
    summary="Obtener sesiones por congreso",
    description="Lista todas las sesiones de un congreso específico"
)
def get_sessions_by_congress(
    congress_id: int,
    db: SessionDep,
    include_details: bool = Query(True, description="Incluir información del speaker"),
    order_by_date: bool = Query(True, description="Ordenar por fecha y hora")
):
    """
    Obtiene todas las sesiones de un congreso.

    **Parámetros:**
    - `congress_id`: ID del congreso
    - `include_details`: Incluir detalles del speaker
    - `order_by_date`: Ordenar por fecha y hora
    """
    try:
        return sesion_cronograma_controller.get_sessions_by_congress(
            db, congress_id,
            include_details=include_details,
            order_by_date=order_by_date
        )
    except Exception as e:
        raise handle_controller_error(e, "fetching sessions by congress")


@sesion_cronograma_router.get(
    "/by-speaker/{speaker_id}",
    summary="Obtener sesiones por speaker",
    description="Lista todas las sesiones de un speaker específico"
)
def get_sessions_by_speaker(
    speaker_id: int,
    db: SessionDep,
    include_details: bool = Query(True, description="Incluir información del congreso")
):
    """
    Obtiene todas las sesiones de un speaker.

    **Parámetros:**
    - `speaker_id`: ID del speaker
    - `include_details`: Incluir detalles del congreso
    """
    try:
        return sesion_cronograma_controller.get_sessions_by_speaker(
            db, speaker_id, include_details=include_details
        )
    except Exception as e:
        raise handle_controller_error(e, "fetching sessions by speaker")


@sesion_cronograma_router.get(
    "/by-date/{fecha}",
    summary="Obtener sesiones por fecha",
    description="Lista todas las sesiones de una fecha específica"
)
def get_sessions_by_date(
    fecha: date,
    db: SessionDep,
    congress_id: Optional[int] = Query(None, description="Filtrar por congreso"),
    include_details: bool = Query(True, description="Incluir detalles relacionados")
):
    """
    Obtiene sesiones por fecha específica.

    **Parámetros:**
    - `fecha`: Fecha de las sesiones (YYYY-MM-DD)
    - `congress_id`: Filtrar por congreso específico
    - `include_details`: Incluir detalles de speakers y congresos
    """
    try:
        return sesion_cronograma_controller.get_sessions_by_date(
            db, fecha, congress_id=congress_id, include_details=include_details
        )
    except Exception as e:
        raise handle_controller_error(e, "fetching sessions by date")


@sesion_cronograma_router.get(
    "/by-date-range",
    summary="Obtener sesiones por rango de fechas",
    description="Lista sesiones en un rango de fechas específico"
)
def get_sessions_by_date_range(
    db: SessionDep,
    start_date: date = Query(..., description="Fecha de inicio (YYYY-MM-DD)"),
    end_date: date = Query(..., description="Fecha de fin (YYYY-MM-DD)"),
    congress_id: Optional[int] = Query(None, description="Filtrar por congreso"),
    include_details: bool = Query(True, description="Incluir detalles relacionados")
):
    """
    Obtiene sesiones en un rango de fechas.

    **Parámetros:**
    - `start_date`: Fecha de inicio del rango
    - `end_date`: Fecha de fin del rango
    - `congress_id`: Filtrar por congreso específico
    - `include_details`: Incluir detalles de speakers y congresos
    """
    try:
        return sesion_cronograma_controller.get_sessions_by_date_range(
            db, start_date, end_date, congress_id=congress_id, include_details=include_details
        )
    except Exception as e:
        raise handle_controller_error(e, "fetching sessions by date range")


@sesion_cronograma_router.get(
    "/by-jornada/{jornada}",
    summary="Obtener sesiones por jornada",
    description="Lista sesiones de una jornada específica (mañana/tarde/noche)"
)
def get_sessions_by_jornada(
    jornada: str,
    db: SessionDep,
    congress_id: Optional[int] = Query(None, description="Filtrar por congreso"),
    fecha: Optional[date] = Query(None, description="Filtrar por fecha")
):
    """
    Obtiene sesiones por jornada.

    **Parámetros:**
    - `jornada`: Jornada (mañana, tarde, noche)
    - `congress_id`: Filtrar por congreso específico
    - `fecha`: Filtrar por fecha específica
    """
    try:
        return sesion_cronograma_controller.get_sessions_by_jornada(
            db, jornada, congress_id=congress_id, fecha=fecha
        )
    except Exception as e:
        raise handle_controller_error(e, "fetching sessions by jornada")


@sesion_cronograma_router.get(
    "/daily-schedule/{congress_id}/{fecha}",
    summary="Obtener cronograma diario",
    description="Cronograma completo organizado para un día específico"
)
def get_daily_schedule(
    congress_id: int,
    fecha: date,
    db: SessionDep,
    group_by_jornada: bool = Query(True, description="Agrupar por jornada")
):
    """
    Obtiene el cronograma organizado de un día específico.

    **Parámetros:**
    - `congress_id`: ID del congreso
    - `fecha`: Fecha del cronograma (YYYY-MM-DD)
    - `group_by_jornada`: Agrupar sesiones por jornada
    """
    try:
        return sesion_cronograma_controller.get_daily_schedule(
            db, congress_id, fecha, group_by_jornada=group_by_jornada
        )
    except Exception as e:
        raise handle_controller_error(e, "fetching daily schedule")


@sesion_cronograma_router.get(
    "/congress-schedule/{congress_id}",
    summary="Obtener resumen del cronograma del congreso",
    description="Resumen estadístico del cronograma completo de un congreso"
)
def get_congress_schedule_summary(
    congress_id: int,
    db: SessionDep
):
    """
    Obtiene resumen del cronograma de un congreso.

    **Parámetros:**
    - `congress_id`: ID del congreso

    **Respuesta:**
    Estadísticas del cronograma: total sesiones, distribución por jornada, etc.
    """
    try:
        return sesion_cronograma_controller.get_congress_schedule_summary(db, congress_id)
    except Exception as e:
        raise handle_controller_error(e, "fetching congress schedule summary")


@sesion_cronograma_router.get(
    "/summary",
    summary="Obtener resumen de sesiones",
    description="Estadísticas generales del sistema de sesiones"
)
def get_session_summary(db: SessionDep):
    """
    Obtiene un resumen estadístico del sistema de sesiones.
    """
    try:
        return sesion_cronograma_controller.get_session_summary(db)
    except Exception as e:
        raise handle_controller_error(e, "fetching session summary")


@sesion_cronograma_router.get(
    "/{session_id}",
    summary="Obtener sesión por ID",
    description="Obtiene los detalles completos de una sesión específica"
)
def get_session_by_id(
    session_id: int,
    db: SessionDep,
    include_speaker: bool = Query(False, description="Incluir información del speaker"),
    include_congress: bool = Query(False, description="Incluir información del congreso")
):
    """
    Obtiene una sesión específica con sus datos.

    **Parámetros:**
    - `session_id`: ID único de la sesión
    - `include_speaker`: Incluir detalles del speaker
    - `include_congress`: Incluir información del congreso
    """
    try:
        session = sesion_cronograma_controller.get_session_by_id(
            db, session_id,
            include_speaker=include_speaker,
            include_congress=include_congress
        )
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session with id {session_id} not found"
            )
        return session
    except HTTPException:
        raise
    except Exception as e:
        raise handle_controller_error(e, "fetching session")


@sesion_cronograma_router.patch(
    "/{session_id}",
    response_model=SesionCronogramaResponse,
    summary="Actualizar una sesión",
    description="Actualiza parcialmente una sesión existente"
)
def update_session(
    session_id: int,
    request: SesionCronogramaUpdateRequest,
    db: SessionDep,
    current_user: CurrentUser
) -> SesionCronogramaResponse:
    """
    Actualiza una sesión existente de forma parcial.

    **Parámetros:**
    - `session_id`: ID de la sesión a actualizar
    - `request`: Datos a actualizar (todos opcionales)

    **Validaciones automáticas:**
    - Verificar conflictos de horario si se cambian datos temporales
    - Validar que speaker pertenezca al congreso si se cambia
    """
    try:
        result = sesion_cronograma_controller.update_session(
            db, session_id, request.session, current_user.id
        )
        return SesionCronogramaResponse(
            message="Session updated successfully",
            session_id=session_id,
            data=result
        )
    except Exception as e:
        db.rollback()
        raise handle_controller_error(e, "updating session")


@sesion_cronograma_router.delete(
    "/{session_id}",
    status_code=status.HTTP_200_OK,
    response_model=SesionCronogramaResponse,
    summary="Eliminar una sesión",
    description="Elimina una sesión del cronograma"
)
def delete_session(
    session_id: int,
    db: SessionDep,
    current_user: CurrentUser
) -> SesionCronogramaResponse:
    """
    Elimina una sesión del cronograma.

    **Parámetros:**
    - `session_id`: ID de la sesión a eliminar
    """
    try:
        result = sesion_cronograma_controller.delete_session(
            db, session_id, current_user.id
        )
        return SesionCronogramaResponse(
            message="Session deleted successfully",
            session_id=session_id,
            data=result
        )
    except Exception as e:
        db.rollback()
        raise handle_controller_error(e, "deleting session")


# ============= Rutas de Verificación y Validación =============

@sesion_cronograma_router.get(
    "/check-conflicts/{speaker_id}",
    summary="Verificar conflictos de horario",
    description="Verifica si hay conflictos de horario para un speaker"
)
def check_time_conflicts(
    speaker_id: int,
    db: SessionDep,
    fecha: date = Query(..., description="Fecha a verificar (YYYY-MM-DD)"),
    hora_inicio: str = Query(..., description="Hora de inicio (HH:MM)", pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$"),
    hora_fin: str = Query(..., description="Hora de fin (HH:MM)", pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$"),
    exclude_session_id: Optional[int] = Query(None, description="ID de sesión a excluir (para actualizaciones)")
):
    """
    Verifica conflictos de horario para un speaker.

    **Parámetros:**
    - `speaker_id`: ID del speaker
    - `fecha`: Fecha a verificar
    - `hora_inicio`: Hora de inicio en formato HH:MM
    - `hora_fin`: Hora de fin en formato HH:MM
    - `exclude_session_id`: ID de sesión a excluir (útil para actualizaciones)

    **Respuesta:**
    Información sobre conflictos encontrados y detalles de las sesiones conflictivas
    """
    try:
        # Convertir strings de tiempo a objetos time
        from datetime import datetime
        hora_inicio_obj = datetime.strptime(hora_inicio, "%H:%M").time()
        hora_fin_obj = datetime.strptime(hora_fin, "%H:%M").time()

        return sesion_cronograma_controller.check_time_conflicts(
            db, speaker_id, fecha, hora_inicio_obj, hora_fin_obj, exclude_session_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid time format: {str(e)}"
        )
    except Exception as e:
        raise handle_controller_error(e, "checking time conflicts")