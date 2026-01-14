import datetime
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from src.models.category import Category, CategoryStatus
from src.repositories.categories_repository import CategoryRepository
from src.utils.Helpers.pagination_helper import PaginationHelper

# Controller para manejar las operaciones de categorías
class CategoriesController:
    @staticmethod
    def create_category(
        db: Session,
        category_data: Category.CategoryCreate,
        created_by: int
    ) -> Category:
        """Crear una nueva categoria"""
        existing_category = CategoryRepository.get_by_name(db, category_data.name)
        if existing_category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe una categoría con ese nombre."
            )
        return CategoryRepository.create(db, category_data, created_by)
    @staticmethod
    def get_all_categories(
        db: Session,
        page: int = 1,
        page_size: int = 10,
        status: CategoryStatus = None,
        include_inactive: bool = False
    ) -> Dict[str, Any]:
        """Obtener todas las categorías con paginación"""
        skip = (page - 1) * page_size
        categories, total = CategoryRepository.get_all(
            db, skip=skip, limit=page_size, status=status, include_inactive=include_inactive
        )
        
        categories_dict = [category.model_dump() for category in categories]
        
        return PaginationHelper.build_pagination_response(
            items=categories_dict,
            total=total,
            page=page,
            page_size=page_size
        )
    @staticmethod
    def get_category_enable(
        db: Session
    ) -> List[Category]:
        """Obtener todas las categorías activas"""
        return CategoryRepository.get_all_enable(db)
    
    @staticmethod
    def get_category_by_id(
        db: Session,
        category_id: int
    ) -> Category:
        """Obtener una categoría por su ID"""
        category = CategoryRepository.get_by_id(db, category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Categoría no encontrada."
            )
        return category
    @staticmethod
    def get_category_by_name(
        db: Session,
        name: str
    ) -> Category:
        """Obtener una categoría por su nombre"""
        category = CategoryRepository.get_by_name(db, name)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Categoría no encontrada."
            )
        return category
    @staticmethod
    def update_category(
        db: Session,
        category_id: int,
        category_data: Category.CategoryUpdate
    ) -> Category:
        """Actualizar una categoría existente"""
        category = CategoryRepository.get_by_id(db, category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Categoría no encontrada."
            )
        return CategoryRepository.update(db, category, category_data)
    
    @staticmethod
    def delete_category(
        db: Session,
        category_id: int,
        current_user_id: int
    ) -> None:
        """soft Delete de una categoría por su ID"""
        category = CategoryRepository.get_by_id(db, category_id)
        if not category:
              raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoría no encontrada."
        )
        return CategoryRepository.delete(db, category)
    
    
    


    