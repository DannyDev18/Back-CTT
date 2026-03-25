from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status as http_status
from sqlalchemy.orm import Session

from .base_controller import BaseController, handle_controller_errors, ControllerUtils
from src.models.speaker_model import Speaker, SpeakerCreate, SpeakerUpdate, SpeakerRead
from src.repositories import speaker_repository, congress_repository
from src.utils.Helpers.pagination_helper import PaginationHelper


class SpeakerController(BaseController[Speaker, SpeakerCreate, SpeakerUpdate, SpeakerRead]):
    """
    Controlador para operaciones con Speaker (Ponentes/Expositores).

    Hereda funcionalidades CRUD básicas del BaseController y agrega
    operaciones específicas para speakers.
    """

    def __init__(self):
        super().__init__(speaker_repository, "Speaker")

    def serialize_to_dict(self, speaker: Speaker, **kwargs) -> Dict[str, Any]:
        """Serializar speaker a diccionario."""
        include_sessions = kwargs.get('include_sessions', False)
        include_congress = kwargs.get('include_congress', False)

        speaker_dict = {
            "id_speaker": speaker.id_speaker,
            "id_congreso": speaker.id_congreso,
            "nombres_completos": speaker.nombres_completos,
            "titulo_academico": speaker.titulo_academico,
            "institucion": speaker.institucion,
            "pais": speaker.pais,
            "foto_url": speaker.foto_url,
            "tipo_speaker": speaker.tipo_speaker
        }

        if include_congress and hasattr(speaker, 'congreso') and speaker.congreso:
            speaker_dict["congress"] = {
                "id_congreso": speaker.congreso.id_congreso,
                "nombre": speaker.congreso.nombre,
                "anio": speaker.congreso.anio,
                "fecha_inicio": speaker.congreso.fecha_inicio.isoformat(),
                "fecha_fin": speaker.congreso.fecha_fin.isoformat()
            }

        if include_sessions and hasattr(speaker, 'sesiones') and speaker.sesiones:
            speaker_dict["sessions"] = [
                {
                    "id_sesion": sesion.id_sesion,
                    "titulo_sesion": sesion.titulo_sesion,
                    "fecha": sesion.fecha.isoformat(),
                    "hora_inicio": sesion.hora_inicio.strftime("%H:%M"),
                    "hora_fin": sesion.hora_fin.strftime("%H:%M"),
                    "jornada": sesion.jornada,
                    "lugar": sesion.lugar
                }
                for sesion in speaker.sesiones
            ]

            # Agregar estadísticas resumidas
            speaker_dict["total_sessions"] = len(speaker.sesiones)

        return speaker_dict

    @handle_controller_errors
    def create_speaker(
        self,
        db: Session,
        speaker_data: SpeakerCreate,
        current_user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Crear nuevo speaker."""
        return self.create(db, speaker_data, current_user_id)

    @handle_controller_errors
    def get_speaker_by_id(
        self,
        db: Session,
        speaker_id: int,
        include_sessions: bool = False,
        include_congress: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Obtener speaker por ID."""
        if include_sessions or include_congress:
            speaker = speaker_repository.get_speaker_with_sessions(db, speaker_id)
        else:
            speaker = speaker_repository.get(db, speaker_id)

        if not speaker:
            return None

        return self.serialize_to_dict(
            speaker,
            include_sessions=include_sessions,
            include_congress=include_congress
        )

    @handle_controller_errors
    def get_speakers_by_congress(
        self,
        db: Session,
        congress_id: int,
        include_sessions: bool = False
    ) -> List[Dict[str, Any]]:
        """Obtener todos los speakers de un congreso."""
        # Verificar que el congreso existe
        congress = congress_repository.get(db, congress_id)
        if not congress:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Congress not found"
            )

        speakers = speaker_repository.get_speakers_by_congress(
            db, congress_id, include_sessions=include_sessions
        )

        return [
            self.serialize_to_dict(speaker if hasattr(speaker, 'id_speaker') else speaker[0], include_sessions=include_sessions)
            for speaker in speakers
        ]

    @handle_controller_errors
    def get_all_speakers(
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
    ) -> Dict[str, Any]:
        """Obtener todos los speakers con paginación y filtros."""
        try:
            speakers, total = speaker_repository.get_speakers_paginated(
                db,
                page=page,
                page_size=page_size,
                congress_id=congress_id,
                tipo_speaker=tipo_speaker,
                pais=pais,
                search_term=search_term,
                order_by=order_by,
                order_desc=order_desc
            )

            speakers_dict = [
                self.serialize_to_dict(speaker if hasattr(speaker, 'id_speaker') else speaker[0])
                for speaker in speakers
            ]

            # Construir parámetros extra para paginación
            extra_params = ControllerUtils.sanitize_filters({
                "congress_id": congress_id,
                "tipo_speaker": tipo_speaker,
                "pais": pais,
                "search_term": search_term,
                "order_by": order_by,
                "order_desc": order_desc
            })

            return PaginationHelper.build_pagination_response(
                items=speakers_dict,
                total=total,
                page=page,
                page_size=page_size,
                base_path="/api/v1/speakers",
                items_key="speakers",
                extra_params=extra_params
            )

        except Exception as e:
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching speakers: {str(e)}"
            )

    @handle_controller_errors
    def get_speakers_by_type(
        self,
        db: Session,
        tipo_speaker: str,
        congress_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Obtener speakers por tipo."""
        speakers = speaker_repository.get_speakers_by_type(db, tipo_speaker, congress_id)
        return [self.serialize_to_dict(speaker if hasattr(speaker, 'id_speaker') else speaker[0]) for speaker in speakers]

    @handle_controller_errors
    def get_speakers_by_country(
        self,
        db: Session,
        pais: str,
        congress_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Obtener speakers por país."""
        speakers = speaker_repository.get_speakers_by_country(db, pais, congress_id)
        return [self.serialize_to_dict(speaker if hasattr(speaker, 'id_speaker') else speaker[0]) for speaker in speakers]

    @handle_controller_errors
    def get_speakers_by_institution(
        self,
        db: Session,
        institucion: str,
        exact_match: bool = False
    ) -> List[Dict[str, Any]]:
        """Obtener speakers por institución."""
        speakers = speaker_repository.get_speakers_by_institution(
            db, institucion, exact_match
        )
        return [self.serialize_to_dict(speaker if hasattr(speaker, 'id_speaker') else speaker[0]) for speaker in speakers]

    @handle_controller_errors
    def search_speakers(
        self,
        db: Session,
        search_term: str,
        congress_id: Optional[int] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Buscar speakers por término."""
        speakers = speaker_repository.search_speakers(
            db, search_term, congress_id, limit
        )
        return [self.serialize_to_dict(speaker if hasattr(speaker, 'id_speaker') else speaker[0]) for speaker in speakers]

    @handle_controller_errors
    def get_frequent_speakers(
        self,
        db: Session,
        min_congresses: int = 2,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Obtener speakers que han participado en múltiples congresos."""
        frequent_speakers = speaker_repository.get_frequent_speakers(
            db, min_congresses, limit
        )

        return ControllerUtils.build_success_response(
            "Frequent speakers retrieved successfully",
            data={
                "frequent_speakers": frequent_speakers,
                "criteria": {
                    "min_congresses": min_congresses,
                    "limit": limit
                }
            }
        )

    @handle_controller_errors
    def get_countries_with_speakers(
        self,
        db: Session,
        congress_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Obtener lista de países representados."""
        countries = speaker_repository.get_countries_with_speakers(db, congress_id)

        return ControllerUtils.build_success_response(
            "Countries with speakers retrieved successfully",
            data={
                "countries": countries,
                "count": len(countries),
                "congress_id": congress_id
            }
        )

    @handle_controller_errors
    def get_institutions_with_speakers(
        self,
        db: Session,
        congress_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Obtener lista de instituciones representadas."""
        institutions = speaker_repository.get_institutions_with_speakers(db, congress_id)

        return ControllerUtils.build_success_response(
            "Institutions with speakers retrieved successfully",
            data={
                "institutions": institutions,
                "count": len(institutions),
                "congress_id": congress_id
            }
        )

    @handle_controller_errors
    def get_speaker_statistics_by_congress(
        self,
        db: Session,
        congress_id: int
    ) -> Dict[str, Any]:
        """Obtener estadísticas de speakers por congreso."""
        # Verificar que el congreso existe
        congress = congress_repository.get(db, congress_id)
        if not congress:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Congress not found"
            )

        stats = speaker_repository.get_speaker_statistics_by_congress(db, congress_id)

        return ControllerUtils.build_success_response(
            "Speaker statistics retrieved successfully",
            data=stats
        )

    @handle_controller_errors
    def update_speaker(
        self,
        db: Session,
        speaker_id: int,
        speaker_data: SpeakerUpdate,
        current_user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Actualizar speaker."""
        return self.update(db, speaker_id, speaker_data, current_user_id)

    @handle_controller_errors
    def delete_speaker(
        self,
        db: Session,
        speaker_id: int,
        current_user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Eliminar speaker."""
        return self.delete(db, speaker_id, current_user_id)

    @handle_controller_errors
    def get_speaker_summary(self, db: Session) -> Dict[str, Any]:
        """Obtener resumen general de speakers."""
        summary = speaker_repository.get_speaker_summary(db)
        return ControllerUtils.build_success_response(
            "Speaker summary retrieved successfully",
            data=summary
        )

    @handle_controller_errors
    def check_speaker_exists_in_congress(
        self,
        db: Session,
        nombres_completos: str,
        congress_id: int,
        exclude_speaker_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Verificar si un speaker ya existe en un congreso."""
        exists = speaker_repository.check_speaker_exists_in_congress(
            db, nombres_completos, congress_id, exclude_speaker_id
        )

        return {
            "exists": exists,
            "message": "Speaker already exists in this congress" if exists else "Speaker can be added to this congress"
        }

    @handle_controller_errors
    def bulk_import_speakers(
        self,
        db: Session,
        congress_id: int,
        speakers_data: List[SpeakerCreate],
        current_user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Importar múltiples speakers para un congreso."""
        try:
            # Verificar que el congreso existe
            congress = congress_repository.get(db, congress_id)
            if not congress:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail="Congress not found"
                )

            # Validar que todos los speakers sean para el mismo congreso
            invalid_speakers = [
                speaker.nombres_completos for speaker in speakers_data
                if speaker.id_congreso != congress_id
            ]
            if invalid_speakers:
                raise ValueError(f"Some speakers are not for congress {congress_id}: {', '.join(invalid_speakers)}")

            # Verificar nombres duplicados en el lote
            names = [speaker.nombres_completos for speaker in speakers_data]
            if len(names) != len(set(names)):
                raise ValueError("Duplicate speaker names found in the batch")

            # Verificar speakers existentes en el congreso
            existing_speakers = []
            for speaker_data in speakers_data:
                if speaker_repository.check_speaker_exists_in_congress(
                    db, speaker_data.nombres_completos, congress_id
                ):
                    existing_speakers.append(speaker_data.nombres_completos)

            if existing_speakers:
                raise ValueError(f"The following speakers already exist in this congress: {', '.join(existing_speakers)}")

            # Crear speakers en lote
            speakers = speaker_repository.bulk_create(db, objs_in=speakers_data)
            db.commit()

            # Actualizar objetos
            for speaker in speakers:
                db.refresh(speaker)

            speakers_dict = [
                self.serialize_to_dict(speaker if hasattr(speaker, 'id_speaker') else speaker[0])
                for speaker in speakers
            ]

            return ControllerUtils.build_success_response(
                f"Successfully imported {len(speakers)} speakers to congress {congress_id}",
                data={
                    "imported_speakers": speakers_dict,
                    "count": len(speakers),
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
                detail=f"Error importing speakers: {str(e)}"
            )

    # Validaciones personalizadas
    def _validate_before_create(
        self,
        db: Session,
        obj_in: SpeakerCreate,
        current_user_id: Optional[int]
    ) -> None:
        """Validaciones antes de crear speaker."""
        # Verificar que el congreso existe
        congress = congress_repository.get(db, obj_in.id_congreso)
        if not congress:
            raise ValueError(f"Congress with ID {obj_in.id_congreso} does not exist")

        # Verificar que el speaker no existe ya en el congreso
        if speaker_repository.check_speaker_exists_in_congress(
            db, obj_in.nombres_completos, obj_in.id_congreso
        ):
            raise ValueError(f"Speaker '{obj_in.nombres_completos}' already exists in this congress")

    def _validate_before_update(
        self,
        db: Session,
        db_obj: Speaker,
        obj_in: SpeakerUpdate,
        current_user_id: Optional[int]
    ) -> None:
        """Validaciones antes de actualizar speaker."""
        update_data = obj_in.model_dump(exclude_unset=True)

        # Si se actualiza el nombre, verificar duplicados en el congreso
        if 'nombres_completos' in update_data:
            new_name = update_data['nombres_completos']
            if new_name != db_obj.nombres_completos:
                if speaker_repository.check_speaker_exists_in_congress(
                    db, new_name, db_obj.id_congreso, exclude_id=db_obj.id_speaker
                ):
                    raise ValueError(f"Speaker '{new_name}' already exists in this congress")

    def _validate_before_delete(
        self,
        db: Session,
        db_obj: Speaker,
        current_user_id: Optional[int]
    ) -> None:
        """Validaciones antes de eliminar speaker."""
        # Verificar si el speaker tiene sesiones programadas
        speaker_with_sessions = speaker_repository.get_speaker_with_sessions(
            db, db_obj.id_speaker
        )

        # Handle both Speaker instances and Row objects
        if speaker_with_sessions:
            if hasattr(speaker_with_sessions, 'sesiones'):
                sesiones = speaker_with_sessions.sesiones
            else:
                # If it's a Row object, extract the Speaker instance
                speaker_obj = speaker_with_sessions[0] if isinstance(speaker_with_sessions, tuple) else speaker_with_sessions
                sesiones = getattr(speaker_obj, 'sesiones', None)

            if sesiones:
                active_sessions = len(sesiones)
                raise ValueError(
                    f"Cannot delete speaker: has {active_sessions} scheduled session(s). "
                    "Remove or reassign sessions first."
                )


# Instancia única del controlador
speaker_controller = SpeakerController()