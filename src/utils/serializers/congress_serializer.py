from typing import List, Optional, Dict, Any
from src.models.congress import Congress, CongressRequirement, CongressContent
from src.utils.serializers.general_serializer import GeneralSerializer


class CongressSerializer:
    """Maneja la serialización/deserialización de los Congresos"""

    @staticmethod
    def congress_to_dict(
        congress: Congress,
        requirement: Optional[CongressRequirement] = None,
        contents: List[CongressContent] = None,
        include_category: bool = False
    ) -> Dict[str, Any]:
        """Convierte un congreso y sus relaciones a diccionario"""
        congress_dict = {
            "id": congress.id,
            "title": congress.title,
            "description": congress.description,
            "place": congress.place,
            "congress_image": congress.congress_image,
            "congress_image_detail": congress.congress_image_detail,
            "category_id": congress.category_id,
            "status": congress.status,
            "objectives": GeneralSerializer.deserialize_json_field(congress.objectives),
            "organizers": GeneralSerializer.deserialize_json_field(congress.organizers),
            "materials": GeneralSerializer.deserialize_json_field(congress.materials),
            "target_audience": GeneralSerializer.deserialize_json_field(congress.target_audience),
            "requirement": None,
            "contents": []
        }

        if include_category and hasattr(congress, 'category_rel') and congress.category_rel:
            congress_dict["category_name"] = congress.category_rel.name
            congress_dict["category_description"] = congress.category_rel.description
            congress_dict["category_svgurl"] = congress.category_rel.svgurl
            congress_dict["category_status"] = congress.category_rel.status

        if requirement:
            congress_dict["requirement"] = CongressSerializer._requirement_to_dict(
                requirement,
                GeneralSerializer.deserialize_json_field(congress.target_audience)
            )

        if contents:
            congress_dict["contents"] = [
                CongressSerializer._content_to_dict(content)
                for content in contents
            ]

        return congress_dict

    @staticmethod
    def _requirement_to_dict(req: CongressRequirement, target_audience: List[str]) -> Dict[str, Any]:
        """Convierte requisitos a diccionario"""
        return {
            "registration": {
                "startDate": str(req.start_date_registration),
                "endDate": str(req.end_date_registration)
            },
            "congressSchedule": {
                "startDate": str(req.start_date_congress),
                "endDate": str(req.end_date_congress),
                "days": GeneralSerializer.deserialize_json_field(req.days),
                "startTime": req.start_time,
                "endTime": req.end_time
            },
            "location": req.location,
            "quota": {
                "min": req.min_quota,
                "max": req.max_quota
            },
            "prices": GeneralSerializer.deserialize_json_field(req.prices),
            "hours": {
                "total": req.in_person_hours + req.autonomous_hours,
                "inPerson": req.in_person_hours,
                "autonomous": req.autonomous_hours
            },
            "targetAudience": target_audience,
            "modality": req.modality,
            "certification": req.certification,
            "prerequisites": GeneralSerializer.deserialize_json_field(req.prerequisites)
        }

    @staticmethod
    def _content_to_dict(content: CongressContent) -> Dict[str, Any]:
        """Convierte contenido a diccionario"""
        return {
            "id": content.id,
            "unit": content.unit,
            "title": content.title,
            "topics": GeneralSerializer.deserialize_json_field(content.topics)
        }
