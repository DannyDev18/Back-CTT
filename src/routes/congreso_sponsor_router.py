from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List, Annotated, Optional
from decimal import Decimal
from pydantic import BaseModel, Field
from src.controllers.congreso_sponsor_controller import congreso_sponsor_controller
from src.dependencies.db_session import SessionDep
from src.models.congreso_sponsor_model import (
    CongresoSponsorCreate,
    CongresoSponsorUpdate,
    CongresoSponsorRead
)
from src.utils.jwt_utils import decode_token
from src.models.user import User

congreso_sponsor_router = APIRouter(prefix="/api/v1/sponsorships", tags=["sponsorships"])
CurrentUser = Annotated[User, Depends(decode_token)]


# ============= Modelos de Request =============

class CongresoSponsorCreateRequest(BaseModel):
    """Modelo para crear una relación de sponsorship"""
    sponsorship: CongresoSponsorCreate


class CongresoSponsorUpdateRequest(BaseModel):
    """Modelo para actualizar una relación de sponsorship"""
    sponsorship: CongresoSponsorUpdate


class CongresoSponsorResponse(BaseModel):
    """Respuesta estándar para operaciones de sponsorships"""
    message: str
    data: Optional[dict] = None


class BulkCongresoSponsorCreateRequest(BaseModel):
    """Modelo para creación en lote de sponsorships"""
    sponsorships: List[CongresoSponsorCreate] = Field(..., min_items=1, max_items=50)


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

@congreso_sponsor_router.post(
    "",
    response_model=CongresoSponsorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una nueva relación de sponsorship",
    description="Crea una nueva relación entre un congreso y un sponsor"
)
def create_sponsorship(
    request: CongresoSponsorCreateRequest,
    db: SessionDep,
    current_user: CurrentUser
) -> CongresoSponsorResponse:
    """
    Crea una nueva relación de sponsorship.

    - **sponsorship**: Información completa del sponsorship

    **Validaciones automáticas:**
    - El congreso debe existir
    - El sponsor debe existir
    - No debe existir ya la relación entre congreso y sponsor
    """
    try:
        result = congreso_sponsor_controller.create_sponsorship(
            db, request.sponsorship, current_user.id
        )
        return CongresoSponsorResponse(
            message="Sponsorship created successfully",
            data=result
        )
    except Exception as e:
        db.rollback()
        raise handle_controller_error(e, "creating sponsorship")


@congreso_sponsor_router.get(
    "",
    summary="Listar todas las relaciones de sponsorship",
    description="Obtiene una lista paginada de sponsorships con filtros opcionales"
)
def get_all_sponsorships(
    db: SessionDep,
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(10, ge=1, le=100, description="Cantidad de sponsorships por página"),
    congress_id: Optional[int] = Query(None, description="Filtrar por congreso"),
    sponsor_id: Optional[int] = Query(None, description="Filtrar por sponsor"),
    categoria: Optional[str] = Query(None, description="Filtrar por categoría (oro, plata, bronce)"),
    min_aporte: Optional[float] = Query(None, description="Aporte mínimo"),
    max_aporte: Optional[float] = Query(None, description="Aporte máximo"),
    order_by: str = Query("aporte", description="Campo para ordenar"),
    order_desc: bool = Query(True, description="Orden descendente")
):
    """
    Obtiene todas las relaciones de sponsorship con paginación y filtros.

    **Parámetros de consulta:**
    - `page`: Número de página (mínimo 1)
    - `page_size`: Sponsorships por página (1-100)
    - `congress_id`: Filtrar por congreso específico
    - `sponsor_id`: Filtrar por sponsor específico
    - `categoria`: Filtrar por categoría de sponsorship
    - `min_aporte`: Aporte mínimo para filtrar
    - `max_aporte`: Aporte máximo para filtrar
    - `order_by`: Campo para ordenar
    - `order_desc`: Orden descendente
    """
    try:
        min_aporte_decimal = Decimal(str(min_aporte)) if min_aporte is not None else None
        max_aporte_decimal = Decimal(str(max_aporte)) if max_aporte is not None else None

        return congreso_sponsor_controller.get_all_sponsorships(
            db,
            page=page,
            page_size=page_size,
            congress_id=congress_id,
            sponsor_id=sponsor_id,
            categoria=categoria,
            min_aporte=min_aporte_decimal,
            max_aporte=max_aporte_decimal,
            order_by=order_by,
            order_desc=order_desc
        )
    except Exception as e:
        raise handle_controller_error(e, "fetching sponsorships")


