from typing import Optional, Dict, Any, List
from sqlmodel import Session
from src.models.post import Post, PostCreate, PostUpdate, PostPlace
from src.repositories.post_repository import PostRepository
from src.utils.serializers.post_serializer import PostSerializer
from src.utils.Helpers.pagination_helper import PaginationHelper


class PostController:
    """Controlador para gestión de posts"""
    
    @staticmethod
    def create_post(post_data: PostCreate, db: Session) -> Dict[str, Any]:
        """Crea un nuevo post"""
        post = Post(
            sub_text=post_data.sub_text,
            main_text=post_data.main_text,
            redirection_url=post_data.redirection_url,
            image_url=post_data.image_url,
            place=post_data.place
        )
        
        created_post = PostRepository.create_post(post, db)
        return PostSerializer.post_to_dict(created_post)
    
    @staticmethod
    def get_post_by_id(post_id: int, db: Session) -> Optional[Dict[str, Any]]:
        """Obtiene un post por ID"""
        post = PostRepository.get_post_by_id(post_id, db)
        if not post:
            return None
        return PostSerializer.post_to_dict(post)
    
    @staticmethod
    def get_all_posts(
        db: Session,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        place: Optional[str] = None
    ) -> Dict[str, Any] | List[Dict[str, Any]]:
        """
        Obtiene todos los posts con paginación opcional y filtro por ubicación
        Si no se especifica paginación, retorna todos los posts
        """
        # Convertir string a enum si es necesario
        place_filter = None
        if place:
            try:
                place_filter = PostPlace(place)
            except ValueError:
                place_filter = None
        
        # Si se solicita paginación
        if page is not None and page_size is not None:
            posts, total = PostRepository.get_posts_paginated(
                db, page, page_size, place_filter
            )
            
            # Serializar posts
            posts_dict = [
                PostSerializer.post_to_dict(post)
                for post in posts
            ]
            
            # Construir respuesta paginada
            extra_params = {"place": place} if place else None
            return PaginationHelper.build_pagination_response(
                items=posts_dict,
                total=total,
                page=page,
                page_size=page_size,
                base_path="/api/v1/posts",
                items_key="posts",
                extra_params=extra_params
            )
        
        # Sin paginación, retornar todos
        if place_filter:
            posts = PostRepository.get_posts_by_place(place_filter, db)
        else:
            posts = PostRepository.get_all_posts(db)
        
        return [PostSerializer.post_to_dict(post) for post in posts]
    
    @staticmethod
    def get_posts_by_place(place: str, db: Session) -> List[Dict[str, Any]]:
        """Obtiene posts filtrados por ubicación"""
        try:
            place_enum = PostPlace(place)
        except ValueError:
            raise ValueError(f"Invalid place value: {place}")
        
        posts = PostRepository.get_posts_by_place(place_enum, db)
        return [PostSerializer.post_to_dict(post) for post in posts]
    
    @staticmethod
    def update_post(
        post_id: int,
        post_data: PostUpdate,
        db: Session
    ) -> Dict[str, Any]:
        """Actualiza un post existente"""
        post = PostRepository.get_post_by_id(post_id, db)
        if not post:
            raise ValueError("Post not found")
        
        # Actualizar solo los campos proporcionados
        update_dict = post_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(post, key, value)
        
        updated_post = PostRepository.update_post(post, db)
        return PostSerializer.post_to_dict(updated_post)
    
    @staticmethod
    def delete_post(post_id: int, db: Session) -> None:
        """Elimina un post"""
        post = PostRepository.get_post_by_id(post_id, db)
        if not post:
            raise ValueError("Post not found")
        
        PostRepository.delete_post(post_id, db)
