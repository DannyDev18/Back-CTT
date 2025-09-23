import json
from datetime import datetime, date, time
from typing import List
from sqlmodel import Session, select
from src.models.course import (
    Course,
    CourseRequirement,
    CourseContent,
    CourseContentTopic,
    CourseBase,
    CourseRequirementBase,
    CourseContentBase,
    CourseContentTopicBase
)

class CourseController:

    @staticmethod
    def create_course_with_requirements(
        course_data: CourseBase,
        requirements_data: CourseRequirementBase,
        contents_data: List[CourseContentBase],
        db: Session
    ) -> Course:
        # Crear el curso principal
        course = Course(
            title=course_data.title,
            description=course_data.description,
            place=course_data.place,
            objectives=json.dumps(course_data.objectives),
            organizers=json.dumps(course_data.organizers),
            materials=json.dumps(course_data.materials),
            target_audience=json.dumps(course_data.target_audience)
        )
        db.add(course)
        db.flush()  # Para obtener el ID del curso

        # Crear los requisitos del curso
        requirements = CourseRequirement(
            course_id=course.id,
            start_date_registration=requirements_data.start_date_registration,
            end_date_registration=requirements_data.end_date_registration,
            start_date_course=requirements_data.start_date_course,
            end_date_course=requirements_data.end_date_course,
            days=json.dumps(requirements_data.days),
            start_time=str(requirements_data.start_time),
            end_time=str(requirements_data.end_time),
            location=requirements_data.location,
            min_quota=requirements_data.min_quota,
            max_quota=requirements_data.max_quota,
            total_hours=requirements_data.total_hours,
            in_person_hours=requirements_data.in_person_hours,
            autonomous_hours=requirements_data.autonomous_hours,
            modality=requirements_data.modality,
            certification=requirements_data.certification,
            prerequisites=json.dumps(requirements_data.prerequisites),
            prices=json.dumps(requirements_data.prices)
        )
        db.add(requirements)

        # Crear los contenidos del curso
        for content_data in contents_data:
            content = CourseContent(
                course_id=course.id,
                unit=content_data.unit,
                title=content_data.title,
                topics_data=json.dumps([
                    {"unit": topic.unit, "title": topic.title}
                    for topic in content_data.topics
                ])
            )
            db.add(content)
            db.flush()  # Para obtener el ID del contenido

            # Crear los topics del contenido
            for topic_data in content_data.topics:
                topic = CourseContentTopic(
                    course_id=course.id,
                    content_id=content.id,
                    unit=topic_data.unit,
                    title=topic_data.title
                )
                db.add(topic)

        db.commit()
        db.refresh(course)
        return course

    @staticmethod
    def get_all_courses(db: Session) -> List[dict]:
        statement = select(Course)
        courses = db.exec(statement).all()

        result = []
        for course in courses:
            course_dict = CourseController._convert_course_to_dict(course, db)
            result.append(course_dict)

        return result

    @staticmethod
    def _convert_course_to_dict(course: Course, db: Session) -> dict:
        """Convierte un objeto Course en un diccionario con todos los datos relacionados"""

        # Obtener requirements
        requirements = db.exec(
            select(CourseRequirement).where(CourseRequirement.course_id == course.id)
        ).first()

        # Obtener contents
        contents = db.exec(
            select(CourseContent).where(CourseContent.course_id == course.id)
        ).all()

        # Convertir datos para respuesta
        course_dict = {
            "id": course.id,
            "title": course.title,
            "description": course.description,
            "place": course.place,
            "objectives": json.loads(course.objectives) if course.objectives else [],
            "organizers": json.loads(course.organizers) if course.organizers else [],
            "materials": json.loads(course.materials) if course.materials else [],
            "target_audience": json.loads(course.target_audience) if course.target_audience else [],
            "requirements": None,
            "contents": []
        }

        if requirements:
            course_dict["requirements"] = {
                "registration": {
                    "startDate": str(requirements.start_date_registration),
                    "endDate": str(requirements.end_date_registration)
                },
                "courseSchedule": {
                    "startDate": str(requirements.start_date_course),
                    "endDate": str(requirements.end_date_course),
                    "days": json.loads(requirements.days) if requirements.days else [],
                    "startTime": requirements.start_time,
                    "endTime": requirements.end_time
                },
                "location": requirements.location,
                "quota": {
                    "min": requirements.min_quota,
                    "max": requirements.max_quota
                },
                "prices": json.loads(requirements.prices) if requirements.prices else [],
                "hours": {
                    "total": requirements.total_hours,
                    "inPerson": requirements.in_person_hours,
                    "autonomous": requirements.autonomous_hours
                },
                "targetAudience": json.loads(course.target_audience) if course.target_audience else [],
                "modality": requirements.modality,
                "certification": requirements.certification,
                "prerequisites": json.loads(requirements.prerequisites) if requirements.prerequisites else []
            }

        for content in contents:
            topics_data = json.loads(content.topics_data) if content.topics_data else []
            topics = []
            for topic_data in topics_data:
                topics.append({
                    "unit": topic_data.get("unit", ""),
                    "title": topic_data.get("title", "")
                })

            course_dict["contents"].append({
                "unit": content.unit,
                "title": content.title,
                "topics": topics
            })

        return course_dict

    @staticmethod
    def get_course_by_id(course_id: int, db: Session) -> Course | None:
        statement = select(Course).where(Course.id == course_id)
        course = db.exec(statement).first()
        return course

    @staticmethod
    def get_course_with_full_data(course_id: int, db: Session) -> dict | None:
        course = CourseController.get_course_by_id(course_id, db)
        if not course:
            return None

        return CourseController._convert_course_to_dict(course, db)
