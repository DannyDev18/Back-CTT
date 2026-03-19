from typing import List, Optional, Tuple
from sqlmodel import Session, select, func, or_, col
from src.models.congress_category import CongressCategory, CongressCategoryStatus
from src.models.congress import Congress
from datetime import datetime


class CongressCategoryRepository:
    """Repository para operaciones CRUD de categorías de congresos"""

    @staticmethod
    def create(
        db: Session,
        category_data: CongressCategory.CongressCategoryCreate,
        created_by: int
    ) -> CongressCategory:
        """
        Crear una nueva categoría de congreso

        Args:
            db: Sesión de base de datos
            category_data: Datos de la categoría de congreso
            created_by: ID del usuario que crea

        Returns:
            Categoría de congreso creada
        """
        category = CongressCategory(
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
    def get_by_id(db: Session, category_id: int) -> Optional[CongressCategory]:
        """Obtener categoría de congreso por ID"""
        return db.get(CongressCategory, category_id)

    @staticmethod
    def get_by_name(db: Session, name: str) -> Optional[CongressCategory]:
        """Obtener categoría de congreso por nombre exacto"""
        statement = (
            select(
                CongressCategory.id,
                CongressCategory.name,
                CongressCategory.description,
                CongressCategory.status,
                CongressCategory.svgurl
            )
            .where(CongressCategory.name == name))
        return db.exec(statement).first()

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: CongressCategoryStatus = None,
        include_inactive: bool = False
    ) -> Tuple[List[CongressCategory], int]:
        """
        Obtener todas las categorías de congresos con paginación

        Args:
            db: Sesión de base de datos
            skip: Registros a saltar (offset)
            limit: Límite de registros
            status: Filtrar por estado específico
            include_inactive: Incluir categorías inactivas

        Returns:
            Tupla (lista de categorías de congresos, total de registros)
        """
        # Query base
        statement = select(CongressCategory)
        count_statement = select(func.count()).select_from(CongressCategory)

        # Filtros
        if status:
            statement = statement.where(CongressCategory.status == status)
            count_statement = count_statement.where(CongressCategory.status == status)
        elif not include_inactive:
            statement = statement.where(CongressCategory.status == CongressCategoryStatus.ACTIVO)
            count_statement = count_statement.where(CongressCategory.status == CongressCategoryStatus.ACTIVO)

        # Ordenar por nombre
        statement = statement.order_by(CongressCategory.name)

        # Contar total
        total = db.exec(count_statement).one()

        # Aplicar paginación
        statement = statement.offset(skip).limit(limit)
        categories = db.exec(statement).all()

        return list(categories), total

    @staticmethod
    def get_by_creator(db: Session, user_id: int) -> List[CongressCategory]:
        """Obtener categorías de congresos creadas por un usuario específico"""
        statement = select(CongressCategory).where(
            CongressCategory.created_by == user_id
        ).order_by(CongressCategory.created_at.desc())

        return list(db.exec(statement).all())

    @staticmethod
    def update(
        db: Session,
        category: CongressCategory,
        category_data: CongressCategory.CongressCategoryUpdate
    ) -> CongressCategory:
        """
        Actualizar una categoría de congreso

        Args:
            db: Sesión de base de datos
            category: Objeto CongressCategory a actualizar
            category_data: Datos a actualizar

        Returns:
            Categoría de congreso actualizada
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
    def delete(db: Session, category: CongressCategory, force: bool = False) -> bool:
        """
        Eliminar una categoría de congreso (soft o hard delete)

        Args:
            db: Sesión de base de datos
            category: Objeto CongressCategory a eliminar
            force: Si True, eliminar físicamente; si False, soft delete

        Returns:
            True si se eliminó correctamente
        """
        # Verificar si tiene congresos asociados
        has_congresss = CongressCategoryRepository.get_congresss_count(db, category.id) > 0

        if has_congresss and not force:
            # Soft delete: marcar como inactiva
            category.status = CongressCategoryStatus.INACTIVO
            category.updated_at = datetime.utcnow()
            db.add(category)
        elif not has_congresss and force:
            # Hard delete: eliminar físicamente
            db.delete(category)
        elif has_congresss and force:
            # No permitir eliminar si tiene congresos
            return False
        else:
            # Soft delete por defecto
            category.status = CongressCategoryStatus.INACTIVO
            category.updated_at = datetime.utcnow()
            db.add(category)

        db.commit()
        return True

    @staticmethod
    def get_congresss_count(db: Session, category_id: int) -> int:
        """Obtener cantidad de congresos asociados a una categoría"""
        count = db.exec(
            select(func.count())
            .select_from(Congress)
            .where(Congress.congress_category_id == category_id)
        ).one()
        return count

    @staticmethod
    def exists_by_name(
        db: Session,
        name: str,
        exclude_id: Optional[int] = None
    ) -> bool:
        """
        Verificar si existe una categoría de congreso con ese nombre

        Args:
            db: Sesión de base de datos
            name: Nombre a verificar
            exclude_id: ID a excluir de la búsqueda (para updates)

        Returns:
            True si existe
        """
        statement = select(CongressCategory).where(CongressCategory.name == name)
        if exclude_id:
            statement = statement.where(CongressCategory.id != exclude_id)
        return db.exec(statement).first() is not None

    @staticmethod
    def search(
        db: Session,
        search_term: str,
        only_active: bool = True
    ) -> List[CongressCategory]:
        """
        Buscar categorías de congresos por nombre o descripción

        Args:
            db: Sesión de base de datos
            search_term: Término de búsqueda
            only_active: Solo categorías activas

        Returns:
            Lista de categorías de congresos que coinciden
        """
        statement = select(CongressCategory).where(
            or_(
                col(CongressCategory.name).ilike(f"%{search_term}%"),
                col(CongressCategory.description).ilike(f"%{search_term}%")
            )
        )

        if only_active:
            statement = statement.where(CongressCategory.status == CongressCategoryStatus.ACTIVO)

        statement = statement.order_by(CongressCategory.name)

        return list(db.exec(statement).all())

    @staticmethod
    def get_enabled(db: Session) -> List[dict]:
        """Obtener todas las categorías de congresos activas"""
        statement = select(
            CongressCategory.id,
            CongressCategory.name,
            CongressCategory.description,
            CongressCategory.svgurl,
            CongressCategory.status
        ).where(
            CongressCategory.status == CongressCategoryStatus.ACTIVO
        ).order_by(CongressCategory.name)

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
    def get_categories_with_congresss_count(
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> List[tuple]:
        """
        Obtener categorías de congresos con cantidad de congresos

        Returns:
            Lista de tuplas (CongressCategory, congresss_count)
        """
        statement = select(
            CongressCategory,
            func.count(Congress.id).label("congresss_count")
        ).join(
            Congress,
            CongressCategory.id == Congress.congress_category_id,
            isouter=True
        ).where(
            CongressCategory.status == CongressCategoryStatus.ACTIVO
        ).group_by(
            CongressCategory.id
        ).order_by(
            CongressCategory.name
        ).offset(skip).limit(limit)

        results = db.exec(statement).all()
        return results
