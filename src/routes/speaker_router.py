from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List, Annotated, Optional
from pydantic import BaseModel, Field
from src.controllers.speaker_controller import speaker_controller
from src.dependencies.db_session import SessionDep
from src.models.speaker_model import (
    SpeakerCreate,
    SpeakerUpdate,
    SpeakerRead
)
from src.utils.jwt_utils import decode_token
from src.models.user import User

speaker_router = APIRouter(prefix="/api/v1/speakers", tags=["speakers"])
CurrentUser = Annotated[User, Depends(decode_token)]


# ============= Modelos de Request =============

class SpeakerCreateRequest(BaseModel):
    """Modelo para crear un speaker"""
    speaker: SpeakerCreate


class SpeakerUpdateRequest(BaseModel):
    """Modelo para actualizar un speaker"""
    speaker: SpeakerUpdate


class SpeakerResponse(BaseModel):
    """Respuesta estándar para operaciones de speakers"""
    message: str
    speaker_id: Optional[int] = None
    data: Optional[dict] = None


class BulkSpeakerCreateRequest(BaseModel):
    """Modelo para creación en lote de speakers"""
    speakers: List[SpeakerCreate] = Field(..., min_items=1, max_items=50)


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

@speaker_router.post(
    "",
    response_model=SpeakerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo speaker",
    description="Crea un nuevo speaker/ponente en el sistema"
)
def create_speaker(
    request: SpeakerCreateRequest,
    db: SessionDep,
    current_user: CurrentUser
) -> SpeakerResponse:
    """
    Crea un nuevo speaker/ponente.

    - **speaker**: Información completa del speaker
    """
    try:
        result = speaker_controller.create_speaker(
            db, request.speaker, current_user.id
        )
        return SpeakerResponse(
            message="Speaker created successfully",
            speaker_id=result.get("id_speaker"),
            data=result
        )
    except Exception as e:
        db.rollback()
        raise handle_controller_error(e, "creating speaker")


@speaker_router.get(
    "",
    summary="Listar todos los speakers",
    description="Obtiene una lista paginada de speakers con filtros opcionales"
)
def get_all_speakers(
    db: SessionDep,
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(10, ge=1, le=100, description="Cantidad de speakers por página"),
    congress_id: Optional[int] = Query(None, description="Filtrar por congreso"),
    tipo_speaker: Optional[str] = Query(None, description="Filtrar por tipo de speaker"),
    pais: Optional[str] = Query(None, description="Filtrar por país"),
    search_term: Optional[str] = Query(None, description="Término de búsqueda en nombres"),
    order_by: str = Query("nombres_completos", description="Campo para ordenar"),
    order_desc: bool = Query(False, description="Orden descendente")
):
    """
    Obtiene todos los speakers con paginación y filtros.

    **Parámetros de consulta:**
    - `page`: Número de página (mínimo 1)
    - `page_size`: Speakers por página (1-100)
    - `congress_id`: Filtrar por congreso específico
    - `tipo_speaker`: Tipo de speaker (ponente, panelista, etc.)
    - `pais`: País del speaker
    - `search_term`: Búsqueda en nombres del speaker
    - `order_by`: Campo para ordenar
    - `order_desc`: Orden descendente
    """
    try:
        return speaker_controller.get_all_speakers(
            db,
            page=page,
            page_size=page_size,
            congress_id=congress_id,
            tipo_speaker=tipo_speaker,
            pais=pais,
            search_term=search_term,
            order_by=order_by,
            order_desc=order_desc
        )
    except Exception as e:
        raise handle_controller_error(e, "fetching speakers")


@speaker_router.get(
    "/search",
    summary="Buscar speakers",
    description="Busca speakers usando coincidencia parcial en nombres"
)
def search_speakers(
    db: SessionDep,
    q: str = Query(..., min_length=1, description="Término de búsqueda", alias="query"),
    congress_id: Optional[int] = Query(None, description="Filtrar por congreso"),
    limit: int = Query(20, ge=1, le=100, description="Límite de resultados")
):
    """
    Busca speakers por término.

    **Parámetros:**
    - `q`: Término de búsqueda (mínimo 1 carácter)
    - `congress_id`: Filtrar por congreso específico
    - `limit`: Límite de resultados
    """
    try:
        return speaker_controller.search_speakers(
            db, search_term=q, congress_id=congress_id, limit=limit
        )
    except Exception as e:
        raise handle_controller_error(e, "searching speakers")


@speaker_router.get(
    "/by-congress/{congress_id}",
    summary="Obtener speakers por congreso",
    description="Lista todos los speakers de un congreso específico"
)
def get_speakers_by_congress(
    congress_id: int,
    db: SessionDep,
    include_sessions: bool = Query(False, description="Incluir información de sesiones")
):
    """
    Obtiene todos los speakers de un congreso.

    **Parámetros:**
    - `congress_id`: ID del congreso
    - `include_sessions`: Incluir detalles de sesiones asignadas
    """
    try:
        return speaker_controller.get_speakers_by_congress(
            db, congress_id, include_sessions=include_sessions
        )
    except Exception as e:
        raise handle_controller_error(e, "fetching speakers by congress")


