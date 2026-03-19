import os
from urllib import request
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException

UPLOAD_DIR = Path("static/images/courses")
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def init_upload_directory():
    """Crea el directorio de uploads si no existe"""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def validate_image(file: UploadFile) -> None:
    """Valida que el archivo sea una imagen válida"""
    # Validar extensión
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de archivo no permitido. Extensiones permitidas: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Validar content type
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="El archivo debe ser una imagen"
        )

async def save_image(file: UploadFile, base_url: str = "http://localhost:8000") -> str:
    """
    Guarda una imagen y retorna la URL completa
    
    Args:
        file: Archivo de imagen a guardar
        base_url: URL base del servidor (ej: http://localhost:8000)
        
    Returns:
        str: URL completa de la imagen guardada (ej: http://localhost:8000/static/images/courses/uuid.jpg)
    """
    validate_image(file)
    # Generar nombre único
    file_ext = Path(file.filename).suffix.lower()
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = UPLOAD_DIR / unique_filename
    
    # Guardar archivo
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
        return f"{base_url}/static/images/courses/{unique_filename}"
    
    except Exception as e:
        # Limpiar archivo si hubo error
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Error al guardar la imagen: {str(e)}")

def delete_image(image_path: str) -> bool:
    """
    Elimina una imagen del sistema de archivos
    
    Args:
        image_path: URL completa o ruta relativa de la imagen 
                   (ej: http://localhost:8000/static/images/courses/uuid.jpg o /static/images/courses/uuid.jpg)
        
    Returns:
        bool: True si se eliminó correctamente
    """
    try:
        # Si es una URL completa, extraer solo la ruta
        if image_path.startswith("http://") or image_path.startswith("https://"):
            # Extraer la ruta después del dominio
            from urllib.parse import urlparse
            parsed = urlparse(image_path)
            image_path = parsed.path
        
        # Convertir ruta relativa a absoluta
        if image_path.startswith("/"):
            image_path = image_path[1:]
        
        file_path = Path(image_path)
        
        # Validar que esté en el directorio permitido (normalizar para comparación)
        normalized_path = file_path.as_posix()
        if not normalized_path.startswith("static/images/courses"):
            return False
        
        if file_path.exists():
            file_path.unlink()
            return True
        
        return False
    
    except Exception:
        return False
