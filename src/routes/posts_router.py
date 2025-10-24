from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import Annotated, Optional
from src.controllers.post_controller import PostController
from src.dependencies.db_session import SessionDep
from src.models.post import PostCreate, PostUpdate, PostResponse
from src.utils.jwt_utils import decode_token
from src.models.user import User

posts_router = APIRouter(prefix="/api/v1/posts", tags=["posts"])


# ============= Manejadores de Errores ============= 

def handle_controller_error(e: Exception, operation: str) -> HTTPException:
    """Maneja errores del controlador de forma consistente"""
    if isinstance(e, ValueError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Error {operation}: {str(e)}"
    )


# ============= Endpoints ============= 

@posts_router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(
    current_user: Annotated[User, Depends(decode_token)],
    post_data: PostCreate,
    db: SessionDep
):
    """
    Crea un nuevo post.
    
    **Campos:**
    - `sub_text`: Texto secundario (opcional)
    - `main_text`: Texto principal (opcional)
    - `redirection_url`: URL de redirección (opcional)
    - `image_url`: URL de la imagen (opcional)
    - `place`: Ubicación del post (Header, Footer, Main)
    """
    try:
        result = PostController.create_post(post_data, db)
        return PostResponse(
            message="Post created successfully",
            post_id=result["id"],
            data=result
        )
    except Exception as e:
        db.rollback()
        raise handle_controller_error(e, "creating post")


@posts_router.get("")
def get_all_posts(
    db: SessionDep,
    page: Optional[int] = Query(None, ge=1, description="Número de página (opcional)"),
    page_size: Optional[int] = Query(None, ge=1, le=100, description="Tamaño de página (opcional)"),
    place: Optional[str] = Query(None, description="Filtrar por ubicación: Header, Footer, Main")
):
    """
    Obtiene todos los posts con paginación opcional.
    
    **Parámetros:**
    - `page`: número de página (opcional, si se omite retorna todos)
    - `page_size`: cantidad de posts por página (opcional)
    - `place`: filtrar por ubicación (Header, Footer, Main)
    
    **Nota:** Si se especifica `page` y `page_size`, retorna respuesta paginada.
    Si se omiten, retorna todos los posts como lista.
    """
    try:
        result = PostController.get_all_posts(db, page, page_size, place)
        return result
    except Exception as e:
        raise handle_controller_error(e, "fetching posts")


@posts_router.get("/{post_id}")
def get_post_by_id(
    post_id: int,
    db: SessionDep
):
    """
    Obtiene un post específico por ID.
    
    **Parámetros:**
    - `post_id`: ID del post
    """
    try:
        result = PostController.get_post_by_id(post_id, db)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Post with id {post_id} not found"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise handle_controller_error(e, "fetching post")


@posts_router.get("/place/{place}")
def get_posts_by_place(
    place: str,
    db: SessionDep
):
    """
    Obtiene posts filtrados por ubicación.
    
    **Parámetros:**
    - `place`: Ubicación (Header, Footer, Main)
    """
    try:
        result = PostController.get_posts_by_place(place, db)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise handle_controller_error(e, "fetching posts by place")


@posts_router.patch("/{post_id}", response_model=PostResponse)
def update_post(
    current_user: Annotated[User, Depends(decode_token)],
    post_id: int,
    post_data: PostUpdate,
    db: SessionDep
):
    """
    Actualiza un post existente de forma parcial.
    
    **Parámetros:**
    - `post_id`: ID del post a actualizar
    - `post_data`: Datos a actualizar (todos opcionales)
    
    **Nota:** Los campos no proporcionados permanecen sin cambios
    """
    try:
        result = PostController.update_post(post_id, post_data, db)
        return PostResponse(
            message="Post updated successfully",
            post_id=post_id,
            data=result
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        raise handle_controller_error(e, "updating post")


@posts_router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    current_user: Annotated[User, Depends(decode_token)],
    post_id: int,
    db: SessionDep
):
    """
    Elimina un post.
    
    **Parámetros:**
    - `post_id`: ID del post a eliminar
    """
    try:
        PostController.delete_post(post_id, db)
        return None
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        raise handle_controller_error(e, "deleting post")
