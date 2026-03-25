from typing import List, Optional, Tuple
from sqlmodel import Session
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from decimal import Decimal

from .base_repository import BaseRepository, handle_repository_errors
from src.models.sponsor_model import Sponsor, SponsorCreate, SponsorUpdate, SponsorRead
from src.models.congreso_sponsor_model import CongresoSponsor
from src.models.congress_model import Congress


class SponsorRepository(BaseRepository[Sponsor, SponsorCreate, SponsorUpdate]):
    """
    Repositorio para operaciones con Sponsor (Patrocinadores).

    Hereda operaciones CRUD básicas del BaseRepository y agrega
    operaciones específicas para sponsors.
    """

    def __init__(self):
        super().__init__(Sponsor)

    @handle_repository_errors
    def get_sponsor_with_congresses(self, db: Session, sponsor_id: int) -> Optional[Sponsor]:
        """
        Obtener un sponsor con todos sus congresos asociados.
        """
        query = (
            select(Sponsor)
            .where(Sponsor.id_sponsor == sponsor_id)
            .options(
                selectinload(Sponsor.congreso_sponsors).selectinload(CongresoSponsor.congreso)
            )
        )
        return db.exec(query).scalars().first()

    @handle_repository_errors
    def get_sponsors_paginated(
        self,
        db: Session,
        page: int = 1,
        page_size: int = 10,
        search_term: Optional[str] = None,
        has_active_sponsorship: Optional[bool] = None,
        order_by: str = "nombre",
        order_desc: bool = False
    ) -> Tuple[List[Sponsor], int]:
        """
        Obtener sponsors paginados con filtros.

        Args:
            search_term: Buscar en nombre y descripción
            has_active_sponsorship: Filtrar por sponsors con sponsorships activos
        """
        # Query base
        query = select(Sponsor)
        count_query = select(func.count()).select_from(Sponsor)

        # Aplicar filtros
        conditions = []

        if search_term:
            search_conditions = or_(
                Sponsor.nombre.ilike(f"%{search_term}%"),
                Sponsor.descripcion.ilike(f"%{search_term}%")
            )
            conditions.append(search_conditions)

        if has_active_sponsorship is not None:
            if has_active_sponsorship:
                # Sponsors que tienen al menos un sponsorship
                sponsorship_exists = (
                    select(CongresoSponsor.id_sponsor)
                    .where(CongresoSponsor.id_sponsor == Sponsor.id_sponsor)
                )
                conditions.append(sponsorship_exists.exists())
            else:
                # Sponsors que no tienen sponsorships
                sponsorship_exists = (
                    select(CongresoSponsor.id_sponsor)
                    .where(CongresoSponsor.id_sponsor == Sponsor.id_sponsor)
                )
                conditions.append(~sponsorship_exists.exists())

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        # Contar total
        total = db.exec(count_query).scalar()

        # Aplicar ordenamiento
        if hasattr(Sponsor, order_by):
            order_column = getattr(Sponsor, order_by)
            if order_desc:
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())

        # Aplicar paginación
        offset = (page - 1) * page_size
        sponsors = db.exec(query.offset(offset).limit(page_size)).all()

        return sponsors, total

    @handle_repository_errors
    def search_sponsors_by_name(
        self,
        db: Session,
        search_term: str,
        limit: int = 20
    ) -> List[Sponsor]:
        """
        Buscar sponsors por nombre (case-insensitive).
        """
        query = select(Sponsor).where(
            Sponsor.nombre.ilike(f"%{search_term}%")
        ).order_by(Sponsor.nombre).limit(limit)

        return db.exec(query).all()

    @handle_repository_errors
    def get_sponsor_by_name(self, db: Session, nombre: str) -> Optional[Sponsor]:
        """
        Obtener sponsor por nombre exacto.
        """
        query = select(Sponsor).where(Sponsor.nombre == nombre)
        return db.exec(query).first()

    @handle_repository_errors
    def check_name_exists(self, db: Session, nombre: str, exclude_id: Optional[int] = None) -> bool:
        """
        Verificar si ya existe un sponsor con el mismo nombre.

        Args:
            exclude_id: ID a excluir de la verificación (para actualizaciones)
        """
        query = select(Sponsor).where(Sponsor.nombre == nombre)

        if exclude_id is not None:
            query = query.where(Sponsor.id_sponsor != exclude_id)

        return db.exec(query).first() is not None

    @handle_repository_errors
    def get_sponsors_by_website_domain(self, db: Session, domain: str) -> List[Sponsor]:
        """
        Obtener sponsors por dominio de sitio web.

        Args:
            domain: Dominio a buscar (ej: "example.com")
        """
        query = select(Sponsor).where(
            Sponsor.sitio_web.ilike(f"%{domain}%")
        ).order_by(Sponsor.nombre)

        return db.exec(query).all()

    @handle_repository_errors
    def get_top_sponsors_by_total_contribution(
        self,
        db: Session,
        limit: int = 10,
        year: Optional[int] = None
    ) -> List[dict]:
        """
        Obtener top sponsors por contribución total.

        Returns:
            List[dict]: Lista con sponsor info y contribución total
        """
        from src.models.congress_model import Congress

        # Query base para obtener sponsors con sus contribuciones
        query = (
            select(
                Sponsor.id_sponsor,
                Sponsor.nombre,
                func.sum(CongresoSponsor.aporte).label('total_contribution'),
                func.count(CongresoSponsor.id_congreso).label('total_sponsorships')
            )
            .join(CongresoSponsor, Sponsor.id_sponsor == CongresoSponsor.id_sponsor)
        )

        # Filtrar por año si se especifica
        if year is not None:
            query = query.join(Congress, CongresoSponsor.id_congreso == Congress.id_congreso)
            query = query.where(Congress.anio == year)

        # Agrupar, ordenar y limitar
        query = (
            query.group_by(Sponsor.id_sponsor, Sponsor.nombre)
            .order_by(func.sum(CongresoSponsor.aporte).desc())
            .limit(limit)
        )

        result = db.exec(query).all()

        return [
            {
                'id_sponsor': r.id_sponsor,
                'nombre': r.nombre,
                'total_contribution': float(r.total_contribution),
                'total_sponsorships': r.total_sponsorships
            }
            for r in result
        ]

    @handle_repository_errors
    def get_sponsor_statistics(self, db: Session, sponsor_id: int) -> dict:
        """
        Obtener estadísticas de un sponsor.

        Returns:
            dict: Estadísticas del sponsor
        """
        # Obtener sponsor con sus sponsorships
        sponsor = self.get_sponsor_with_congresses(db, sponsor_id)

        if not sponsor:
            return {}

        stats = {
            'total_sponsorships': len(sponsor.congreso_sponsors),
            'total_contribution': 0,
            'contribution_by_category': {},
            'congresses_sponsored': [],
            'years_active': set()
        }

        # Calcular estadísticas
        for congreso_sponsor in sponsor.congreso_sponsors:
            congress = congreso_sponsor.congreso
            categoria = congreso_sponsor.categoria
            aporte = float(congreso_sponsor.aporte)

            stats['total_contribution'] += aporte
            stats['contribution_by_category'][categoria] = stats['contribution_by_category'].get(categoria, 0) + aporte
            stats['congresses_sponsored'].append({
                'nombre': congress.nombre,
                'anio': congress.anio,
                'categoria': categoria,
                'aporte': aporte
            })
            stats['years_active'].add(congress.anio)

        # Convertir set a lista ordenada
        stats['years_active'] = sorted(list(stats['years_active']), reverse=True)

        return stats

    @handle_repository_errors
    def get_sponsors_without_recent_activity(
        self,
        db: Session,
        years_threshold: int = 2
    ) -> List[Sponsor]:
        """
        Obtener sponsors que no han tenido actividad reciente.

        Args:
            years_threshold: Umbral de años sin actividad
        """
        from src.models.congress_model import Congress
        from datetime import datetime

        current_year = datetime.now().year
        cutoff_year = current_year - years_threshold

        # Subquery para sponsors con actividad reciente
        recent_sponsors = (
            select(CongresoSponsor.id_sponsor)
            .join(Congress, CongresoSponsor.id_congreso == Congress.id_congreso)
            .where(Congress.anio > cutoff_year)
        )

        # Sponsors que NO están en la lista de recientes
        query = select(Sponsor).where(
            ~Sponsor.id_sponsor.in_(recent_sponsors)
        ).order_by(Sponsor.nombre)

        return db.exec(query).all()

    @handle_repository_errors
    def get_sponsor_summary(self, db: Session) -> dict:
        """
        Obtener resumen general de sponsors.
        """
        total_query = select(func.count()).select_from(Sponsor)
        total_sponsors = db.exec(total_query).scalar()

        # Sponsors activos (con al menos un sponsorship)
        active_sponsors_query = (
            select(func.count(func.distinct(CongresoSponsor.id_sponsor)))
            .select_from(CongresoSponsor)
        )
        active_sponsors = db.exec(active_sponsors_query).scalar()

        # Contribución total
        total_contribution_query = select(func.sum(CongresoSponsor.aporte)).select_from(CongresoSponsor)
        total_contribution = db.exec(total_contribution_query).scalar() or 0

        return {
            'total_sponsors': total_sponsors,
            'active_sponsors': active_sponsors,
            'inactive_sponsors': total_sponsors - active_sponsors,
            'total_contribution': float(total_contribution)
        }


# Instancia única del repositorio
sponsor_repository = SponsorRepository()