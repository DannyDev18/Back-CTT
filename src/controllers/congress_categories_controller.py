import datetime
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from src.models.congress_category import CongressCategory, CongressCategoryStatus
from src.repositories.congress_categories_repository import CongressCategoryRepository
from src.utils.Helpers.pagination_helper import PaginationHelper


# Controller para manejar las operaciones de categorías de congresos
class CongressCategoriesController:
    @staticmethod
    def create_congress_category(
        db: Session,
        category_data: CongressCategory.CongressCategoryCreate,
        created_by: int
    ) -> CongressCategory:
        """Crear una nueva categoría de congreso"""
        existing_category = CongressCategoryRepository.get_by_name(db, category_data.name)
        if existing_category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe una categoría de congreso con ese nombre."
            )
        return CongressCategoryRepository.create(db, category_data, created_by)

    @staticmethod
    def get_all_congress_categories(
        db: Session,
        page: int = 1,
        page_size: int = 10,
        status: CongressCategoryStatus = None,
        include_inactive: bool = False
    ) -> Dict[str, Any]:
        """Obtener todas las categorías de congresos con paginación"""
        skip = (page - 1) * page_size
        categories, total = CongressCategoryRepository.get_all(
            db, skip=skip, limit=page_size, status=status, include_inactive=include_inactive
        )

        categories_dict = [category.model_dump() for category in categories]

        # Construir parámetros extra para filtros
        extra_params = {}
        if status:
            extra_params["status"] = status.value
        if include_inactive:
            extra_params["include_inactive"] = str(include_inactive).lower()

        return PaginationHelper.build_pagination_response(
            items=categories_dict,
            total=total,
            page=page,
            page_size=page_size,
            base_path="/api/v1/congress-categories",
            items_key="items",
            extra_params=extra_params if extra_params else None
        )

    @staticmethod
    def get_congress_category_enable(
        db: Session
    ) -> List[CongressCategory]:
        """Obtener todas las categorías de congresos activas"""
        return CongressCategoryRepository.get_enabled(db)

    @staticmethod
    def get_congress_category_by_id(
        db: Session,
        category_id: int
    ) -> CongressCategory:
        """Obtener una categoría de congreso por su ID"""
        category = CongressCategoryRepository.get_by_id(db, category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Categoría de congreso no encontrada."
            )
        return category

    @staticmethod
    def get_congress_category_by_name(
        db: Session,
        name: str
    ) -> CongressCategory:
        """Obtener una categoría de congreso por su nombre"""
        category = CongressCategoryRepository.get_by_name(db, name)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Categoría de congreso no encontrada."
            )
        return category

    @staticmethod
    def update_congress_category(
        db: Session,
        category_id: int,
        category_data: CongressCategory.CongressCategoryUpdate
    ) -> CongressCategory:
        """Actualizar una categoría de congreso existente"""
        category = CongressCategoryRepository.get_by_id(db, category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Categoría de congreso no encontrada."
            )
        return CongressCategoryRepository.update(db, category, category_data)

    @staticmethod
    def delete_congress_category(
        db: Session,
        category_id: int,
        current_user_id: int
    ) -> None:
        """soft Delete de una categoría de congreso por su ID"""
        category = CongressCategoryRepository.get_by_id(db, category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Categoría de congreso no encontrada."
            )
        return CongressCategoryRepository.delete(db, category)
