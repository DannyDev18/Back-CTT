from typing import List, Optional, Tuple
from sqlmodel import Session
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload, joinedload

from .base_repository import BaseRepository, handle_repository_errors
from src.models.speaker_model import Speaker, SpeakerCreate, SpeakerUpdate, SpeakerRead
from src.models.sesion_cronograma_model import SesionCronograma


class SpeakerRepository(BaseRepository[Speaker, SpeakerCreate, SpeakerUpdate]):
    """
    Repositorio para operaciones con Speaker (Ponentes/Expositores).

    Hereda operaciones CRUD básicas del BaseRepository y agrega
    operaciones específicas para speakers.
    """

    def __init__(self):
        super().__init__(Speaker)

    @handle_repository_errors
    def get_speaker_with_sessions(self, db: Session, speaker_id: int) -> Optional[Speaker]:
        """
        Obtener un speaker con todas sus sesiones y congreso asociados.
        """
        query = (
            select(Speaker)
            .where(Speaker.id_speaker == speaker_id)
            .options(
                selectinload(Speaker.sesiones),
                selectinload(Speaker.congreso)
            )
        )
        return db.exec(query).scalars().first()

    @handle_repository_errors
    def get_speakers_by_congress(
        self,
        db: Session,
        congress_id: int,
        include_sessions: bool = False
    ) -> List[Speaker]:
        """
        Obtener todos los speakers de un congreso específico.

        Args:
            congress_id: ID del congreso
            include_sessions: Si incluir las sesiones de cada speaker
        """
        query = select(Speaker).where(Speaker.id_congreso == congress_id)

        if include_sessions:
            query = query.options(selectinload(Speaker.sesiones))

        query = query.order_by(Speaker.nombres_completos)

        return db.execute(query).scalars().all()

    @handle_repository_errors
    def get_speakers_paginated(
        self,
        db: Session,
        page: int = 1,
        page_size: int = 10,
        congress_id: Optional[int] = None,
        tipo_speaker: Optional[str] = None,
        pais: Optional[str] = None,
        search_term: Optional[str] = None,
        order_by: str = "nombres_completos",
        order_desc: bool = False
    ) -> Tuple[List[Speaker], int]:
        """
        Obtener speakers paginados con filtros.

        Args:
            congress_id: Filtrar por congreso
            tipo_speaker: Filtrar por tipo de speaker
            pais: Filtrar por país
            search_term: Buscar en nombre, institución
        """
        # Query base
        query = select(Speaker)
        count_query = select(func.count()).select_from(Speaker)

        # Aplicar filtros
        conditions = []

        if congress_id is not None:
            conditions.append(Speaker.id_congreso == congress_id)

        if tipo_speaker:
            conditions.append(Speaker.tipo_speaker == tipo_speaker)

        if pais:
            conditions.append(Speaker.pais.ilike(f"%{pais}%"))

        if search_term:
            search_conditions = or_(
                Speaker.nombres_completos.ilike(f"%{search_term}%"),
                Speaker.institucion.ilike(f"%{search_term}%"),
                Speaker.titulo_academico.ilike(f"%{search_term}%")
            )
            conditions.append(search_conditions)

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        # Contar total
        total = db.exec(count_query).scalar()

        # Aplicar ordenamiento
        if hasattr(Speaker, order_by):
            order_column = getattr(Speaker, order_by)
            if order_desc:
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())

        # Aplicar paginación
        offset = (page - 1) * page_size
        speakers = db.exec(query.offset(offset).limit(page_size)).all()

        return speakers, total

    @handle_repository_errors
    def get_speakers_by_type(
        self,
        db: Session,
        tipo_speaker: str,
        congress_id: Optional[int] = None
    ) -> List[Speaker]:
        """
        Obtener speakers por tipo (keynote, conferencia, taller, panel).
        """
        query = select(Speaker).where(Speaker.tipo_speaker == tipo_speaker)

        if congress_id is not None:
            query = query.where(Speaker.id_congreso == congress_id)

        query = query.order_by(Speaker.nombres_completos)

        return db.execute(query).scalars().all()

    @handle_repository_errors
    def get_speakers_by_country(
        self,
        db: Session,
        pais: str,
        congress_id: Optional[int] = None
    ) -> List[Speaker]:
        """
        Obtener speakers por país.
        """
        query = select(Speaker).where(Speaker.pais.ilike(f"%{pais}%"))

        if congress_id is not None:
            query = query.where(Speaker.id_congreso == congress_id)

        query = query.order_by(Speaker.nombres_completos)

        return db.execute(query).scalars().all()

    @handle_repository_errors
    def search_speakers(
        self,
        db: Session,
        search_term: str,
        congress_id: Optional[int] = None,
        limit: int = 20
    ) -> List[Speaker]:
        """
        Buscar speakers por término en nombres, institución o título académico.
        """
        search_conditions = or_(
            Speaker.nombres_completos.ilike(f"%{search_term}%"),
            Speaker.institucion.ilike(f"%{search_term}%"),
            Speaker.titulo_academico.ilike(f"%{search_term}%")
        )

        query = select(Speaker).where(search_conditions)

        if congress_id is not None:
            query = query.where(Speaker.id_congreso == congress_id)

        query = query.order_by(Speaker.nombres_completos).limit(limit)

        return db.execute(query).scalars().all()

    @handle_repository_errors
    def get_speakers_by_institution(
        self,
        db: Session,
        institucion: str,
        exact_match: bool = False
    ) -> List[Speaker]:
        """
        Obtener speakers por institución.

        Args:
            exact_match: Si hacer búsqueda exacta o parcial
        """
        if exact_match:
            query = select(Speaker).where(Speaker.institucion == institucion)
        else:
            query = select(Speaker).where(Speaker.institucion.ilike(f"%{institucion}%"))

        query = query.order_by(Speaker.nombres_completos)

        return db.execute(query).scalars().all()

    @handle_repository_errors
    def get_countries_with_speakers(self, db: Session, congress_id: Optional[int] = None) -> List[str]:
        """
        Obtener lista de países que tienen speakers.
        """
        query = select(Speaker.pais).distinct()

        if congress_id is not None:
            query = query.where(Speaker.id_congreso == congress_id)

        query = query.order_by(Speaker.pais)

        results = db.exec(query).all()
        # Extract values from SQLAlchemy Row objects and convert to strings
        return [str(row.pais) if hasattr(row, 'pais') else str(row[0] if isinstance(row, tuple) else row) for row in results]

    @handle_repository_errors
    def get_institutions_with_speakers(self, db: Session, congress_id: Optional[int] = None) -> List[str]:
        """
        Obtener lista de instituciones que tienen speakers.
        """
        query = select(Speaker.institucion).distinct()

        if congress_id is not None:
            query = query.where(Speaker.id_congreso == congress_id)

        query = query.order_by(Speaker.institucion)

        results = db.exec(query).all()
        # Extract values from SQLAlchemy Row objects and convert to strings
        return [str(row.institucion) if hasattr(row, 'institucion') else str(row[0] if isinstance(row, tuple) else row) for row in results]

    @handle_repository_errors
    def get_speaker_statistics_by_congress(self, db: Session, congress_id: int) -> dict:
        """
        Obtener estadísticas de speakers por congreso.
        """
        speakers = self.get_speakers_by_congress(db, congress_id, include_sessions=True)

        stats = {
            'total_speakers': len(speakers),
            'speakers_by_type': {},
            'speakers_by_country': {},
            'speakers_by_institution': {},
            'speakers_with_sessions': 0,
            'total_sessions': 0
        }

        # Calcular estadísticas
        for speaker in speakers:
            # Handle both Speaker instances and Row objects
            if hasattr(speaker, 'tipo_speaker'):
                # Direct Speaker instance
                speaker_obj = speaker
            else:
                # Row object containing Speaker instance
                speaker_obj = speaker[0] if isinstance(speaker, tuple) else speaker

            # Por tipo
            tipo = speaker_obj.tipo_speaker
            stats['speakers_by_type'][tipo] = stats['speakers_by_type'].get(tipo, 0) + 1

            # Por país
            pais = speaker_obj.pais
            stats['speakers_by_country'][pais] = stats['speakers_by_country'].get(pais, 0) + 1

            # Por institución
            institucion = speaker_obj.institucion
            stats['speakers_by_institution'][institucion] = stats['speakers_by_institution'].get(institucion, 0) + 1

            # Sesiones
            if hasattr(speaker_obj, 'sesiones') and speaker_obj.sesiones:
                stats['speakers_with_sessions'] += 1
                stats['total_sessions'] += len(speaker_obj.sesiones)

        return stats

    @handle_repository_errors
    def get_frequent_speakers(
        self,
        db: Session,
        min_congresses: int = 2,
        limit: int = 20
    ) -> List[dict]:
        """
        Obtener speakers que han participado en múltiples congresos.

        Args:
            min_congresses: Número mínimo de congresos para considerar "frecuente"
        """
        # Agrupar por speaker (usando nombres completos como identificador)
        query = (
            select(
                Speaker.nombres_completos,
                Speaker.titulo_academico,
                Speaker.institucion,
                func.count(func.distinct(Speaker.id_congreso)).label('total_congresses'),
                func.group_concat(func.distinct(Speaker.id_congreso)).label('congress_ids')
            )
            .group_by(Speaker.nombres_completos, Speaker.titulo_academico, Speaker.institucion)
            .having(func.count(func.distinct(Speaker.id_congreso)) >= min_congresses)
            .order_by(func.count(func.distinct(Speaker.id_congreso)).desc())
            .limit(limit)
        )

        result = db.exec(query).all()

        return [
            {
                'nombres_completos': r.nombres_completos,
                'titulo_academico': r.titulo_academico,
                'institucion': r.institucion,
                'total_congresses': r.total_congresses,
                'congress_ids': r.congress_ids
            }
            for r in result
        ]

    @handle_repository_errors
    def check_speaker_exists_in_congress(
        self,
        db: Session,
        nombres_completos: str,
        congress_id: int,
        exclude_id: Optional[int] = None
    ) -> bool:
        """
        Verificar si ya existe un speaker con el mismo nombre en el congreso.

        Args:
            exclude_id: ID a excluir de la verificación (para actualizaciones)
        """
        query = select(Speaker).where(
            and_(
                Speaker.nombres_completos == nombres_completos,
                Speaker.id_congreso == congress_id
            )
        )

        if exclude_id is not None:
            query = query.where(Speaker.id_speaker != exclude_id)

        return db.exec(query).scalars().first() is not None

    @handle_repository_errors
    def get_speaker_summary(self, db: Session) -> dict:
        """
        Obtener resumen general de speakers.
        """
        total_query = select(func.count()).select_from(Speaker)
        total_speakers = db.exec(total_query).scalar()

        # Speakers únicos (por nombre)
        unique_speakers_query = select(func.count(func.distinct(Speaker.nombres_completos))).select_from(Speaker)
        unique_speakers = db.exec(unique_speakers_query).scalar()

        # Congresos únicos con speakers
        congresses_with_speakers_query = select(func.count(func.distinct(Speaker.id_congreso))).select_from(Speaker)
        congresses_with_speakers = db.exec(congresses_with_speakers_query).scalar()

        # Top países
        top_countries_query = (
            select(Speaker.pais, func.count().label('count'))
            .group_by(Speaker.pais)
            .order_by(func.count().desc())
            .limit(5)
        )
        top_countries = db.exec(top_countries_query).all()

        return {
            'total_speakers': total_speakers,
            'unique_speakers': unique_speakers,
            'congresses_with_speakers': congresses_with_speakers,
            'top_countries': [{'pais': r.pais, 'count': r.count} for r in top_countries]
        }


# Instancia única del repositorio
speaker_repository = SpeakerRepository()