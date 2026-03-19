from fastapi import APIRouter, File, Request, UploadFile, HTTPException, Depends
from src.utils.pdf_utils import save_pdf
from src.utils.pdf_utils import delete_pdf as delete_pdf_util
from src.utils.platform_jwt_utils import decode_platform_token
from typing import Annotated
from src.models.user_platform import UserPlatform
from pydantic import BaseModel
import os


pdf_router = APIRouter(prefix="/api/v1/pdf", tags=["pdf"])
CurrentUser = Annotated[UserPlatform, Depends(decode_platform_token)]

# Modelos de respuesta para documentación Swagger
class PDFUploadResponse(BaseModel):
    """Respuesta al subir un PDF exitosamente"""
    message: str
    pdf_url: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "PDF subido exitosamente",
                "pdf_url": "http://localhost:8000/static/pdf/categories/123e4567-e89b-12d3-a456-426614174000.pdf"
            }
        }
class PDFDeleteResponse(BaseModel):
    """Respuesta al eliminar un PDF exitosamente"""
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "PDF eliminado exitosamente"
            }
        }
pdf_router = APIRouter(prefix="/api/v1/pdf", tags=["pdf"])
@pdf_router.post(
    "/upload",
    response_model=PDFUploadResponse,
    status_code=200,
    responses={
        200: {
            "description": "PDF subido exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "message": "PDF subido exitosamente",
                        "pdf_url": "http://localhost:8000/static/pdf/categories/123e4567-e89b-12d3-a456-426614174000.pdf"
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
        409: {
            "description": "El PDF ya existe en el sistema",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Este PDF ya existe en el sistema. URL: http://localhost:8000/static/pdf/articles/123.pdf"
                    }
                }
            }
        },
        500: {
            "description": "Error del servidor al subir el PDF"
        }
    }
)
async def upload_pdf(
    request: Request,
    file: Annotated[UploadFile, File(...)] ,
    #current_user: Annotated[UserPlatform, Depends(decode_platform_token)]
):
    """
    Endpoint para subir un archivo PDF
    
    Args:
        request: Objeto de solicitud HTTP
        file: Archivo PDF a subir
        current_user: Usuario autenticado
        
    Returns:
        URL completa del PDF subido
    """
    base_url = os.getenv("BACKEND_URL", f"{request.url.scheme}://{request.url.netloc}")
    pdf_url = await save_pdf(file, base_url)
    return PDFUploadResponse(
        message="PDF subido exitosamente",
        pdf_url=pdf_url
    )
@pdf_router.delete(
    "/delete",
    response_model=PDFDeleteResponse,
    status_code=200,
    responses={
        200: {
            "description": "PDF eliminado exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "message": "PDF eliminado exitosamente"
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
            "description": "Error del servidor al eliminar el PDF"
        }
    }
)
async def delete_pdf(   
    request: Request,
    file_url: str,
    current_user: Annotated[UserPlatform, Depends(decode_platform_token)]
):
    """
    Endpoint para eliminar un archivo PDF dado su URL completa
    
    Args:
        request: Objeto de solicitud HTTP
        file_url: URL completa del PDF a eliminar
        current_user: Usuario autenticado
        
    Returns:
        Mensaje de confirmación de eliminación
    """
   
    deleted = await delete_pdf_util(file_url)
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="El archivo PDF no existe"
        )
    return PDFDeleteResponse(
        message="PDF eliminado exitosamente"
    )
