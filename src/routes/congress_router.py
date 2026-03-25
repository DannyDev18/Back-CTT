from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List, Annotated, Optional
from datetime import date
from pydantic import BaseModel, Field
from src.controllers.congress_controller import congress_controller
from src.dependencies.db_session import SessionDep
from src.models.congress_model import (
    CongressCreate,
    CongressUpdate,
    CongressRead,
    CongressLegacyCreate,
    CongressLegacyUpdate
)
from src.utils.jwt_utils import decode_token
from src.models.user import User

congress_router = APIRouter(prefix="/api/v1/congresses-new", tags=["congresses-new"])
CurrentUser = Annotated[User, Depends(decode_token)]


# ============= Modelos de Request =============

class CongressCreateRequest(BaseModel):
    """Modelo para crear un congreso"""
    congress: CongressCreate


class CongressUpdateRequest(BaseModel):
    """Modelo para actualizar un congreso"""
    congress: CongressUpdate


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
    description="Crea un nuevo congreso con la estructura nueva del sistema"
)
def create_congress(
    request: CongressCreateRequest,
    db: SessionDep,
    current_user: CurrentUser
) -> CongressResponse:
    """
    Crea un nuevo congreso.

    - **congress**: Información completa del congreso
    """
    try:
        result = congress_controller.create_congress(
            db, request.congress, current_user.id
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
            db, congress_id, request.congress, current_user.id
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