@congreso_sponsor_router.get(
    "/by-congress/{congress_id}",
    summary="Obtener sponsorships por congreso",
    description="Lista todas las relaciones de sponsorship de un congreso específico"
)
def get_sponsorships_by_congress(
    congress_id: int,
    db: SessionDep,
    include_sponsor: bool = Query(True, description="Incluir información del sponsor")
):
    """
    Obtiene todas las relaciones de sponsorship de un congreso.

    **Parámetros:**
    - `congress_id`: ID del congreso
    - `include_sponsor`: Incluir detalles del sponsor
    """
    try:
        return congreso_sponsor_controller.get_sponsorships_by_congress(
            db, congress_id, include_sponsor=include_sponsor
        )
    except Exception as e:
        raise handle_controller_error(e, "fetching sponsorships by congress")


@congreso_sponsor_router.get(
    "/by-sponsor/{sponsor_id}",
    summary="Obtener sponsorships por sponsor",
    description="Lista todas las relaciones de sponsorship de un sponsor específico"
)
def get_sponsorships_by_sponsor(
    sponsor_id: int,
    db: SessionDep,
    include_congress: bool = Query(True, description="Incluir información del congreso")
):
    """
    Obtiene todas las relaciones de sponsorship de un sponsor.

    **Parámetros:**
    - `sponsor_id`: ID del sponsor
    - `include_congress`: Incluir detalles del congreso
    """
    try:
        return congreso_sponsor_controller.get_sponsorships_by_sponsor(
            db, sponsor_id, include_congress=include_congress
        )
    except Exception as e:
        raise handle_controller_error(e, "fetching sponsorships by sponsor")


@congreso_sponsor_router.get(
    "/by-category/{categoria}",
    summary="Obtener sponsorships por categoría",
    description="Lista sponsorships de una categoría específica"
)
def get_sponsorships_by_category(
    categoria: str,
    db: SessionDep,
    congress_id: Optional[int] = Query(None, description="Filtrar por congreso")
):
    """
    Obtiene sponsorships por categoría.

    **Parámetros:**
    - `categoria`: Categoría del sponsorship (oro, plata, bronce)
    - `congress_id`: Filtrar por congreso específico (opcional)
    """
    try:
        return congreso_sponsor_controller.get_sponsorships_by_category(
            db, categoria, congress_id=congress_id
        )
    except Exception as e:
        raise handle_controller_error(e, "fetching sponsorships by category")


@congreso_sponsor_router.get(
    "/top-contributors/{congress_id}",
    summary="Obtener top contribuyentes por congreso",
    description="Lista los sponsors con mayor contribución para un congreso específico"
)
def get_top_contributors_by_congress(
    congress_id: int,
    db: SessionDep,
    limit: int = Query(10, ge=1, le=50, description="Límite de contributors")
):
    """
    Obtiene los top contribuyentes para un congreso.

    **Parámetros:**
    - `congress_id`: ID del congreso
    - `limit`: Cantidad máxima de contributors
    """
    try:
        return congreso_sponsor_controller.get_top_contributors_by_congress(
            db, congress_id, limit=limit
        )
    except Exception as e:
        raise handle_controller_error(e, "fetching top contributors")


@congreso_sponsor_router.get(
    "/statistics/{congress_id}",
    summary="Obtener estadísticas de sponsorship por congreso",
    description="Estadísticas detalladas de sponsorships para un congreso específico"
)
def get_sponsorship_statistics_by_congress(
    congress_id: int,
    db: SessionDep
):
    """
    Obtiene estadísticas de sponsorships para un congreso.

    **Parámetros:**
    - `congress_id`: ID del congreso

    **Respuesta:**
    Estadísticas completas: total sponsors, contribución por categoría, promedios, etc.
    """
    try:
        return congreso_sponsor_controller.get_sponsorship_statistics_by_congress(
            db, congress_id
        )
    except Exception as e:
        raise handle_controller_error(e, "fetching sponsorship statistics")


