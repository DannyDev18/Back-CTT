from typing import List, Optional, Dict, Any
from src.models.course import (
    Course,
    CourseRequirement,
    CourseContent
)
from src.utils.serializers.general_serializer import GeneralSerializer

class CourseSerializer:
    """Maneja la serialización/deserialización de los Cursos"""
    
    @staticmethod
    def course_to_dict(course: Course, 
                        requirements: Optional[CourseRequirement] = None, 
                        contents: List[CourseContent] = None, 
                        include_category: bool = False) -> Dict[str, Any]:
        """Convierte un curso y sus relaciones a diccionario"""
        course_dict = {
            "id": course.id,
            "title": course.title,
            "description": course.description,
            "place": course.place,
            "course_image": course.course_image,
            "course_image_detail": course.course_image_detail,
            "category_id": course.category_id,
            "status": course.status,
            "objectives": GeneralSerializer.deserialize_json_field(course.objectives),
            "organizers": GeneralSerializer.deserialize_json_field(course.organizers),
            "materials": GeneralSerializer.deserialize_json_field(course.materials),
            "target_audience": GeneralSerializer.deserialize_json_field(course.target_audience),
            "requirements": None,
            "contents": []
        }
        if include_category and hasattr(course, 'category_rel') and course.category_rel:
            course_dict["category"] = course.category_rel.name
            course_dict["category_name"] = course.category_rel.name
            course_dict["category_description"] = course.category_rel.description
            course_dict["category_svgurl"] = course.category_rel.svgurl
            course_dict["category_status"] = course.category_rel.status
        elif hasattr(course, 'category_rel') and course.category_rel:
            # Include basic category name even if include_category is False
            course_dict["category"] = course.category_rel.name
        

        if requirements:
            course_dict["requirements"] = CourseSerializer._requirements_to_dict(
                requirements, 
                GeneralSerializer.deserialize_json_field(course.target_audience)
            )
        
        if contents:
            course_dict["contents"] = [
                CourseSerializer._content_to_dict(content) 
                for content in contents
            ]
        
        return course_dict
    
    @staticmethod
    def _requirements_to_dict(req: CourseRequirement, target_audience: List[str]) -> Dict[str, Any]:
        """Convierte requisitos a diccionario"""
        return {
            "registration": {
                "startDate": str(req.start_date_registration),
                "endDate": str(req.end_date_registration)
            },
            "courseSchedule": {
                "startDate": str(req.start_date_course),
                "endDate": str(req.end_date_course),
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
                "total": req.in_person_hours + req.autonomous_hours,  # Calculado aquí
                "inPerson": req.in_person_hours,
                "autonomous": req.autonomous_hours
            },
            "targetAudience": target_audience,
            "modality": req.modality,
            "certification": req.certification,
            "prerequisites": GeneralSerializer.deserialize_json_field(req.prerequisites)
        }
    
    @staticmethod
    def _content_to_dict(content: CourseContent) -> Dict[str, Any]:
        """Convierte contenido a diccionario"""
        topics = GeneralSerializer.deserialize_json_field(content.topics)
        return {
            "unit": content.unit,
            "title": content.title,
            "topics": topics
        }
