from typing import Generic, TypeVar, Type, List, Optional, Tuple, Any, Dict
from sqlmodel import Session
from sqlalchemy import select, func, desc, asc, or_
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

# Tipos genéricos para el repositorio base
ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Repositorio base con operaciones CRUD genéricas.

    Proporciona métodos comunes que pueden ser heredados y extendidos
    por repositorios específicos de cada modelo.
    """

    def __init__(self, model: Type[ModelType]):
        """
        Inicializar repositorio base.

        Args:
            model: Clase del modelo SQLAlchemy
        """
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """Obtener un registro por ID."""
        return db.get(self.model, id)

    def get_multi(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        order_by: str = None,
        order_desc: bool = False
    ) -> List[ModelType]:
        """Obtener múltiples registros con paginación y ordenamiento."""
        query = select(self.model)

        if order_by and hasattr(self.model, order_by):
            order_column = getattr(self.model, order_by)
            if order_desc:
                query = query.order_by(desc(order_column))
            else:
                query = query.order_by(asc(order_column))

        return db.exec(query.offset(skip).limit(limit)).all()

    def get_count(self, db: Session, **filters) -> int:
        """Contar registros con filtros opcionales."""
        query = select(func.count()).select_from(self.model)

        if filters:
            conditions = []
            for field, value in filters.items():
                if hasattr(self.model, field) and value is not None:
                    conditions.append(getattr(self.model, field) == value)
            if conditions:
                query = query.where(*conditions)

        return db.exec(query).scalar()

    def get_paginated(
        self,
        db: Session,
        page: int = 1,
        page_size: int = 10,
        order_by: str = None,
        order_desc: bool = False,
        **filters
    ) -> Tuple[List[ModelType], int]:
        """
        Obtener registros paginados con filtros y ordenamiento.

        Returns:
            Tuple[List[ModelType], int]: (registros, total_count)
        """
        # Contar total
        total = self.get_count(db, **filters)

        # Query base
        query = select(self.model)

        # Aplicar filtros
        if filters:
            conditions = []
            for field, value in filters.items():
                if hasattr(self.model, field) and value is not None:
                    conditions.append(getattr(self.model, field) == value)
            if conditions:
                query = query.where(*conditions)

        # Aplicar ordenamiento
        if order_by and hasattr(self.model, order_by):
            order_column = getattr(self.model, order_by)
            if order_desc:
                query = query.order_by(desc(order_column))
            else:
                query = query.order_by(asc(order_column))

        # Aplicar paginación
        offset = (page - 1) * page_size
        items = db.exec(query.offset(offset).limit(page_size)).all()

        return items, total

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """Crear un nuevo registro."""
        obj_data = obj_in.model_dump() if hasattr(obj_in, 'model_dump') else obj_in.dict()
        db_obj = self.model(**obj_data)
        db.add(db_obj)
        db.commit()  # Para obtener el ID y persistir cambios
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: UpdateSchemaType
    ) -> ModelType:
        """Actualizar un registro existente."""
        obj_data = obj_in.model_dump(exclude_unset=True) if hasattr(obj_in, 'model_dump') else obj_in.dict(exclude_unset=True)

        for field, value in obj_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, *, id: Any) -> ModelType:
        """Eliminar un registro por ID."""
        obj = db.get(self.model, id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj

    def search(
        self,
        db: Session,
        search_term: str,
        search_fields: List[str],
        **filters
    ) -> List[ModelType]:
        """
        Buscar registros por término en campos específicos.

        Args:
            search_term: Término de búsqueda
            search_fields: Lista de campos donde buscar
            **filters: Filtros adicionales
        """
        query = select(self.model)

        # Aplicar búsqueda
        if search_term and search_fields:
            search_conditions = []
            for field in search_fields:
                if hasattr(self.model, field):
                    column = getattr(self.model, field)
                    if hasattr(column.type, 'python_type') and column.type.python_type == str:
                        search_conditions.append(column.ilike(f"%{search_term}%"))

            if search_conditions:
                query = query.where(or_(*search_conditions))

        # Aplicar filtros adicionales
        if filters:
            conditions = []
            for field, value in filters.items():
                if hasattr(self.model, field) and value is not None:
                    conditions.append(getattr(self.model, field) == value)
            if conditions:
                query = query.where(*conditions)

        return db.exec(query).all()

    def exists(self, db: Session, **filters) -> bool:
        """Verificar si existe al menos un registro con los filtros dados."""
        query = select(self.model)

        if filters:
            conditions = []
            for field, value in filters.items():
                if hasattr(self.model, field) and value is not None:
                    conditions.append(getattr(self.model, field) == value)
            if conditions:
                query = query.where(*conditions)

        return db.exec(query.limit(1)).first() is not None

    def bulk_create(self, db: Session, *, objs_in: List[CreateSchemaType]) -> List[ModelType]:
        """Crear múltiples registros en lote."""
        db_objs = []
        for obj_in in objs_in:
            obj_data = obj_in.model_dump() if hasattr(obj_in, 'model_dump') else obj_in.dict()
            db_obj = self.model(**obj_data)
            db.add(db_obj)
            db_objs.append(db_obj)

        db.commit()
        for db_obj in db_objs:
            db.refresh(db_obj)

        return db_objs


class RepositoryError(Exception):
    """Excepción base para errores de repositorio."""
    pass


class NotFoundError(RepositoryError):
    """Error cuando no se encuentra un registro."""
    pass


class DuplicateError(RepositoryError):
    """Error cuando se intenta crear un registro duplicado."""
    pass


def handle_repository_errors(func):
    """Decorador para manejar errores comunes de repositorio."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Aquí puedes agregar logging
            raise RepositoryError(f"Error en operación de repositorio: {str(e)}")

    return wrapper