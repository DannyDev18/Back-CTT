from typing import Generic, TypeVar, Type, Dict, Any, Optional, List, Tuple
from abc import ABC, abstractmethod
from fastapi import HTTPException, status as http_status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.repositories.base_repository import BaseRepository
from src.utils.Helpers.pagination_helper import PaginationHelper

# Tipos genéricos
ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
ReadSchemaType = TypeVar("ReadSchemaType", bound=BaseModel)
RepositoryType = TypeVar("RepositoryType", bound=BaseRepository)


class BaseController(Generic[ModelType, CreateSchemaType, UpdateSchemaType, ReadSchemaType], ABC):
    """
    Controlador base con operaciones CRUD genéricas.

    Proporciona métodos comunes que pueden ser heredados y extendidos
    por controladores específicos de cada modelo.
    """

    def __init__(self, repository: RepositoryType, entity_name: str):
        """
        Inicializar controlador base.

        Args:
            repository: Instancia del repositorio
            entity_name: Nombre de la entidad para mensajes de error
        """
        self.repository = repository
        self.entity_name = entity_name

    # Métodos abstractos que deben implementar las subclases
    @abstractmethod
    def serialize_to_dict(self, model: ModelType, **kwargs) -> Dict[str, Any]:
        """Serializar modelo a diccionario."""
        pass

    # Métodos CRUD genéricos
    def create(
        self,
        db: Session,
        obj_in: CreateSchemaType,
        current_user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Crear nuevo registro."""
        try:
            # Validaciones personalizadas pre-creación
            self._validate_before_create(db, obj_in, current_user_id)

            # Crear usando el repositorio
            db_obj = self.repository.create(db, obj_in=obj_in)
            db.commit()
            db.refresh(db_obj)

            # Procesar después de crear
            self._post_create_process(db, db_obj, current_user_id)

            return self.serialize_to_dict(db_obj)

        except ValueError as e:
            db.rollback()
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating {self.entity_name.lower()}: {str(e)}"
            )

    def get_by_id(self, db: Session, id: Any) -> Optional[Dict[str, Any]]:
        """Obtener registro por ID."""
        try:
            db_obj = self.repository.get(db, id)
            if not db_obj:
                return None

            return self.serialize_to_dict(db_obj)

        except Exception as e:
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching {self.entity_name.lower()}: {str(e)}"
            )

    def get_multi(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 10,
        **filters
    ) -> List[Dict[str, Any]]:
        """Obtener múltiples registros."""
        try:
            db_objs = self.repository.get_multi(db, skip=skip, limit=limit)
            return [self.serialize_to_dict(obj) for obj in db_objs]

        except Exception as e:
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching {self.entity_name.lower()}s: {str(e)}"
            )

    def get_paginated(
        self,
        db: Session,
        page: int = 1,
        page_size: int = 10,
        base_path: str = "",
        **filters
    ) -> Dict[str, Any]:
        """Obtener registros paginados."""
        try:
            # Limpiar filtros None
            clean_filters = {k: v for k, v in filters.items() if v is not None}

            db_objs, total = self.repository.get_paginated(
                db,
                page=page,
                page_size=page_size,
                **clean_filters
            )

            items_dict = [self.serialize_to_dict(obj) for obj in db_objs]

            return PaginationHelper.build_pagination_response(
                items=items_dict,
                total=total,
                page=page,
                page_size=page_size,
                base_path=base_path or f"/api/v1/{self.entity_name.lower()}s",
                items_key=f"{self.entity_name.lower()}s",
                extra_params=clean_filters
            )

        except Exception as e:
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching paginated {self.entity_name.lower()}s: {str(e)}"
            )

    def update(
        self,
        db: Session,
        id: Any,
        obj_in: UpdateSchemaType,
        current_user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Actualizar registro."""
        try:
            db_obj = self.repository.get(db, id)
            if not db_obj:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail=f"{self.entity_name} not found"
                )

            # Validaciones personalizadas pre-actualización
            self._validate_before_update(db, db_obj, obj_in, current_user_id)

            # Actualizar usando el repositorio
            updated_obj = self.repository.update(db, db_obj=db_obj, obj_in=obj_in)
            db.commit()
            db.refresh(updated_obj)

            # Procesar después de actualizar
            self._post_update_process(db, updated_obj, current_user_id)

            return self.serialize_to_dict(updated_obj)

        except HTTPException:
            db.rollback()
            raise
        except ValueError as e:
            db.rollback()
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating {self.entity_name.lower()}: {str(e)}"
            )

    def delete(
        self,
        db: Session,
        id: Any,
        current_user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Eliminar registro."""
        try:
            db_obj = self.repository.get(db, id)
            if not db_obj:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail=f"{self.entity_name} not found"
                )

            # Validaciones personalizadas pre-eliminación
            self._validate_before_delete(db, db_obj, current_user_id)

            # Eliminar usando el repositorio
            deleted_obj = self.repository.delete(db, id=id)
            db.commit()

            # Procesar después de eliminar
            self._post_delete_process(db, deleted_obj, current_user_id)

            return {"message": f"{self.entity_name} deleted successfully"}

        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting {self.entity_name.lower()}: {str(e)}"
            )

    def search(
        self,
        db: Session,
        search_term: str,
        search_fields: List[str],
        limit: int = 20,
        **filters
    ) -> List[Dict[str, Any]]:
        """Buscar registros por término."""
        try:
            # Limpiar filtros None
            clean_filters = {k: v for k, v in filters.items() if v is not None}

            db_objs = self.repository.search(
                db,
                search_term=search_term,
                search_fields=search_fields,
                **clean_filters
            )

            return [self.serialize_to_dict(obj) for obj in db_objs[:limit]]

        except Exception as e:
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error searching {self.entity_name.lower()}s: {str(e)}"
            )

    def exists(self, db: Session, **filters) -> Dict[str, bool]:
        """Verificar si existe un registro."""
        try:
            exists = self.repository.exists(db, **filters)
            return {"exists": exists}

        except Exception as e:
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error checking {self.entity_name.lower()} existence: {str(e)}"
            )

    # Métodos hook que pueden ser sobrescritos por las subclases
    def _validate_before_create(
        self,
        db: Session,
        obj_in: CreateSchemaType,
        current_user_id: Optional[int]
    ) -> None:
        """Validaciones personalizadas antes de crear."""
        pass

    def _validate_before_update(
        self,
        db: Session,
        db_obj: ModelType,
        obj_in: UpdateSchemaType,
        current_user_id: Optional[int]
    ) -> None:
        """Validaciones personalizadas antes de actualizar."""
        pass

    def _validate_before_delete(
        self,
        db: Session,
        db_obj: ModelType,
        current_user_id: Optional[int]
    ) -> None:
        """Validaciones personalizadas antes de eliminar."""
        pass

    def _post_create_process(
        self,
        db: Session,
        db_obj: ModelType,
        current_user_id: Optional[int]
    ) -> None:
        """Procesamiento después de crear."""
        pass

    def _post_update_process(
        self,
        db: Session,
        db_obj: ModelType,
        current_user_id: Optional[int]
    ) -> None:
        """Procesamiento después de actualizar."""
        pass

    def _post_delete_process(
        self,
        db: Session,
        db_obj: ModelType,
        current_user_id: Optional[int]
    ) -> None:
        """Procesamiento después de eliminar."""
        pass


class ControllerError(Exception):
    """Excepción base para errores de controlador."""
    pass


class ValidationError(ControllerError):
    """Error de validación."""
    pass


class NotFoundError(ControllerError):
    """Error cuando no se encuentra un registro."""
    pass


def handle_controller_errors(func):
    """Decorador para manejar errores comunes de controlador."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HTTPException:
            # Re-raise HTTPExceptions sin modificar
            raise
        except ValueError as e:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal server error: {str(e)}"
            )

    return wrapper


# Utilidades auxiliares para controladores
class ControllerUtils:
    """Utilidades comunes para controladores."""

    @staticmethod
    def validate_required_fields(data: dict, required_fields: List[str]) -> None:
        """Validar campos requeridos."""
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")

    @staticmethod
    def sanitize_filters(filters: dict) -> dict:
        """Limpiar filtros removiendo valores None y vacíos."""
        return {
            k: v for k, v in filters.items()
            if v is not None and v != "" and v != []
        }

    @staticmethod
    def build_success_response(
        message: str,
        data: Any = None,
        meta: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Construir respuesta de éxito estándar."""
        response = {"message": message}
        if data is not None:
            response["data"] = data
        if meta:
            response["meta"] = meta
        return response

    @staticmethod
    def build_error_response(
        message: str,
        errors: List[str] = None,
        error_code: str = None
    ) -> Dict[str, Any]:
        """Construir respuesta de error estándar."""
        response = {"message": message}
        if errors:
            response["errors"] = errors
        if error_code:
            response["error_code"] = error_code
        return response