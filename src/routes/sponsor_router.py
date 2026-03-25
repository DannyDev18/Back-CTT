from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List, Annotated, Optional
from decimal import Decimal
from pydantic import BaseModel, Field
from src.controllers.sponsor_controller import sponsor_controller
from src.dependencies.db_session import SessionDep
from src.models.sponsor_model import (
    SponsorCreate,
    SponsorUpdate,
    SponsorRead
)
from src.utils.jwt_utils import decode_token
from src.models.user import User

sponsor_router = APIRouter(prefix="/api/v1/sponsors", tags=["sponsors"])
CurrentUser = Annotated[User, Depends(decode_token)]


# ============= Modelos de Request =============

class SponsorCreateRequest(BaseModel):
    """Modelo para crear un sponsor"""
    sponsor: SponsorCreate


class SponsorUpdateRequest(BaseModel):
    """Modelo para actualizar un sponsor"""
    sponsor: SponsorUpdate


class SponsorResponse(BaseModel):
    """Respuesta estándar para operaciones de sponsors"""
    message: str
    sponsor_id: Optional[int] = None
    data: Optional[dict] = None


class BulkSponsorCreateRequest(BaseModel):
    """Modelo para creación en lote de sponsors"""
    sponsors: List[SponsorCreate] = Field(..., min_items=1, max_items=50)


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

@sponsor_router.post(
    "",
    response_model=SponsorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo sponsor",
    description="Crea un nuevo sponsor en el sistema"
)
def create_sponsor(
    request: SponsorCreateRequest,
    db: SessionDep,
    current_user: CurrentUser
) -> SponsorResponse:
    """
    Crea un nuevo sponsor.

    - **sponsor**: Información completa del sponsor
    """
    try:
        result = sponsor_controller.create_sponsor(
            db, request.sponsor, current_user.id
        )
        return SponsorResponse(
            message="Sponsor created successfully",
            sponsor_id=result.get("id_sponsor"),
            data=result
        )
    except Exception as e:
        db.rollback()
        raise handle_controller_error(e, "creating sponsor")


@sponsor_router.get(
    "",
    summary="Listar todos los sponsors",
    description="Obtiene una lista paginada de sponsors con filtros opcionales"
)
def get_all_sponsors(
    db: SessionDep,
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(10, ge=1, le=100, description="Cantidad de sponsors por página"),
    search_term: Optional[str] = Query(None, description="Término de búsqueda en nombre"),
    has_active_sponsorship: Optional[bool] = Query(None, description="Filtrar por sponsors con sponsorships activos"),
    order_by: str = Query("nombre", description="Campo para ordenar"),
    order_desc: bool = Query(False, description="Orden descendente")
):
    """
    Obtiene todos los sponsors con paginación y filtros.

    **Parámetros de consulta:**
    - `page`: Número de página (mínimo 1)
    - `page_size`: Sponsors por página (1-100)
    - `search_term`: Búsqueda en nombre del sponsor
    - `has_active_sponsorship`: Solo sponsors con sponsorships activos
    - `order_by`: Campo para ordenar (nombre, descripcion)
    - `order_desc`: Orden descendente (true/false)
    """
    try:
        return sponsor_controller.get_all_sponsors(
            db,
            page=page,
            page_size=page_size,
            search_term=search_term,
            has_active_sponsorship=has_active_sponsorship,
            order_by=order_by,
            order_desc=order_desc
        )
    except Exception as e:
        raise handle_controller_error(e, "fetching sponsors")


@sponsor_router.get(
    "/search",
    summary="Buscar sponsors por nombre",
    description="Busca sponsors usando coincidencia parcial en el nombre"
)
def search_sponsors_by_name(
    db: SessionDep,
    q: str = Query(..., min_length=1, description="Término de búsqueda", alias="query"),
    limit: int = Query(20, ge=1, le=100, description="Límite de resultados")
):
    """
    Busca sponsors por nombre.

    **Parámetros:**
    - `q`: Término de búsqueda (mínimo 1 carácter)
    - `limit`: Límite de resultados
    """
    try:
        return sponsor_controller.search_sponsors_by_name(
            db, search_term=q, limit=limit
        )
    except Exception as e:
        raise handle_controller_error(e, "searching sponsors")


