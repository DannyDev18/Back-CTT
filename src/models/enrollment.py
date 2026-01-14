from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Enum as SQLEnum, DateTime

class EnrollmentStatus(str, Enum):
    INTERESADO = "Interesado"
    ORDEN_GENERADA = "Generada la orden"
    PAGADO = "Pagado"
    FACTURADO = "Facturado"
    ANULADO = "Anulado"

# === Modelo de Tabla ===
class Enrollment(SQLModel, table=True):
    __tablename__ = "enrollments"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    id_user_platform: int = Field(foreign_key="users_platform.id", nullable=False)
    id_course: int = Field(foreign_key="course.id", nullable=False)
    enrollment_date: datetime = Field(
        sa_column=Column(DateTime, nullable=False, default=datetime.utcnow)
    )
    status: EnrollmentStatus = Field(
        sa_column=Column(SQLEnum(EnrollmentStatus), nullable=False),
        default=EnrollmentStatus.INTERESADO
    )
    payment_order_url: Optional[str] = Field(default=None, max_length=500)

# === Modelos de Request (Create) ===
class EnrollmentCreate(SQLModel):
    """Modelo para crear una inscripción"""
    id_user_platform: int = Field(description="ID del usuario de la plataforma")
    id_course: int = Field(description="ID del curso")
    status: EnrollmentStatus = Field(
        default=EnrollmentStatus.INTERESADO,
        description="Estado inicial de la inscripción"
    )
    payment_order_url: Optional[str] = Field(
        default=None,
        max_length=500,
        description="URL de la orden de pago"
    )

# === Modelos de Request (Update) ===
class EnrollmentUpdate(SQLModel):
    """Modelo para actualizar una inscripción"""
    status: Optional[EnrollmentStatus] = Field(
        default=None,
        description="Nuevo estado de la inscripción"
    )
    payment_order_url: Optional[str] = Field(
        default=None,
        max_length=500,
        description="URL de la orden de pago"
    )

# === Modelos de Response ===
class EnrollmentResponse(SQLModel):
    """Modelo de respuesta para una inscripción"""
    id: int
    id_user_platform: int
    id_course: int
    enrollment_date: datetime
    status: EnrollmentStatus
    payment_order_url: Optional[str]

class EnrollmentWithDetails(EnrollmentResponse):
    """Modelo de respuesta con detalles del usuario y curso"""
    user_name: str
    user_email: str
    course_title: str
    course_category_id: str
    course_image: Optional[str]