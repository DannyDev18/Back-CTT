import os
import uuid
from pathlib import Path
from fastapi import Request, UploadFile, HTTPException
# Definiciones específicas para SVG
Upload_Dir = Path("static/svg/categories")
Allowed_Extensions = {".svg"}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB

# Inicializar directorio de uploads
def init_svg_directory():
    """Crea el directorio de uploads si no existe"""
    Upload_Dir.mkdir(parents=True, exist_ok=True)

def validate_svg(file: UploadFile) -> None:
    """Valida que el archivo sea un svg valido"""
    # Validar extensión
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in Allowed_Extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de archivo no permitido. Extensiones permitidas: {', '.join(Allowed_Extensions)}"
        )
    
    # Validar content type
    if file.content_type != "image/svg+xml":
        raise HTTPException(
            status_code=400,
            detail="El archivo debe ser un SVG"
        )
async def save_svg(
        file: UploadFile,
        request: Request
        )-> str:
    """ Guarda un SVG y retorna la URL completa"""
    validate_svg(file)
    # generar nombre unico
    base_url = os.getenv("BACKEND_URL") or str(request.base_url).rstrip("/")
    file_ext = Path(file.filename).suffix.lower()
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = Upload_Dir / unique_filename
    # guardar archivo
    try:
        contents = await file.read()
        
        # Validar tamaño
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"El archivo es muy grande. Tamaño máximo: {MAX_FILE_SIZE / (1024*1024)}MB"
            )
        
        with open(file_path, "wb") as f:
            f.write(contents)
          # Retornar URL completa
        return f"{base_url}/static/svg/categories/{unique_filename}"
    except Exception as e:
        # Limpiar archivo si hubo error
        if file_path.exists():
            os.remove(file_path)
        raise HTTPException(
            status_code=500,
            detail="Error al guardar el archivo SVG"
        ) from e
  
def delete_svg(file_url: str) -> bool:
    """Elimina un SVG dado su URL completa"""
    try:
        filename = Path(file_url).name
        file_path = (Upload_Dir/filename).resolve()
        # Asegurarse de que el archivo esté dentro del directorio permitido
        if not str(file_path).startswith(str(Upload_Dir.resolve())):
            raise HTTPException(
                status_code=400,
                detail="Ruta de archivo inválida"
            )
        if file_path.suffix.lower() not in Allowed_Extensions:
            raise HTTPException(
                status_code=400,
                detail="Tipo de archivo no permitido para eliminación"
            )
        if not file_path.exists():
            return False
        if file_path.exists():
            file_path.unlink()
            return True
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Error al eliminar el archivo SVG"
        )
    