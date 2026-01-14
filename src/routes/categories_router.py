from fastapi import APIRouter, Depends, status
from sqlmodel import Session
from typing import List, Optional
from src.dependencies.auth import get_current_user
from src.controllers.categories_controller import CategoriesController
from src.dependencies.db_session import get_db
from src.models.category import Category, CategoryStatus
from src.models.user import User

categories_router = APIRouter(prefix="/api/v1/categories", tags=["categories"])


# ============= Modelos de Request =============
class CategoryCreateRequest(Category.CategoryCreate):
    """Modelo para crear una categoría"""
    pass


class CategoryUpdateRequest(Category.CategoryUpdate):
    """Modelo para actualizar una categoría"""
    pass


# ============= Rutas de Categorías =============
@categories_router.post(
    "/",
    response_model=Category,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una nueva categoría",
    description="Crear una nueva categoría con los datos proporcionados."
)
def create_category(
    category_data: CategoryCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Crear una nueva categoría"""
    return CategoriesController.create_category(
        db,
        category_data,
        current_user.id
    )


@categories_router.get(
    "/enabled",
    response_model=List[Category],
    summary="Obtener todas las categorías activas",
    description="Obtener todas las categorías que están en estado activo."
)
def get_enabled_categories(db: Session = Depends(get_db)):
    """Obtener todas las categorías activas"""
    return CategoriesController.get_category_enable(db)


@categories_router.get(
    "/",
    summary="Obtener todas las categorías con paginación",
    description="Obtener todas las categorías con paginación, filtrado por estado."
)
def get_all_categories(
    page: int = 1,
    page_size: int = 10,
    status_filter: Optional[CategoryStatus] = None,
    include_inactive: bool = False,
    db: Session = Depends(get_db)
):
    """Obtener todas las categorías con paginación"""
    return CategoriesController.get_all_categories(
        db,
        page,
        page_size,
        status_filter,
        include_inactive
    )


@categories_router.get(
    "/{category_id}",
    response_model=Category,
    summary="Obtener una categoría por su ID",
    description="Obtener una categoría específica utilizando su ID."
)
def get_category_by_id(
    category_id: int,
    db: Session = Depends(get_db)
):
    """Obtener una categoría por su ID"""
    return CategoriesController.get_category_by_id(db, category_id)


@categories_router.get(
    "/by-name/{name}",
    response_model=Category,
    summary="Obtener una categoría por su nombre",
    description="Obtener una categoría específica utilizando su nombre."
)
def get_category_by_name(
    name: str,
    db: Session = Depends(get_db)
):
    """Obtener una categoría por su nombre"""
    return CategoriesController.get_category_by_name(db, name)


@categories_router.put(
    "/{category_id}",
    response_model=Category,
    summary="Actualizar una categoría",
    description="Actualizar los datos de una categoría existente."
)
def update_category(
    category_id: int,
    category_data: CategoryUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Actualizar una categoría existente"""
    return CategoriesController.update_category(
        db,
        category_id,
        category_data
    )


@categories_router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una categoría",
    description="Eliminar (soft delete) una categoría existente."
)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
): 
    """soft Delete de una categoría por su ID"""
    return CategoriesController.delete_category(db, category_id, current_user.id)