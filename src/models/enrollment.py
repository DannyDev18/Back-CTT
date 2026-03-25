from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Enum as SQLEnum, DateTime, CheckConstraint, Index, text
from pydantic import model_validator


class EnrollmentStatus(str, Enum):
    INTERESADO = "Interesado"
    ORDEN_GENERADA = "Generada la orden"
    PAGADO = "Pagado"
    FACTURADO = "Facturado"
    ANULADO = "Anulado"


# === Modelo de Tabla ===
class Enrollment(SQLModel, table=True):
    __tablename__ = "enrollments"
    __table_args__ = (
        # Regla: exactamente uno de id_course o id_congress debe estar presente
        CheckConstraint(
            "(id_course IS NOT NULL AND id_congress IS NULL) OR "
            "(id_course IS NULL AND id_congress IS NOT NULL)",
            name="chk_enrollment_course_xor_congress"
        ),
        # Índices únicos filtrados (SQL Server permite múltiples NULLs en índices normales,
        # usar WHERE para excluir NULLs y forzar unicidad solo en valores no nulos)
        Index(
            "uq_enrollment_user_course",
            "id_user_platform", "id_course",
            unique=True,
            mssql_where=text("id_course IS NOT NULL")
        ),
        Index(
            "uq_enrollment_user_congress",
            "id_user_platform", "id_congress",
            unique=True,
            mssql_where=text("id_congress IS NOT NULL")
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    id_user_platform: int = Field(foreign_key="users_platform.id", nullable=False)
    # Exactamente uno de los dos debe ser no-nulo (enforced por chk_enrollment_course_xor_congress)
    id_course: Optional[int] = Field(default=None, foreign_key="course.id", nullable=True)
    id_congress: Optional[int] = Field(default=None, foreign_key="congresos.id_congreso", nullable=True)
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
    """Inscripción a curso O congreso — nunca ambos, nunca ninguno."""
    id_user_platform: int = Field(description="ID del usuario de la plataforma")
    id_course: Optional[int] = Field(
        default=None,
        description="ID del curso. Exclusivo con id_congress."
    )
    id_congress: Optional[int] = Field(
        default=None,
        description="ID del congreso. Exclusivo con id_course."
    )
    status: EnrollmentStatus = Field(
        default=EnrollmentStatus.INTERESADO,
        description="Estado inicial de la inscripción"
    )
    payment_order_url: Optional[str] = Field(
        default=None,
        max_length=500,
        description="URL de la orden de pago"
    )

    @model_validator(mode="after")
    def validate_course_xor_congress(self) -> "EnrollmentCreate":
        has_course = self.id_course is not None
        has_congress = self.id_congress is not None
        if has_course and has_congress:
            raise ValueError("No se puede especificar id_course e id_congress al mismo tiempo.")
        if not has_course and not has_congress:
            raise ValueError("Debe especificarse id_course o id_congress (no ninguno).")
        return self


# === Modelos de Request (Update) ===
class EnrollmentUpdate(SQLModel):
    """Actualización de estado y/o URL de pago — no cambia el recurso inscrito."""
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
    """Respuesta base de una inscripción."""
    id: int
    id_user_platform: int
    id_course: Optional[int]
    id_congress: Optional[int]
    enrollment_date: datetime
    status: EnrollmentStatus
    payment_order_url: Optional[str]


class EnrollmentWithDetails(EnrollmentResponse):
    """Respuesta enriquecida con datos del usuario y del recurso inscrito."""
    user_name: str
    user_email: str
    # Detalles de curso — None cuando la inscripción es a un congreso
    course_title: Optional[str]
    course_category_id: Optional[int]
    course_image: Optional[str]
    # Detalles de congreso — None cuando la inscripción es a un curso
    congress_title: Optional[str]
