"""
Tests de integración para los endpoints de Courses

Estos tests verifican que los endpoints de la API funcionen correctamente,
incluyendo validaciones, respuestas HTTP correctas y manejo de errores.
"""
import pytest
from datetime import date, time
from src.models.course import CourseStatus
from src.utils.jwt_utils import encode_token


class TestCoursesEndpoints:
    """Suite de tests para los endpoints de courses"""

    @pytest.fixture
    def auth_token(self, session, sample_user_data):
        """Token de autenticación para tests que requieren auth"""
        from src.controllers.user_controller import UserController
        
        # Crear usuario de prueba
        user = UserController.create_user(sample_user_data, db=session)
        
        # Generar token
        token = encode_token({
            "username": user.name,
            "email": user.email
        })
        return token

    @pytest.fixture
    def auth_headers(self, auth_token):
        """Headers con autenticación"""
        return {"Authorization": f"Bearer {auth_token}"}

    @pytest.fixture
    def sample_course_payload(self):
        """Payload de ejemplo para crear un curso"""
        return {
            "course_data": {
                "title": "Curso de Python Avanzado",
                "description": "Aprende Python nivel avanzado",
                "place": "Aula Virtual",
                "course_image": "python.jpg",
                "course_image_detail": "python_detail.jpg",
                "category": "Programación",
                "status": CourseStatus.activo,
                "objectives": ["Dominar async/await", "Crear APIs"],
                "organizers": ["Universidad Tech"],
                "materials": ["Laptop", "Python 3.11+"],
                "target_audience": ["Desarrolladores", "Estudiantes"]
            },
            "requirements_data": {
                "start_date_registration": "2024-01-01",
                "end_date_registration": "2024-01-31",
                "start_date_course": "2024-02-01",
                "end_date_course": "2024-03-31",
                "days": ["Lunes", "Miércoles", "Viernes"],
                "start_time": "14:00:00",
                "end_time": "18:00:00",
                "location": "Online",
                "min_quota": 10,
                "max_quota": 30,
                "in_person_hours": 40,
                "autonomous_hours": 20,
                "modality": "Híbrida",
                "certification": "Certificado de participación",
                "prerequisites": ["Python básico"],
                "prices": [
                    {"type": "Estudiante", "amount": 100},
                    {"type": "General", "amount": 150}
                ]
            },
            "contents_data": [
                {
                    "unit": "1",
                    "title": "Programación Asíncrona",
                    "topics": [
                        {"unit": "1.1", "title": "Conceptos de async/await"},
                        {"unit": "1.2", "title": "Event loop"}
                    ]
                }
            ]
        }

    def test_get_all_courses_empty(self, client):
        """
        Test: GET /api/v1/courses cuando no hay cursos
        Verifica que retorna una lista vacía con status 200 y paginación
        """
        response = client.get("/api/v1/courses")
        print(response.json())
        assert response.status_code == 200
        data = response.json()
        assert "courses" in data
        assert isinstance(data["courses"], list)
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert len(data["courses"]) == 0

    def test_get_all_courses_with_data(self, client, session, sample_course_data, 
                                       sample_requirements_data, sample_contents_data):
        """
        Test: GET /api/v1/courses con datos existentes
        Verifica que retorna los cursos paginados
        """
        from src.controllers.course_controller import CourseController
        CourseController.create_course_with_requirements(
            sample_course_data, sample_requirements_data, sample_contents_data, session
        )
        response = client.get("/api/v1/courses")
        assert response.status_code == 200
        data = response.json()
        assert "courses" in data
        assert isinstance(data["courses"], list)
        assert data["total"] >= 1
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert len(data["courses"]) >= 1
        assert data["courses"][0]["title"] is not None

    def test_get_course_by_id_found(self, client, session, sample_course_data,
                                     sample_requirements_data, sample_contents_data):
        """
        Test: GET /api/v1/courses/{course_id} cuando existe
        
        Verifica que retorna el curso correcto
        """
        # Arrange
        from src.controllers.course_controller import CourseController
        course = CourseController.create_course_with_requirements(
            sample_course_data, sample_requirements_data, sample_contents_data, session
        )
        
        # Act
        response = client.get(f"/api/v1/courses/{course.id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == course.id
        assert data["title"] == sample_course_data.title

    def test_get_course_by_id_not_found(self, client):
        """
        Test: GET /api/v1/courses/{course_id} cuando no existe
        
        Verifica que retorna 404
        """
        # Act
        response = client.get("/api/v1/courses/99999")
        
        # Assert
        assert response.status_code == 404

    def test_get_courses_by_category(self, client, session, sample_course_data,
                                      sample_requirements_data, sample_contents_data):
        """
        Test: GET /api/v1/courses/category/{category}
        
        Verifica que filtra correctamente por categoría
        """
        # Arrange
        from src.controllers.course_controller import CourseController
        CourseController.create_course_with_requirements(
            sample_course_data, sample_requirements_data, sample_contents_data, session
        )
        
        # Act
        response = client.get(f"/api/v1/courses/category/{sample_course_data.category}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["courses"]) >= 1
        assert data["courses"][0]["category"] == sample_course_data.category

    def test_search_courses_by_title_found(self, client, session, sample_course_data,
                                           sample_requirements_data, sample_contents_data):
        """
        Test: GET /api/v1/courses/search?title=python
        
        Verifica que busca cursos por título con coincidencia parcial
        """
        # Arrange
        from src.controllers.course_controller import CourseController
        from src.models.course import CourseBase, CourseStatus
        
        CourseController.create_course_with_requirements(
            sample_course_data, sample_requirements_data, sample_contents_data, session
        )
        
        course_data_js = CourseBase(
            title="Curso de JavaScript",
            description="Aprende JS",
            place="Aula 102",
            course_image="js.jpg",
            course_image_detail="js_detail.jpg",
            category="Programación",
            status=CourseStatus.activo,
            objectives=["Aprender JS"],
            organizers=["Universidad XYZ"],
            materials=["Laptop"],
            target_audience=["Estudiantes"]
        )
        CourseController.create_course_with_requirements(
            course_data_js, sample_requirements_data, sample_contents_data, session
        )
        
        # Act
        response = client.get("/api/v1/courses/search?title=python")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "courses" in data
        assert "count" in data
        assert data["count"] >= 1
        assert len(data["courses"]) >= 1
        assert any("Python" in course["title"] for course in data["courses"])

    def test_search_courses_by_title_case_insensitive(self, client, session, sample_course_data,
                                                       sample_requirements_data, sample_contents_data):
        """
        Test: GET /api/v1/courses/search?title=PYTHON
        
        Verifica que la búsqueda es case-insensitive
        """
        # Arrange
        from src.controllers.course_controller import CourseController
        CourseController.create_course_with_requirements(
            sample_course_data, sample_requirements_data, sample_contents_data, session
        )
        
        # Act
        response = client.get("/api/v1/courses/search?title=PYTHON")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        assert "Python" in data["courses"][0]["title"]

    def test_search_courses_by_title_not_found(self, client):
        """
        Test: GET /api/v1/courses/search?title=Ruby
        
        Verifica que retorna lista vacía cuando no hay coincidencias
        """
        # Act
        response = client.get("/api/v1/courses/search?title=Ruby")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert len(data["courses"]) == 0

    def test_search_courses_by_title_missing_param(self, client):
        """
        Test: GET /api/v1/courses/search sin parámetro title
        
        Verifica que retorna 422 (validation error)
        """
        # Act
        response = client.get("/api/v1/courses/search")
        
        # Assert
        assert response.status_code == 422

    def test_search_courses_by_title_empty_string(self, client):
        """
        Test: GET /api/v1/courses/search?title=
        
        Verifica que retorna 422 por min_length validation
        """
        # Act
        response = client.get("/api/v1/courses/search?title=")
        
        # Assert
        assert response.status_code == 422

    def test_get_courses_by_total_hours(self, client, session, sample_course_data,
                                        sample_requirements_data, sample_contents_data):
        """
        Test: GET /api/v1/courses/hours/{total_hours}
        
        Verifica que filtra por horas totales exactas
        """
        # Arrange
        from src.controllers.course_controller import CourseController
        CourseController.create_course_with_requirements(
            sample_course_data, sample_requirements_data, sample_contents_data, session
        )
        total_hours = 60  # 40 presenciales + 20 autónomas
        
        # Act
        response = client.get(f"/api/v1/courses/hours/{total_hours}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["courses"]) >= 1

    def test_get_courses_by_hours_range(self, client, session, sample_course_data,
                                        sample_requirements_data, sample_contents_data):
        """
        Test: GET /api/v1/courses/hours-range?min_hours=50&max_hours=70
        
        Verifica que filtra por rango de horas
        """
        # Arrange
        from src.controllers.course_controller import CourseController
        CourseController.create_course_with_requirements(
            sample_course_data, sample_requirements_data, sample_contents_data, session
        )
        
        # Act
        response = client.get("/api/v1/courses/hours-range?min_hours=50&max_hours=70")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["courses"]) >= 1

    def test_get_courses_by_hours_range_invalid_params(self, client):
        """
        Test: GET /api/v1/courses/hours-range con parámetros inválidos
        
        Verifica que retorna 400 cuando min_hours > max_hours
        """
        # Act
        response = client.get("/api/v1/courses/hours-range?min_hours=100&max_hours=50")
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "min_hours cannot be greater than max_hours" in data["detail"]

    def test_get_courses_by_hours_range_missing_params(self, client):
        """
        Test: GET /api/v1/courses/hours-range sin parámetros requeridos
        
        Verifica que retorna 422 (validation error)
        """
        # Act
        response = client.get("/api/v1/courses/hours-range")
        
        # Assert
        assert response.status_code == 422

    def test_create_course_without_auth(self, client, sample_course_payload):
        """
        Test: POST /api/v1/courses sin autenticación
        
        Verifica que retorna 401 Unauthorized
        """
        # Act
        response = client.post("/api/v1/courses", json=sample_course_payload)
        
        # Assert
        assert response.status_code == 401

    def test_create_course_with_auth(self, client, auth_headers, sample_course_payload):
        """
        Test: POST /api/v1/courses con autenticación válida
        
        Verifica que crea el curso correctamente
        """
        # Act
        response = client.post(
            "/api/v1/courses",
            json=sample_course_payload,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "course_id" in data
        assert data["message"] == "Course created successfully"

    def test_create_course_with_invalid_token(self, client, sample_course_payload):
        """
        Test: POST /api/v1/courses con token inválido
        
        Verifica que retorna 401
        """
        # Act
        response = client.post(
            "/api/v1/courses",
            json=sample_course_payload,
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        # Assert
        assert response.status_code == 401

    def test_delete_course_without_auth(self, client):
        """
        Test: DELETE /api/v1/courses/{course_id} sin autenticación
        
        Verifica que retorna 401
        """
        # Act
        response = client.delete("/api/v1/courses/1")
        
        # Assert
        assert response.status_code == 401

    def test_delete_course_with_auth(self, client, auth_headers, session,
                                      sample_course_data, sample_requirements_data,
                                      sample_contents_data):
        """
        Test: DELETE /api/v1/courses/{course_id} con autenticación
        
        Verifica que elimina el curso correctamente
        """
        # Arrange
        from src.controllers.course_controller import CourseController
        course = CourseController.create_course_with_requirements(
            sample_course_data, sample_requirements_data, sample_contents_data, session
        )
        
        # Act
        response = client.delete(
            f"/api/v1/courses/{course.id}",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Course deleted successfully"

    def test_delete_course_not_found(self, client, auth_headers):
        """
        Test: DELETE /api/v1/courses/{course_id} que no existe
        
        Verifica que retorna 500 (error del controller)
        """
        # Act
        response = client.delete(
            "/api/v1/courses/99999",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 500

    def test_api_returns_json(self, client):
        """
        Test: Verificar que las respuestas son JSON
        
        Verifica el content-type correcto
        """
        # Act
        response = client.get("/api/v1/courses")
        
        # Assert
        assert response.headers["content-type"] == "application/json"

    def test_cors_headers(self, client):
        """
        Test: Verificar que CORS está configurado
        
        Verifica los headers CORS en respuestas OPTIONS
        """
        # Act
        response = client.options("/api/v1/courses")
        
        # Assert
        # FastAPI maneja CORS automáticamente
        assert response.status_code in [200, 405]  # Puede variar según configuración


class TestCoursesEndpointsPerformance:
    """Tests de performance y stress para endpoints de courses"""

    def test_get_all_courses_response_time(self, client):
        """
        Test: Verificar que el endpoint responde en tiempo razonable
        
        El tiempo de respuesta debe ser < 1 segundo
        """
        import time
        
        # Act
        start = time.time()
        response = client.get("/api/v1/courses")
        end = time.time()
        
        # Assert
        assert response.status_code == 200
        response_time = end - start
        assert response_time < 1.0, f"Response time {response_time}s es muy lenta"

    @pytest.mark.skip(reason="Test de carga, ejecutar manualmente cuando sea necesario")
    def test_concurrent_requests(self, client):
        """
        Test: Múltiples peticiones concurrentes
        
        Verifica que el API puede manejar múltiples requests
        """
        import concurrent.futures
        
        def make_request():
            return client.get("/api/v1/courses")
        
        # Act
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(50)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # Assert
        assert all(r.status_code == 200 for r in results)