@congreso_sponsor_router.get(
    "/funding-summary",
    summary="Obtener resumen de financiamiento",
    description="Resumen de financiamiento por congreso"
)
def get_congress_funding_summary(
    db: SessionDep,
    year: Optional[int] = Query(None, description="Filtrar por año específico")
):
    """
    Obtiene resumen de financiamiento por congreso.

    **Parámetros:**
    - `year`: Filtrar por año específico (opcional)

    **Respuesta:**
    Lista de congresos con totales de financiamiento y número de sponsors
    """
    try:
        return congreso_sponsor_controller.get_congress_funding_summary(
            db, year=year
        )
    except Exception as e:
        raise handle_controller_error(e, "fetching funding summary")


@congreso_sponsor_router.get(
    "/loyalty-analysis",
    summary="Análisis de lealtad de sponsors",
    description="Análisis de sponsors que han patrocinado múltiples congresos"
)
def get_sponsor_loyalty_analysis(
    db: SessionDep,
    min_sponsorships: int = Query(2, ge=2, description="Número mínimo de sponsorships")
):
    """
    Análisis de lealtad de sponsors.

    **Parámetros:**
    - `min_sponsorships`: Número mínimo de sponsorships para considerarse leal

    **Respuesta:**
    Lista de sponsors leales con métricas de contribución y lealtad
    """
    try:
        return congreso_sponsor_controller.get_sponsor_loyalty_analysis(
            db, min_sponsorships=min_sponsorships
        )
    except Exception as e:
        raise handle_controller_error(e, "fetching loyalty analysis")


@congreso_sponsor_router.get(
    "/category-trends",
    summary="Análisis de tendencias por categoría",
    description="Tendencias de categorías de sponsorship a lo largo del tiempo"
)
def get_category_trends(
    db: SessionDep,
    years: Optional[List[int]] = Query(None, description="Lista de años específicos")
):
    """
    Análisis de tendencias por categoría de sponsorship.

    **Parámetros:**
    - `years`: Lista de años específicos (opcional)

    **Respuesta:**
    Tendencias por año y categoría con número de sponsors y contribuciones
    """
    try:
        return congreso_sponsor_controller.get_category_trends(
            db, years=years
        )
    except Exception as e:
        raise handle_controller_error(e, "fetching category trends")


@congreso_sponsor_router.get(
    "/summary",
    summary="Obtener resumen de sponsorships",
    description="Estadísticas generales del sistema de sponsorships"
)
def get_sponsorship_summary(db: SessionDep):
    """
    Obtiene un resumen estadístico del sistema de sponsorships.
    """
    try:
        return congreso_sponsor_controller.get_sponsorship_summary(db)
    except Exception as e:
        raise handle_controller_error(e, "fetching sponsorship summary")


@congreso_sponsor_router.get(
    "/{congress_id}/{sponsor_id}",
    summary="Obtener sponsorship específico",
    description="Obtiene los detalles de una relación específica entre congreso y sponsor"
)
def get_sponsorship(
    congress_id: int,
    sponsor_id: int,
    db: SessionDep,
    include_congress: bool = Query(False, description="Incluir información del congreso"),
    include_sponsor: bool = Query(False, description="Incluir información del sponsor")
):
    """
    Obtiene una relación de sponsorship específica.

    **Parámetros:**
    - `congress_id`: ID del congreso
    - `sponsor_id`: ID del sponsor
    - `include_congress`: Incluir detalles del congreso
    - `include_sponsor`: Incluir detalles del sponsor
    """
    try:
        sponsorship = congreso_sponsor_controller.get_sponsorship(
            db, congress_id, sponsor_id,
            include_congress=include_congress,
            include_sponsor=include_sponsor
        )
        if not sponsorship:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sponsorship between congress {congress_id} and sponsor {sponsor_id} not found"
            )
        return sponsorship
    except HTTPException:
        raise
    except Exception as e:
        raise handle_controller_error(e, "fetching sponsorship")