@speaker_router.get(
    "/by-type/{tipo_speaker}",
    summary="Obtener speakers por tipo",
    description="Lista speakers filtrados por tipo (ponente, panelista, etc.)"
)
def get_speakers_by_type(
    tipo_speaker: str,
    db: SessionDep,
    congress_id: Optional[int] = Query(None, description="Filtrar por congreso")
):
    """
    Obtiene speakers por tipo.

    **Parámetros:**
    - `tipo_speaker`: Tipo de speaker
    - `congress_id`: Filtrar por congreso específico (opcional)
    """
    try:
        return speaker_controller.get_speakers_by_type(
            db, tipo_speaker, congress_id=congress_id
        )
    except Exception as e:
        raise handle_controller_error(e, "fetching speakers by type")


@speaker_router.get(
    "/by-country/{pais}",
    summary="Obtener speakers por país",
    description="Lista speakers de un país específico"
)
def get_speakers_by_country(
    pais: str,
    db: SessionDep,
    congress_id: Optional[int] = Query(None, description="Filtrar por congreso")
):
    """
    Obtiene speakers por país.

    **Parámetros:**
    - `pais`: País del speaker
    - `congress_id`: Filtrar por congreso específico (opcional)
    """
    try:
        return speaker_controller.get_speakers_by_country(
            db, pais, congress_id=congress_id
        )
    except Exception as e:
        raise handle_controller_error(e, "fetching speakers by country")


@speaker_router.get(
    "/by-institution",
    summary="Obtener speakers por institución",
    description="Lista speakers de una institución específica"
)
def get_speakers_by_institution(
    db: SessionDep,
    institucion: str = Query(..., description="Nombre de la institución"),
    exact_match: bool = Query(False, description="Búsqueda exacta o parcial")
):
    """
    Obtiene speakers por institución.

    **Parámetros:**
    - `institucion`: Nombre de la institución
    - `exact_match`: Si la búsqueda debe ser exacta
    """
    try:
        return speaker_controller.get_speakers_by_institution(
            db, institucion, exact_match=exact_match
        )
    except Exception as e:
        raise handle_controller_error(e, "fetching speakers by institution")


@speaker_router.get(
    "/frequent",
    summary="Obtener speakers frecuentes",
    description="Lista speakers que han participado en múltiples congresos"
)
def get_frequent_speakers(
    db: SessionDep,
    min_congresses: int = Query(2, ge=2, description="Número mínimo de congresos"),
    limit: int = Query(20, ge=1, le=100, description="Límite de resultados")
):
    """
    Obtiene speakers que han participado en múltiples congresos.

    **Parámetros:**
    - `min_congresses`: Número mínimo de congresos para considerarse frecuente
    - `limit`: Límite de resultados
    """
    try:
        return speaker_controller.get_frequent_speakers(
            db, min_congresses=min_congresses, limit=limit
        )
    except Exception as e:
        raise handle_controller_error(e, "fetching frequent speakers")


@speaker_router.get(
    "/countries",
    summary="Obtener países con speakers",
    description="Lista países que tienen speakers registrados"
)
def get_countries_with_speakers(
    db: SessionDep,
    congress_id: Optional[int] = Query(None, description="Filtrar por congreso")
):
    """
    Obtiene lista de países representados por speakers.

    **Parámetros:**
    - `congress_id`: Filtrar por congreso específico (opcional)
    """
    try:
        return speaker_controller.get_countries_with_speakers(
            db, congress_id=congress_id
        )
    except Exception as e:
        raise handle_controller_error(e, "fetching countries with speakers")


@speaker_router.get(
    "/institutions",
    summary="Obtener instituciones con speakers",
    description="Lista instituciones que tienen speakers registrados"
)
def get_institutions_with_speakers(
    db: SessionDep,
    congress_id: Optional[int] = Query(None, description="Filtrar por congreso")
):
    """
    Obtiene lista de instituciones representadas por speakers.

    **Parámetros:**
    - `congress_id`: Filtrar por congreso específico (opcional)
    """
    try:
        return speaker_controller.get_institutions_with_speakers(
            db, congress_id=congress_id
        )
    except Exception as e:
        raise handle_controller_error(e, "fetching institutions with speakers")


@speaker_router.get(
    "/summary",
    summary="Obtener resumen de speakers",
    description="Estadísticas generales del sistema de speakers"
)
def get_speaker_summary(db: SessionDep):
    """
    Obtiene un resumen estadístico del sistema de speakers.
    """
    try:
        return speaker_controller.get_speaker_summary(db)
    except Exception as e:
        raise handle_controller_error(e, "fetching speaker summary")


