import os
import uuid
from pathlib import Path
from fastapi import Request, UploadFile, HTTPException

UPLOAD_DIR = Path("static/svg/categories")
ALLOWED_EXTENSIONS = {".svg"}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB


def init_svg_directory():
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def validate_svg(file: UploadFile) -> None:
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="Archivo requerido")

    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de archivo no permitido. Extensiones permitidas: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    content_type = (file.content_type or "").lower()
    # Algunos clientes pueden enviar vacío u octet-stream; extensión ya está validada.
    if content_type and "image/svg+xml" not in content_type and content_type != "application/octet-stream":
        raise HTTPException(status_code=400, detail="El archivo debe ser un SVG")


async def save_svg(file: UploadFile, request: Request) -> str:
    validate_svg(file)
    init_svg_directory()

    file_ext = Path(file.filename).suffix.lower()
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = UPLOAD_DIR / unique_filename

    base_url = os.getenv("BACKEND_URL") or f"{request.url.scheme}://{request.url.netloc}"

    try:
        contents = await file.read()

        if not contents:
            raise HTTPException(status_code=400, detail="El archivo está vacío")

        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"El archivo es muy grande. Tamaño máximo: {MAX_FILE_SIZE / (1024 * 1024)}MB",
            )

        with open(file_path, "wb") as f:
            f.write(contents)

        return f"{base_url}/static/svg/categories/{unique_filename}"

    except HTTPException:
        raise
    except Exception as e:
        if file_path.exists():
            os.remove(file_path)
        raise HTTPException(status_code=500, detail="Error al guardar el archivo SVG") from e


def delete_svg(file_url: str) -> bool:
    try:
        filename = Path(file_url).name
        file_path = (UPLOAD_DIR / filename).resolve()

        if not str(file_path).startswith(str(UPLOAD_DIR.resolve())):
            raise HTTPException(status_code=400, detail="Ruta de archivo inválida")

        if file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Tipo de archivo no permitido para eliminación")

        if not file_path.exists():
            return False

        file_path.unlink()
        return True

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Error al eliminar el archivo SVG")