from sqlmodel import SQLModel, Field
from typing import Optional
from enum import Enum
from pydantic import field_validator


class PostPlace(str, Enum):
    """Ubicación del post en la aplicación"""
    HEADER = "Header"
    FOOTER = "Footer"
    MAIN = "Main"


class Post(SQLModel, table=True):
    """Modelo de tabla para Posts"""
    __tablename__ = "posts"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    sub_text: Optional[str] = Field(default=None, max_length=255)
    main_text: Optional[str] = Field(default=None, max_length=500)
    redirection_url: Optional[str] = Field(default=None, max_length=500)
    image_url: Optional[str] = Field(default=None, max_length=500)
    place: PostPlace = Field(description="Ubicación del post: Header, Footer, Main")


class PostCreate(SQLModel):
    """Modelo para crear un post"""
    sub_text: Optional[str] = Field(default=None, max_length=255)
    main_text: Optional[str] = Field(default=None, max_length=500)
    redirection_url: Optional[str] = Field(default=None, max_length=500)
    image_url: Optional[str] = Field(default=None, max_length=500)
    place: PostPlace
    
    @field_validator('redirection_url', 'image_url')
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('URL debe comenzar con http:// o https://')
        return v


class PostUpdate(SQLModel):
    """Modelo para actualizar un post (todos los campos opcionales)"""
    sub_text: Optional[str] = Field(default=None, max_length=255)
    main_text: Optional[str] = Field(default=None, max_length=500)
    redirection_url: Optional[str] = Field(default=None, max_length=500)
    image_url: Optional[str] = Field(default=None, max_length=500)
    place: Optional[PostPlace] = None
    
    @field_validator('redirection_url', 'image_url')
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('URL debe comenzar con http:// o https://')
        return v


class PostResponse(SQLModel):
    """Modelo de respuesta para operaciones de post"""
    message: str
    post_id: Optional[int] = None
    data: Optional[dict] = None
