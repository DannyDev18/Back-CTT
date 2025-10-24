from sqlmodel import Session, select
from typing import Optional, Tuple, List
from sqlalchemy import func
from src.models.post import Post, PostPlace


class PostRepository:
    """Maneja las operaciones de base de datos para posts"""
    
    @staticmethod
    def get_post_by_id(post_id: int, db: Session) -> Optional[Post]:
        """Obtiene un post por ID"""
        statement = select(Post).where(Post.id == post_id)
        return db.exec(statement).first()
    
    @staticmethod
    def get_all_posts(db: Session) -> List[Post]:
        """Obtiene todos los posts"""
        statement = select(Post).order_by(Post.id)
        return db.exec(statement).all()
    
    @staticmethod
    def get_posts_by_place(place: PostPlace, db: Session) -> List[Post]:
        """Obtiene posts filtrados por ubicación"""
        statement = select(Post).where(Post.place == place).order_by(Post.id)
        return db.exec(statement).all()
    
    @staticmethod
    def get_posts_paginated(
        db: Session,
        page: int,
        page_size: int,
        place: Optional[PostPlace] = None
    ) -> Tuple[List[Post], int]:
        """Obtiene posts paginados con filtro opcional por ubicación"""
        # Query base
        statement = select(Post)
        
        # Query para contar
        count_statement = select(func.count()).select_from(Post)
        
        # Filtro por ubicación
        if place:
            statement = statement.where(Post.place == place)
            count_statement = count_statement.where(Post.place == place)
        
        # Ordenar
        statement = statement.order_by(Post.id)
        
        # Contar total
        total = db.exec(count_statement).one()
        
        # Paginar
        offset = (page - 1) * page_size
        posts = db.exec(statement.offset(offset).limit(page_size)).all()
        
        return posts, total
    
    @staticmethod
    def create_post(post: Post, db: Session) -> Post:
        """Crea un nuevo post"""
        db.add(post)
        db.commit()
        db.refresh(post)
        return post
    
    @staticmethod
    def update_post(post: Post, db: Session) -> Post:
        """Actualiza un post existente"""
        db.add(post)
        db.commit()
        db.refresh(post)
        return post
    
    @staticmethod
    def delete_post(post_id: int, db: Session) -> None:
        """Elimina un post (hard delete)"""
        post = PostRepository.get_post_by_id(post_id, db)
        if post:
            db.delete(post)
            db.commit()
