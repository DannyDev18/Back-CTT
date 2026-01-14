from typing import Dict, Any
from datetime import datetime

class EnrollmentSerializer:
    """Serializador para manejar la conversión de datos de inscripciones"""
    
    @staticmethod
    def serialize_enrollment(enrollment) -> Dict[str, Any]:
        """Serializa un objeto Enrollment a diccionario"""
        return {
            "id": enrollment.id,
            "id_user_platform": enrollment.id_user_platform,
            "id_course": enrollment.id_course,
            "enrollment_date": enrollment.enrollment_date.isoformat() if isinstance(enrollment.enrollment_date, datetime) else enrollment.enrollment_date,
            "status": enrollment.status.value if hasattr(enrollment.status, 'value') else enrollment.status,
            "payment_order_url": enrollment.payment_order_url
        }
    
    @staticmethod
    def serialize_enrollment_with_user(enrollment, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Serializa una inscripción con datos del usuario"""
        base = EnrollmentSerializer.serialize_enrollment(enrollment)
        base.update({
            "user_name": user_data.get("name"),
            "user_email": user_data.get("email"),
            "user_cellphone": user_data.get("cellphone")
        })
        return base
    
    @staticmethod
    def serialize_enrollment_with_course(enrollment, course_data: Dict[str, Any]) -> Dict[str, Any]:
        """Serializa una inscripción con datos del curso"""
        base = EnrollmentSerializer.serialize_enrollment(enrollment)
        base.update({
            "course_title": course_data.get("title"),
            "course_category_id": course_data.get("category_id"),
            "course_category_name": course_data.get("category_name"),
            "course_category_description": course_data.get("category_description"),
            "course_category_svgurl": course_data.get("category_svgurl"),
            "course_image": course_data.get("image")
        })
        return base
    
    @staticmethod
    def serialize_enrollment_full(
        enrollment,
        user_data: Dict[str, Any],
        course_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Serializa una inscripción con datos completos del usuario y curso"""
        base = EnrollmentSerializer.serialize_enrollment(enrollment)
        base.update({
            "user": {
                "id": user_data.get("id"),
                "name": user_data.get("name"),
                "email": user_data.get("email"),
                "cellphone": user_data.get("cellphone")
            },
            "course": {
                "id": course_data.get("id"),
                "title": course_data.get("title"),
                "category": {
                    "id": course_data.get("category_id"),
                    "name": course_data.get("category_name"),
                    "description": course_data.get("category_description"),
                    "svgurl": course_data.get("category_svgurl"),
                    "status": course_data.get("category_status")
                },
                "image": course_data.get("image")
            }
        })
        return base
