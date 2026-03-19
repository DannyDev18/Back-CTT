from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from typing import Annotated
from pydantic import BaseModel
from src.utils.svg_utils import save_svg
from src.utils.jwt_utils import decode_token
from src.models.user import User
import os

# Modelos de respuesta para documentación Swagger
class SVGUploadResponse(BaseModel):
    """Respuesta al subir un SVG exitosamente"""
    message: str
    svg_url: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "SVG subido exitosamente",
                "svg_url": "http://localhost:8000/static/svg/categories/123e4567-e89b-12d3-a456-426614174000.svg"
            }
        }
class SVGDeleteResponse(BaseModel):
    """Respuesta al eliminar un SVG exitosamente"""
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "SVG eliminado exitosamente"
            }
        }
svg_router = APIRouter(prefix="/api/v1/svg", tags=["svg"])

@svg_router.post(
    "/upload",
    response_model=SVGUploadResponse,
    status_code=200,
    responses={
        200: {
            "description": "SVG subido exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "message": "SVG subido exitosamente",
                        "svg_url": "http://localhost:8000/static/svg/categories/123e4567-e89b-12d3-a456-426614174000.svg"
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
            "description": "Error del servidor al subir el SVG"
        }
    }
)
async def upload_svg(
    request: Request,
    file: Annotated[UploadFile, File(...)] ,
    current_user: Annotated[User, Depends(decode_token)]
):
    """
    Endpoint para subir un archivo SVG
    
    Args:
        request: Objeto de solicitud HTTP
        file: Archivo SVG a subir
        current_user: Usuario autenticado
        
    Returns:
        URL completa del SVG subido
    """
    base_url = os.getenv("BACKEND_URL", f"{request.url.scheme}://{request.url.netloc}")
    svg_url = await save_svg(file, base_url)
    return SVGUploadResponse(
        message="SVG subido exitosamente",
        svg_url=svg_url
    )
@svg_router.delete(
    "/delete",
    response_model=SVGDeleteResponse,
    status_code=200,
    responses={
        200: {
            "description": "SVG eliminado exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "message": "SVG eliminado exitosamente"
                    }
                }
            }
        },
        400: {
            "description": "Ruta de archivo inválida o tipo no permitido"
        },
        401: {
            "description": "No autenticado"
        },
        500: {
            "description": "Error del servidor al eliminar el SVG"
        }
    }
)
async def delete_svg(   
    request: Request,
    file_url: str,
    current_user: Annotated[User, Depends(decode_token)]
):
    """
    Endpoint para eliminar un archivo SVG dado su URL completa
    
    Args:
        request: Objeto de solicitud HTTP
        file_url: URL completa del SVG a eliminar
        current_user: Usuario autenticado
        
    Returns:
        Mensaje de confirmación de eliminación
    """
    from src.utils.svg_utils import delete_svg as delete_svg_util
    deleted = delete_svg_util(file_url)
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="El archivo SVG no existe"
        )
    return SVGDeleteResponse(
        message="SVG eliminado exitosamente"
    )
