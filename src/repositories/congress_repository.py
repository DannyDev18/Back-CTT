from sqlmodel import Session, select
from typing import List, Optional, Tuple
from sqlalchemy.orm import selectinload
from src.models.congress import (
    Congress,
    CongressRequirement,
    CongressContent,
    CongressRequirementCreate,
    CongressContentCreate,
    CongressStatus,
)
from src.utils.serializers.general_serializer import GeneralSerializer


class CongressRepository:
    """Maneja las operaciones de base de datos para Congresos"""

    @staticmethod
    def get_congress_with_relations(congress_id: int, db: Session) -> Optional[Congress]:
        """Obtiene un congreso con todas sus relaciones cargadas (evita N+1)"""
        statement = (
            select(Congress)
            .where(Congress.id == congress_id)
            .options(
                selectinload(Congress.requirement),
                selectinload(Congress.contents),
                selectinload(Congress.category_rel)
            )
        )
        return db.exec(statement).first()

    @staticmethod
    def get_congresses_paginated(
        db: Session,
        page: int,
        page_size: int,
        status: CongressStatus,
        category_id: Optional[int] = None
    ) -> Tuple[List[Congress], int]:
        """Obtiene congresos paginados con todas sus relaciones (evita N+1)"""
        from sqlalchemy import func

        statement = (
            select(Congress)
            .where(Congress.status == status)
            .options(
                selectinload(Congress.requirement),
                selectinload(Congress.contents),
                selectinload(Congress.category_rel)
            )
        )

        count_statement = (
            select(func.count())
            .select_from(Congress)
            .where(Congress.status == status)
        )

        if category_id is not None:
            statement = statement.where(Congress.category_id == category_id)
            count_statement = count_statement.where(Congress.category_id == category_id)

        statement = statement.order_by(Congress.id)

        total = db.exec(count_statement).one()

        offset = (page - 1) * page_size
        congresses = db.exec(statement.offset(offset).limit(page_size)).all()

        return congresses, total

    @staticmethod
    def search_congresses_by_title(
        db: Session,
        search_term: str,
        status: CongressStatus = CongressStatus.ACTIVO
    ) -> List[Congress]:
        """Busca congresos por título (case-insensitive)"""
        statement = (
            select(Congress)
            .where(
                Congress.status == status,
                Congress.title.ilike(f"%{search_term}%")
            )
            .options(
                selectinload(Congress.requirement),
                selectinload(Congress.contents),
                selectinload(Congress.category_rel)
            )
            .order_by(Congress.title)
        )
        return db.exec(statement).all()

    @staticmethod
    def create_congress_requirements(
        congress_id: int,
        requirements_data: CongressRequirementCreate,
        db: Session
    ) -> CongressRequirement:
        """Crea los requisitos de un congreso"""
        requirement = CongressRequirement(
            congress_id=congress_id,
            start_date_registration=requirements_data.start_date_registration,
            end_date_registration=requirements_data.end_date_registration,
            start_date_congress=requirements_data.start_date_congress,
            end_date_congress=requirements_data.end_date_congress,
            days=GeneralSerializer.serialize_json_field(requirements_data.days),
            start_time=requirements_data.start_time,
            end_time=requirements_data.end_time,
            location=requirements_data.location,
            min_quota=requirements_data.min_quota,
            max_quota=requirements_data.max_quota,
            in_person_hours=requirements_data.in_person_hours,
            autonomous_hours=requirements_data.autonomous_hours,
            modality=requirements_data.modality,
            certification=requirements_data.certification,
            prerequisites=GeneralSerializer.serialize_json_field(requirements_data.prerequisites),
            prices=GeneralSerializer.serialize_json_field(requirements_data.prices)
        )
        db.add(requirement)
        return requirement

    @staticmethod
    def create_congress_contents(
        congress_id: int,
        contents_data: List[CongressContentCreate],
        db: Session
    ) -> List[CongressContent]:
        """Crea los contenidos de un congreso"""
        contents = []
        for content_data in contents_data:
            content = CongressContent(
                congress_id=congress_id,
                unit=content_data.unit,
                title=content_data.title,
                topics=GeneralSerializer.serialize_json_field(
                    [{"unit": t.unit, "title": t.title} for t in content_data.topics]
                )
            )
            db.add(content)
            contents.append(content)
        return contents

    @staticmethod
    def delete_congress_contents(congress_id: int, db: Session) -> None:
        """Elimina todos los contenidos de un congreso"""
        contents = db.exec(
            select(CongressContent).where(CongressContent.congress_id == congress_id)
        ).all()
        for content in contents:
            db.delete(content)
