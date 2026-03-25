from typing import List, Optional, Tuple
from sqlmodel import Session
from sqlalchemy import select, func, and_, or_, between
from sqlalchemy.orm import selectinload, joinedload
from datetime import date, time, datetime, timedelta

from .base_repository import BaseRepository, handle_repository_errors
from src.models.sesion_cronograma_model import (
    SesionCronograma, SesionCronogramaCreate, SesionCronogramaUpdate,
    SesionCronogramaRead, SesionCronogramaWithSpeaker
)


class SesionCronogramaRepository(BaseRepository[SesionCronograma, SesionCronogramaCreate, SesionCronogramaUpdate]):
    """
    Repositorio para operaciones con SesionCronograma (Cronograma de Sesiones).

    Hereda operaciones CRUD básicas del BaseRepository y agrega
    operaciones específicas para sesiones de cronograma.
    """

    def __init__(self):
        super().__init__(SesionCronograma)

    @handle_repository_errors
    def get_session_with_details(self, db: Session, session_id: int) -> Optional[SesionCronograma]:
        """
        Obtener una sesión con todos sus detalles (speaker y congreso).
        """
        query = (
            select(SesionCronograma)
            .where(SesionCronograma.id_sesion == session_id)
            .options(
                selectinload(SesionCronograma.speaker),
                selectinload(SesionCronograma.congreso)
            )
        )
        return db.exec(query).scalars().first()

    @handle_repository_errors
    def get_sessions_by_congress(
        self,
        db: Session,
        congress_id: int,
        include_details: bool = True,
        order_by_date: bool = True
    ) -> List[SesionCronograma]:
        """
        Obtener todas las sesiones de un congreso específico.

        Args:
            congress_id: ID del congreso
            include_details: Si incluir detalles del speaker
            order_by_date: Si ordenar por fecha y hora
        """
        query = select(SesionCronograma).where(SesionCronograma.id_congreso == congress_id)

        if include_details:
            query = query.options(
                selectinload(SesionCronograma.speaker),
                selectinload(SesionCronograma.congreso)
            )

        if order_by_date:
            query = query.order_by(
                SesionCronograma.fecha,
                SesionCronograma.hora_inicio
            )

        return db.exec(query).scalars().all()

    @handle_repository_errors
    def get_sessions_by_date(
        self,
        db: Session,
        fecha: date,
        congress_id: Optional[int] = None,
        include_details: bool = True
    ) -> List[SesionCronograma]:
        """
        Obtener todas las sesiones de una fecha específica.
        """
        query = select(SesionCronograma).where(SesionCronograma.fecha == fecha)

        if congress_id is not None:
            query = query.where(SesionCronograma.id_congreso == congress_id)

        if include_details:
            query = query.options(
                selectinload(SesionCronograma.speaker),
                selectinload(SesionCronograma.congreso)
            )

        query = query.order_by(SesionCronograma.hora_inicio)

        return db.exec(query).scalars().all()

    @handle_repository_errors
    def get_sessions_by_date_range(
        self,
        db: Session,
        start_date: date,
        end_date: date,
        congress_id: Optional[int] = None,
        include_details: bool = True
    ) -> List[SesionCronograma]:
        """
        Obtener sesiones en un rango de fechas.
        """
        query = select(SesionCronograma).where(
            between(SesionCronograma.fecha, start_date, end_date)
        )

        if congress_id is not None:
            query = query.where(SesionCronograma.id_congreso == congress_id)

        if include_details:
            query = query.options(
                selectinload(SesionCronograma.speaker),
                selectinload(SesionCronograma.congreso)
            )

        query = query.order_by(
            SesionCronograma.fecha,
            SesionCronograma.hora_inicio
        )

        return db.exec(query).all()

    @handle_repository_errors
    def get_sessions_by_speaker(
        self,
        db: Session,
        speaker_id: int,
        include_details: bool = True
    ) -> List[SesionCronograma]:
        """
        Obtener todas las sesiones de un speaker específico.
        """
        query = select(SesionCronograma).where(SesionCronograma.id_speaker == speaker_id)

        if include_details:
            query = query.options(
                selectinload(SesionCronograma.speaker),
                selectinload(SesionCronograma.congreso)
            )

        query = query.order_by(
            SesionCronograma.fecha,
            SesionCronograma.hora_inicio
        )

        return db.exec(query).all()

    @handle_repository_errors
    def get_sessions_by_jornada(
        self,
        db: Session,
        jornada: str,
        congress_id: Optional[int] = None,
        fecha: Optional[date] = None
    ) -> List[SesionCronograma]:
        """
        Obtener sesiones por jornada (mañana, tarde, noche).
        """
        query = select(SesionCronograma).where(SesionCronograma.jornada == jornada)

        if congress_id is not None:
            query = query.where(SesionCronograma.id_congreso == congress_id)

        if fecha is not None:
            query = query.where(SesionCronograma.fecha == fecha)

        query = query.order_by(SesionCronograma.hora_inicio)

        return db.exec(query).all()

    @handle_repository_errors
    def get_sessions_paginated(
        self,
        db: Session,
        page: int = 1,
        page_size: int = 10,
        congress_id: Optional[int] = None,
        speaker_id: Optional[int] = None,
        fecha: Optional[date] = None,
        jornada: Optional[str] = None,
        search_term: Optional[str] = None,
        order_by: str = "fecha",
        order_desc: bool = False
    ) -> Tuple[List[SesionCronograma], int]:
        """
        Obtener sesiones paginadas con filtros.
        """
        # Query base
        query = select(SesionCronograma).options(
            selectinload(SesionCronograma.speaker),
            selectinload(SesionCronograma.congreso)
        )
        count_query = select(func.count()).select_from(SesionCronograma)

        # Aplicar filtros
        conditions = []

        if congress_id is not None:
            conditions.append(SesionCronograma.id_congreso == congress_id)

        if speaker_id is not None:
            conditions.append(SesionCronograma.id_speaker == speaker_id)

        if fecha is not None:
            conditions.append(SesionCronograma.fecha == fecha)

        if jornada:
            conditions.append(SesionCronograma.jornada == jornada)

        if search_term:
            search_conditions = or_(
                SesionCronograma.titulo_sesion.ilike(f"%{search_term}%"),
                SesionCronograma.lugar.ilike(f"%{search_term}%")
            )
            conditions.append(search_conditions)

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        # Contar total
        total = db.exec(count_query).scalar()

        # Aplicar ordenamiento
        if hasattr(SesionCronograma, order_by):
            order_column = getattr(SesionCronograma, order_by)
            if order_desc:
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())

        # Ordenamiento secundario por hora si se ordena por fecha
        if order_by == "fecha":
            query = query.order_by(
                SesionCronograma.fecha.desc() if order_desc else SesionCronograma.fecha.asc(),
                SesionCronograma.hora_inicio
            )

        # Aplicar paginación
        offset = (page - 1) * page_size
        sessions = db.exec(query.offset(offset).limit(page_size)).all()

        return sessions, total

    @handle_repository_errors
    def search_sessions(
        self,
        db: Session,
        search_term: str,
        congress_id: Optional[int] = None,
        limit: int = 20
    ) -> List[SesionCronograma]:
        """
        Buscar sesiones por término en título o lugar.
        """
        search_conditions = or_(
            SesionCronograma.titulo_sesion.ilike(f"%{search_term}%"),
            SesionCronograma.lugar.ilike(f"%{search_term}%")
        )

        query = select(SesionCronograma).where(search_conditions)

        if congress_id is not None:
            query = query.where(SesionCronograma.id_congreso == congress_id)

        query = query.options(
            selectinload(SesionCronograma.speaker),
            selectinload(SesionCronograma.congreso)
        ).order_by(
            SesionCronograma.fecha,
            SesionCronograma.hora_inicio
        ).limit(limit)

        return db.exec(query).all()

    @handle_repository_errors
    def get_conflicting_sessions(
        self,
        db: Session,
        speaker_id: int,
        fecha: date,
        hora_inicio: time,
        hora_fin: time,
        exclude_session_id: Optional[int] = None
    ) -> List[SesionCronograma]:
        """
        Obtener sesiones que entran en conflicto de horario para un speaker.

        Args:
            exclude_session_id: ID de sesión a excluir (para actualizaciones)
        """
        query = select(SesionCronograma).where(
            and_(
                SesionCronograma.id_speaker == speaker_id,
                SesionCronograma.fecha == fecha,
                or_(
                    # Nueva sesión inicia durante una existente
                    and_(
                        SesionCronograma.hora_inicio <= hora_inicio,
                        SesionCronograma.hora_fin > hora_inicio
                    ),
                    # Nueva sesión termina durante una existente
                    and_(
                        SesionCronograma.hora_inicio < hora_fin,
                        SesionCronograma.hora_fin >= hora_fin
                    ),
                    # Nueva sesión contiene a una existente
                    and_(
                        hora_inicio <= SesionCronograma.hora_inicio,
                        hora_fin >= SesionCronograma.hora_fin
                    )
                )
            )
        )

        if exclude_session_id is not None:
            query = query.where(SesionCronograma.id_sesion != exclude_session_id)

        return db.exec(query).scalars().all()

    @handle_repository_errors
    def get_congress_schedule_summary(self, db: Session, congress_id: int) -> dict:
        """
        Obtener resumen del cronograma de un congreso.
        """
        sessions = self.get_sessions_by_congress(db, congress_id, include_details=True)

        summary = {
            'total_sessions': len(sessions),
            'sessions_by_date': {},
            'sessions_by_jornada': {},
            'sessions_by_speaker_type': {},
            'unique_dates': set(),
            'unique_speakers': set(),
            'unique_locations': set(),
            'duration_stats': {
                'total_minutes': 0,
                'average_duration': 0,
                'shortest_session': None,
                'longest_session': None
            }
        }

        durations = []

        for session in sessions:
            fecha_str = session.fecha.strftime('%Y-%m-%d')
            jornada = session.jornada
            speaker = session.speaker
            location = session.lugar

            # Contadores por fecha
            summary['sessions_by_date'][fecha_str] = summary['sessions_by_date'].get(fecha_str, 0) + 1

            # Contadores por jornada
            summary['sessions_by_jornada'][jornada] = summary['sessions_by_jornada'].get(jornada, 0) + 1

            # Contadores por tipo de speaker
            if speaker:
                speaker_type = speaker.tipo_speaker
                summary['sessions_by_speaker_type'][speaker_type] = summary['sessions_by_speaker_type'].get(speaker_type, 0) + 1
                summary['unique_speakers'].add(speaker.id_speaker)

            # Sets únicos
            summary['unique_dates'].add(session.fecha)
            summary['unique_locations'].add(location)

            # Duración de sesión
            session_datetime_start = datetime.combine(session.fecha, session.hora_inicio)
            session_datetime_end = datetime.combine(session.fecha, session.hora_fin)
            duration_minutes = (session_datetime_end - session_datetime_start).total_seconds() / 60
            durations.append(duration_minutes)

        # Estadísticas de duración
        if durations:
            total_minutes = sum(durations)
            summary['duration_stats']['total_minutes'] = total_minutes
            summary['duration_stats']['average_duration'] = total_minutes / len(durations)
            summary['duration_stats']['shortest_session'] = min(durations)
            summary['duration_stats']['longest_session'] = max(durations)

        # Convertir sets a listas
        summary['unique_dates'] = len(summary['unique_dates'])
        summary['unique_speakers'] = len(summary['unique_speakers'])
        summary['unique_locations'] = len(summary['unique_locations'])

        return summary

    @handle_repository_errors
    def get_daily_schedule(
        self,
        db: Session,
        congress_id: int,
        fecha: date,
        group_by_jornada: bool = True
    ) -> dict:
        """
        Obtener cronograma detallado de un día específico.
        """
        sessions = self.get_sessions_by_date(db, fecha, congress_id, include_details=True)

        if group_by_jornada:
            schedule = {
                'fecha': fecha,
                'total_sessions': len(sessions),
                'jornadas': {}
            }

            for session in sessions:
                jornada = session.jornada
                if jornada not in schedule['jornadas']:
                    schedule['jornadas'][jornada] = []

                schedule['jornadas'][jornada].append({
                    'id_sesion': session.id_sesion,
                    'titulo': session.titulo_sesion,
                    'hora_inicio': session.hora_inicio,
                    'hora_fin': session.hora_fin,
                    'lugar': session.lugar,
                    'speaker': {
                        'nombre': session.speaker.nombres_completos if session.speaker else None,
                        'institucion': session.speaker.institucion if session.speaker else None,
                        'tipo': session.speaker.tipo_speaker if session.speaker else None
                    }
                })
        else:
            schedule = {
                'fecha': fecha,
                'total_sessions': len(sessions),
                'sessions': [
                    {
                        'id_sesion': session.id_sesion,
                        'titulo': session.titulo_sesion,
                        'hora_inicio': session.hora_inicio,
                        'hora_fin': session.hora_fin,
                        'jornada': session.jornada,
                        'lugar': session.lugar,
                        'speaker': {
                            'nombre': session.speaker.nombres_completos if session.speaker else None,
                            'institucion': session.speaker.institucion if session.speaker else None,
                            'tipo': session.speaker.tipo_speaker if session.speaker else None
                        }
                    }
                    for session in sessions
                ]
            }

        return schedule

    @handle_repository_errors
    def check_time_conflict(
        self,
        db: Session,
        speaker_id: int,
        fecha: date,
        hora_inicio: time,
        hora_fin: time,
        exclude_session_id: Optional[int] = None
    ) -> bool:
        """
        Verificar si existe conflicto de horario para un speaker.
        """
        conflicts = self.get_conflicting_sessions(
            db, speaker_id, fecha, hora_inicio, hora_fin, exclude_session_id
        )
        return len(conflicts) > 0

    @handle_repository_errors
    def get_session_summary(self, db: Session) -> dict:
        """
        Obtener resumen general de sesiones.
        """
        total_query = select(func.count()).select_from(SesionCronograma)
        total_sessions = db.exec(total_query).scalar()

        # Sesiones por congreso
        sessions_per_congress_query = (
            select(func.count(func.distinct(SesionCronograma.id_congreso)))
            .select_from(SesionCronograma)
        )
        congresses_with_sessions = db.exec(sessions_per_congress_query).scalar()

        # Sesiones futuras
        today = date.today()
        future_sessions_query = (
            select(func.count())
            .select_from(SesionCronograma)
            .where(SesionCronograma.fecha > today)
        )
        future_sessions = db.exec(future_sessions_query).scalar()

        return {
            'total_sessions': total_sessions,
            'congresses_with_sessions': congresses_with_sessions,
            'future_sessions': future_sessions
        }


# Instancia única del repositorio
sesion_cronograma_repository = SesionCronogramaRepository()