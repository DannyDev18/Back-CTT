from typing import List, Optional, Tuple
from sqlmodel import Session
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload, joinedload
from decimal import Decimal

from .base_repository import BaseRepository, handle_repository_errors
from src.models.congreso_sponsor_model import (
    CongresoSponsor, CongresoSponsorCreate, CongresoSponsorUpdate,
    CongresoSponsorRead, CongresoSponsorWithDetails, CongresoSponsorSummary
)


class CongresoSponsorRepository(BaseRepository[CongresoSponsor, CongresoSponsorCreate, CongresoSponsorUpdate]):
    """
    Repositorio para operaciones con CongresoSponsor (Relación Congreso-Sponsor).

    Hereda operaciones CRUD básicas del BaseRepository y agrega
    operaciones específicas para la relación muchos-a-muchos entre congresos y sponsors.
    """

    def __init__(self):
        super().__init__(CongresoSponsor)

    @handle_repository_errors
    def get_sponsorship_with_details(
        self,
        db: Session,
        congress_id: int,
        sponsor_id: int
    ) -> Optional[CongresoSponsor]:
        """
        Obtener un sponsorship con detalles del congreso y sponsor.
        """
        query = (
            select(CongresoSponsor)
            .where(
                and_(
                    CongresoSponsor.id_congreso == congress_id,
                    CongresoSponsor.id_sponsor == sponsor_id
                )
            )
            .options(
                selectinload(CongresoSponsor.congreso),
                selectinload(CongresoSponsor.sponsor)
            )
        )
        result = db.execute(query)
        return result.scalar_one_or_none()

    @handle_repository_errors
    def get_sponsorships_by_congress(
        self,
        db: Session,
        congress_id: int,
        include_details: bool = True
    ) -> List[CongresoSponsor]:
        """
        Obtener todos los sponsorships de un congreso específico.
        """
        query = select(CongresoSponsor).where(CongresoSponsor.id_congreso == congress_id)

        if include_details:
            query = query.options(
                selectinload(CongresoSponsor.sponsor),
                selectinload(CongresoSponsor.congreso)
            )

        query = query.order_by(CongresoSponsor.aporte.desc())

        result = db.execute(query)
        return result.scalars().all()

    @handle_repository_errors
    def get_sponsorships_by_sponsor(
        self,
        db: Session,
        sponsor_id: int,
        include_details: bool = True
    ) -> List[CongresoSponsor]:
        """
        Obtener todos los sponsorships de un sponsor específico.
        """
        query = select(CongresoSponsor).where(CongresoSponsor.id_sponsor == sponsor_id)

        if include_details:
            query = query.options(
                selectinload(CongresoSponsor.congreso),
                selectinload(CongresoSponsor.sponsor)
            )

        query = query.order_by(CongresoSponsor.aporte.desc())

        result = db.execute(query)
        return result.scalars().all()

    @handle_repository_errors
    def get_sponsorships_by_category(
        self,
        db: Session,
        categoria: str,
        congress_id: Optional[int] = None,
        include_details: bool = True
    ) -> List[CongresoSponsor]:
        """
        Obtener sponsorships por categoría.
        """
        query = select(CongresoSponsor).where(CongresoSponsor.categoria == categoria)

        if congress_id is not None:
            query = query.where(CongresoSponsor.id_congreso == congress_id)

        if include_details:
            query = query.options(
                selectinload(CongresoSponsor.congreso),
                selectinload(CongresoSponsor.sponsor)
            )

        query = query.order_by(CongresoSponsor.aporte.desc())

        return db.execute(query).scalars().all()

    @handle_repository_errors
    def get_sponsorships_paginated(
        self,
        db: Session,
        page: int = 1,
        page_size: int = 10,
        congress_id: Optional[int] = None,
        sponsor_id: Optional[int] = None,
        categoria: Optional[str] = None,
        min_aporte: Optional[Decimal] = None,
        max_aporte: Optional[Decimal] = None,
        order_by: str = "aporte",
        order_desc: bool = True
    ) -> Tuple[List[CongresoSponsor], int]:
        """
        Obtener sponsorships paginados con filtros.
        """
        # Query base
        query = select(CongresoSponsor).options(
            selectinload(CongresoSponsor.congreso),
            selectinload(CongresoSponsor.sponsor)
        )
        count_query = select(func.count()).select_from(CongresoSponsor)

        # Aplicar filtros
        conditions = []

        if congress_id is not None:
            conditions.append(CongresoSponsor.id_congreso == congress_id)

        if sponsor_id is not None:
            conditions.append(CongresoSponsor.id_sponsor == sponsor_id)

        if categoria:
            conditions.append(CongresoSponsor.categoria == categoria)

        if min_aporte is not None:
            conditions.append(CongresoSponsor.aporte >= min_aporte)

        if max_aporte is not None:
            conditions.append(CongresoSponsor.aporte <= max_aporte)

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        # Contar total
        total = db.exec(count_query).scalar()

        # Aplicar ordenamiento
        if hasattr(CongresoSponsor, order_by):
            order_column = getattr(CongresoSponsor, order_by)
            if order_desc:
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())

        # Aplicar paginación
        offset = (page - 1) * page_size
        sponsorships = db.exec(query.offset(offset).limit(page_size)).all()

        return sponsorships, total

    @handle_repository_errors
    def get_top_contributors_by_congress(
        self,
        db: Session,
        congress_id: int,
        limit: int = 10
    ) -> List[dict]:
        """
        Obtener top contribuyentes para un congreso específico.
        """
        # First get the entities with relationships loaded
        query = (
            select(CongresoSponsor)
            .where(CongresoSponsor.id_congreso == congress_id)
            .options(selectinload(CongresoSponsor.sponsor))
            .order_by(CongresoSponsor.aporte.desc())
            .limit(limit)
        )

        sponsorships = db.exec(query).scalars().all()

        result = []
        for sponsorship in sponsorships:
            sponsor_info = {
                'id': sponsorship.id_sponsor,
                'nombre': 'Unknown',
                'logo_url': None
            }

            if sponsorship.sponsor:
                sponsor_info.update({
                    'id': sponsorship.sponsor.id_sponsor,
                    'nombre': sponsorship.sponsor.nombre,
                    'logo_url': sponsorship.sponsor.logo_url
                })

            result.append({
                'sponsor': sponsor_info,
                'categoria': sponsorship.categoria,
                'aporte': float(sponsorship.aporte)
            })

        return result

    @handle_repository_errors
    def get_sponsorship_statistics_by_congress(self, db: Session, congress_id: int) -> dict:
        """
        Obtener estadísticas de sponsorships para un congreso.
        """
        sponsorships = self.get_sponsorships_by_congress(db, congress_id, include_details=True)

        stats = {
            'total_sponsors': len(sponsorships),
            'total_contribution': 0,
            'sponsors_by_category': {},
            'contribution_by_category': {},
            'average_contribution': 0,
            'highest_contribution': 0,
            'lowest_contribution': float('inf') if sponsorships else 0
        }

        if not sponsorships:
            stats['lowest_contribution'] = 0
            return stats

        for sponsorship in sponsorships:
            categoria = sponsorship.categoria
            aporte = float(sponsorship.aporte)

            # Totales
            stats['total_contribution'] += aporte

            # Por categoría
            stats['sponsors_by_category'][categoria] = stats['sponsors_by_category'].get(categoria, 0) + 1
            stats['contribution_by_category'][categoria] = stats['contribution_by_category'].get(categoria, 0) + aporte

            # Min/Max
            stats['highest_contribution'] = max(stats['highest_contribution'], aporte)
            stats['lowest_contribution'] = min(stats['lowest_contribution'], aporte)

        # Promedio
        if stats['total_sponsors'] > 0:
            stats['average_contribution'] = stats['total_contribution'] / stats['total_sponsors']

        return stats

    @handle_repository_errors
    def get_congress_funding_summary(self, db: Session, year: Optional[int] = None) -> List[dict]:
        """
        Obtener resumen de financiamiento por congreso.

        Args:
            year: Filtrar por año específico
        """
        from src.models.congress_model import Congress

        query = (
            select(
                Congress.id_congreso,
                Congress.nombre,
                Congress.anio,
                func.count(CongresoSponsor.id_sponsor).label('total_sponsors'),
                func.sum(CongresoSponsor.aporte).label('total_funding'),
                func.avg(CongresoSponsor.aporte).label('avg_contribution')
            )
            .join(CongresoSponsor, Congress.id_congreso == CongresoSponsor.id_congreso)
        )

        if year is not None:
            query = query.where(Congress.anio == year)

        query = (
            query.group_by(Congress.id_congreso, Congress.nombre, Congress.anio)
            .order_by(func.sum(CongresoSponsor.aporte).desc())
        )

        result = db.exec(query).all()

        return [
            {
                'congress': {
                    'id': r.id_congreso,
                    'nombre': r.nombre,
                    'anio': r.anio
                },
                'total_sponsors': r.total_sponsors,
                'total_funding': float(r.total_funding) if r.total_funding else 0,
                'avg_contribution': float(r.avg_contribution) if r.avg_contribution else 0
            }
            for r in result
        ]

    @handle_repository_errors
    def get_sponsor_loyalty_analysis(self, db: Session, min_sponsorships: int = 2) -> List[dict]:
        """
        Análisis de lealtad de sponsors (sponsors que patrocinan múltiples congresos).
        """
        from src.models.sponsor_model import Sponsor

        query = (
            select(
                Sponsor.id_sponsor,
                Sponsor.nombre,
                func.count(CongresoSponsor.id_congreso).label('total_sponsorships'),
                func.sum(CongresoSponsor.aporte).label('total_contribution'),
                func.avg(CongresoSponsor.aporte).label('avg_contribution')
            )
            .join(CongresoSponsor, Sponsor.id_sponsor == CongresoSponsor.id_sponsor)
            .group_by(Sponsor.id_sponsor, Sponsor.nombre)
            .having(func.count(CongresoSponsor.id_congreso) >= min_sponsorships)
            .order_by(func.count(CongresoSponsor.id_congreso).desc())
        )

        result = db.exec(query).all()

        return [
            {
                'sponsor': {
                    'id': r.id_sponsor,
                    'nombre': r.nombre
                },
                'total_sponsorships': r.total_sponsorships,
                'total_contribution': float(r.total_contribution),
                'avg_contribution': float(r.avg_contribution),
                'loyalty_score': r.total_sponsorships * float(r.avg_contribution)  # Métrica simple de lealtad
            }
            for r in result
        ]

    @handle_repository_errors
    def get_category_trends(self, db: Session, years: Optional[List[int]] = None) -> dict:
        """
        Analizar tendencias por categoría de sponsorship a lo largo de los años.
        """
        from src.models.congress_model import Congress

        query = (
            select(
                Congress.anio,
                CongresoSponsor.categoria,
                func.count(CongresoSponsor.id_sponsor).label('sponsor_count'),
                func.sum(CongresoSponsor.aporte).label('total_contribution')
            )
            .join(Congress, CongresoSponsor.id_congreso == Congress.id_congreso)
        )

        if years:
            query = query.where(Congress.anio.in_(years))

        query = (
            query.group_by(Congress.anio, CongresoSponsor.categoria)
            .order_by(Congress.anio, CongresoSponsor.categoria)
        )

        result = db.exec(query).all()

        # Organizar por año y categoría
        trends = {}
        for r in result:
            year = r.anio
            categoria = r.categoria

            if year not in trends:
                trends[year] = {}

            trends[year][categoria] = {
                'sponsor_count': r.sponsor_count,
                'total_contribution': float(r.total_contribution)
            }

        return trends

    @handle_repository_errors
    def check_sponsorship_exists(
        self,
        db: Session,
        congress_id: int,
        sponsor_id: int
    ) -> bool:
        """
        Verificar si ya existe una relación de sponsorship entre congreso y sponsor.
        """
        query = select(CongresoSponsor).where(
            and_(
                CongresoSponsor.id_congreso == congress_id,
                CongresoSponsor.id_sponsor == sponsor_id
            )
        )

        return db.execute(query).scalar_one_or_none() is not None

    @handle_repository_errors
    def create_sponsorship(
        self,
        db: Session,
        congress_id: int,
        sponsor_id: int,
        categoria: str,
        aporte: Decimal
    ) -> CongresoSponsor:
        """
        Crear una nueva relación de sponsorship.
        """
        sponsorship = CongresoSponsor(
            id_congreso=congress_id,
            id_sponsor=sponsor_id,
            categoria=categoria,
            aporte=aporte
        )

        db.add(sponsorship)
        db.flush()
        db.refresh(sponsorship)

        return sponsorship

    @handle_repository_errors
    def update_sponsorship(
        self,
        db: Session,
        congress_id: int,
        sponsor_id: int,
        categoria: Optional[str] = None,
        aporte: Optional[Decimal] = None
    ) -> Optional[CongresoSponsor]:
        """
        Actualizar una relación de sponsorship existente.
        """
        sponsorship = self.get_sponsorship_with_details(db, congress_id, sponsor_id)

        if not sponsorship:
            return None

        if categoria is not None:
            sponsorship.categoria = categoria

        if aporte is not None:
            sponsorship.aporte = aporte

        db.flush()
        db.refresh(sponsorship)

        return sponsorship

    @handle_repository_errors
    def delete_sponsorship(
        self,
        db: Session,
        congress_id: int,
        sponsor_id: int
    ) -> bool:
        """
        Eliminar una relación de sponsorship.

        Returns:
            bool: True si se eliminó, False si no existía
        """
        query = select(CongresoSponsor).where(
            and_(
                CongresoSponsor.id_congreso == congress_id,
                CongresoSponsor.id_sponsor == sponsor_id
            )
        )

        sponsorship = db.exec(query).scalars().first()

        if sponsorship:
            db.delete(sponsorship)
            db.flush()
            return True

        return False

    @handle_repository_errors
    def get_sponsorship_summary(self, db: Session) -> dict:
        """
        Obtener resumen general de sponsorships.
        """
        total_query = select(func.count()).select_from(CongresoSponsor)
        total_sponsorships = db.exec(total_query).scalar()

        # Contribución total
        total_contribution_query = select(func.sum(CongresoSponsor.aporte)).select_from(CongresoSponsor)
        total_contribution = db.exec(total_contribution_query).scalar() or 0

        # Sponsors únicos
        unique_sponsors_query = select(func.count(func.distinct(CongresoSponsor.id_sponsor))).select_from(CongresoSponsor)
        unique_sponsors = db.exec(unique_sponsors_query).scalar()

        # Congresos con sponsors
        congresses_with_sponsors_query = select(func.count(func.distinct(CongresoSponsor.id_congreso))).select_from(CongresoSponsor)
        congresses_with_sponsors = db.exec(congresses_with_sponsors_query).scalar()

        return {
            'total_sponsorships': total_sponsorships,
            'total_contribution': float(total_contribution),
            'unique_sponsors': unique_sponsors,
            'congresses_with_sponsors': congresses_with_sponsors,
            'average_contribution_per_sponsorship': float(total_contribution) / total_sponsorships if total_sponsorships > 0 else 0
        }


# Instancia única del repositorio
congreso_sponsor_repository = CongresoSponsorRepository()