@sponsor_router.get(
    "/by-domain/{domain}",
    summary="Obtener sponsors por dominio",
    description="Lista sponsors que tienen sitios web con un dominio específico"
)
def get_sponsors_by_website_domain(
    domain: str,
    db: SessionDep
):
    """
    Obtiene sponsors por dominio de sitio web.

    **Parámetros:**
    - `domain`: Dominio a buscar (ej: "example.com")
    """
    try:
        return sponsor_controller.get_sponsors_by_website_domain(db, domain)
    except Exception as e:
        raise handle_controller_error(e, "fetching sponsors by domain")


@sponsor_router.get(
    "/top-contributors",
    summary="Obtener top sponsors por contribución",
    description="Lista los sponsors con mayor contribución total"
)
def get_top_sponsors_by_contribution(
    db: SessionDep,
    limit: int = Query(10, ge=1, le=50, description="Límite de sponsors"),
    year: Optional[int] = Query(None, description="Filtrar por año específico")
):
    """
    Obtiene los top sponsors por contribución.

    **Parámetros:**
    - `limit`: Cantidad máxima de sponsors
    - `year`: Filtrar por contribuciones de un año específico
    """
    try:
        return sponsor_controller.get_top_sponsors_by_contribution(
            db, limit=limit, year=year
        )
    except Exception as e:
        raise handle_controller_error(e, "fetching top sponsors")


@sponsor_router.get(
    "/inactive",
    summary="Obtener sponsors sin actividad reciente",
    description="Lista sponsors que no han tenido sponsorships recientes"
)
def get_sponsors_without_recent_activity(
    db: SessionDep,
    years_threshold: int = Query(2, ge=1, le=10, description="Años sin actividad")
):
    """
    Obtiene sponsors sin actividad reciente.

    **Parámetros:**
    - `years_threshold`: Años sin actividad para considerar inactivo
    """
    try:
        return sponsor_controller.get_sponsors_without_recent_activity(
            db, years_threshold=years_threshold
        )
    except Exception as e:
        raise handle_controller_error(e, "fetching inactive sponsors")


@sponsor_router.get(
    "/summary",
    summary="Obtener resumen de sponsors",
    description="Estadísticas generales del sistema de sponsors"
)
def get_sponsor_summary(db: SessionDep):
    """
    Obtiene un resumen estadístico del sistema de sponsors.
    """
    try:
        return sponsor_controller.get_sponsor_summary(db)
    except Exception as e:
        raise handle_controller_error(e, "fetching sponsor summary")


@sponsor_router.get(
    "/{sponsor_id}",
    summary="Obtener sponsor por ID",
    description="Obtiene los detalles completos de un sponsor específico"
)
def get_sponsor_by_id(
    sponsor_id: int,
    db: SessionDep,
    include_congresses: bool = Query(False, description="Incluir información de congresos patrocinados")
):
    """
    Obtiene un sponsor específico con sus datos.

    **Parámetros:**
    - `sponsor_id`: ID único del sponsor
    - `include_congresses`: Incluir detalles de congresos patrocinados
    """
    try:
        sponsor = sponsor_controller.get_sponsor_by_id(
            db, sponsor_id, include_congresses=include_congresses
        )
        if not sponsor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sponsor with id {sponsor_id} not found"
            )
        return sponsor
    except HTTPException:
        raise
    except Exception as e:
        raise handle_controller_error(e, "fetching sponsor")


@sponsor_router.get(
    "/{sponsor_id}/statistics",
    summary="Obtener estadísticas de sponsor",
    description="Estadísticas detalladas de un sponsor específico"
)
def get_sponsor_statistics(
    sponsor_id: int,
    db: SessionDep
):
    """
    Obtiene estadísticas detalladas de un sponsor.

    **Parámetros:**
    - `sponsor_id`: ID del sponsor

    **Respuesta:**
    Estadísticas completas incluyendo sponsorships, contribuciones, etc.
    """
    try:
        return sponsor_controller.get_sponsor_statistics(db, sponsor_id)
    except Exception as e:
        raise handle_controller_error(e, "fetching sponsor statistics")


