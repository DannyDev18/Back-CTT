from fastapi import APIRouter, Depends, status
from sqlmodel import Session
from typing import Annotated, List, Optional
from src.utils.jwt_utils import decode_token
from src.controllers.congress_categories_controller import CongressCategoriesController
from src.dependencies.db_session import SessionDep, get_db
from src.models.congress_category import CongressCategory, CongressCategoryStatus
from src.models.user import User


congress_categories_router = APIRouter(prefix="/api/v1/congress-categories", tags=["congress-categories"])
CurrentUser = Annotated[User, Depends(decode_token)]


# ============= Modelos de Request =============
class CongressCategoryCreateRequest(CongressCategory.CongressCategoryCreate):
    """Modelo para crear una categoría de congreso"""
    pass


class CongressCategoryUpdateRequest(CongressCategory.CongressCategoryUpdate):
    """Modelo para actualizar una categoría de congreso"""
    pass


# ============= Rutas de Categorías de Congresos =============
@congress_categories_router.post(
    "/",
    response_model=CongressCategory,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una nueva categoría de congreso",
    description="Crear una nueva categoría de congreso con los datos proporcionados."
)
def create_congress_category(
    category_data: CongressCategoryCreateRequest,
    db: SessionDep,
    current_user: CurrentUser
):
    """Crear una nueva categoría de congreso"""
    return CongressCategoriesController.create_congress_category(
        db=db,
        category_data=category_data,
        created_by=current_user.id
    )


@congress_categories_router.get(
    "/enabled",
    response_model=List[dict],
    summary="Obtener todas las categorías de congresos activas",
    description="Obtener todas las categorías de congresos que están en estado activo."
)
def get_enabled_congress_categories(
    db: SessionDep,
):
    """Obtener todas las categorías de congresos activas"""
    return CongressCategoriesController.get_congress_category_enable(db=db)


@congress_categories_router.get(
    "/",
    summary="Obtener todas las categorías de congresos con paginación",
    description="Obtener todas las categorías de congresos con paginación, filtrado por estado."
)
def get_all_congress_categories(
    db: SessionDep,
    current_user: CurrentUser,
    page: int = 1,
    page_size: int = 10,
    status_filter: Optional[CongressCategoryStatus] = None,
    include_inactive: bool = False
):
    """Obtener todas las categorías de congresos con paginación"""
    return CongressCategoriesController.get_all_congress_categories(
        db,
        page,
        page_size,
        status_filter,
        include_inactive
    )


@congress_categories_router.get(
    "/{category_id}",
    response_model=CongressCategory,
    summary="Obtener una categoría de congreso por su ID",
    description="Obtener una categoría de congreso específica utilizando su ID."
)
def get_congress_category_by_id(
    category_id: int,
    db: SessionDep,
):
    """Obtener una categoría de congreso por su ID"""
    return CongressCategoriesController.get_congress_category_by_id(db, category_id)


@congress_categories_router.get(
    "/by-name/{name}",
    response_model=CongressCategory,
    summary="Obtener una categoría de congreso por su nombre",
    description="Obtener una categoría de congreso específica utilizando su nombre."
)
def get_congress_category_by_name(
    name: str,
    db: SessionDep,
):
    """Obtener una categoría de congreso por su nombre"""
    return CongressCategoriesController.get_congress_category_by_name(db, name)


@congress_categories_router.put(
    "/{category_id}",
    response_model=CongressCategory,
    summary="Actualizar una categoría de congreso",
    description="Actualizar los datos de una categoría de congreso existente."
)
def update_congress_category(
    category_id: int,
    category_data: CongressCategoryUpdateRequest,
    db: SessionDep,
    current_user: CurrentUser
):
    """Actualizar una categoría de congreso existente"""
    return CongressCategoriesController.update_congress_category(
        db,
        category_id,
        category_data
    )


@congress_categories_router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una categoría de congreso",
    description="Eliminar (soft delete) una categoría de congreso existente."
)
def delete_congress_category(
    category_id: int,
    db: SessionDep,
    current_user: CurrentUser
):
    """soft Delete de una categoría de congreso por su ID"""
    CongressCategoriesController.delete_congress_category(db, category_id, current_user.id)
    return None
