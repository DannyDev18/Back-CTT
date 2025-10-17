from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from typing import Annotated
from pydantic import BaseModel
from src.utils.image_utils import save_image, delete_image
from src.utils.jwt_utils import decode_token
from src.models.user import User
import os

# Modelos de respuesta para documentación Swagger
class ImageUploadResponse(BaseModel):
    """Respuesta al subir una imagen exitosamente"""
    message: str
    image_url: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Imagen subida exitosamente",
                "image_url": "http://localhost:8000/static/images/courses/123e4567-e89b-12d3-a456-426614174000.jpg"
            }
        }

class ImageDeleteResponse(BaseModel):
    """Respuesta al eliminar una imagen exitosamente"""
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Imagen eliminada exitosamente"
            }
        }

images_router = APIRouter(prefix="/api/v1/images", tags=["images"])

@images_router.post(
    "/upload",
    response_model=ImageUploadResponse,
    status_code=200,
    responses={
        200: {
            "description": "Imagen subida exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Imagen subida exitosamente",
                        "image_url": "http://localhost:8000/static/images/courses/123e4567-e89b-12d3-a456-426614174000.jpg"
                    }
                }
            }
        },
        400: {
            "description": "Archivo inválido o tipo no permitido"
        },
        401: {
            "description": "No autenticado"
        },
        500: {
            "description": "Error del servidor al subir la imagen"
        }
    }
)
async def upload_image(
    request: Request,
    current_user: Annotated[User, Depends(decode_token)],
    file: UploadFile = File(...)
):
    """
    Sube una imagen y retorna la URL completa para usarla en cursos
    
    - **file**: Archivo de imagen (JPG, PNG, GIF, WEBP)
    - **Tamaño máximo**: 5MB
    - **Requiere**: Autenticación JWT
    """
    try:
        # Obtener URL base del servidor desde variables de entorno o request
        base_url = os.getenv("BACKEND_URL", f"{request.url.scheme}://{request.url.netloc}")
        
        image_url = await save_image(file, base_url=base_url)
        return {
            "message": "Imagen subida exitosamente",
            "image_url": image_url
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al subir imagen: {str(e)}")

@images_router.delete(
    "/delete",
    response_model=ImageDeleteResponse,
    status_code=200,
    responses={
        200: {
            "description": "Imagen eliminada exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Imagen eliminada exitosamente"
                    }
                }
            }
        },
        401: {
            "description": "No autenticado"
        },
        404: {
            "description": "Imagen no encontrada o no se pudo eliminar"
        }
    }
)
async def delete_image_endpoint(
    current_user: Annotated[User, Depends(decode_token)],
    image_url: str
):
    """
    Elimina una imagen del servidor
    
    - **image_url**: URL de la imagen a eliminar
    - **Requiere**: Autenticación JWT
    """
    success = delete_image(image_url)
    
    if success:
        return {"message": "Imagen eliminada exitosamente"}
    else:
        raise HTTPException(status_code=404, detail="Imagen no encontrada o no se pudo eliminar")
