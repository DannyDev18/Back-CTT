from typing import List, Optional, Dict, Any
from datetime import date, time
from fastapi import HTTPException, status as http_status
from sqlalchemy.orm import Session

from .base_controller import BaseController, handle_controller_errors, ControllerUtils
from src.models.sesion_cronograma_model import (
    SesionCronograma, SesionCronogramaCreate, SesionCronogramaUpdate,
    SesionCronogramaRead, SesionCronogramaWithSpeaker
)
from src.repositories import sesion_cronograma_repository, congress_repository, speaker_repository
from src.utils.Helpers.pagination_helper import PaginationHelper


class SesionCronogramaController(BaseController[SesionCronograma, SesionCronogramaCreate, SesionCronogramaUpdate, SesionCronogramaRead]):
    """
    Controlador para operaciones con SesionCronograma (Cronograma de Sesiones).

    Hereda funcionalidades CRUD básicas del BaseController y agrega
    operaciones específicas para sesiones de cronograma.
    """

    def __init__(self):
        super().__init__(sesion_cronograma_repository, "SesionCronograma")

    def serialize_to_dict(self, sesion: SesionCronograma, **kwargs) -> Dict[str, Any]:
        """Serializar sesión a diccionario."""
        include_speaker = kwargs.get('include_speaker', False)
        include_congress = kwargs.get('include_congress', False)

        sesion_dict = {
            "id_sesion": sesion.id_sesion,
            "id_congreso": sesion.id_congreso,
            "id_speaker": sesion.id_speaker,
            "fecha": sesion.fecha.isoformat(),
            "hora_inicio": sesion.hora_inicio.strftime("%H:%M"),
            "hora_fin": sesion.hora_fin.strftime("%H:%M"),
            "titulo_sesion": sesion.titulo_sesion,
            "jornada": sesion.jornada,
            "lugar": sesion.lugar
        }

        if include_speaker and hasattr(sesion, 'speaker') and sesion.speaker:
            sesion_dict["speaker"] = {
                "id_speaker": sesion.speaker.id_speaker,
                "nombres_completos": sesion.speaker.nombres_completos,
                "titulo_academico": sesion.speaker.titulo_academico,
                "institucion": sesion.speaker.institucion,
                "pais": sesion.speaker.pais,
                "tipo_speaker": sesion.speaker.tipo_speaker
            }

        if include_congress and hasattr(sesion, 'congreso') and sesion.congreso:
            sesion_dict["congress"] = {
                "id_congreso": sesion.congreso.id_congreso,
                "nombre": sesion.congreso.nombre,
                "anio": sesion.congreso.anio,
                "fecha_inicio": sesion.congreso.fecha_inicio.isoformat(),
                "fecha_fin": sesion.congreso.fecha_fin.isoformat()
            }

        return sesion_dict

    @handle_controller_errors
    def create_session(
        self,
        db: Session,
        session_data: SesionCronogramaCreate,
        current_user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Crear nueva sesión del cronograma."""
        return self.create(db, session_data, current_user_id)

    @handle_controller_errors
    def get_session_by_id(
        self,
        db: Session,
        session_id: int,
        include_speaker: bool = False,
        include_congress: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Obtener sesión por ID."""
        if include_speaker or include_congress:
            sesion = sesion_cronograma_repository.get_session_with_details(db, session_id)
        else:
            sesion = sesion_cronograma_repository.get(db, session_id)

        if not sesion:
            return None

        return self.serialize_to_dict(
            sesion,
            include_speaker=include_speaker,
            include_congress=include_congress
        )

    @handle_controller_errors
    def get_sessions_by_congress(
        self,
        db: Session,
        congress_id: int,
        include_details: bool = True,
        order_by_date: bool = True
    ) -> List[Dict[str, Any]]:
        """Obtener todas las sesiones de un congreso."""
        # Verificar que el congreso existe
        congress = congress_repository.get(db, congress_id)
        if not congress:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Congress not found"
            )

        sessions = sesion_cronograma_repository.get_sessions_by_congress(
            db, congress_id, include_details, order_by_date
        )

        return [
            self.serialize_to_dict(
                sesion if hasattr(sesion, 'id_sesion') else sesion[0],
                include_speaker=include_details,
                include_congress=False
            )
            for sesion in sessions
        ]

    @handle_controller_errors
    def get_sessions_by_date(
        self,
        db: Session,
        fecha: date,
        congress_id: Optional[int] = None,
        include_details: bool = True
    ) -> List[Dict[str, Any]]:
        """Obtener sesiones por fecha."""
        sessions = sesion_cronograma_repository.get_sessions_by_date(
            db, fecha, congress_id, include_details
        )

        return [
            self.serialize_to_dict(
                sesion if hasattr(sesion, 'id_sesion') else sesion[0],
                include_speaker=include_details,
                include_congress=congress_id is None
            )
            for sesion in sessions
        ]

    @handle_controller_errors
    def get_sessions_by_speaker(
        self,
        db: Session,
        speaker_id: int,
        include_details: bool = True
    ) -> List[Dict[str, Any]]:
        """Obtener sesiones de un speaker específico."""
        # Verificar que el speaker existe
        speaker = speaker_repository.get(db, speaker_id)
        if not speaker:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Speaker not found"
            )

        sessions = sesion_cronograma_repository.get_sessions_by_speaker(
            db, speaker_id, include_details
        )

        return [
            self.serialize_to_dict(
                sesion if hasattr(sesion, 'id_sesion') else sesion[0],
                include_speaker=False,
                include_congress=include_details
            )
            for sesion in sessions
        ]

    @handle_controller_errors
    def get_all_sessions(
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
    ) -> Dict[str, Any]:
        """Obtener todas las sesiones con paginación y filtros."""
        try:
            sessions, total = sesion_cronograma_repository.get_sessions_paginated(
                db,
                page=page,
                page_size=page_size,
                congress_id=congress_id,
                speaker_id=speaker_id,
                fecha=fecha,
                jornada=jornada,
                search_term=search_term,
                order_by=order_by,
                order_desc=order_desc
            )

            sessions_dict = [
                self.serialize_to_dict(sesion if hasattr(sesion, 'id_sesion') else sesion[0], include_speaker=True)
                for sesion in sessions
            ]

            # Construir parámetros extra para paginación
            extra_params = ControllerUtils.sanitize_filters({
                "congress_id": congress_id,
                "speaker_id": speaker_id,
                "fecha": fecha.isoformat() if fecha else None,
                "jornada": jornada,
                "search_term": search_term,
                "order_by": order_by,
                "order_desc": order_desc
            })

            return PaginationHelper.build_pagination_response(
                items=sessions_dict,
                total=total,
                page=page,
                page_size=page_size,
                base_path="/api/v1/sessions",
                items_key="sessions",
                extra_params=extra_params
            )

        except Exception as e:
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching sessions: {str(e)}"
            )

    @handle_controller_errors
    def get_sessions_by_date_range(
        self,
        db: Session,
        start_date: date,
        end_date: date,
        congress_id: Optional[int] = None,
        include_details: bool = True
    ) -> List[Dict[str, Any]]:
        """Obtener sesiones en un rango de fechas."""
        sessions = sesion_cronograma_repository.get_sessions_by_date_range(
            db, start_date, end_date, congress_id, include_details
        )

        return [
            self.serialize_to_dict(
                sesion if hasattr(sesion, 'id_sesion') else sesion[0],
                include_speaker=include_details,
                include_congress=congress_id is None
            )
            for sesion in sessions
        ]

    @handle_controller_errors
    def get_sessions_by_jornada(
        self,
        db: Session,
        jornada: str,
        congress_id: Optional[int] = None,
        fecha: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """Obtener sesiones por jornada."""
        sessions = sesion_cronograma_repository.get_sessions_by_jornada(
            db, jornada, congress_id, fecha
        )

        return [self.serialize_to_dict(sesion if hasattr(sesion, 'id_sesion') else sesion[0], include_speaker=True) for sesion in sessions]

    @handle_controller_errors
    def search_sessions(
        self,
        db: Session,
        search_term: str,
        congress_id: Optional[int] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Buscar sesiones por término."""
        sessions = sesion_cronograma_repository.search_sessions(
            db, search_term, congress_id, limit
        )

        return [
            self.serialize_to_dict(sesion if hasattr(sesion, 'id_sesion') else sesion[0], include_speaker=True)
            for sesion in sessions
        ]

    @handle_controller_errors
    def get_daily_schedule(
        self,
        db: Session,
        congress_id: int,
        fecha: date,
        group_by_jornada: bool = True
    ) -> Dict[str, Any]:
        """Obtener cronograma detallado de un día específico."""
        # Verificar que el congreso existe
        congress = congress_repository.get(db, congress_id)
        if not congress:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Congress not found"
            )

        schedule = sesion_cronograma_repository.get_daily_schedule(
            db, congress_id, fecha, group_by_jornada
        )

        return ControllerUtils.build_success_response(
            "Daily schedule retrieved successfully",
            data=schedule
        )

    @handle_controller_errors
    def get_congress_schedule_summary(self, db: Session, congress_id: int) -> Dict[str, Any]:
        """Obtener resumen del cronograma de un congreso."""
        # Verificar que el congreso existe
        congress = congress_repository.get(db, congress_id)
        if not congress:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Congress not found"
            )

        summary = sesion_cronograma_repository.get_congress_schedule_summary(db, congress_id)

        return ControllerUtils.build_success_response(
            "Congress schedule summary retrieved successfully",
            data=summary
        )

    @handle_controller_errors
    def check_time_conflicts(
        self,
        db: Session,
        speaker_id: int,
        fecha: date,
        hora_inicio: time,
        hora_fin: time,
        exclude_session_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Verificar conflictos de horario para un speaker."""
        # Verificar que el speaker existe
        speaker = speaker_repository.get(db, speaker_id)
        if not speaker:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Speaker not found"
            )

        has_conflicts = sesion_cronograma_repository.check_time_conflict(
            db, speaker_id, fecha, hora_inicio, hora_fin, exclude_session_id
        )

        if has_conflicts:
            # Obtener detalles de los conflictos
            conflicts = sesion_cronograma_repository.get_conflicting_sessions(
                db, speaker_id, fecha, hora_inicio, hora_fin, exclude_session_id
            )

            conflict_details = [
                {
                    "id_sesion": conflict.id_sesion,
                    "titulo_sesion": conflict.titulo_sesion,
                    "fecha": conflict.fecha.isoformat(),
                    "hora_inicio": conflict.hora_inicio.strftime("%H:%M"),
                    "hora_fin": conflict.hora_fin.strftime("%H:%M"),
                    "lugar": conflict.lugar
                }
                for conflict in conflicts
            ]

            return {
                "has_conflicts": True,
                "message": f"Time conflict detected for speaker {speaker_id}",
                "conflicts": conflict_details
            }

        return {
            "has_conflicts": False,
            "message": "No time conflicts found"
        }

    @handle_controller_errors
    def update_session(
        self,
        db: Session,
        session_id: int,
        session_data: SesionCronogramaUpdate,
        current_user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Actualizar sesión."""
        return self.update(db, session_id, session_data, current_user_id)

    @handle_controller_errors
    def delete_session(
        self,
        db: Session,
        session_id: int,
        current_user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Eliminar sesión."""
        return self.delete(db, session_id, current_user_id)

    @handle_controller_errors
    def get_session_summary(self, db: Session) -> Dict[str, Any]:
        """Obtener resumen general de sesiones."""
        summary = sesion_cronograma_repository.get_session_summary(db)
        return ControllerUtils.build_success_response(
            "Session summary retrieved successfully",
            data=summary
        )

    # Validaciones personalizadas
    def _validate_before_create(
        self,
        db: Session,
        obj_in: SesionCronogramaCreate,
        current_user_id: Optional[int]
    ) -> None:
        """Validaciones antes de crear sesión."""
        # Verificar que el congreso existe
        congress = congress_repository.get(db, obj_in.id_congreso)
        if not congress:
            raise ValueError(f"Congress with ID {obj_in.id_congreso} does not exist")

        # Verificar que el speaker existe
        speaker = speaker_repository.get(db, obj_in.id_speaker)
        if not speaker:
            raise ValueError(f"Speaker with ID {obj_in.id_speaker} does not exist")

        # Verificar que el speaker pertenece al congreso
        if speaker.id_congreso != obj_in.id_congreso:
            raise ValueError(f"Speaker {obj_in.id_speaker} does not belong to congress {obj_in.id_congreso}")

        # Verificar conflictos de horario
        if sesion_cronograma_repository.check_time_conflict(
            db, obj_in.id_speaker, obj_in.fecha, obj_in.hora_inicio, obj_in.hora_fin
        ):
            raise ValueError(f"Time conflict detected for speaker {obj_in.id_speaker} on {obj_in.fecha}")

    def _validate_before_update(
        self,
        db: Session,
        db_obj: SesionCronograma,
        obj_in: SesionCronogramaUpdate,
        current_user_id: Optional[int]
    ) -> None:
        """Validaciones antes de actualizar sesión."""
        update_data = obj_in.model_dump(exclude_unset=True)

        # Si se actualiza el speaker, verificar que existe y pertenece al congreso
        if 'id_speaker' in update_data:
            new_speaker_id = update_data['id_speaker']
            speaker = speaker_repository.get(db, new_speaker_id)
            if not speaker:
                raise ValueError(f"Speaker with ID {new_speaker_id} does not exist")

            if speaker.id_congreso != db_obj.id_congreso:
                raise ValueError(f"Speaker {new_speaker_id} does not belong to congress {db_obj.id_congreso}")

        # Verificar conflictos de horario si se actualizan datos temporales
        time_fields = ['id_speaker', 'fecha', 'hora_inicio', 'hora_fin']
        if any(field in update_data for field in time_fields):
            new_speaker_id = update_data.get('id_speaker', db_obj.id_speaker)
            new_fecha = update_data.get('fecha', db_obj.fecha)
            new_hora_inicio = update_data.get('hora_inicio', db_obj.hora_inicio)
            new_hora_fin = update_data.get('hora_fin', db_obj.hora_fin)

            if sesion_cronograma_repository.check_time_conflict(
                db, new_speaker_id, new_fecha, new_hora_inicio, new_hora_fin,
                exclude_session_id=db_obj.id_sesion
            ):
                raise ValueError(f"Time conflict detected for speaker {new_speaker_id} on {new_fecha}")


# Instancia única del controlador
sesion_cronograma_controller = SesionCronogramaController()