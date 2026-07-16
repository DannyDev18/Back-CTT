from typing import List, Optional, Dict, Any
from datetime import date
from fastapi import HTTPException, status as http_status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .base_controller import BaseController, handle_controller_errors, ControllerUtils
from src.models.congress_model import (
    Congress, CongressCreate, CongressUpdate, CongressRead,
    CongressLegacyCreate, CongressLegacyUpdate, CongressLegacyRead
)
from src.models.congreso_sponsor_model import CongresoSponsor, CongresoSponsorNested
from src.models.sesion_cronograma_model import SesionCronograma, SesionCronogramaNested
from src.models.sponsor_model import Sponsor
from src.models.speaker_model import Speaker
from src.repositories import congress_repository
from src.repositories.congreso_sponsor_repository import congreso_sponsor_repository
from src.repositories.sesion_cronograma_repository import sesion_cronograma_repository
from src.repositories.speaker_repository import speaker_repository
from src.repositories.enrollment_repository import EnrollmentRepository
from src.utils.Helpers.pagination_helper import PaginationHelper


class CongressController(BaseController[Congress, CongressCreate, CongressUpdate, CongressRead]):
    """
    Controlador para operaciones con Congress (Congresos).

    Hereda funcionalidades CRUD básicas del BaseController y agrega
    operaciones específicas para congresos.
    """

    def __init__(self):
        super().__init__(congress_repository, "Congress")

    def serialize_to_dict(self, congress: Congress, **kwargs) -> Dict[str, Any]:
        """Serializar congreso a diccionario."""
        include_relations = kwargs.get('include_relations', False)
        congress_obj = congress

        congress_dict = {
            "id_congreso": congress_obj.id_congreso,
            "nombre": congress_obj.nombre,
            "edicion": congress_obj.edicion,
            "anio": congress_obj.anio,
            "fecha_inicio": congress_obj.fecha_inicio.isoformat(),
            "fecha_fin": congress_obj.fecha_fin.isoformat(),
            "descripcion_general": congress_obj.descripcion_general,
            "poster_cover_url": congress_obj.poster_cover_url
        }

        if include_relations:
            # Incluir relaciones si están cargadas
            if hasattr(congress_obj, 'speakers') and congress_obj.speakers:
                congress_dict["speakers"] = [
                    {
                        "id_speaker": speaker.id_speaker,
                        "nombres_completos": speaker.nombres_completos,
                        "tipo_speaker": speaker.tipo_speaker,
                        "institucion": speaker.institucion,
                        "pais": speaker.pais
                    }
                    for speaker in congress_obj.speakers
                ]

            if hasattr(congress_obj, 'sesiones') and congress_obj.sesiones:
                congress_dict["sesiones"] = [
                    {
                        "id_sesion": sesion.id_sesion,
                        "titulo_sesion": sesion.titulo_sesion,
                        "fecha": sesion.fecha.isoformat(),
                        "hora_inicio": sesion.hora_inicio.strftime("%H:%M"),
                        "hora_fin": sesion.hora_fin.strftime("%H:%M"),
                        "jornada": sesion.jornada,
                        "lugar": sesion.lugar
                    }
                    for sesion in congress_obj.sesiones
                ]

            if hasattr(congress_obj, 'congreso_sponsors') and congress_obj.congreso_sponsors:
                congress_dict["sponsors"] = [
                    {
                        "sponsor_name": cs.sponsor.nombre if cs.sponsor else "Unknown",
                        "categoria": cs.categoria,
                        "aporte": float(cs.aporte)
                    }
                    for cs in congress_obj.congreso_sponsors
                ]

        return congress_dict

    @handle_controller_errors
    def create_congress(
        self,
        db: Session,
        congress_data: CongressCreate,
        current_user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Crear nuevo congreso."""
        return self.create(db, congress_data, current_user_id)

    @handle_controller_errors
    def create_congress_with_relations(
        self,
        db: Session,
        congress_data: CongressCreate,
        sponsors_data: List[CongresoSponsorNested],
        sessions_data: List[SesionCronogramaNested],
        current_user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Crear un congreso junto con sus sponsors y sesiones de cronograma en una
        sola transacción atómica (todo o nada), igual que la creación de cursos.

        Sponsors y speakers se referencian por id (deben existir de antemano).
        """
        # --- Validaciones previas (antes de escribir nada) ---
        if congress_repository.check_edition_exists(db, congress_data.edicion, congress_data.anio):
            raise ValueError(
                f"Congress with edition '{congress_data.edicion}' and year {congress_data.anio} already exists"
            )

        sponsor_ids = [s.id_sponsor for s in sponsors_data]
        if len(sponsor_ids) != len(set(sponsor_ids)):
            raise ValueError("Duplicate id_sponsor found in sponsors list")

        # Validar existencia de sponsors/speakers con una sola query por tipo
        # (en vez de una SELECT por elemento de la lista).
        if sponsor_ids:
            existing_sponsor_ids = set(
                db.execute(
                    select(Sponsor.id_sponsor).where(Sponsor.id_sponsor.in_(sponsor_ids))
                ).scalars().all()
            )
            missing_sponsor_ids = [sid for sid in sponsor_ids if sid not in existing_sponsor_ids]
            if missing_sponsor_ids:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail=f"Sponsor with id {missing_sponsor_ids[0]} not found"
                )

        speaker_ids = [s.id_speaker for s in sessions_data]
        if speaker_ids:
            existing_speaker_ids = set(
                db.execute(
                    select(Speaker.id_speaker).where(Speaker.id_speaker.in_(speaker_ids))
                ).scalars().all()
            )
        else:
            existing_speaker_ids = set()

        for session_data in sessions_data:
            if session_data.id_speaker not in existing_speaker_ids:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail=f"Speaker with id {session_data.id_speaker} not found"
                )
            if not (congress_data.fecha_inicio <= session_data.fecha <= congress_data.fecha_fin):
                raise ValueError(
                    f"Session date {session_data.fecha} is outside the congress date range "
                    f"({congress_data.fecha_inicio} - {congress_data.fecha_fin})"
                )

        try:
            # --- Escritura: flush intermedio para obtener el id, un solo commit final ---
            congress = Congress(**congress_data.model_dump())
            db.add(congress)
            db.flush()

            for sponsor_data in sponsors_data:
                db.add(CongresoSponsor(
                    id_congreso=congress.id_congreso,
                    id_sponsor=sponsor_data.id_sponsor,
                    categoria=sponsor_data.categoria,
                    aporte=sponsor_data.aporte,
                ))

            for session_data in sessions_data:
                db.add(SesionCronograma(
                    id_congreso=congress.id_congreso,
                    id_speaker=session_data.id_speaker,
                    fecha=session_data.fecha,
                    hora_inicio=session_data.hora_inicio,
                    hora_fin=session_data.hora_fin,
                    titulo_sesion=session_data.titulo_sesion,
                    jornada=session_data.jornada,
                    lugar=session_data.lugar,
                ))

            db.commit()
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating congress with relations: {str(e)}"
            )

        congress_with_relations = congress_repository.get_congress_with_relations(db, congress.id_congreso)
        return self.serialize_to_dict(congress_with_relations, include_relations=True)

    @handle_controller_errors
    def get_congress_by_id(self, db: Session, congress_id: int) -> Optional[Dict[str, Any]]:
        """Obtener congreso por ID con relaciones."""
        congress = congress_repository.get_congress_with_relations(db, congress_id)
        if not congress:
            return None

        return self.serialize_to_dict(congress, include_relations=True)

    @handle_controller_errors
    def get_all_congresses(
        self,
        db: Session,
        page: int = 1,
        page_size: int = 10,
        year: Optional[int] = None,
        search_term: Optional[str] = None,
        order_by: str = "fecha_inicio",
        order_desc: bool = True
    ) -> Dict[str, Any]:
        """Obtener todos los congresos con paginación y filtros."""
        try:
            congresses, total = congress_repository.get_congresses_paginated(
                db,
                page=page,
                page_size=page_size,
                year=year,
                search_term=search_term,
                order_by=order_by,
                order_desc=order_desc
            )

            congresses_dict = [
                self.serialize_to_dict(congress) for congress in congresses
            ]

            # Construir parámetros extra para paginación
            extra_params = ControllerUtils.sanitize_filters({
                "year": year,
                "search_term": search_term,
                "order_by": order_by,
                "order_desc": order_desc
            })

            return PaginationHelper.build_pagination_response(
                items=congresses_dict,
                total=total,
                page=page,
                page_size=page_size,
                base_path="/api/v1/congresses",
                items_key="congresses",
                extra_params=extra_params
            )

        except Exception as e:
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching congresses: {str(e)}"
            )

    @handle_controller_errors
    def get_congresses_by_year(self, db: Session, year: int) -> List[Dict[str, Any]]:
        """Obtener congresos por año."""
        congresses = congress_repository.get_congresses_by_year(db, year)
        return [self.serialize_to_dict(congress) for congress in congresses]

    @handle_controller_errors
    def get_upcoming_congresses(
        self,
        db: Session,
        limit: int = 10,
        include_details: bool = False
    ) -> List[Dict[str, Any]]:
        """Obtener próximos congresos."""
        congresses = congress_repository.get_upcoming_congresses(
            db,
            limit=limit,
            include_relations=include_details
        )

        return [
            self.serialize_to_dict(congress, include_relations=include_details)
            for congress in congresses
        ]

    @handle_controller_errors
    def get_current_congresses(self, db: Session) -> List[Dict[str, Any]]:
        """Obtener congresos actualmente en curso."""
        congresses = congress_repository.get_current_congresses(db)
        return [self.serialize_to_dict(congress) for congress in congresses]

    @handle_controller_errors
    def search_congresses(
        self,
        db: Session,
        search_term: str,
        year: Optional[int] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Buscar congresos por término."""
        congresses = congress_repository.search_congresses(
            db,
            search_term=search_term,
            year=year,
            limit=limit
        )

        return [self.serialize_to_dict(congress) for congress in congresses]

    @handle_controller_errors
    def get_congresses_by_date_range(
        self,
        db: Session,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """Obtener congresos en un rango de fechas."""
        congresses = congress_repository.get_congresses_by_date_range(
            db, start_date, end_date
        )

        return [self.serialize_to_dict(congress) for congress in congresses]

    @handle_controller_errors
    def update_congress(
        self,
        db: Session,
        congress_id: int,
        congress_data: CongressUpdate,
        current_user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Actualizar congreso."""
        return self.update(db, congress_id, congress_data, current_user_id)

    @handle_controller_errors
    def delete_congress(
        self,
        db: Session,
        congress_id: int,
        current_user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Eliminar congreso.

        Política de borrado: se bloquea con 409 si el congreso tiene sesiones de
        cronograma, speakers o inscripciones (enrollments) asociados (requieren
        limpieza explícita primero, ya que son FKs NOT NULL o con reglas de
        integridad propias hacia congresos y no admiten quedar huérfanos).
        Los sponsors asociados (tabla pivote `congreso_sponsors`) se eliminan en
        cascada, ya que no representan datos con valor propio fuera del congreso.
        """
        congress = congress_repository.get(db, congress_id)
        if not congress:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Congress not found"
            )

        sessions = sesion_cronograma_repository.get_sessions_by_congress(
            db, congress_id, include_details=False
        )
        if sessions:
            raise HTTPException(
                status_code=http_status.HTTP_409_CONFLICT,
                detail="Cannot delete a congress with associated schedule sessions. "
                       "Remove the sessions first."
            )

        speakers = speaker_repository.get_speakers_by_congress(db, congress_id)
        if speakers:
            raise HTTPException(
                status_code=http_status.HTTP_409_CONFLICT,
                detail="Cannot delete a congress with associated speakers. "
                       "Remove the speakers first."
            )

        if EnrollmentRepository.has_enrollments_for_congress(congress_id, db):
            raise HTTPException(
                status_code=http_status.HTTP_409_CONFLICT,
                detail="Cannot delete a congress with associated enrollments. "
                       "Remove the enrollments first."
            )

        try:
            sponsorships = congreso_sponsor_repository.get_sponsorships_by_congress(
                db, congress_id, include_details=False
            )
            for sponsorship in sponsorships:
                db.delete(sponsorship)

            db.delete(congress)
            db.commit()
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting congress: {str(e)}"
            )

        return {"message": "Congress deleted successfully"}

    @handle_controller_errors
    def get_congress_statistics(self, db: Session, congress_id: int) -> Dict[str, Any]:
        """Obtener estadísticas detalladas de un congreso."""
        # Verificar que el congreso existe
        congress = congress_repository.get(db, congress_id)
        if not congress:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Congress not found"
            )

        stats = congress_repository.get_congress_statistics(db, congress_id)
        return ControllerUtils.build_success_response(
            "Congress statistics retrieved successfully",
            data=stats
        )

    @handle_controller_errors
    def get_years_with_congresses(self, db: Session) -> Dict[str, Any]:
        """Obtener años que tienen congresos."""
        years = congress_repository.get_years_with_congresses(db)
        return ControllerUtils.build_success_response(
            "Years with congresses retrieved successfully",
            data={"years": years}
        )

    @handle_controller_errors
    def get_congress_summary(self, db: Session) -> Dict[str, Any]:
        """Obtener resumen general de congresos."""
        summary = congress_repository.get_congress_summary(db)
        return ControllerUtils.build_success_response(
            "Congress summary retrieved successfully",
            data=summary
        )

    @handle_controller_errors
    def check_edition_availability(
        self,
        db: Session,
        edicion: str,
        anio: int,
        exclude_congress_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Verificar disponibilidad de edición y año."""
        exists = congress_repository.check_edition_exists(
            db, edicion, anio, exclude_congress_id
        )

        return {
            "available": not exists,
            "message": "Edition and year combination is available" if not exists
                      else "Edition and year combination already exists"
        }

    # Validaciones personalizadas
    def _validate_before_create(
        self,
        db: Session,
        obj_in: CongressCreate,
        current_user_id: Optional[int]
    ) -> None:
        """Validaciones antes de crear congreso."""
        # Verificar que la combinación edicion + año no existe
        if congress_repository.check_edition_exists(db, obj_in.edicion, obj_in.anio):
            raise ValueError(f"Congress with edition '{obj_in.edicion}' and year {obj_in.anio} already exists")

        # Validar fechas
        if obj_in.fecha_fin <= obj_in.fecha_inicio:
            raise ValueError("End date must be after start date")

    def _validate_before_update(
        self,
        db: Session,
        db_obj: Congress,
        obj_in: CongressUpdate,
        current_user_id: Optional[int]
    ) -> None:
        """Validaciones antes de actualizar congreso."""
        update_data = obj_in.model_dump(exclude_unset=True)

        # Si se actualiza edición o año, verificar disponibilidad
        new_edicion = update_data.get('edicion', db_obj.edicion)
        new_anio = update_data.get('anio', db_obj.anio)

        if (new_edicion != db_obj.edicion or new_anio != db_obj.anio):
            if congress_repository.check_edition_exists(
                db, new_edicion, new_anio, exclude_id=db_obj.id_congreso
            ):
                raise ValueError(f"Congress with edition '{new_edicion}' and year {new_anio} already exists")

        # Validar fechas si se actualizan
        new_fecha_inicio = update_data.get('fecha_inicio', db_obj.fecha_inicio)
        new_fecha_fin = update_data.get('fecha_fin', db_obj.fecha_fin)

        if new_fecha_fin <= new_fecha_inicio:
            raise ValueError("End date must be after start date")

    # === MÉTODOS DE COMPATIBILIDAD CON ESTRUCTURA ANTERIOR ===

    @handle_controller_errors
    def create_legacy_congress(
        self,
        db: Session,
        congress_data: CongressLegacyCreate,
        current_user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Crear congreso usando estructura legacy."""
        # Convertir de formato legacy al nuevo
        from datetime import timedelta
        today = date.today()
        new_congress_data = CongressCreate(
            nombre=congress_data.title,
            edicion=f"{congress_data.title[:7]}-01",  # Generar edición (máx. 10 caracteres, columna edicion)
            anio=today.year,  # Usar año actual
            fecha_inicio=today,  # Valores por defecto
            fecha_fin=today + timedelta(days=1),  # Un día después para cumplir validación
            descripcion_general=congress_data.description or "Sin descripción",
            poster_cover_url=congress_data.congress_image or ""
        )

        return self.create_congress(db, new_congress_data, current_user_id)

    @handle_controller_errors
    def get_legacy_congress_format(self, db: Session, congress_id: int) -> Optional[Dict[str, Any]]:
        """Obtener congreso en formato legacy."""
        congress = congress_repository.get(db, congress_id)
        if not congress:
            return None

        # Convertir al formato legacy
        return {
            "id": congress.id_congreso,
            "title": congress.nombre,
            "description": congress.descripcion_general,
            "place": "",  # No disponible en nuevo modelo
            "congress_image": congress.poster_cover_url,
            "congress_image_detail": "",  # No disponible
            "status": "activo",  # Por defecto
            "objectives": [],
            "organizers": [],
            "materials": [],
            "target_audience": []
        }


# Instancia única del controlador
congress_controller = CongressController()