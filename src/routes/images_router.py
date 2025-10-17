from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from typing import Annotated
from src.utils.image_utils import save_image, delete_image
from src.utils.jwt_utils import decode_token
from src.models.user import User
import os

images_router = APIRouter(prefix="/api/v1/images", tags=["images"])

@images_router.post("/upload")
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

@images_router.delete("/delete")
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