@congreso_sponsor_router.patch(
    "/{congress_id}/{sponsor_id}",
    response_model=CongresoSponsorResponse,
    summary="Actualizar una relación de sponsorship",
    description="Actualiza parcialmente una relación de sponsorship existente"
)
def update_sponsorship(
    congress_id: int,
    sponsor_id: int,
    request: CongresoSponsorUpdateRequest,
    db: SessionDep,
    current_user: CurrentUser
) -> CongresoSponsorResponse:
    """
    Actualiza una relación de sponsorship existente.

    **Parámetros:**
    - `congress_id`: ID del congreso
    - `sponsor_id`: ID del sponsor
    - `request`: Datos a actualizar (todos opcionales)

    **Nota:** No se pueden cambiar las claves primarias (congress_id y sponsor_id)
    """
    try:
        result = congreso_sponsor_controller.update_sponsorship(
            db, congress_id, sponsor_id, request.sponsorship, current_user.id
        )
        return CongresoSponsorResponse(
            message="Sponsorship updated successfully",
            data=result
        )
    except Exception as e:
        db.rollback()
        raise handle_controller_error(e, "updating sponsorship")


@congreso_sponsor_router.delete(
    "/{congress_id}/{sponsor_id}",
    status_code=status.HTTP_200_OK,
    response_model=CongresoSponsorResponse,
    summary="Eliminar una relación de sponsorship",
    description="Elimina una relación de sponsorship del sistema"
)
def delete_sponsorship(
    congress_id: int,
    sponsor_id: int,
    db: SessionDep,
    current_user: CurrentUser
) -> CongresoSponsorResponse:
    """
    Elimina una relación de sponsorship.

    **Parámetros:**
    - `congress_id`: ID del congreso
    - `sponsor_id`: ID del sponsor
    """
    try:
        result = congreso_sponsor_controller.delete_sponsorship(
            db, congress_id, sponsor_id, current_user.id
        )
        return CongresoSponsorResponse(
            message="Sponsorship deleted successfully",
            data=result
        )
    except Exception as e:
        db.rollback()
        raise handle_controller_error(e, "deleting sponsorship")


# ============= Rutas de Verificación =============

@congreso_sponsor_router.get(
    "/check-exists/{congress_id}/{sponsor_id}",
    summary="Verificar si existe sponsorship",
    description="Verifica si ya existe una relación entre un congreso y un sponsor"
)
def check_sponsorship_exists(
    congress_id: int,
    sponsor_id: int,
    db: SessionDep
):
    """
    Verifica si existe una relación de sponsorship.

    **Parámetros:**
    - `congress_id`: ID del congreso
    - `sponsor_id`: ID del sponsor
    """
    try:
        return congreso_sponsor_controller.check_sponsorship_exists(
            db, congress_id, sponsor_id
        )
    except Exception as e:
        raise handle_controller_error(e, "checking sponsorship existence")


# ============= Rutas de Operaciones en Lote =============

@congreso_sponsor_router.post(
    "/bulk-create/{congress_id}",
    response_model=CongresoSponsorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear sponsorships en lote para un congreso",
    description="Crea múltiples relaciones de sponsorship para un congreso específico"
)
def bulk_create_sponsorships(
    congress_id: int,
    request: BulkCongresoSponsorCreateRequest,
    db: SessionDep,
    current_user: CurrentUser
) -> CongresoSponsorResponse:
    """
    Crea múltiples sponsorships para un congreso específico.

    **Parámetros:**
    - `congress_id`: ID del congreso
    - `sponsorships`: Lista de sponsorships a crear (máximo 50)

    **Validaciones:**
    - Todos los sponsorships deben ser para el congreso especificado
    - Sponsors únicos en el lote
    - Sponsors no deben tener sponsorships existentes para el congreso
    - Todos los sponsors deben existir
    """
    try:
        result = congreso_sponsor_controller.bulk_create_sponsorships(
            db, congress_id, request.sponsorships, current_user.id
        )
        return CongresoSponsorResponse(
            message=f"Successfully created {result['data']['count']} sponsorships",
            data=result
        )
    except Exception as e:
        db.rollback()
        raise handle_controller_error(e, "bulk creating sponsorships")