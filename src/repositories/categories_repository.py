from typing import List, Optional, Tuple
from sqlmodel import Session, select, func, or_, col
from src.models.category import Category, CategoryStatus
from src.models.course import Course
from datetime import datetime

class CategoryRepository:
    """Repository para operaciones CRUD de categorías"""

    @staticmethod
    def create(
        db: Session, 
        category_data: Category.CategoryCreate,
        created_by: int
    ) -> Category:
        """
        Crear una nueva categoría
        
        Args:
            db: Sesión de base de datos
            category_data: Datos de la categoría
            created_by: ID del usuario que crea
            
        Returns:
            Categoría creada
        """
        category = Category(
            name=category_data.name,
            description=category_data.description,
            svgurl=category_data.svgurl,
            status=category_data.status,
            created_by=created_by,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(category)
        db.commit()
        db.refresh(category)
        return category

    @staticmethod
    def get_by_id(db: Session, category_id: int) -> Optional[Category]:
        """Obtener categoría por ID"""
        return db.get(Category, category_id)

    @staticmethod
    def get_by_name(db: Session, name: str) -> Optional[Category]:
        """Obtener categoría por nombre exacto"""
        statement = (
            select(
                Category.id,
                Category.name, 
                Category.description,
                Category.status,
                Category.svgurl
                )
                .where(Category.name == name))
        return db.exec(statement).first()

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: CategoryStatus = None,
        include_inactive: bool = False
    ) -> Tuple[List[Category], int]:
        """
        Obtener todas las categorías con paginación
        
        Args:
            db: Sesión de base de datos
            skip: Registros a saltar (offset)
            limit: Límite de registros
            status: Filtrar por estado específico
            include_inactive: Incluir categorías inactivas
            
        Returns:
            Tupla (lista de categorías, total de registros)
        """
        # Query base
        statement = select(Category)
        count_statement = select(func.count()).select_from(Category)
        
        # Filtros
        if status:
            statement = statement.where(Category.status == status)
            count_statement = count_statement.where(Category.status == status)
        elif not include_inactive:
            statement = statement.where(Category.status == CategoryStatus.ACTIVO)
            count_statement = count_statement.where(Category.status == CategoryStatus.ACTIVO)
        
        # Ordenar por nombre
        statement = statement.order_by(Category.name)
        
        # Contar total
        total = db.exec(count_statement).one()
        
        # Aplicar paginación
        statement = statement.offset(skip).limit(limit)
        categories = db.exec(statement).all()
        
        return list(categories), total

    @staticmethod
    def get_by_creator(db: Session, user_id: int) -> List[Category]:
        """Obtener categorías creadas por un usuario específico"""
        statement = select(Category).where(
            Category.created_by == user_id
        ).order_by(Category.created_at.desc())
        
        return list(db.exec(statement).all())

    @staticmethod
    def update(
        db: Session,
        category: Category,
        category_data: Category.CategoryUpdate
    ) -> Category:
        """
        Actualizar una categoría
        
        Args:
            db: Sesión de base de datos
            category: Objeto Category a actualizar
            category_data: Datos a actualizar
            
        Returns:
            Categoría actualizada
        """
        # Actualizar solo campos proporcionados
        update_data = category_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(category, key, value)
        
        # Actualizar timestamp
        category.updated_at = datetime.utcnow()
        
        db.add(category)
        db.commit()
        db.refresh(category)
        return category

    @staticmethod
    def delete(db: Session, category: Category, force: bool = False) -> bool:
        """
        Eliminar una categoría (soft o hard delete)
        
        Args:
            db: Sesión de base de datos
            category: Objeto Category a eliminar
            force: Si True, eliminar físicamente; si False, soft delete
            
        Returns:
            True si se eliminó correctamente
        """
        # Verificar si tiene cursos asociados
        has_courses = CategoryRepository.get_courses_count(db, category.id) > 0
        
        if has_courses and not force:
            # Soft delete: marcar como inactiva
            category.status = CategoryStatus.INACTIVO
            category.updated_at = datetime.utcnow()
            db.add(category)
        elif not has_courses and force:
            # Hard delete: eliminar físicamente
            db.delete(category)
        elif has_courses and force:
            # No permitir eliminar si tiene cursos
            return False
        else:
            # Soft delete por defecto
            category.status = CategoryStatus.INACTIVO
            category.updated_at = datetime.utcnow()
            db.add(category)
        
        db.commit()
        return True

    @staticmethod
    def get_courses_count(db: Session, category_id: int) -> int:
        """Obtener cantidad de cursos asociados a una categoría"""
        count = db.exec(
            select(func.count())
            .select_from(Course)
            .where(Course.category_id == category_id)
        ).one()
        return count

    @staticmethod
    def exists_by_name(
        db: Session, 
        name: str, 
        exclude_id: Optional[int] = None
    ) -> bool:
        """
        Verificar si existe una categoría con ese nombre
        
        Args:
            db: Sesión de base de datos
            name: Nombre a verificar
            exclude_id: ID a excluir de la búsqueda (para updates)
            
        Returns:
            True si existe
        """
        statement = select(Category).where(Category.name == name)
        if exclude_id:
            statement = statement.where(Category.id != exclude_id)
        return db.exec(statement).first() is not None

    @staticmethod
    def search(
        db: Session,
        search_term: str,
        only_active: bool = True
    ) -> List[Category]:
        """
        Buscar categorías por nombre o descripción
        
        Args:
            db: Sesión de base de datos
            search_term: Término de búsqueda
            only_active: Solo categorías activas
            
        Returns:
            Lista de categorías que coinciden
        """
        statement = select(Category).where(
            or_(
                col(Category.name).ilike(f"%{search_term}%"),
                col(Category.description).ilike(f"%{search_term}%")
            )
        )
        
        if only_active:
            statement = statement.where(Category.status == CategoryStatus.ACTIVO)
        
        statement = statement.order_by(Category.name)
        
        return list(db.exec(statement).all())
    @staticmethod
    def get_enabled(db: Session) -> List[dict]:
        """Obtener todas las categorías activas"""
        statement = select(Category.id,Category.name,Category.description,Category.svgurl,Category.status).where(Category.status == CategoryStatus.ACTIVO).order_by(Category.name)
        
        result = db.exec(statement).all()
        return [
            {
                "id": row.id,
                "name": row.name,
                "description": row.description,
                "svgurl": row.svgurl,
                "status": row.status

        }
            for row in result
        ]
    @staticmethod
    def get_categories_with_courses_count(
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> List[tuple]:
        """
        Obtener categorías con cantidad de cursos
        
        Returns:
            Lista de tuplas (Category, courses_count)
        """
        statement = select(
            Category,
            func.count(Course.id).label("courses_count")
        ).join(
            Course, 
            Category.id == Course.category_id, 
            isouter=True
        ).where(
            Category.status == CategoryStatus.ACTIVO
        ).group_by(
            Category.id
        ).order_by(
            Category.name
        ).offset(skip).limit(limit)
        
        results = db.exec(statement).all()
        return results