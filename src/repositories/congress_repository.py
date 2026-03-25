from typing import List, Optional, Tuple
from sqlmodel import Session
from sqlalchemy import select, func, and_, or_, extract
from sqlalchemy.orm import selectinload, joinedload
from datetime import date, datetime

from .base_repository import BaseRepository, handle_repository_errors
from src.models.congress_model import Congress, CongressCreate, CongressUpdate, CongressRead
from src.models.congreso_sponsor_model import CongresoSponsor


class CongressRepository(BaseRepository[Congress, CongressCreate, CongressUpdate]):
    """
    Repositorio para operaciones con Congress (Congresos).

    Hereda operaciones CRUD básicas del BaseRepository y agrega
    operaciones específicas para congresos.
    """

    def __init__(self):
        super().__init__(Congress)

    @handle_repository_errors
    def get_congress_with_relations(self, db: Session, congress_id: int) -> Optional[Congress]:
        """
        Obtener un congreso con todas sus relaciones cargadas.

        Incluye: speakers, sesiones, sponsors
        """
        query = (
            select(Congress)
            .where(Congress.id_congreso == congress_id)
            .options(
                selectinload(Congress.speakers),
                selectinload(Congress.sesiones),
                selectinload(Congress.congreso_sponsors).selectinload(CongresoSponsor.sponsor)
            )
        )
        return db.execute(query).scalar_one_or_none()

    @handle_repository_errors
    def get_congresses_paginated(
        self,
        db: Session,
        page: int = 1,
        page_size: int = 10,
        year: Optional[int] = None,
        search_term: Optional[str] = None,
        order_by: str = "fecha_inicio",
        order_desc: bool = True
    ) -> Tuple[List[Congress], int]:
        """
        Obtener congresos paginados con filtros.

        Args:
            year: Filtrar por año
            search_term: Buscar en nombre y descripción
        """
        # Query base
        query = select(Congress)
        count_query = select(func.count()).select_from(Congress)

        # Aplicar filtros
        conditions = []

        if year is not None:
            conditions.append(Congress.anio == year)

        if search_term:
            search_conditions = or_(
                Congress.nombre.ilike(f"%{search_term}%"),
                Congress.descripcion_general.ilike(f"%{search_term}%"),
                Congress.edicion.ilike(f"%{search_term}%")
            )
            conditions.append(search_conditions)

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        # Contar total
        total = db.exec(count_query).scalar()

        # Aplicar ordenamiento
        if hasattr(Congress, order_by):
            order_column = getattr(Congress, order_by)
            if order_desc:
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())

        # Aplicar paginación
        offset = (page - 1) * page_size
        congresses = db.exec(query.offset(offset).limit(page_size)).all()

        return congresses, total

    @handle_repository_errors
    def get_congress_by_edition_and_year(
        self,
        db: Session,
        edicion: str,
        anio: int
    ) -> Optional[Congress]:
        """
        Obtener congreso por edición y año (combinación única).
        """
        query = select(Congress).where(
            and_(
                Congress.edicion == edicion,
                Congress.anio == anio
            )
        )
        return db.execute(query).scalar_one_or_none()

    @handle_repository_errors
    def get_congresses_by_date_range(
        self,
        db: Session,
        start_date: date,
        end_date: date
    ) -> List[Congress]:
        """
        Obtener congresos que se realizan en un rango de fechas.
        """
        query = select(Congress).where(
            or_(
                # Congresos que inician en el rango
                and_(
                    Congress.fecha_inicio >= start_date,
                    Congress.fecha_inicio <= end_date
                ),
                # Congresos que terminan en el rango
                and_(
                    Congress.fecha_fin >= start_date,
                    Congress.fecha_fin <= end_date
                ),
                # Congresos que abarcan todo el rango
                and_(
                    Congress.fecha_inicio <= start_date,
                    Congress.fecha_fin >= end_date
                )
            )
        ).order_by(Congress.fecha_inicio)

        return db.execute(query).scalars().all()

    @handle_repository_errors
    def get_upcoming_congresses(
        self,
        db: Session,
        limit: int = 10,
        include_relations: bool = False
    ) -> List[Congress]:
        """
        Obtener próximos congresos (que aún no han empezado).
        """
        today = date.today()
        query = select(Congress).where(
            Congress.fecha_inicio > today
        ).order_by(Congress.fecha_inicio)

        if include_relations:
            query = query.options(
                selectinload(Congress.speakers),
                selectinload(Congress.sesiones),
                selectinload(Congress.congreso_sponsors)
            )

        return db.exec(query.limit(limit)).all()

    @handle_repository_errors
    def get_current_congresses(self, db: Session) -> List[Congress]:
        """
        Obtener congresos que están ocurriendo actualmente.
        """
        today = date.today()
        query = select(Congress).where(
            and_(
                Congress.fecha_inicio <= today,
                Congress.fecha_fin >= today
            )
        ).order_by(Congress.fecha_inicio)

        return db.execute(query).scalars().all()

    @handle_repository_errors
    def get_congresses_by_year(self, db: Session, year: int) -> List[Congress]:
        """
        Obtener todos los congresos de un año específico.
        """
        query = select(Congress).where(
            Congress.anio == year
        ).order_by(Congress.fecha_inicio)

        return db.execute(query).scalars().all()

    @handle_repository_errors
    def get_years_with_congresses(self, db: Session) -> List[int]:
        """
        Obtener lista de años que tienen congresos.
        """
        query = select(Congress.anio).distinct().order_by(Congress.anio.desc())
        results = db.exec(query).all()
        # Extract values from SQLAlchemy Row objects and convert to integers
        return [int(row.anio) if hasattr(row, 'anio') else int(row[0] if isinstance(row, tuple) else row) for row in results]

    @handle_repository_errors
    def search_congresses(
        self,
        db: Session,
        search_term: str,
        year: Optional[int] = None,
        limit: int = 20
    ) -> List[Congress]:
        """
        Buscar congresos por término en nombre, descripción o edición.
        """
        search_conditions = or_(
            Congress.nombre.ilike(f"%{search_term}%"),
            Congress.descripcion_general.ilike(f"%{search_term}%"),
            Congress.edicion.ilike(f"%{search_term}%")
        )

        query = select(Congress).where(search_conditions)

        if year is not None:
            query = query.where(Congress.anio == year)

        query = query.order_by(Congress.fecha_inicio.desc()).limit(limit)

        return db.execute(query).scalars().all()

    @handle_repository_errors
    def get_congress_statistics(self, db: Session, congress_id: int) -> dict:
        """
        Obtener estadísticas de un congreso.

        Returns:
            dict: Estadísticas del congreso
        """
        # Obtener congreso con relaciones
        congress = self.get_congress_with_relations(db, congress_id)

        if not congress:
            return {}

        stats = {
            'total_speakers': len(congress.speakers),
            'total_sesiones': len(congress.sesiones),
            'total_sponsors': len(congress.congreso_sponsors),
            'duracion_dias': (congress.fecha_fin - congress.fecha_inicio).days + 1,
            'speakers_por_tipo': {},
            'sponsors_por_categoria': {},
            'total_aporte_sponsors': 0
        }

        # Estadísticas de speakers por tipo
        for speaker in congress.speakers:
            tipo = speaker.tipo_speaker
            stats['speakers_por_tipo'][tipo] = stats['speakers_por_tipo'].get(tipo, 0) + 1

        # Estadísticas de sponsors
        for congreso_sponsor in congress.congreso_sponsors:
            categoria = congreso_sponsor.categoria
            stats['sponsors_por_categoria'][categoria] = stats['sponsors_por_categoria'].get(categoria, 0) + 1
            stats['total_aporte_sponsors'] += float(congreso_sponsor.aporte)

        return stats

    @handle_repository_errors
    def check_edition_exists(self, db: Session, edicion: str, anio: int, exclude_id: Optional[int] = None) -> bool:
        """
        Verificar si ya existe un congreso con la misma edición y año.

        Args:
            exclude_id: ID a excluir de la verificación (para actualizaciones)
        """
        query = select(Congress).where(
            and_(
                Congress.edicion == edicion,
                Congress.anio == anio
            )
        )

        if exclude_id is not None:
            query = query.where(Congress.id_congreso != exclude_id)

        return db.execute(query).scalar_one_or_none() is not None

    @handle_repository_errors
    def get_congress_summary(self, db: Session) -> dict:
        """
        Obtener resumen general de congresos.
        """
        total_query = select(func.count()).select_from(Congress)
        total_congresses = db.exec(total_query).scalar()

        current_year = datetime.now().year
        current_year_query = select(func.count()).select_from(Congress).where(Congress.anio == current_year)
        current_year_congresses = db.exec(current_year_query).scalar()

        today = date.today()
        upcoming_query = select(func.count()).select_from(Congress).where(Congress.fecha_inicio > today)
        upcoming_congresses = db.exec(upcoming_query).scalar()

        return {
            'total_congresses': total_congresses,
            'current_year_congresses': current_year_congresses,
            'upcoming_congresses': upcoming_congresses,
        }


# Instancia única del repositorio
congress_repository = CongressRepository()