from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional
import bcrypt
from pydantic import BaseModel, EmailStr, field_validator
from .base import Base


# === Modelo SQLAlchemy ===
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    # Email con restricciones de SQL Server
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relaciones (usando forward references)
    categories: Mapped[List["Category"]] = relationship("Category", back_populates="creator")
    congress_categories: Mapped[List["CongressCategory"]] = relationship("CongressCategory", back_populates="creator")

    def verify_password(self, plain_password: str) -> bool:
        """Verificar contraseña con bcrypt"""
        # Truncate to 72 bytes as required by bcrypt
        password_bytes = plain_password[:72].encode('utf-8')
        hashed_bytes = self.password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash de contraseña con bcrypt"""
        # Truncate to 72 bytes as required by bcrypt
        password_bytes = password[:72].encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')


# === Modelos Pydantic ===
class UserRead(BaseModel):
    """Modelo de lectura para User"""
    id: int
    name: str
    last_name: str
    email: EmailStr

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    """Modelo de creación para User"""
    name: str
    last_name: str
    email: EmailStr
    password: str

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('El nombre debe tener al menos 2 caracteres')
        return v.strip().title()

    @field_validator('last_name')
    @classmethod
    def validate_last_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('El apellido debe tener al menos 2 caracteres')
        return v.strip().title()

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        return v

    class Config:
        str_strip_whitespace = True


class UserUpdate(BaseModel):
    """Modelo de actualización para User"""
    name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if v is not None and len(v.strip()) < 2:
            raise ValueError('El nombre debe tener al menos 2 caracteres')
        return v.strip().title() if v else v

    @field_validator('last_name')
    @classmethod
    def validate_last_name(cls, v):
        if v is not None and len(v.strip()) < 2:
            raise ValueError('El apellido debe tener al menos 2 caracteres')
        return v.strip().title() if v else v

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if v is not None and len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        return v

    class Config:
        str_strip_whitespace = True


class UserWithStats(BaseModel):
    """Modelo de usuario con estadísticas"""
    id: int
    name: str
    last_name: str
    email: EmailStr
    categories_count: int
    congress_categories_count: int

    class Config:
        from_attributes = True
