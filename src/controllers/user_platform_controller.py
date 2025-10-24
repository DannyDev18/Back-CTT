from typing import Optional, Dict, Any
from sqlmodel import Session
from src.models.user_platform import UserPlatform, UserPlatformType
from src.dependencies.db_session import SessionDep
from src.repositories.user_platform_repository import UserPlatformRepository
from src.utils.serializers.user_platform_serializer import UserPlatformSerializer
from src.utils.Helpers.pagination_helper import PaginationHelper


class UserPlatformController:
    """Controlador para gestión de usuarios de la plataforma"""

    @staticmethod
    def get_user_by_email(email: str, db: SessionDep) -> Optional[UserPlatform]:
        """Obtiene un usuario por email"""
        return UserPlatformRepository.get_user_by_email(email, db)

    @staticmethod
    def get_user_by_identification(identification: str, db: SessionDep) -> Optional[UserPlatform]:
        """Obtiene un usuario por identificación"""
        return UserPlatformRepository.get_user_by_identification(identification, db)

    @staticmethod
    def create_user(user: UserPlatform, db: SessionDep) -> UserPlatform:
        """Crea un nuevo usuario"""
        return UserPlatformRepository.create_user(user, db)

    @staticmethod
    def get_all_users(
        db: Session,
        page: int = 1,
        page_size: int = 10,
        type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Obtiene todos los usuarios con paginación"""
        # Convertir string a enum si es necesario
        type_filter = None
        if type:
            try:
                type_filter = UserPlatformType(type)
            except ValueError:
                type_filter = None
        
        # Obtener usuarios paginados
        users, total = UserPlatformRepository.get_users_paginated(
            db, page, page_size, type_filter
        )
        
        # Serializar usuarios
        users_dict = [
            UserPlatformSerializer.user_to_dict(user, include_password=False)
            for user in users
        ]
        
        # Construir respuesta paginada
        extra_params = {"type": type} if type else None
        return PaginationHelper.build_pagination_response(
            items=users_dict,
            total=total,
            page=page,
            page_size=page_size,
            base_path="/api/v1/users",
            items_key="users",
            extra_params=extra_params
        )
