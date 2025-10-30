from fastapi import APIRouter, HTTPException, Depends, status
from typing import Annotated
from src.controllers.post_controller import PostController
from src.dependencies.db_session import SessionDep
from src.models.post import PostUpdate, PostResponse
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

@posts_router.get("")
def get_banners_config(db: SessionDep):
    """
    Obtiene la configuración de banners.
    
    **Estructura de respuesta:**
    ```json
    {
      "banner": {
        "subtitulo": "Texto del subtítulo",
        "titulo": "Texto del título",
        "boton": {
          "texto": "Texto del botón",
          "direccion": "/ruta-del-boton"
        },
        "imagenes": [
          {
            "imagen": "url-de-la-imagen-1"
          }
        ]
      },
      "banner2": {
        "imagenes": [
          {
            "imagen": "url-de-la-imagen",
            "titulo": "Título del banner 2",
            "subtitulo": "Subtítulo del banner 2",
            "descripcion": "Descripción del banner 2",
            "boton": {
              "texto": "Texto del botón",
              "direccion": "/ruta-del-boton"
            }
          }
        ]
      },
      "banner3": {
        "imagenes": [
          {
            "imagen": "url-de-la-imagen",
            "titulo": "Título del banner 3",
            "subtitulo": "Subtítulo del banner 3",
            "descripcion": "Descripción del banner 3",
            "boton": {
              "texto": "Texto del botón",
              "direccion": "/ruta-del-boton"
            }
          }
        ]
      }
    }
    ```
    """
    try:
        result = PostController.get_config(db)
        return result
    except Exception as e:
        raise handle_controller_error(e, "fetching banners config")


@posts_router.put("", response_model=PostResponse)
def update_banners_config(
    current_user: Annotated[User, Depends(decode_token)],
    config_data: PostUpdate,
    db: SessionDep
):
    """
    Actualiza la configuración de banners.
    
    **Campos:**
    - `banner`: Configuración del banner 1 (opcional)
    - `banner2`: Configuración del banner 2 (opcional)
    - `banner3`: Configuración del banner 3 (opcional)
    
    **Nota:** Los campos no proporcionados permanecen sin cambios.
    """
    try:
        result = PostController.update_config(config_data, db)
        return PostResponse(
            message="Banners config updated successfully",
            data=result
        )
    except Exception as e:
        db.rollback()
        raise handle_controller_error(e, "updating banners config")
