from typing import Dict, Any
from src.models.post import Post


class PostSerializer:
    """Maneja la serialización de posts"""
    
    @staticmethod
    def post_to_dict(post: Post) -> Dict[str, Any]:
        """Convierte un post a diccionario"""
        return {
            "id": post.id,
            "sub_text": post.sub_text,
            "main_text": post.main_text,
            "redirection_url": post.redirection_url,
            "image_url": post.image_url,
            "place": post.place.value if post.place else None
        }
