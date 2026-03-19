from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Enum as SQLEnum, DateTime


class CongressCategoryStatus(str, Enum):
    ACTIVO = "activo"
    INACTIVO = "inactivo"


class CongressCategory(SQLModel, table=True):
    __tablename__ = "congress_categories"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True, nullable=False, max_length=150)
    description: Optional[str] = Field(default=None, max_length=500)
    svgurl: Optional[str] = Field(default=None, max_length=500)
    status: CongressCategoryStatus = Field(
        sa_column=Column(SQLEnum(CongressCategoryStatus), nullable=False),
        default=CongressCategoryStatus.ACTIVO
    )
    created_at: datetime = Field(default_factory=datetime.now, nullable=False)
    updated_at: Optional[datetime] = Field(default=None)
    created_by: int = Field(
        default=None,
        foreign_key="user.id"
    )

    # Relaciones
    congresss: List["Congress"] = Relationship(back_populates="congress_category_rel")
    creator: Optional["User"] = Relationship(
        back_populates="congress_categories",
        sa_relationship_kwargs={"foreign_keys": lambda: [CongressCategory.created_by]}
    )

    # === Modelos de Request (Create) ===
    class CongressCategoryCreate(SQLModel):
        """Modelo para crear una categoría de congreso"""
        name: str = Field(
            min_length=1,
            max_length=150,
            description="Nombre de la categoría de congreso"
        )
        description: Optional[str] = Field(
            default=None,
            max_length=500,
            description="Descripción de la categoría de congreso"
        )
        svgurl: Optional[str] = Field(
            default=None,
            max_length=500,
            description="URL del SVG de la categoría de congreso"
        )
        status: CongressCategoryStatus = Field(
            default=CongressCategoryStatus.ACTIVO,
            description="Estado inicial de la categoría de congreso"
        )

    # === Modelos de Request (Update) ===
    class CongressCategoryUpdate(SQLModel):
        """Modelo para actualizar una categoría de congreso"""
        name: Optional[str] = Field(
            default=None,
            min_length=1,
            max_length=150,
            description="Nombre de la categoría de congreso"
        )
        description: Optional[str] = Field(
            default=None,
            max_length=500,
            description="Descripción de la categoría de congreso"
        )
        svgurl: Optional[str] = Field(
            default=None,
            max_length=500,
            description="URL del SVG de la categoría de congreso"
        )
        status: Optional[CongressCategoryStatus] = Field(
            default=None,
            description="Nuevo estado de la categoría de congreso"
        )

    # === Modelos de Response ===
    class CongressCategoryResponse(SQLModel):
        """Modelo de respuesta para una categoría de congreso"""
        id: int
        name: str
        description: Optional[str]
        svgurl: Optional[str]
        status: CongressCategoryStatus
        created_at: datetime
        updated_at: Optional[datetime]
        created_by: int

    class CongressCategoryWithCreator(CongressCategoryResponse):
        """Modelo de respuesta con el creador de la categoría de congreso"""
        creator_name: Optional[str]
        creator_email: Optional[str]
        congresss_count: int

    class CongressCategoryWithCongresss(CongressCategoryResponse):
        """Modelo de respuesta con los congresos asociados a la categoría"""
        congresss: List["Congress"]


# al final de congress_category.py
CongressCategory.update_forward_refs()
from src.models.congress import Congress
from src.models.user import User
