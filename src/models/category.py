from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import date, datetime
from enum import Enum
from sqlalchemy import Column, Enum as SQLEnum, DateTime


class CategoryStatus(str, Enum):
    ACTIVO = "activo"
    INACTIVO = "inactivo"
class Category(SQLModel, table=True):
        __tablename__ = "categories"
        id: Optional[int] = Field(default=None, primary_key=True)
        name: str = Field(index=True, unique=True, nullable=False, max_length=150)
        description: Optional[str] = Field(default=None, max_length=500)
        svgurl: Optional[str] = Field(default=None, max_length=500)
        status: CategoryStatus = Field(
              sa_column=Column(SQLEnum(CategoryStatus), nullable=False),
              default=CategoryStatus.ACTIVO
        )
        created_at: datetime = Field(default_factory=datetime.now, nullable=False)
        updated_at: Optional[datetime] = Field(default=None)
        created_by: int = Field(
              default=None, 
              foreign_key="user.id")
        
        # Relaciones
        courses: List["Course"] = Relationship(back_populates="category_rel")
        congresss: List["Congress"] = Relationship(back_populates="category_rel")
        creator: Optional["User"] = Relationship(
            back_populates="categories",
            sa_relationship_kwargs={"foreign_keys": lambda: [Category.created_by]}
            )
        
        # === Modelos de Request (Create) ===
        class CategoryCreate(SQLModel):
            """Modelo para crear una categoria"""
            name: str = Field(
                min_length=1,
                max_length=150,
                description="Nombre de la categoría"
            )
            description: Optional[str] = Field(
            default=None,
            max_length=500,
            description="Descripción de la categoría"
            )
            svgurl: Optional[str] = Field(
            default=None,
            max_length=500,
            description="URL del SVG de la categoría"
            )
            status: CategoryStatus = Field(
            default=CategoryStatus.ACTIVO,
            description="Estado inicial de la categoría"
            )
        # === Modelos de Request (Update) ===
        class CategoryUpdate(SQLModel):
            """Modelo para actualizar una categoria"""
            name: Optional[str] = Field(
            default= None,
            min_length=1,
            max_length=150,
            description="Nombre de la categoría"
            )
            description: Optional[str] = Field(
            default=None,
            max_length=500,
            description="Descripción de la categoría"
            )
            svgurl: Optional[str] = Field(
            default=None,
            max_length=500,
            description="URL del SVG de la categoría"
            )

            status: Optional[CategoryStatus] = Field(
            default=None,
            description="Nuevo estado de la categoría"
            )
        # === Modelos de Response ===
        class CategoryResponse(SQLModel):
            """Modelo de respuesta para una categoría"""
            id: int
            name: str
            description: Optional[str]
            svgurl: Optional[str]
            status: CategoryStatus
            created_at: datetime
            updated_at: Optional[datetime]
            created_by: int
        class CategoryWithCreator(CategoryResponse):
            """Modelo de respuesta con el creador de la categoría"""
            creator_name: Optional[str]
            creator_email: Optional[str]
            courses_count: int
        class CategoryWithCourses(CategoryResponse):
            """Modelo de respuesta con los cursos asociados a la categoría"""
            courses: List["Course"]
        # al final de category.py
Category.update_forward_refs()
from src.models.course import Course
from src.models.congress import Congress
from src.models.user import User

        

