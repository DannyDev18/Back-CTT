from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime
from sqlalchemy import UniqueConstraint, Column, DateTime
from pydantic import BaseModel
import src.models.enrollment  # Ensures enrollments table is registered in SQLModel.metadata


class SessionAttendance(SQLModel, table=True):
    __tablename__ = "session_attendance"
    __table_args__ = (
        UniqueConstraint("id_enrollment", "id_sesion", name="uq_enrollment_session"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    id_enrollment: int = Field(foreign_key="enrollments.id", nullable=False)
    id_sesion: int = Field(foreign_key="sesiones_cronograma.id_sesion", nullable=False)
    check_in_time: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, nullable=False, default=datetime.utcnow),
    )
    scanned_by_user_id: Optional[int] = Field(default=None, nullable=True)
    notes: Optional[str] = Field(default=None, max_length=255, nullable=True)


class SessionAttendanceRead(BaseModel):
    id: int
    id_enrollment: int
    id_sesion: int
    check_in_time: datetime
    scanned_by_user_id: Optional[int] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class SessionAttendanceCreate(BaseModel):
    id_enrollment: int
    id_sesion: int
    scanned_by_user_id: Optional[int] = None
    notes: Optional[str] = None


class AttendanceScanPayload(BaseModel):
    qr_payload: str
    id_sesion: int
    notes: Optional[str] = None