@sponsor_router.patch(
    "/{sponsor_id}",
    response_model=SponsorResponse,
    summary="Actualizar un sponsor",
    description="Actualiza parcialmente un sponsor existente"
)
def update_sponsor(
    sponsor_id: int,
    request: SponsorUpdateRequest,
    db: SessionDep,
    current_user: CurrentUser
) -> SponsorResponse:
    """
    Actualiza un sponsor existente de forma parcial.

    **Parámetros:**
    - `sponsor_id`: ID del sponsor a actualizar
    - `request`: Datos a actualizar (todos opcionales)
    """
    try:
        result = sponsor_controller.update_sponsor(
            db, sponsor_id, request.sponsor, current_user.id
        )
        return SponsorResponse(
            message="Sponsor updated successfully",
            sponsor_id=sponsor_id,
            data=result
        )
    except Exception as e:
        db.rollback()
        raise handle_controller_error(e, "updating sponsor")


@sponsor_router.delete(
    "/{sponsor_id}",
    status_code=status.HTTP_200_OK,
    response_model=SponsorResponse,
    summary="Eliminar un sponsor",
    description="Elimina un sponsor del sistema"
)
def delete_sponsor(
    sponsor_id: int,
    db: SessionDep,
    current_user: CurrentUser
) -> SponsorResponse:
    """
    Elimina un sponsor.

    **Parámetros:**
    - `sponsor_id`: ID del sponsor a eliminar

    **Nota:** Solo se puede eliminar si no tiene sponsorships activos
    """
    try:
        result = sponsor_controller.delete_sponsor(
            db, sponsor_id, current_user.id
        )
        return SponsorResponse(
            message="Sponsor deleted successfully",
            sponsor_id=sponsor_id,
            data=result
        )
    except Exception as e:
        db.rollback()
        raise handle_controller_error(e, "deleting sponsor")


# ============= Rutas de Verificación =============

@sponsor_router.get(
    "/check-name/{nombre}",
    summary="Verificar disponibilidad de nombre",
    description="Verifica si un nombre de sponsor está disponible"
)
def check_name_availability(
    nombre: str,
    db: SessionDep,
    exclude_sponsor_id: Optional[int] = Query(None, description="ID de sponsor a excluir")
):
    """
    Verifica la disponibilidad de un nombre de sponsor.

    **Parámetros:**
    - `nombre`: Nombre del sponsor a verificar
    - `exclude_sponsor_id`: ID a excluir de la verificación (para actualizaciones)
    """
    try:
        return sponsor_controller.check_name_availability(
            db, nombre, exclude_sponsor_id
        )
    except Exception as e:
        raise handle_controller_error(e, "checking name availability")


# ============= Rutas de Operaciones en Lote =============

@sponsor_router.post(
    "/bulk-import",
    response_model=SponsorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Importar sponsors en lote",
    description="Crea múltiples sponsors de una vez"
)
def bulk_import_sponsors(
    request: BulkSponsorCreateRequest,
    db: SessionDep,
    current_user: CurrentUser
) -> SponsorResponse:
    """
    Importa múltiples sponsors en una sola operación.

    **Parámetros:**
    - `sponsors`: Lista de sponsors a crear (máximo 50)

    **Validaciones:**
    - Nombres únicos en el lote
    - Nombres no existentes en BD
    - Todos los campos requeridos
    """
    try:
        result = sponsor_controller.bulk_import_sponsors(
            db, request.sponsors, current_user.id
        )
        return SponsorResponse(
            message=f"Successfully imported {result['data']['count']} sponsors",
            data=result
        )
    except Exception as e:
        db.rollback()
        raise handle_controller_error(e, "bulk importing sponsors")