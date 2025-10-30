from sqlmodel import SQLModel, Field, Column, JSON
from typing import Optional, List
from pydantic import BaseModel


class Boton(BaseModel):
    """Modelo para botón"""
    texto: str
    direccion: str


class ImagenBanner1(BaseModel):
    """Modelo para imagen del banner 1"""
    imagen: str


class Banner1(BaseModel):
    """Modelo para banner 1"""
    subtitulo: Optional[str] = None
    titulo: Optional[str] = None
    boton: Optional[Boton] = None
    imagenes: Optional[List[ImagenBanner1]] = None


class ImagenBanner2(BaseModel):
    """Modelo para imagen del banner 2"""
    imagen: str
    titulo: Optional[str] = None
    subtitulo: Optional[str] = None
    descripcion: Optional[str] = None
    boton: Optional[Boton] = None


class Banner2(BaseModel):
    """Modelo para banner 2"""
    imagenes: Optional[List[ImagenBanner2]] = None


class ImagenBanner3(BaseModel):
    """Modelo para imagen del banner 3"""
    imagen: str
    titulo: Optional[str] = None
    subtitulo: Optional[str] = None
    descripcion: Optional[str] = None
    boton: Optional[Boton] = None


class Banner3(BaseModel):
    """Modelo para banner 3"""
    imagenes: Optional[List[ImagenBanner3]] = None


class BannersConfig(BaseModel):
    """Modelo para la configuración completa de banners"""
    banner: Optional[Banner1] = None
    banner2: Optional[Banner2] = None
    banner3: Optional[Banner3] = None


class Post(SQLModel, table=True):
    """Modelo de tabla para configuración de banners"""
    __tablename__ = "posts"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    config: dict = Field(default={}, sa_column=Column(JSON))


class PostUpdate(BaseModel):
    """Modelo para actualizar la configuración de banners"""
    banner: Optional[Banner1] = None
    banner2: Optional[Banner2] = None
    banner3: Optional[Banner3] = None


class PostResponse(SQLModel):
    """Modelo de respuesta para operaciones de post"""
    message: str
    data: Optional[dict] = None
