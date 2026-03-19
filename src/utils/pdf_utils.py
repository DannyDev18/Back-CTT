import os
from pathlib import Path
from fastapi import Request, UploadFile, HTTPException
import uuid
import hashlib
import json

# Definiciones específicas para PDF
UploadFile_Dir = Path("static/pdf/articles")
AllowedExtensions = {".pdf"}
MAXFileSize = 10 * 1024 * 1024  # 5MB
HASH_REGISTER_FILE = Path("static/pdf/pdf_hashes.json")

# Inicializar directorio de uploads
def init_pdf_directory():
    """Crea el directorio de uploads si no existe"""
    UploadFile_Dir.mkdir(parents=True, exist_ok=True)
    HASH_REGISTER_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not HASH_REGISTER_FILE.exists():
        with open(HASH_REGISTER_FILE, "w") as f:
            json.dump({}, f)
def calculate_file_hash(contents: bytes) -> str:
    """Calcula el hash SHA256 de un archivo dado su contenido"""
    sha256 = hashlib.sha256()
    sha256.update(contents)
    return sha256.hexdigest()
def load_hash_register() -> dict:
    """Carga el registro de hashes desde el archivo JSON"""
    try:
        with open(HASH_REGISTER_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
def save_hash_register(hash_register: dict) -> None:
    """Guarda el registro de hashes en el archivo JSON"""
    with open(HASH_REGISTER_FILE, "w") as f:
        json.dump(hash_register, f, indent=4)
def check_duplicate_file(contents: bytes) -> tuple[bool, str]:
    """Verifica si un archivo con el mismo hash ya existe"""
    file_hash = calculate_file_hash(contents)
    registry = load_hash_register()

    if file_hash in registry:
        return True, registry[file_hash]
    return False, None
def register_file_hash(file_hash: str, file_url: str) -> None:
    """Registra el hash de un pdf junto con su URL"""
    registry = load_hash_register()
    registry[file_hash] = file_url
    save_hash_register(registry)
def unregister_file_hash(file_url: str) -> None:
    """Elimina el registro del hash de un pdf"""
    registry = load_hash_register()
    hash_to_remove = None
    for hash_key, url in registry.items():
        if url == file_url:
            hash_to_remove = hash_key
            break
    if hash_to_remove:
        del registry[hash_to_remove]
        save_hash_register(registry)
def validate_pdf(file: UploadFile) -> None:
    """Valida que el archivo sea un PDF valido"""
    # Validar extensión
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in AllowedExtensions:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de archivo no permitido. Extensiones permitidas: {', '.join(AllowedExtensions)}"
        )
    
    # Validar content type
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="El archivo debe ser un PDF"
        )

    # Validar tamaño del archivo
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)
    if file_size > MAXFileSize:
        raise HTTPException(
            status_code=400,
            detail=f"El archivo es demasiado grande. El tamaño máximo permitido es {MAXFileSize / (1024 * 1024)} MB."
        )
async def save_pdf(file: UploadFile, base_url: str) -> str:
    """Guarda un PDF y retorna la URL completa"""
    validate_pdf(file)
    
    # Leer contenido del archivo una sola vez
    contents = await file.read()
    
    # Verificar si el PDF ya existe (por contenido)
    is_duplicate, existing_url = check_duplicate_file(contents)
    if is_duplicate:
        raise HTTPException(
            status_code=409,
            detail=f"Este PDF ya existe en el sistema. URL: {existing_url}"
        )
    
    # Generar nombre único
    file_ext = Path(file.filename).suffix.lower()
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = UploadFile_Dir / unique_filename
    
    # Guardar archivo
    try:
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Retornar URL completa
        pdf_url = f"{base_url}/static/pdf/articles/{unique_filename}"
        
        # Registrar hash del archivo
        file_hash = calculate_file_hash(contents)
        register_file_hash(file_hash, pdf_url)
        
        return pdf_url
    except Exception as e:
        # Limpiar archivo si hubo error
        if file_path.exists():
            os.remove(file_path)
        raise HTTPException(
            status_code=500,
            detail=f"Error al guardar el archivo PDF: {str(e)}"
        ) from e
async def delete_pdf(file_url: str) -> bool:
    """Elimina un PDF dado su URL completa"""
    try:
        filename = file_url.split("/")[-1]
        file_path = UploadFile_Dir / filename
        
        if file_path.suffix.lower() not in AllowedExtensions:
            raise HTTPException(
                status_code=400,
                detail="Tipo de archivo no permitido para eliminación"
            )
        
        if not file_path.exists():
            return False
        
        # Eliminar archivo físico
        file_path.unlink()
        
        # Eliminar registro de hash
        unregister_file_hash(file_url)
        
        return True
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al eliminar el archivo PDF: {str(e)}"
        ) from e

