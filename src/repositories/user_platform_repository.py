from sqlmodel import Session, select
from typing import Optional, Tuple, List
from sqlalchemy import func
from src.models.user_platform import UserPlatform, UserPlatformType


class UserPlatformRepository:
    """Maneja las operaciones de base de datos para usuarios"""
    
    @staticmethod
    def get_user_by_email(email: str, db: Session) -> Optional[UserPlatform]:
        """Obtiene un usuario por email"""
        statement = select(UserPlatform).where(UserPlatform.email == email)
        return db.exec(statement).first()
    
    @staticmethod
    def get_user_by_identification(identification: str, db: Session) -> Optional[UserPlatform]:
        """Obtiene un usuario por identificación"""
        statement = select(UserPlatform).where(UserPlatform.identification == identification)
        return db.exec(statement).first()
    
    @staticmethod
    def get_user_by_id(user_id: int, db: Session) -> Optional[UserPlatform]:
        """Obtiene un usuario por ID"""
        statement = select(UserPlatform).where(UserPlatform.id == user_id)
        return db.exec(statement).first()
    
    @staticmethod
    def create_user(user: UserPlatform, db: Session) -> UserPlatform:
        """Crea un nuevo usuario"""
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def get_users_paginated(
        db: Session,
        page: int,
        page_size: int,
        type: Optional[UserPlatformType] = None
    ) -> Tuple[List[UserPlatform], int]:
        """Obtiene usuarios paginados con filtro opcional por tipo"""
        # Query base
        statement = select(UserPlatform)
        
        # Query para contar
        count_statement = select(func.count()).select_from(UserPlatform)
        
        # Filtro por tipo
        if type:
            statement = statement.where(UserPlatform.type == type)
            count_statement = count_statement.where(UserPlatform.type == type)
        
        # Ordenar
        statement = statement.order_by(UserPlatform.id)
        
        # Contar total
        total = db.exec(count_statement).one()
        
        # Paginar
        offset = (page - 1) * page_size
        users = db.exec(statement.offset(offset).limit(page_size)).all()
        
        return users, total
    
    @staticmethod
    def update_user(user: UserPlatform, db: Session) -> UserPlatform:
        """Actualiza un usuario existente"""
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def delete_user(user_id: int, db: Session) -> None:
        """Elimina un usuario (hard delete)"""
        user = UserPlatformRepository.get_user_by_id(user_id, db)
        if user:
            db.delete(user)
            db.commit()