@speaker_router.get(
    "/{speaker_id}",
    summary="Obtener speaker por ID",
    description="Obtiene los detalles completos de un speaker específico"
)
def get_speaker_by_id(
    speaker_id: int,
    db: SessionDep,
    include_sessions: bool = Query(False, description="Incluir información de sesiones"),
    include_congress: bool = Query(False, description="Incluir información del congreso")
):
    """
    Obtiene un speaker específico con sus datos.

    **Parámetros:**
    - `speaker_id`: ID único del speaker
    - `include_sessions`: Incluir detalles de sesiones asignadas
    - `include_congress`: Incluir información del congreso
    """
    try:
        speaker = speaker_controller.get_speaker_by_id(
            db, speaker_id,
            include_sessions=include_sessions,
            include_congress=include_congress
        )
        if not speaker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Speaker with id {speaker_id} not found"
            )
        return speaker
    except HTTPException:
        raise
    except Exception as e:
        raise handle_controller_error(e, "fetching speaker")


@speaker_router.get(
    "/{congress_id}/statistics",
    summary="Obtener estadísticas de speakers por congreso",
    description="Estadísticas detalladas de speakers para un congreso específico"
)
def get_speaker_statistics_by_congress(
    congress_id: int,
    db: SessionDep
):
    """
    Obtiene estadísticas de speakers para un congreso.

    **Parámetros:**
    - `congress_id`: ID del congreso

    **Respuesta:**
    Estadísticas por país, tipo, institución, etc.
    """
    try:
        return speaker_controller.get_speaker_statistics_by_congress(db, congress_id)
    except Exception as e:
        raise handle_controller_error(e, "fetching speaker statistics")


@speaker_router.patch(
    "/{speaker_id}",
    response_model=SpeakerResponse,
    summary="Actualizar un speaker",
    description="Actualiza parcialmente un speaker existente"
)
def update_speaker(
    speaker_id: int,
    request: SpeakerUpdateRequest,
    db: SessionDep,
    current_user: CurrentUser
) -> SpeakerResponse:
    """
    Actualiza un speaker existente de forma parcial.

    **Parámetros:**
    - `speaker_id`: ID del speaker a actualizar
    - `request`: Datos a actualizar (todos opcionales)
    """
    try:
        result = speaker_controller.update_speaker(
            db, speaker_id, request.speaker, current_user.id
        )
        return SpeakerResponse(
            message="Speaker updated successfully",
            speaker_id=speaker_id,
            data=result
        )
    except Exception as e:
        db.rollback()
        raise handle_controller_error(e, "updating speaker")


@speaker_router.delete(
    "/{speaker_id}",
    status_code=status.HTTP_200_OK,
    response_model=SpeakerResponse,
    summary="Eliminar un speaker",
    description="Elimina un speaker del sistema"
)
def delete_speaker(
    speaker_id: int,
    db: SessionDep,
    current_user: CurrentUser
) -> SpeakerResponse:
    """
    Elimina un speaker.

    **Parámetros:**
    - `speaker_id`: ID del speaker a eliminar

    **Nota:** Solo se puede eliminar si no tiene sesiones programadas
    """
    try:
        result = speaker_controller.delete_speaker(
            db, speaker_id, current_user.id
        )
        return SpeakerResponse(
            message="Speaker deleted successfully",
            speaker_id=speaker_id,
            data=result
        )
    except Exception as e:
        db.rollback()
        raise handle_controller_error(e, "deleting speaker")


# ============= Rutas de Verificación =============

@speaker_router.get(
    "/check-exists/{congress_id}/{nombres_completos}",
    summary="Verificar si speaker existe en congreso",
    description="Verifica si un speaker ya existe en un congreso específico"
)
def check_speaker_exists_in_congress(
    congress_id: int,
    nombres_completos: str,
    db: SessionDep,
    exclude_speaker_id: Optional[int] = Query(None, description="ID de speaker a excluir")
):
    """
    Verifica si un speaker existe en un congreso.

    **Parámetros:**
    - `congress_id`: ID del congreso
    - `nombres_completos`: Nombre completo del speaker
    - `exclude_speaker_id`: ID a excluir de la verificación
    """
    try:
        return speaker_controller.check_speaker_exists_in_congress(
            db, nombres_completos, congress_id, exclude_speaker_id
        )
    except Exception as e:
        raise handle_controller_error(e, "checking speaker existence")


# ============= Rutas de Operaciones en Lote =============

@speaker_router.post(
    "/bulk-import/{congress_id}",
    response_model=SpeakerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Importar speakers en lote para un congreso",
    description="Crea múltiples speakers para un congreso específico"
)
def bulk_import_speakers(
    congress_id: int,
    request: BulkSpeakerCreateRequest,
    db: SessionDep,
    current_user: CurrentUser
) -> SpeakerResponse:
    """
    Importa múltiples speakers para un congreso específico.

    **Parámetros:**
    - `congress_id`: ID del congreso
    - `speakers`: Lista de speakers a crear (máximo 50)

    **Validaciones:**
    - Todos los speakers deben ser para el congreso especificado
    - Nombres únicos en el lote y en la BD
    - Congress debe existir
    """
    try:
        result = speaker_controller.bulk_import_speakers(
            db, congress_id, request.speakers, current_user.id
        )
        return SpeakerResponse(
            message=f"Successfully imported {result['data']['count']} speakers",
            data=result
        )
    except Exception as e:
        db.rollback()
        raise handle_controller_error(e, "bulk importing speakers")