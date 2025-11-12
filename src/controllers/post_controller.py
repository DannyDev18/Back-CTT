from typing import Dict, Any
from sqlmodel import Session
from src.models.post import PostUpdate, BannersConfig
from src.repositories.post_repository import PostRepository
from src.utils.serializers.post_serializer import PostSerializer


class PostController:
    """Controlador para gestión de configuración de banners"""
    
    @staticmethod
    def get_config(db: Session) -> Dict[str, Any]:
        """Obtiene la configuración de banners"""
        post = PostRepository.get_config(db)
        
        if not post:
            # Retornar configuración vacía si no existe
            return {
                "banner": None,
                "banner2": None,
                "banner3": None
            }
        
        return PostSerializer.post_to_dict(post)
    
    @staticmethod
    def update_config(config_data: PostUpdate, db: Session) -> Dict[str, Any]:
        """Actualiza la configuración de banners"""
        # Convertir a dict incluyendo campos None para permitir eliminar campos
        # y usando mode='json' para serializar correctamente los objetos Pydantic anidados
        config_dict = config_data.model_dump(mode='json', exclude_none=True)
        
        # Obtener configuración actual
        current_post = PostRepository.get_config(db)
        
        if current_post:
            # Merge con configuración existente
            current_config = current_post.config.copy() if current_post.config else {}
            current_config.update(config_dict)
            updated_post = PostRepository.update_config(current_config, db)
        else:
            # Crear nueva configuración
            updated_post = PostRepository.update_config(config_dict, db)
        
        return PostSerializer.post_to_dict(updated_post)
