from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from typing import Annotated
from pydantic import BaseModel
from src.utils.svg_utils import save_svg
from src.utils.jwt_utils import decode_token
from src.models.user import User

class SVGUploadResponse(BaseModel):
    message: str
    svg_url: str

class SVGDeleteResponse(BaseModel):
    message: str

svg_router = APIRouter(prefix="/api/v1/svg", tags=["svg"])


@svg_router.post("/upload", response_model=SVGUploadResponse, status_code=200)
async def upload_svg(
    request: Request,
    file: Annotated[UploadFile, File(...)],
    current_user: Annotated[User, Depends(decode_token)],
):
    # IMPORTANTE: pasar request completo, no base_url string
    svg_url = await save_svg(file, request)
    return SVGUploadResponse(
        message="SVG subido exitosamente",
        svg_url=svg_url,
    )


@svg_router.delete("/delete", response_model=SVGDeleteResponse, status_code=200)
async def delete_svg(
    request: Request,
    file_url: str,
    current_user: Annotated[User, Depends(decode_token)],
):
    from src.utils.svg_utils import delete_svg as delete_svg_util

    deleted = delete_svg_util(file_url)
    if not deleted:
        raise HTTPException(status_code=404, detail="El archivo SVG no existe")
    return SVGDeleteResponse(message="SVG eliminado exitosamente")