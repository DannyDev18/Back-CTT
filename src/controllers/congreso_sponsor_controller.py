from typing import List, Optional, Dict, Any
from decimal import Decimal
from fastapi import HTTPException, status as http_status
from sqlalchemy.orm import Session

from .base_controller import BaseController, handle_controller_errors, ControllerUtils
from src.models.congreso_sponsor_model import (
    CongresoSponsor, CongresoSponsorCreate, CongresoSponsorUpdate,
    CongresoSponsorRead, CongresoSponsorWithDetails, CongresoSponsorSummary
)
from src.repositories import congreso_sponsor_repository, congress_repository, sponsor_repository
from src.utils.Helpers.pagination_helper import PaginationHelper


class CongresoSponsorController(BaseController[CongresoSponsor, CongresoSponsorCreate, CongresoSponsorUpdate, CongresoSponsorRead]):
    """
    Controlador para operaciones con CongresoSponsor (Relación Congreso-Sponsor).

    Hereda funcionalidades CRUD básicas del BaseController y agrega
    operaciones específicas para la relación muchos-a-muchos entre congresos y sponsors.
    """

    def __init__(self):
        super().__init__(congreso_sponsor_repository, "CongresoSponsor")

    def serialize_to_dict(self, sponsorship: CongresoSponsor, **kwargs) -> Dict[str, Any]:
        """Serializar sponsorship a diccionario."""
        include_congress = kwargs.get('include_congress', False)
        include_sponsor = kwargs.get('include_sponsor', False)

        sponsorship_dict = {
            "id_congreso": sponsorship.id_congreso,
            "id_sponsor": sponsorship.id_sponsor,
            "categoria": sponsorship.categoria,
            "aporte": float(sponsorship.aporte)
        }

        if include_congress and hasattr(sponsorship, 'congreso') and sponsorship.congreso:
            sponsorship_dict["congress"] = {
                "id_congreso": sponsorship.congreso.id_congreso,
                "nombre": sponsorship.congreso.nombre,
                "edicion": sponsorship.congreso.edicion,
                "anio": sponsorship.congreso.anio,
                "fecha_inicio": sponsorship.congreso.fecha_inicio.isoformat(),
                "fecha_fin": sponsorship.congreso.fecha_fin.isoformat()
            }

        if include_sponsor and hasattr(sponsorship, 'sponsor') and sponsorship.sponsor:
            sponsorship_dict["sponsor"] = {
                "id_sponsor": sponsorship.sponsor.id_sponsor,
                "nombre": sponsorship.sponsor.nombre,
                "logo_url": sponsorship.sponsor.logo_url,
                "sitio_web": sponsorship.sponsor.sitio_web,
                "descripcion": sponsorship.sponsor.descripcion
            }

        return sponsorship_dict

    @handle_controller_errors
    def create_sponsorship(
        self,
        db: Session,
        sponsorship_data: CongresoSponsorCreate,
        current_user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Crear nueva relación de sponsorship."""
        return self.create(db, sponsorship_data, current_user_id)

    @handle_controller_errors
    def get_sponsorship(
        self,
        db: Session,
        congress_id: int,
        sponsor_id: int,
        include_congress: bool = False,
        include_sponsor: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Obtener sponsorship por IDs compuestos."""
        if include_congress or include_sponsor:
            sponsorship = congreso_sponsor_repository.get_sponsorship_with_details(
                db, congress_id, sponsor_id
            )
        else:
            sponsorship = congreso_sponsor_repository.get_sponsorship_with_details(
                db, congress_id, sponsor_id
            )

        if not sponsorship:
            return None

        return self.serialize_to_dict(
            sponsorship,
            include_congress=include_congress,
            include_sponsor=include_sponsor
        )

    @handle_controller_errors
    def get_sponsorships_by_congress(
        self,
        db: Session,
        congress_id: int,
        include_sponsor: bool = True
    ) -> List[Dict[str, Any]]:
        """Obtener todos los sponsorships de un congreso."""
        # Verificar que el congreso existe
        congress = congress_repository.get(db, congress_id)
        if not congress:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Congress not found"
            )

        sponsorships = congreso_sponsor_repository.get_sponsorships_by_congress(
            db, congress_id, include_details=include_sponsor
        )

        return [
            self.serialize_to_dict(
                sponsorship if hasattr(sponsorship, 'id_congreso') else sponsorship[0],
                include_sponsor=include_sponsor,
                include_congress=False
            )
            for sponsorship in sponsorships
        ]

    @handle_controller_errors
    def get_sponsorships_by_sponsor(
        self,
        db: Session,
        sponsor_id: int,
        include_congress: bool = True
    ) -> List[Dict[str, Any]]:
        """Obtener todos los sponsorships de un sponsor."""
        # Verificar que el sponsor existe
        sponsor = sponsor_repository.get(db, sponsor_id)
        if not sponsor:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Sponsor not found"
            )

        sponsorships = congreso_sponsor_repository.get_sponsorships_by_sponsor(
            db, sponsor_id, include_details=include_congress
        )

        return [
            self.serialize_to_dict(
                sponsorship if hasattr(sponsorship, 'id_congreso') else sponsorship[0],
                include_congress=include_congress,
                include_sponsor=False
            )
            for sponsorship in sponsorships
        ]

    @handle_controller_errors
    def get_all_sponsorships(
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
    ) -> Dict[str, Any]:
        """Obtener todos los sponsorships con paginación y filtros."""
        try:
            sponsorships, total = congreso_sponsor_repository.get_sponsorships_paginated(
                db,
                page=page,
                page_size=page_size,
                congress_id=congress_id,
                sponsor_id=sponsor_id,
                categoria=categoria,
                min_aporte=min_aporte,
                max_aporte=max_aporte,
                order_by=order_by,
                order_desc=order_desc
            )

            sponsorships_dict = [
                self.serialize_to_dict(
                    sponsorship if hasattr(sponsorship, 'id_congreso') else sponsorship[0],
                    include_congress=True,
                    include_sponsor=True
                )
                for sponsorship in sponsorships
            ]

            # Construir parámetros extra para paginación
            extra_params = ControllerUtils.sanitize_filters({
                "congress_id": congress_id,
                "sponsor_id": sponsor_id,
                "categoria": categoria,
                "min_aporte": float(min_aporte) if min_aporte else None,
                "max_aporte": float(max_aporte) if max_aporte else None,
                "order_by": order_by,
                "order_desc": order_desc
            })

            return PaginationHelper.build_pagination_response(
                items=sponsorships_dict,
                total=total,
                page=page,
                page_size=page_size,
                base_path="/api/v1/sponsorships",
                items_key="sponsorships",
                extra_params=extra_params
            )

        except Exception as e:
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching sponsorships: {str(e)}"
            )

    @handle_controller_errors
    def get_sponsorships_by_category(
        self,
        db: Session,
        categoria: str,
        congress_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Obtener sponsorships por categoría."""
        sponsorships = congreso_sponsor_repository.get_sponsorships_by_category(
            db, categoria, congress_id, include_details=True
        )

        return [
            self.serialize_to_dict(
                sponsorship if hasattr(sponsorship, 'id_congreso') else sponsorship[0],
                include_congress=congress_id is None,
                include_sponsor=True
            )
            for sponsorship in sponsorships
        ]

    @handle_controller_errors
    def get_top_contributors_by_congress(
        self,
        db: Session,
        congress_id: int,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Obtener top contribuyentes para un congreso."""
        # Verificar que el congreso existe
        congress = congress_repository.get(db, congress_id)
        if not congress:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Congress not found"
            )

        top_contributors = congreso_sponsor_repository.get_top_contributors_by_congress(
            db, congress_id, limit
        )

        return ControllerUtils.build_success_response(
            "Top contributors retrieved successfully",
            data={
                "top_contributors": top_contributors,
                "congress_id": congress_id,
                "limit": limit
            }
        )

    @handle_controller_errors
    def get_sponsorship_statistics_by_congress(
        self,
        db: Session,
        congress_id: int
    ) -> Dict[str, Any]:
        """Obtener estadísticas de sponsorships para un congreso."""
        # Verificar que el congreso existe
        congress = congress_repository.get(db, congress_id)
        if not congress:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Congress not found"
            )

        stats = congreso_sponsor_repository.get_sponsorship_statistics_by_congress(
            db, congress_id
        )

        return ControllerUtils.build_success_response(
            "Sponsorship statistics retrieved successfully",
            data=stats
        )

    @handle_controller_errors
    def get_congress_funding_summary(
        self,
        db: Session,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """Obtener resumen de financiamiento por congreso."""
        funding_summary = congreso_sponsor_repository.get_congress_funding_summary(
            db, year
        )

        return ControllerUtils.build_success_response(
            "Congress funding summary retrieved successfully",
            data={
                "funding_summary": funding_summary,
                "year_filter": year,
                "total_congresses": len(funding_summary)
            }
        )

    @handle_controller_errors
    def get_sponsor_loyalty_analysis(
        self,
        db: Session,
        min_sponsorships: int = 2
    ) -> Dict[str, Any]:
        """Análisis de lealtad de sponsors."""
        loyalty_analysis = congreso_sponsor_repository.get_sponsor_loyalty_analysis(
            db, min_sponsorships
        )

        return ControllerUtils.build_success_response(
            "Sponsor loyalty analysis retrieved successfully",
            data={
                "loyal_sponsors": loyalty_analysis,
                "min_sponsorships": min_sponsorships,
                "total_loyal_sponsors": len(loyalty_analysis)
            }
        )

    @handle_controller_errors
    def get_category_trends(
        self,
        db: Session,
        years: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """Analizar tendencias por categoría de sponsorship."""
        trends = congreso_sponsor_repository.get_category_trends(db, years)

        return ControllerUtils.build_success_response(
            "Category trends analysis retrieved successfully",
            data={
                "trends": trends,
                "years_filter": years,
                "total_years": len(trends)
            }
        )

    @handle_controller_errors
    def update_sponsorship(
        self,
        db: Session,
        congress_id: int,
        sponsor_id: int,
        sponsorship_data: CongresoSponsorUpdate,
        current_user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Actualizar sponsorship."""
        # Verificar que el sponsorship existe
        existing_sponsorship = congreso_sponsor_repository.get_sponsorship_with_details(
            db, congress_id, sponsor_id
        )
        if not existing_sponsorship:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Sponsorship not found"
            )

        # Validaciones personalizadas
        self._validate_before_update(db, existing_sponsorship, sponsorship_data, current_user_id)

        # Actualizar usando el repositorio
        update_data = sponsorship_data.model_dump(exclude_unset=True)
        updated_sponsorship = congreso_sponsor_repository.update_sponsorship(
            db,
            congress_id,
            sponsor_id,
            categoria=update_data.get('categoria'),
            aporte=update_data.get('aporte')
        )

        db.commit()

        if updated_sponsorship:
            db.refresh(updated_sponsorship)
            return self.serialize_to_dict(
                updated_sponsorship,
                include_congress=True,
                include_sponsor=True
            )
        else:
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update sponsorship"
            )

    @handle_controller_errors
    def delete_sponsorship(
        self,
        db: Session,
        congress_id: int,
        sponsor_id: int,
        current_user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Eliminar sponsorship."""
        # Verificar que el sponsorship existe
        existing_sponsorship = congreso_sponsor_repository.get_sponsorship_with_details(
            db, congress_id, sponsor_id
        )
        if not existing_sponsorship:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Sponsorship not found"
            )

        # Validaciones personalizadas
        self._validate_before_delete(db, existing_sponsorship, current_user_id)

        # Eliminar usando el repositorio
        deleted = congreso_sponsor_repository.delete_sponsorship(db, congress_id, sponsor_id)

        if deleted:
            db.commit()
            return {"message": "Sponsorship deleted successfully"}
        else:
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete sponsorship"
            )

    @handle_controller_errors
    def get_sponsorship_summary(self, db: Session) -> Dict[str, Any]:
        """Obtener resumen general de sponsorships."""
        summary = congreso_sponsor_repository.get_sponsorship_summary(db)
        return ControllerUtils.build_success_response(
            "Sponsorship summary retrieved successfully",
            data=summary
        )

    @handle_controller_errors
    def check_sponsorship_exists(
        self,
        db: Session,
        congress_id: int,
        sponsor_id: int
    ) -> Dict[str, Any]:
        """Verificar si existe una relación de sponsorship."""
        exists = congreso_sponsor_repository.check_sponsorship_exists(
            db, congress_id, sponsor_id
        )

        return {
            "exists": exists,
            "message": "Sponsorship exists" if exists else "Sponsorship does not exist"
        }

    @handle_controller_errors
    def bulk_create_sponsorships(
        self,
        db: Session,
        congress_id: int,
        sponsorships_data: List[CongresoSponsorCreate],
        current_user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Crear múltiples sponsorships para un congreso."""
        try:
            # Verificar que el congreso existe
            congress = congress_repository.get(db, congress_id)
            if not congress:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail="Congress not found"
                )

            # Validar que todos los sponsorships sean para el mismo congreso
            invalid_sponsorships = [
                str(s.id_sponsor) for s in sponsorships_data
                if s.id_congreso != congress_id
            ]
            if invalid_sponsorships:
                raise ValueError(f"Some sponsorships are not for congress {congress_id}: {', '.join(invalid_sponsorships)}")

            # Verificar sponsors duplicados en el lote
            sponsor_ids = [s.id_sponsor for s in sponsorships_data]
            if len(sponsor_ids) != len(set(sponsor_ids)):
                raise ValueError("Duplicate sponsor IDs found in the batch")

            # Verificar sponsorships existentes
            existing_sponsors = []
            for sponsorship_data in sponsorships_data:
                if congreso_sponsor_repository.check_sponsorship_exists(
                    db, congress_id, sponsorship_data.id_sponsor
                ):
                    existing_sponsors.append(str(sponsorship_data.id_sponsor))

            if existing_sponsors:
                raise ValueError(f"The following sponsors already have sponsorships for this congress: {', '.join(existing_sponsors)}")

            # Verificar que todos los sponsors existen
            for sponsorship_data in sponsorships_data:
                sponsor = sponsor_repository.get(db, sponsorship_data.id_sponsor)
                if not sponsor:
                    raise ValueError(f"Sponsor with ID {sponsorship_data.id_sponsor} does not exist")

            # Crear sponsorships en lote
            created_sponsorships = []
            for sponsorship_data in sponsorships_data:
                sponsorship = congreso_sponsor_repository.create_sponsorship(
                    db,
                    congress_id=sponsorship_data.id_congreso,
                    sponsor_id=sponsorship_data.id_sponsor,
                    categoria=sponsorship_data.categoria,
                    aporte=sponsorship_data.aporte
                )
                created_sponsorships.append(sponsorship)

            db.commit()

            # Actualizar objetos
            for sponsorship in created_sponsorships:
                db.refresh(sponsorship)

            sponsorships_dict = [
                self.serialize_to_dict(sponsorship, include_sponsor=True)
                for sponsorship in created_sponsorships
            ]

            return ControllerUtils.build_success_response(
                f"Successfully created {len(created_sponsorships)} sponsorships for congress {congress_id}",
                data={
                    "created_sponsorships": sponsorships_dict,
                    "count": len(created_sponsorships),
                    "congress_id": congress_id
                }
            )

        except HTTPException:
            db.rollback()
            raise
        except ValueError as e:
            db.rollback()
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating sponsorships: {str(e)}"
            )

    # Validaciones personalizadas
    def _validate_before_create(
        self,
        db: Session,
        obj_in: CongresoSponsorCreate,
        current_user_id: Optional[int]
    ) -> None:
        """Validaciones antes de crear sponsorship."""
        # Verificar que el congreso existe
        congress = congress_repository.get(db, obj_in.id_congreso)
        if not congress:
            raise ValueError(f"Congress with ID {obj_in.id_congreso} does not exist")

        # Verificar que el sponsor existe
        sponsor = sponsor_repository.get(db, obj_in.id_sponsor)
        if not sponsor:
            raise ValueError(f"Sponsor with ID {obj_in.id_sponsor} does not exist")

        # Verificar que no existe ya la relación
        if congreso_sponsor_repository.check_sponsorship_exists(
            db, obj_in.id_congreso, obj_in.id_sponsor
        ):
            raise ValueError(f"Sponsorship already exists between congress {obj_in.id_congreso} and sponsor {obj_in.id_sponsor}")

    def _validate_before_update(
        self,
        db: Session,
        db_obj: CongresoSponsor,
        obj_in: CongresoSponsorUpdate,
        current_user_id: Optional[int]
    ) -> None:
        """Validaciones antes de actualizar sponsorship."""
        # No hay validaciones específicas para actualización ya que
        # no se pueden cambiar las claves primarias (congreso y sponsor)
        pass

    def _validate_before_delete(
        self,
        db: Session,
        db_obj: CongresoSponsor,
        current_user_id: Optional[int]
    ) -> None:
        """Validaciones antes de eliminar sponsorship."""
        # Verificar si hay dependencias que requieren el sponsorship
        # Por ahora no hay validaciones específicas, pero se podría agregar
        # lógica para verificar si el sponsorship está siendo utilizado
        # en otros contextos (reportes, análisis históricos, etc.)
        pass


# Instancia única del controlador
congreso_sponsor_controller = CongresoSponsorController()