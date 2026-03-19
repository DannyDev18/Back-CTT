from typing import List, Optional, Dict, Any
from fastapi import HTTPException
from fastapi import status as http_status
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from src.models.congress import (
    Congress,
    CongressCreate,
    CongressUpdate,
    CongressRequirementCreate,
    CongressRequirementUpdate,
    CongressContentCreate,
    CongressStatus,
)
from src.utils.serializers.general_serializer import GeneralSerializer
from src.utils.serializers.congress_serializer import CongressSerializer
from src.repositories.congress_repository import CongressRepository
from src.utils.Helpers.pagination_helper import PaginationHelper
from src.repositories.categories_repository import CategoryRepository


class CongressController:

    @staticmethod
    def create_congress_with_requirements(
        congress_data: CongressCreate,
        requirements_data: CongressRequirementCreate,
        contents_data: List[CongressContentCreate],
        db: Session,
        current_user_id: int
    ) -> Dict[str, Any]:
        """Crea un congreso completo con requisitos y contenidos"""
        category = CategoryRepository.get_by_id(db, congress_data.category_id)
        if not category:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )

        congress = Congress(
            title=congress_data.title,
            description=congress_data.description,
            place=congress_data.place,
            congress_image=congress_data.congress_image,
            congress_image_detail=congress_data.congress_image_detail,
            category_id=congress_data.category_id,
            status=congress_data.status,
            objectives=GeneralSerializer.serialize_json_field(congress_data.objectives),
            organizers=GeneralSerializer.serialize_json_field(congress_data.organizers),
            materials=GeneralSerializer.serialize_json_field(congress_data.materials),
            target_audience=GeneralSerializer.serialize_json_field(congress_data.target_audience)
        )
        db.add(congress)
        db.flush()

        requirement = CongressRepository.create_congress_requirements(
            congress.id, requirements_data, db
        )

        contents = CongressRepository.create_congress_contents(
            congress.id, contents_data, db
        )

        db.commit()
        db.refresh(congress)

        return CongressSerializer.congress_to_dict(congress, requirement, contents)

    @staticmethod
    def get_all_congresses(
        db: Session,
        page: int = 1,
        page_size: int = 10,
        status: CongressStatus = CongressStatus.ACTIVO,
        category_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Obtiene todos los congresos con paginación"""
        if category_id is not None:
            category = CategoryRepository.get_by_id(db, category_id)
            if not category:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail="Category not found"
                )

        congresses, total = CongressRepository.get_congresses_paginated(
            db, page, page_size, status, category_id
        )

        congresses_dict = [
            CongressSerializer.congress_to_dict(
                congress,
                congress.requirement,
                congress.contents,
                include_category=True
            )
            for congress in congresses
        ]

        return PaginationHelper.build_pagination_response(
            items=congresses_dict,
            total=total,
            page=page,
            page_size=page_size,
            base_path="/api/v1/congresses",
            items_key="congresses",
            extra_params={"status": status.value, **({"category_id": category_id} if category_id else {})}
        )

    @staticmethod
    def get_congress_by_id(congress_id: int, db: Session) -> Optional[Dict[str, Any]]:
        """Obtiene un congreso por ID con todos sus datos"""
        congress = CongressRepository.get_congress_with_relations(congress_id, db)
        if not congress:
            return None

        return CongressSerializer.congress_to_dict(
            congress,
            congress.requirement,
            congress.contents,
            include_category=True
        )

    @staticmethod
    def get_congresses_by_category(category_id: int, db: Session) -> List[Dict[str, Any]]:
        """Obtiene congresos por categoría"""
        category = CategoryRepository.get_by_id(db, category_id)
        if not category:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Categoría no encontrada"
            )

        statement = (
            select(Congress)
            .where(Congress.category_id == category_id)
            .options(
                selectinload(Congress.requirement),
                selectinload(Congress.contents),
                selectinload(Congress.category_rel)
            )
        )
        congresses = db.exec(statement).all()

        return [
            CongressSerializer.congress_to_dict(
                congress,
                congress.requirement,
                congress.contents,
                include_category=True
            )
            for congress in congresses
        ]

    @staticmethod
    def search_congresses_by_title(search_term: str, db: Session) -> List[Dict[str, Any]]:
        """Busca congresos por título (case-insensitive)"""
        congresses = CongressRepository.search_congresses_by_title(db, search_term)

        return [
            CongressSerializer.congress_to_dict(
                congress,
                congress.requirement,
                congress.contents,
                include_category=True
            )
            for congress in congresses
        ]

    @staticmethod
    def update_congress_with_requirements(
        congress_id: int,
        db: Session,
        congress_data: Optional[CongressUpdate] = None,
        requirements_data: Optional[CongressRequirementUpdate] = None,
        contents_data: Optional[List[CongressContentCreate]] = None
    ) -> Dict[str, Any]:
        """Actualiza un congreso y sus relaciones"""
        congress = CongressRepository.get_congress_with_relations(congress_id, db)
        if not congress:
            raise ValueError("Congress not found")

        if congress_data:
            update_dict = congress_data.model_dump(exclude_unset=True)
            if 'category_id' in update_dict:
                category = CategoryRepository.get_by_id(db, update_dict['category_id'])
                if not category:
                    raise HTTPException(
                        status_code=http_status.HTTP_404_NOT_FOUND,
                        detail="Category not found"
                    )
            for key, value in update_dict.items():
                if key in ['objectives', 'organizers', 'materials', 'target_audience']:
                    setattr(congress, key, GeneralSerializer.serialize_json_field(value))
                else:
                    setattr(congress, key, value)

        if requirements_data and congress.requirement:
            update_dict = requirements_data.model_dump(exclude_unset=True)
            for key, value in update_dict.items():
                if key in ['days', 'prerequisites', 'prices']:
                    setattr(congress.requirement, key, GeneralSerializer.serialize_json_field(value))
                else:
                    setattr(congress.requirement, key, value)

        if contents_data is not None:
            CongressRepository.delete_congress_contents(congress_id, db)
            db.flush()
            contents = CongressRepository.create_congress_contents(congress_id, contents_data, db)
        else:
            contents = congress.contents

        db.commit()
        db.refresh(congress)

        return CongressSerializer.congress_to_dict(
            congress,
            congress.requirement,
            contents,
            include_category=True
        )

    @staticmethod
    def delete_congress(congress_id: int, db: Session) -> None:
        """Soft delete: marca el congreso como inactivo"""
        congress = CongressRepository.get_congress_with_relations(congress_id, db)
        if not congress:
            raise ValueError("Congress not found")
        if congress.status == CongressStatus.INACTIVO:
            raise ValueError("Congress is already deleted")

        congress.status = CongressStatus.INACTIVO
        db.commit()
