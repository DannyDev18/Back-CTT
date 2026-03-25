"""
Tests unitarios para el CourseController

Estos tests verifican que los métodos del controller funcionen correctamente
utilizando una base de datos en memoria y datos de prueba.
"""
import pytest
from datetime import date, time

from src.controllers.course_controller import CourseController
from sqlalchemy import select
from src.models.course import (
    CourseRequirement,
    CourseContent,
    CourseStatus,
    CourseCreate,
    CourseRequirementCreate,
    CourseContentCreate,
    CourseContentTopicRead
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
            db=session,
            current_user_id=1
        )
        
        # Assert (verificar)
        assert course is not None
        assert isinstance(course, dict)
        assert course["id"] is not None
        assert course["title"] == "Curso de Python"
        assert course["category"] == "Programación"
        
        # Verificar que los requisitos se crearon
        course_id = course["id"]
        requirements = session.exec(
            select(CourseRequirement).where(CourseRequirement.course_id == course_id)
        ).scalars().first()
        assert requirements is not None
        assert requirements.in_person_hours + requirements.autonomous_hours == 60  # 40 + 20
        assert requirements.min_quota == 10
        assert requirements.max_quota == 30
        
        # Verificar que los contenidos se crearon
        contents = session.exec(
            select(CourseContent).where(CourseContent.course_id == course_id)
        ).scalars().all()
        assert len(contents) == 2
        assert contents[0].title == "Introducción a Python"
        
        # Verificar que los topics están en el campo JSON
        import json
        topics_data = json.loads(contents[0].topics)
        assert len(topics_data) == 2  # 2 topics en el primer contenido

    def test_get_all_courses_empty(self, session):
        """
        Test: Obtener todos los cursos cuando no hay ninguno
        Verifica que retorna una respuesta paginada vacía
        """
        result = CourseController.get_all_courses(db=session)
        assert isinstance(result, dict)
        assert result["total"] == 0
        assert result["page"] == 1
        assert result["page_size"] == 10
        assert isinstance(result["courses"], list)
        assert len(result["courses"]) == 0



    def test_get_all_courses_with_data(
        self,
        session,
        sample_course_data,
        sample_requirements_data,
        sample_contents_data,
        sample_category
    ):
        """
        Test: Obtener todos los cursos cuando existen datos
        Verifica que retorna todos los cursos con su información completa y paginada
        """
        # Crear 2 cursos de prueba
        CourseController.create_course_with_requirements(
            course_data=sample_course_data,
            requirements_data=sample_requirements_data,
            contents_data=sample_contents_data,
            db=session,
            current_user_id=1
        )
        course_data2 = CourseCreate(
            title="Curso de JavaScript",
            description="Aprende JS",
            place="Aula 102",
            course_image="js.jpg",
            course_image_detail="js_detail.jpg",
            category_id=sample_category.id,
            status=CourseStatus.ACTIVO,
            objectives=["Aprender JS"],
            organizers=["Universidad XYZ"],
            materials=["Laptop"],
            target_audience=["Estudiantes"]
        )
        CourseController.create_course_with_requirements(
            course_data=course_data2,
            requirements_data=sample_requirements_data,
            contents_data=sample_contents_data,
            db=session,
            current_user_id=1
        )
        result = CourseController.get_all_courses(db=session)
        assert isinstance(result, dict)
        assert result["total"] >= 2
        assert result["page"] == 1
        assert result["page_size"] == 10
        assert isinstance(result["courses"], list)
        assert len(result["courses"]) >= 2
        titles = [c["title"] for c in result["courses"]]
        assert "Curso de Python" in titles or "Curso de JavaScript" in titles
        assert "requirements" in result["courses"][0]
        assert "contents" in result["courses"][0]

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
            db=session,
            current_user_id=1
        )
        
        # Act
        course = CourseController.get_course_by_id(created_course["id"], db=session)
        
        # Assert
        assert course is not None
        assert course["id"] == created_course["id"]
        assert course["title"] == "Curso de Python"

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
        sample_contents_data,
        sample_category
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
            db=session,
            current_user_id=1
        )
        
        # Crear curso de otra categoría
        course_data_design = CourseCreate(
            title="Curso de Diseño",
            description="Aprende diseño",
            place="Aula 103",
            course_image="design.jpg",
            course_image_detail="design_detail.jpg",
            category_id=sample_category.id,
            status=CourseStatus.ACTIVO,
            objectives=["Aprender diseño"],
            organizers=["Universidad XYZ"],
            materials=["Laptop"],
            target_audience=["Estudiantes"]
        )
        CourseController.create_course_with_requirements(
            course_data=course_data_design,
            requirements_data=sample_requirements_data,
            contents_data=sample_contents_data,
            db=session,
            current_user_id=1
        )
        
        # Act
        programming_courses = CourseController.get_courses_by_category(
            category_id=sample_category.id,
            db=session
        )
        
        # Assert
        assert len(programming_courses) == 2  # sample_course_data + course_data_design
        assert programming_courses[0]["category"] == "Programación"
        assert programming_courses[0]["title"] == "Curso de Python"

    def test_search_courses_by_title(
        self,
        session,
        sample_course_data,
        sample_requirements_data,
        sample_contents_data,
        sample_category
    ):
        """
        Test: Buscar cursos por título con coincidencia parcial
        
        Verifica que la búsqueda funciona con coincidencias parciales y case-insensitive
        """
        # Arrange
        CourseController.create_course_with_requirements(
            course_data=sample_course_data,
            requirements_data=sample_requirements_data,
            contents_data=sample_contents_data,
            db=session,
            current_user_id=1
        )

        course_data_js = CourseCreate(
            title="Curso de JavaScript Avanzado",
            description="Aprende JavaScript",
            place="Aula 102",
            course_image="js.jpg",
            course_image_detail="js_detail.jpg",
            category_id=sample_category.id,
            status=CourseStatus.ACTIVO,
            objectives=["Aprender JS"],
            organizers=["Universidad XYZ"],
            materials=["Laptop"],
            target_audience=["Estudiantes"]
        )
        CourseController.create_course_with_requirements(
            course_data=course_data_js,
            requirements_data=sample_requirements_data,
            contents_data=sample_contents_data,
            db=session,
            current_user_id=1
        )
        
        # Act - Buscar por término parcial
        results_python = CourseController.search_courses_by_title("python", db=session)
        results_javascript = CourseController.search_courses_by_title("JavaScript", db=session)
        results_curso = CourseController.search_courses_by_title("Curso", db=session)
        results_not_found = CourseController.search_courses_by_title("Ruby", db=session)
        
        # Assert
        assert len(results_python) == 1
        assert results_python[0]["title"] == "Curso de Python"
        
        assert len(results_javascript) == 1
        assert "JavaScript" in results_javascript[0]["title"]
        
        assert len(results_curso) >= 2
        
        assert len(results_not_found) == 0

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
            db=session,
            current_user_id=1
        )
        
        # Act
        course_dict = CourseController.get_course_by_id(
            created_course["id"],
            db=session
        )
        
        # Assert
        assert course_dict is not None
        assert course_dict["id"] == created_course["id"]
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
        course_dict = CourseController.get_course_by_id(999, db=session)
        
        # Assert
        assert course_dict is None

    # Test deshabilitado: get_courses_by_total_hours ya no existe en el controller
    # Ahora se usa get_courses_by_hours_range
    # def test_get_courses_by_total_hours(
    #     self,
    #     session,
    #     sample_course_data,
    #     sample_requirements_data,
    #     sample_contents_data
    # ):
    #     """
    #     Test: Obtener cursos por total de horas exacto
    #     
    #     Verifica que filtra cursos por el total de horas especificado
    #     """
    #     pass

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
            db=session,
            current_user_id=1
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
            db=session,
            current_user_id=1
        )
        course_id = course["id"]
        
        # Act
        CourseController.delete_course(course_id, db=session)
        
        # Assert
        deleted_course = CourseController.get_course_by_id(course_id, db=session)
        assert deleted_course["status"] == CourseStatus.INACTIVO

    def test_delete_course_not_found(self, session):
        """
        Test: Intentar eliminar un curso que no existe
        
        Verifica que lanza una excepción cuando el curso no existe
        """
        # Act & Assert
        with pytest.raises(ValueError, match="Course not found"):
            CourseController.delete_course(999, db=session)

    def test_update_course_with_requirements(
        self,
        session,
        sample_course_data,
        sample_requirements_data,
        sample_contents_data
    ):
        """
        Test: Actualizar un curso existente con nuevos datos
        
        Verifica que:
        - El curso se actualiza correctamente
        - Los requisitos se actualizan
        - Los contenidos se actualizan
        """
        # Arrange
        course = CourseController.create_course_with_requirements(
            course_data=sample_course_data,
            requirements_data=sample_requirements_data,
            contents_data=sample_contents_data,
            db=session,
            current_user_id=1
        )
        course_id = course["id"]
        
        from src.models.course import CourseUpdate, CourseRequirementUpdate
        
        updated_course_data = CourseUpdate(
            title="Curso de Python Avanzado",
            description="Aprende Python avanzado",
            place="Aula 201",
            course_image="python_advanced.jpg",
            course_image_detail="python_advanced_detail.jpg",
            category="Programación",
            status=CourseStatus.ACTIVO,
            objectives=["Aprender Python avanzado"],
            organizers=["Universidad ABC"],
            materials=["Laptop", "Libros"],
            target_audience=["Desarrolladores"]
        )
        
        updated_requirements_data = CourseRequirementUpdate(
            start_date_registration=date(2024, 2, 1),
            end_date_registration=date(2024, 2, 28),
            start_date_course=date(2024, 3, 1),
            end_date_course=date(2024, 4, 30),
            days=["Martes", "Jueves"],
            start_time=time(10, 0),
            end_time=time(14, 0),
            location="Aula Virtual",
            min_quota=15,
            max_quota=40,
            in_person_hours=50,
            autonomous_hours=30,
            modality="En línea",
            certification="Certificado Avanzado",
            prerequisites=["Conocimientos básicos de Python"],
            prices=[{"type": "General", "amount": 200}]
        )
        
        updated_contents_data = [
            CourseContentCreate(
                unit="Unidad 1 - Avanzado",
                title="Funciones Avanzadas",
                topics=[
                    CourseContentTopicRead(unit="Unidad 1", title="Decoradores"),
                    CourseContentTopicRead(unit="Unidad 1", title="Generadores")
                ]
            )
        ]
        
        # Act
        updated_course = CourseController.update_course_with_requirements(
            course_id=course_id,
            db=session,
            course_data=updated_course_data,
            requirements_data=updated_requirements_data,    
            contents_data=updated_contents_data
        )

        # Assert
        assert updated_course["title"] == "Curso de Python Avanzado"
        assert updated_course["place"] == "Aula 201"
        # Verificar requisitos actualizados
        requirements = session.exec(
            select(CourseRequirement).where(CourseRequirement.course_id == course_id)
        ).scalars().first()
        assert requirements.start_date_registration == date(2024, 2, 1)
        assert requirements.in_person_hours + requirements.autonomous_hours == 80  # 50 + 30
        assert requirements.min_quota == 15
        assert requirements.max_quota == 40
        # Verificar contenidos actualizados
        contents = session.exec(
            select(CourseContent).where(CourseContent.course_id == course_id)
        ).scalars().all()
        assert len(contents) == 1
        assert contents[0].unit == "Unidad 1 - Avanzado"
        assert contents[0].title == "Funciones Avanzadas"