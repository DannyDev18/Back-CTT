from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status as http_status
from sqlalchemy.orm import Session

from .base_controller import BaseController, handle_controller_errors, ControllerUtils
from src.models.sponsor_model import Sponsor, SponsorCreate, SponsorUpdate, SponsorRead
from src.repositories import sponsor_repository
from src.utils.Helpers.pagination_helper import PaginationHelper


class SponsorController(BaseController[Sponsor, SponsorCreate, SponsorUpdate, SponsorRead]):
    """
    Controlador para operaciones con Sponsor (Patrocinadores).

    Hereda funcionalidades CRUD básicas del BaseController y agrega
    operaciones específicas para sponsors.
    """

    def __init__(self):
        super().__init__(sponsor_repository, "Sponsor")

    def serialize_to_dict(self, sponsor: Sponsor, **kwargs) -> Dict[str, Any]:
        """Serializar sponsor a diccionario."""
        include_congresses = kwargs.get('include_congresses', False)

        # Handle both Sponsor instances and Row objects
        if hasattr(sponsor, 'id_sponsor'):
            sponsor_obj = sponsor
        else:
            # If it's a Row object, extract the Sponsor instance (first element of the tuple)
            sponsor_obj = sponsor[0]

        sponsor_dict = {
            "id_sponsor": sponsor_obj.id_sponsor,
            "nombre": sponsor_obj.nombre,
            "logo_url": sponsor_obj.logo_url,
            "sitio_web": sponsor_obj.sitio_web,
            "descripcion": sponsor_obj.descripcion
        }

        if include_congresses and hasattr(sponsor_obj, 'congreso_sponsors') and sponsor_obj.congreso_sponsors:
            sponsor_dict["sponsorships"] = [
                {
                    "congress_id": cs.id_congreso,
                    "congress_name": cs.congreso.nombre if cs.congreso else "Unknown",
                    "congress_year": cs.congreso.anio if cs.congreso else None,
                    "categoria": cs.categoria,
                    "aporte": float(cs.aporte)
                }
                for cs in sponsor_obj.congreso_sponsors
            ]

            # Agregar estadísticas resumidas
            sponsor_dict["total_sponsorships"] = len(sponsor_obj.congreso_sponsors)
            sponsor_dict["total_contribution"] = sum(
                float(cs.aporte) for cs in sponsor_obj.congreso_sponsors
            )

        return sponsor_dict

    @handle_controller_errors
    def create_sponsor(
        self,
        db: Session,
        sponsor_data: SponsorCreate,
        current_user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Crear nuevo sponsor."""
        return self.create(db, sponsor_data, current_user_id)

    @handle_controller_errors
    def get_sponsor_by_id(
        self,
        db: Session,
        sponsor_id: int,
        include_congresses: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Obtener sponsor por ID."""
        if include_congresses:
            sponsor = sponsor_repository.get_sponsor_with_congresses(db, sponsor_id)
        else:
            sponsor = sponsor_repository.get(db, sponsor_id)

        if not sponsor:
            return None

        return self.serialize_to_dict(sponsor, include_congresses=include_congresses)

    @handle_controller_errors
    def get_all_sponsors(
        self,
        db: Session,
        page: int = 1,
        page_size: int = 10,
        search_term: Optional[str] = None,
        has_active_sponsorship: Optional[bool] = None,
        order_by: str = "nombre",
        order_desc: bool = False
    ) -> Dict[str, Any]:
        """Obtener todos los sponsors con paginación y filtros."""
        try:
            sponsors, total = sponsor_repository.get_sponsors_paginated(
                db,
                page=page,
                page_size=page_size,
                search_term=search_term,
                has_active_sponsorship=has_active_sponsorship,
                order_by=order_by,
                order_desc=order_desc
            )

            sponsors_dict = [
                self.serialize_to_dict(sponsor if hasattr(sponsor, 'id_sponsor') else sponsor[0])
                for sponsor in sponsors
            ]

            # Construir parámetros extra para paginación
            extra_params = ControllerUtils.sanitize_filters({
                "search_term": search_term,
                "has_active_sponsorship": has_active_sponsorship,
                "order_by": order_by,
                "order_desc": order_desc
            })

            return PaginationHelper.build_pagination_response(
                items=sponsors_dict,
                total=total,
                page=page,
                page_size=page_size,
                base_path="/api/v1/sponsors",
                items_key="sponsors",
                extra_params=extra_params
            )

        except Exception as e:
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching sponsors: {str(e)}"
            )

    @handle_controller_errors
    def search_sponsors_by_name(
        self,
        db: Session,
        search_term: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Buscar sponsors por nombre."""
        sponsors = sponsor_repository.search_sponsors_by_name(db, search_term, limit)
        return [self.serialize_to_dict(sponsor if hasattr(sponsor, 'id_sponsor') else sponsor[0]) for sponsor in sponsors]

    @handle_controller_errors
    def get_sponsors_by_website_domain(
        self,
        db: Session,
        domain: str
    ) -> List[Dict[str, Any]]:
        """Obtener sponsors por dominio de sitio web."""
        sponsors = sponsor_repository.get_sponsors_by_website_domain(db, domain)
        return [self.serialize_to_dict(sponsor if hasattr(sponsor, 'id_sponsor') else sponsor[0]) for sponsor in sponsors]

    @handle_controller_errors
    def get_top_sponsors_by_contribution(
        self,
        db: Session,
        limit: int = 10,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """Obtener top sponsors por contribución total."""
        top_sponsors = sponsor_repository.get_top_sponsors_by_total_contribution(
            db, limit=limit, year=year
        )

        return ControllerUtils.build_success_response(
            "Top sponsors retrieved successfully",
            data={
                "top_sponsors": top_sponsors,
                "criteria": {
                    "limit": limit,
                    "year": year,
                    "metric": "total_contribution"
                }
            }
        )

    @handle_controller_errors
    def get_sponsors_without_recent_activity(
        self,
        db: Session,
        years_threshold: int = 2
    ) -> Dict[str, Any]:
        """Obtener sponsors sin actividad reciente."""
        inactive_sponsors = sponsor_repository.get_sponsors_without_recent_activity(
            db, years_threshold
        )

        sponsors_dict = [
            self.serialize_to_dict(sponsor if hasattr(sponsor, 'id_sponsor') else sponsor[0])
            for sponsor in inactive_sponsors
        ]

        return ControllerUtils.build_success_response(
            f"Inactive sponsors (>{years_threshold} years) retrieved successfully",
            data={
                "inactive_sponsors": sponsors_dict,
                "count": len(sponsors_dict),
                "years_threshold": years_threshold
            }
        )

    @handle_controller_errors
    def update_sponsor(
        self,
        db: Session,
        sponsor_id: int,
        sponsor_data: SponsorUpdate,
        current_user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Actualizar sponsor."""
        return self.update(db, sponsor_id, sponsor_data, current_user_id)

    @handle_controller_errors
    def delete_sponsor(
        self,
        db: Session,
        sponsor_id: int,
        current_user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Eliminar sponsor."""
        return self.delete(db, sponsor_id, current_user_id)

    @handle_controller_errors
    def get_sponsor_statistics(self, db: Session, sponsor_id: int) -> Dict[str, Any]:
        """Obtener estadísticas detalladas de un sponsor."""
        # Verificar que el sponsor existe
        sponsor = sponsor_repository.get(db, sponsor_id)
        if not sponsor:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Sponsor not found"
            )

        stats = sponsor_repository.get_sponsor_statistics(db, sponsor_id)
        return ControllerUtils.build_success_response(
            "Sponsor statistics retrieved successfully",
            data=stats
        )

    @handle_controller_errors
    def get_sponsor_summary(self, db: Session) -> Dict[str, Any]:
        """Obtener resumen general de sponsors."""
        summary = sponsor_repository.get_sponsor_summary(db)
        return ControllerUtils.build_success_response(
            "Sponsor summary retrieved successfully",
            data=summary
        )

    @handle_controller_errors
    def check_name_availability(
        self,
        db: Session,
        nombre: str,
        exclude_sponsor_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Verificar disponibilidad de nombre."""
        exists = sponsor_repository.check_name_exists(db, nombre, exclude_sponsor_id)

        return {
            "available": not exists,
            "message": "Name is available" if not exists else "Name already exists"
        }

    @handle_controller_errors
    def bulk_import_sponsors(
        self,
        db: Session,
        sponsors_data: List[SponsorCreate],
        current_user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Importar múltiples sponsors en lote."""
        try:
            # Validar que no haya nombres duplicados en el lote
            names = [sponsor.nombre for sponsor in sponsors_data]
            if len(names) != len(set(names)):
                raise ValueError("Duplicate names found in the batch")

            # Verificar nombres existentes en BD
            existing_names = []
            for sponsor_data in sponsors_data:
                if sponsor_repository.check_name_exists(db, sponsor_data.nombre):
                    existing_names.append(sponsor_data.nombre)

            if existing_names:
                raise ValueError(f"The following sponsor names already exist: {', '.join(existing_names)}")

            # Crear sponsors en lote
            sponsors = sponsor_repository.bulk_create(db, objs_in=sponsors_data)
            db.commit()

            # Actualizar objetos
            for sponsor in sponsors:
                db.refresh(sponsor)

            sponsors_dict = [
                self.serialize_to_dict(sponsor if hasattr(sponsor, 'id_sponsor') else sponsor[0])
                for sponsor in sponsors
            ]

            return ControllerUtils.build_success_response(
                f"Successfully imported {len(sponsors)} sponsors",
                data={
                    "imported_sponsors": sponsors_dict,
                    "count": len(sponsors)
                }
            )

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
                detail=f"Error importing sponsors: {str(e)}"
            )

    # Validaciones personalizadas
    def _validate_before_create(
        self,
        db: Session,
        obj_in: SponsorCreate,
        current_user_id: Optional[int]
    ) -> None:
        """Validaciones antes de crear sponsor."""
        # Verificar que el nombre no existe
        if sponsor_repository.check_name_exists(db, obj_in.nombre):
            raise ValueError(f"Sponsor with name '{obj_in.nombre}' already exists")

    def _validate_before_update(
        self,
        db: Session,
        db_obj: Sponsor,
        obj_in: SponsorUpdate,
        current_user_id: Optional[int]
    ) -> None:
        """Validaciones antes de actualizar sponsor."""
        update_data = obj_in.model_dump(exclude_unset=True)

        # Si se actualiza el nombre, verificar disponibilidad
        if 'nombre' in update_data:
            new_name = update_data['nombre']
            if new_name != db_obj.nombre:
                if sponsor_repository.check_name_exists(
                    db, new_name, exclude_id=db_obj.id_sponsor
                ):
                    raise ValueError(f"Sponsor with name '{new_name}' already exists")

    def _validate_before_delete(
        self,
        db: Session,
        db_obj: Sponsor,
        current_user_id: Optional[int]
    ) -> None:
        """Validaciones antes de eliminar sponsor."""
        # Verificar si el sponsor tiene sponsorships activos
        sponsor_with_relations = sponsor_repository.get_sponsor_with_congresses(
            db, db_obj.id_sponsor
        )

        if sponsor_with_relations and sponsor_with_relations.congreso_sponsors:
            active_sponsorships = len(sponsor_with_relations.congreso_sponsors)
            raise ValueError(
                f"Cannot delete sponsor: has {active_sponsorships} active sponsorship(s). "
                "Remove sponsorships first."
            )


# Instancia única del controlador
sponsor_controller = SponsorController()