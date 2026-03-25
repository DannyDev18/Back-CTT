from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import date, time
from pydantic import BaseModel, field_validator
from .base import Jornada

if TYPE_CHECKING:
    from .congress_model import Congress
    from .speaker_model import Speaker


# === Modelo SQLModel ===
class SesionCronograma(SQLModel, table=True):
    __tablename__ = "sesiones_cronograma"

    id_sesion: Optional[int] = Field(default=None, primary_key=True)
    id_congreso: int = Field(foreign_key="congresos.id_congreso")
    id_speaker: int = Field(foreign_key="speakers.id_speaker")
    fecha: date
    hora_inicio: time
    hora_fin: time
    titulo_sesion: str = Field(max_length=200)
    jornada: str = Field(max_length=20)
    lugar: str = Field(max_length=150)

    # Relaciones (usando forward references)
    congreso: Optional["Congress"] = Relationship(back_populates="sesiones")
    speaker: Optional["Speaker"] = Relationship(back_populates="sesiones")


# === Modelos Pydantic ===
class SesionCronogramaRead(BaseModel):
    """Modelo de lectura para SesionCronograma"""
    id_sesion: int
    id_congreso: int
    id_speaker: int
    fecha: date
    hora_inicio: time
    hora_fin: time
    titulo_sesion: str
    jornada: str
    lugar: str

    class Config:
        from_attributes = True


class SesionCronogramaCreate(BaseModel):
    """Modelo de creación para SesionCronograma"""
    id_congreso: int
    id_speaker: int
    fecha: date
    hora_inicio: time
    hora_fin: time
    titulo_sesion: str
    jornada: str
    lugar: str

    @field_validator('hora_fin')
    @classmethod
    def validate_horas(cls, v, values):
        if 'hora_inicio' in values.data and v <= values.data['hora_inicio']:
            raise ValueError('La hora de fin debe ser posterior a la hora de inicio')
        return v

    @field_validator('titulo_sesion')
    @classmethod
    def validate_titulo_sesion(cls, v):
        if len(v.strip()) < 5:
            raise ValueError('El título de la sesión debe tener al menos 5 caracteres')
        return v.strip()

    @field_validator('jornada')
    @classmethod
    def validate_jornada(cls, v):
        valid_jornadas = [e.value for e in Jornada]
        if v not in valid_jornadas:
            raise ValueError(f'La jornada debe ser una de: {", ".join(valid_jornadas)}')
        return v

    @field_validator('lugar')
    @classmethod
    def validate_lugar(cls, v):
        if len(v.strip()) < 3:
            raise ValueError('El lugar debe tener al menos 3 caracteres')
        return v.strip()

    # @field_validator('fecha')
    # @classmethod
    # def validate_fecha(cls, v):
    #     from datetime import date as dt_date
    #     if v < dt_date.today():
    #         raise ValueError('La fecha no puede ser en el pasado')
    #     return v

    class Config:
        str_strip_whitespace = True


class SesionCronogramaUpdate(BaseModel):
    """Modelo de actualización para SesionCronograma"""
    id_speaker: Optional[int] = None
    fecha: Optional[date] = None
    hora_inicio: Optional[time] = None
    hora_fin: Optional[time] = None
    titulo_sesion: Optional[str] = None
    jornada: Optional[str] = None
    lugar: Optional[str] = None

    @field_validator('titulo_sesion')
    @classmethod
    def validate_titulo_sesion(cls, v):
        if v is not None and len(v.strip()) < 5:
            raise ValueError('El título de la sesión debe tener al menos 5 caracteres')
        return v.strip() if v else v

    @field_validator('jornada')
    @classmethod
    def validate_jornada(cls, v):
        if v is not None:
            valid_jornadas = [e.value for e in Jornada]
            if v not in valid_jornadas:
                raise ValueError(f'La jornada debe ser una de: {", ".join(valid_jornadas)}')
        return v

    @field_validator('lugar')
    @classmethod
    def validate_lugar(cls, v):
        if v is not None and len(v.strip()) < 3:
            raise ValueError('El lugar debe tener al menos 3 caracteres')
        return v.strip() if v else v

    @field_validator('fecha')
    @classmethod
    def validate_fecha(cls, v):
        if v is not None:
            from datetime import date as dt_date
            if v < dt_date.today():
                raise ValueError('La fecha no puede ser en el pasado')
        return v

    class Config:
        str_strip_whitespace = True


# === Modelo extendido con información del speaker ===
class SesionCronogramaWithSpeaker(BaseModel):
    """Modelo de lectura para SesionCronograma con información del speaker"""
    id_sesion: int
    id_congreso: int
    fecha: date
    hora_inicio: time
    hora_fin: time
    titulo_sesion: str
    jornada: str
    lugar: str
    speaker_nombre: str
    speaker_titulo: str
    speaker_institucion: str

    class Config:
        from_attributes = True