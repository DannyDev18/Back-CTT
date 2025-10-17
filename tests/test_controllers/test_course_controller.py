"""
Tests unitarios para el CourseController

Estos tests verifican que los métodos del controller funcionen correctamente
utilizando una base de datos en memoria y datos de prueba.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import date, time
import json

from src.controllers.course_controller import CourseController
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


class TestCourseController:
    """Suite de tests para CourseController"""

    def test_create_course_with_requirements(
        self,
        session,
        sample_course_data,
        sample_requirements_data,
        sample_contents_data
    ):
        """
        Test: Crear un curso completo con requisitos y contenidos
        
        Verifica que:
        - El curso se crea correctamente
        - Los requisitos se asocian al curso
        - Los contenidos y topics se crean correctamente
        - El total de horas se calcula automáticamente
        """
        # Arrange (preparar)
        controller = CourseController()
        
        # Act (ejecutar)
        course = controller.create_course_with_requirements(
            course_data=sample_course_data,
            requirements_data=sample_requirements_data,
            contents_data=sample_contents_data,
            db=session
        )
        
        # Assert (verificar)
        assert course is not None
        assert course.id is not None
        assert course.title == "Curso de Python"
        assert course.category == "Programación"
        
        # Verificar que los requisitos se crearon
        requirements = session.query(CourseRequirement).filter(
            CourseRequirement.course_id == course.id
        ).first()
        assert requirements is not None
        assert requirements.total_hours == 60  # 40 presenciales + 20 autónomas
        assert requirements.min_quota == 10
        assert requirements.max_quota == 30
        
        # Verificar que los contenidos se crearon
        contents = session.query(CourseContent).filter(
            CourseContent.course_id == course.id
        ).all()
        assert len(contents) == 2
        assert contents[0].title == "Introducción a Python"
        
        # Verificar que los topics se crearon
        topics = session.query(CourseContentTopic).filter(
            CourseContentTopic.course_id == course.id
        ).all()
        assert len(topics) == 4  # 2 topics por cada contenido

    def test_get_all_courses_empty(self, session):
        """
        Test: Obtener todos los cursos cuando no hay ninguno
        
        Verifica que retorna una lista vacía cuando no hay cursos
        """
        # Act
        courses = CourseController.get_all_courses(db=session)
        
        # Assert
        assert courses == []
        assert isinstance(courses, list)

    def test_get_all_courses_with_data(
        self,
        session,
        sample_course_data,
        sample_requirements_data,
        sample_contents_data
    ):
        """
        Test: Obtener todos los cursos cuando existen datos
        
        Verifica que retorna todos los cursos con su información completa
        """
        # Arrange
        # Crear 2 cursos de prueba
        course1 = CourseController.create_course_with_requirements(
            course_data=sample_course_data,
            requirements_data=sample_requirements_data,
            contents_data=sample_contents_data,
            db=session
        )
        
        course_data2 = CourseBase(
            title="Curso de JavaScript",
            description="Aprende JS",
            place="Aula 102",
            course_image="js.jpg",
            category="Programación",
            status="active",
            objectives=["Aprender JS"],
            organizers=["Universidad XYZ"],
            materials=["Laptop"],
            target_audience=["Estudiantes"]
        )
        course2 = CourseController.create_course_with_requirements(
            course_data=course_data2,
            requirements_data=sample_requirements_data,
            contents_data=sample_contents_data,
            db=session
        )
        
        # Act
        courses = CourseController.get_all_courses(db=session)
        
        # Assert
        assert len(courses) == 2
        assert courses[0]["title"] in ["Curso de Python", "Curso de JavaScript"]
        assert "requirements" in courses[0]
        assert "contents" in courses[0]

    def test_get_course_by_id_found(
        self,
        session,
        sample_course_data,
        sample_requirements_data,
        sample_contents_data
    ):
        """
        Test: Obtener curso por ID cuando existe
        
        Verifica que retorna el curso correcto cuando existe
        """
        # Arrange
        created_course = CourseController.create_course_with_requirements(
            course_data=sample_course_data,
            requirements_data=sample_requirements_data,
            contents_data=sample_contents_data,
            db=session
        )
        
        # Act
        course = CourseController.get_course_by_id(created_course.id, db=session)
        
        # Assert
        assert course is not None
        assert course.id == created_course.id
        assert course.title == "Curso de Python"

    def test_get_course_by_id_not_found(self, session):
        """
        Test: Obtener curso por ID cuando no existe
        
        Verifica que retorna None cuando el curso no existe
        """
        # Act
        course = CourseController.get_course_by_id(999, db=session)
        
        # Assert
        assert course is None

    def test_get_courses_by_category(
        self,
        session,
        sample_course_data,
        sample_requirements_data,
        sample_contents_data
    ):
        """
        Test: Obtener cursos filtrados por categoría
        
        Verifica que retorna solo los cursos de la categoría especificada
        """
        # Arrange
        # Crear curso de Programación
        CourseController.create_course_with_requirements(
            course_data=sample_course_data,
            requirements_data=sample_requirements_data,
            contents_data=sample_contents_data,
            db=session
        )
        
        # Crear curso de otra categoría
        course_data_design = CourseBase(
            title="Curso de Diseño",
            description="Aprende diseño",
            place="Aula 103",
            course_image="design.jpg",
            category="Diseño",
            status="active",
            objectives=["Aprender diseño"],
            organizers=["Universidad XYZ"],
            materials=["Laptop"],
            target_audience=["Estudiantes"]
        )
        CourseController.create_course_with_requirements(
            course_data=course_data_design,
            requirements_data=sample_requirements_data,
            contents_data=sample_contents_data,
            db=session
        )
        
        # Act
        programming_courses = CourseController.get_courses_by_category(
            category="Programación",
            db=session
        )
        
        # Assert
        assert len(programming_courses) == 1
        assert programming_courses[0]["category"] == "Programación"
        assert programming_courses[0]["title"] == "Curso de Python"

    def test_get_course_with_full_data(
        self,
        session,
        sample_course_data,
        sample_requirements_data,
        sample_contents_data
    ):
        """
        Test: Obtener curso completo con todos sus datos relacionados
        
        Verifica que retorna el curso con requirements y contents
        """
        # Arrange
        created_course = CourseController.create_course_with_requirements(
            course_data=sample_course_data,
            requirements_data=sample_requirements_data,
            contents_data=sample_contents_data,
            db=session
        )
        
        # Act
        course_dict = CourseController.get_course_with_full_data(
            created_course.id,
            db=session
        )
        
        # Assert
        assert course_dict is not None
        assert course_dict["id"] == created_course.id
        assert course_dict["requirements"] is not None
        assert "registration" in course_dict["requirements"]
        assert "courseSchedule" in course_dict["requirements"]
        assert len(course_dict["contents"]) == 2

    def test_get_course_with_full_data_not_found(self, session):
        """
        Test: Obtener curso completo cuando no existe
        
        Verifica que retorna None cuando el curso no existe
        """
        # Act
        course_dict = CourseController.get_course_with_full_data(999, db=session)
        
        # Assert
        assert course_dict is None

    def test_get_courses_by_total_hours(
        self,
        session,
        sample_course_data,
        sample_requirements_data,
        sample_contents_data
    ):
        """
        Test: Obtener cursos por total de horas exacto
        
        Verifica que filtra cursos por el total de horas especificado
        """
        # Arrange
        # Crear curso con 60 horas (40 + 20)
        CourseController.create_course_with_requirements(
            course_data=sample_course_data,
            requirements_data=sample_requirements_data,
            contents_data=sample_contents_data,
            db=session
        )
        
        # Crear otro curso con diferentes horas
        requirements_data_80h = CourseRequirementBase(
            start_date_registration=date(2024, 1, 1),
            end_date_registration=date(2024, 1, 31),
            start_date_course=date(2024, 2, 1),
            end_date_course=date(2024, 3, 31),
            days=["Lunes", "Miércoles"],
            start_time=time(14, 0),
            end_time=time(18, 0),
            location="Aula Virtual",
            min_quota=10,
            max_quota=30,
            in_person_hours=60,
            autonomous_hours=20,
            modality="Híbrida",
            certification="Certificado",
            prerequisites=["Ninguno"],
            prices=[{"type": "General", "amount": 150}]
        )
        
        course_data2 = CourseBase(
            title="Curso Avanzado",
            description="Curso avanzado",
            place="Aula 102",
            course_image="advanced.jpg",
            category="Programación",
            status="active",
            objectives=["Avanzar"],
            organizers=["Universidad XYZ"],
            materials=["Laptop"],
            target_audience=["Profesionales"]
        )
        
        CourseController.create_course_with_requirements(
            course_data=course_data2,
            requirements_data=requirements_data_80h,
            contents_data=sample_contents_data,
            db=session
        )
        
        # Act
        courses_60h = CourseController.get_courses_by_total_hours(60, db=session)
        courses_80h = CourseController.get_courses_by_total_hours(80, db=session)
        
        # Assert
        assert len(courses_60h) == 1
        assert courses_60h[0]["requirements"]["hours"]["total"] == 60
        assert len(courses_80h) == 1
        assert courses_80h[0]["requirements"]["hours"]["total"] == 80

    def test_get_courses_by_hours_range(
        self,
        session,
        sample_course_data,
        sample_requirements_data,
        sample_contents_data
    ):
        """
        Test: Obtener cursos por rango de horas
        
        Verifica que filtra cursos dentro del rango especificado
        """
        # Arrange
        CourseController.create_course_with_requirements(
            course_data=sample_course_data,
            requirements_data=sample_requirements_data,
            contents_data=sample_contents_data,
            db=session
        )
        
        # Act
        courses = CourseController.get_courses_by_hours_range(
            min_hours=50,
            max_hours=70,
            db=session
        )
        
        # Assert
        assert len(courses) == 1
        assert courses[0]["requirements"]["hours"]["total"] == 60

    def test_delete_course_success(
        self,
        session,
        sample_course_data,
        sample_requirements_data,
        sample_contents_data
    ):
        """
        Test: Eliminar un curso existente
        
        Verifica que el curso se elimina correctamente
        """
        # Arrange
        course = CourseController.create_course_with_requirements(
            course_data=sample_course_data,
            requirements_data=sample_requirements_data,
            contents_data=sample_contents_data,
            db=session
        )
        course_id = course.id
        
        # Act
        CourseController.delete_course(course_id, db=session)
        
        # Assert
        deleted_course = CourseController.get_course_by_id(course_id, db=session)
        assert deleted_course is None

    def test_delete_course_not_found(self, session):
        """
        Test: Intentar eliminar un curso que no existe
        
        Verifica que lanza una excepción cuando el curso no existe
        """
        # Act & Assert
        with pytest.raises(ValueError, match="Course not found"):
            CourseController.delete_course(999, db=session)
