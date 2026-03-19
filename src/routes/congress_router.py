from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List, Annotated, Optional
from pydantic import BaseModel, Field
from src.controllers.congress_controller import CongressController
from src.dependencies.db_session import SessionDep
from src.models.congress import (
    CongressCreate,
    CongressRequirementCreate,
    CongressContentCreate,
    CongressUpdate,
    CongressRequirementUpdate,
    CongressContentCreate as CongressContentUpdate,
    CongressStatus,
)
from src.utils.jwt_utils import decode_token
from src.models.user import User

congresses_router = APIRouter(prefix="/api/v1/congresses", tags=["congresses"])


# ============= Modelos de Request =============

class CongressCreateRequest(BaseModel):
    """Modelo para crear un congreso completo"""
    congress: CongressCreate
    requirements: CongressRequirementCreate
    contents: List[CongressContentCreate] = Field(default_factory=list)


class CongressUpdateRequest(BaseModel):
    """Modelo para actualizar un congreso completo"""
    congress: Optional[CongressUpdate] = None
    requirements: Optional[CongressRequirementUpdate] = None
    contents: Optional[List[CongressContentUpdate]] = None


class CongressResponse(BaseModel):
    """Respuesta estándar para operaciones de congresos"""
    message: str
    congress_id: Optional[int] = None
    data: Optional[dict] = None


# ============= Manejadores de Errores =============

def handle_controller_error(e: Exception, operation: str) -> HTTPException:
    """Maneja errores del controlador de forma consistente"""
    if isinstance(e, ValueError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Error {operation}: {str(e)}"
    )


# ============= Rutas CRUD =============

@congresses_router.post(
    "",
    response_model=CongressResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo congreso",
    description="Crea un congreso completo con requisitos y contenidos"
)
def create_congress(
    request: CongressCreateRequest,
    db: SessionDep,
    current_user: Annotated[User, Depends(decode_token)]
) -> CongressResponse:
    """
    Crea un nuevo congreso con todos sus datos relacionados.

    - **congress**: Información básica del congreso
    - **requirements**: Requisitos y detalles del congreso
    - **contents**: Lista de contenidos del congreso
    """
    try:
        result = CongressController.create_congress_with_requirements(
            request.congress,
            request.requirements,
            request.contents,
            db,
            current_user.id
        )
        return CongressResponse(
            message="Congress created successfully",
            congress_id=result.get("id"),
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise handle_controller_error(e, "creating congress")


@congresses_router.get(
    "",
    summary="Listar todos los congresos",
    description="Obtiene una lista paginada de congresos con filtros opcionales"
)
def get_all_congresses(
    db: SessionDep,
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(10, ge=1, le=100, description="Cantidad de congresos por página"),
    status_filter: CongressStatus = Query(CongressStatus.ACTIVO, alias="status", description="Estado del congreso"),
    category_id: Optional[int] = Query(None, description="Filtrar por categoría")
):
    """
    Obtiene todos los congresos con paginación.

    **Parámetros de consulta:**
    - `page`: Número de página (mínimo 1)
    - `page_size`: Congresos por página (1-100)
    - `status`: Estado del congreso (activo/inactivo)
    - `category_id`: Filtrar por categoría específica

    **Respuesta:**
    Incluye información de paginación y lista de congresos
    """
    try:
        return CongressController.get_all_congresses(
            db,
            page=page,
            page_size=page_size,
            status=status_filter,
            category_id=category_id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise handle_controller_error(e, "fetching congresses")


@congresses_router.get(
    "/search",
    summary="Buscar congresos por título",
    description="Busca congresos usando coincidencia parcial en el título (case-insensitive)"
)
def search_congresses_by_title(
    db: SessionDep,
    q: str = Query(..., min_length=1, description="Término de búsqueda", alias="query"),
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(10, ge=1, le=100, description="Cantidad de resultados")
):
    """
    Busca congresos por título.

    **Parámetros:**
    - `q`: Término de búsqueda (mínimo 1 carácter)
    - `page`: Número de página para resultados
    - `page_size`: Cantidad de resultados por página
    """
    try:
        congresses = CongressController.search_congresses_by_title(q, db)

        total = len(congresses)
        start = (page - 1) * page_size
        end = start + page_size

        return {
            "query": q,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "congresses": congresses[start:end]
        }
    except Exception as e:
        raise handle_controller_error(e, "searching congresses")


@congresses_router.get(
    "/category/{category_id}",
    summary="Obtener congresos por categoría",
    description="Lista todos los congresos de una categoría específica"
)
def get_congresses_by_category(
    category_id: int,
    db: SessionDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    """
    Obtiene todos los congresos de una categoría.

    **Parámetros:**
    - `category_id`: ID de la categoría
    - `page`: Número de página
    - `page_size`: Congresos por página
    """
    try:
        congresses = CongressController.get_congresses_by_category(category_id, db)

        total = len(congresses)
        start = (page - 1) * page_size
        end = start + page_size

        return {
            "category_id": category_id,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "congresses": congresses[start:end]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise handle_controller_error(e, "fetching congresses by category")


@congresses_router.get(
    "/{congress_id}",
    summary="Obtener congreso por ID",
    description="Obtiene los detalles completos de un congreso específico"
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
    Detalles completos del congreso incluyendo requisitos y contenidos
    """
    try:
        congress = CongressController.get_congress_by_id(congress_id, db)
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


@congresses_router.patch(
    "/{congress_id}",
    response_model=CongressResponse,
    summary="Actualizar un congreso",
    description="Actualiza parcialmente un congreso existente. Solo se modifican los campos proporcionados."
)
def update_congress(
    congress_id: int,
    request: CongressUpdateRequest,
    db: SessionDep,
    current_user: Annotated[User, Depends(decode_token)]
) -> CongressResponse:
    """
    Actualiza un congreso existente de forma parcial.

    **Parámetros:**
    - `congress_id`: ID del congreso a actualizar
    - `request`: Datos a actualizar (todos opcionales)

    **Nota:** Los campos no proporcionados permanecen sin cambios
    """
    try:
        result = CongressController.update_congress_with_requirements(
            congress_id,
            db,
            request.congress,
            request.requirements,
            request.contents
        )
        return CongressResponse(
            message="Congress updated successfully",
            congress_id=congress_id,
            data=result
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        raise handle_controller_error(e, "updating congress")


@congresses_router.delete(
    "/{congress_id}",
    status_code=status.HTTP_200_OK,
    response_model=CongressResponse,
    summary="Eliminar un congreso",
    description="Realiza un soft delete marcando el congreso como inactivo"
)
def delete_congress(
    congress_id: int,
    db: SessionDep,
    current_user: Annotated[User, Depends(decode_token)]
) -> CongressResponse:
    """
    Elimina un congreso (soft delete).

    **Parámetros:**
    - `congress_id`: ID del congreso a eliminar

    **Nota:** El congreso se marca como inactivo, no se elimina físicamente
    """
    try:
        CongressController.delete_congress(congress_id, db)
        return CongressResponse(
            message="Congress deleted successfully",
            congress_id=congress_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        raise handle_controller_error(e, "deleting congress")
