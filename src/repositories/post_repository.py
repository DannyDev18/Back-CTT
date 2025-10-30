from sqlmodel import Session, select
from typing import Optional
from src.models.post import Post


class PostRepository:
    """Maneja las operaciones de base de datos para configuración de banners"""
    
    @staticmethod
    def get_config(db: Session) -> Optional[Post]:
        """Obtiene la configuración de banners (siempre retorna el primer registro)"""
        statement = select(Post).limit(1)
        return db.exec(statement).first()
    
    @staticmethod
    def create_config(config: dict, db: Session) -> Post:
        """Crea la configuración inicial de banners"""
        post = Post(config=config)
        db.add(post)
        db.commit()
        db.refresh(post)
        return post
    
    @staticmethod
    def update_config(config: dict, db: Session) -> Post:
        """Actualiza la configuración de banners"""
        post = PostRepository.get_config(db)
        
        if not post:
            # Si no existe, crear una nueva configuración
            return PostRepository.create_config(config, db)
        
        # Actualizar la configuración existente
        post.config = config
        db.add(post)
        db.commit()
        db.refresh(post)
        return post
