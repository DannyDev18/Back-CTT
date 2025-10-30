from typing import Dict, Any
from src.models.post import Post


class PostSerializer:
    """Maneja la serialización de configuración de banners"""
    
    @staticmethod
    def post_to_dict(post: Post) -> Dict[str, Any]:
        """Convierte la configuración de banners a diccionario"""
        return post.config if post.config else {
            "banner": None,
            "banner2": None,
            "banner3": None
        }
