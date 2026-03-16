# 🌐 Guía de Testing para Endpoints (Routes/API)

## 📋 Tabla de Contenidos
1. [Introducción](#introducción)
2. [¿Qué son los Tests de Endpoints?](#qué-son-los-tests-de-endpoints)
3. [TestClient de FastAPI](#testclient-de-fastapi)
4. [Estructura de Tests](#estructura-de-tests)
5. [Patrones Comunes](#patrones-comunes)
6. [Ejemplos Prácticos](#ejemplos-prácticos)
7. [Testing de Autenticación](#testing-de-autenticación)
8. [Mejores Prácticas](#mejores-prácticas)

---

## 🎯 Introducción

Los tests de endpoints (también llamados **tests de integración** o **tests de API**) verifican que tus rutas HTTP funcionen correctamente, incluyendo:

- ✅ Códigos de estado HTTP correctos (200, 404, 401, etc.)
- ✅ Formato de respuestas JSON
- ✅ Validación de parámetros
- ✅ Autenticación y autorización
- ✅ Manejo de errores
- ✅ Headers HTTP

---

## 📚 ¿Qué son los Tests de Endpoints?

### Diferencia entre Tests Unitarios y Tests de Endpoints

| Aspecto | Tests Unitarios | Tests de Endpoints |
|---------|----------------|-------------------|
| **Alcance** | Función individual | Endpoint completo (HTTP) |
| **Base de datos** | Mock/In-memory | In-memory (TestClient) |
| **HTTP** | No involucrado | Sí (requests/responses) |
| **Velocidad** | Muy rápido | Rápido |
| **Qué testea** | Lógica de negocio | API completa |

### Ejemplo Visual

```
┌─────────────────────────────────────────┐
│  Test de Endpoint (Integración)        │
│  ┌───────────────────────────────────┐  │
│  │ HTTP Request                      │  │
│  │ GET /api/v1/courses              │  │
│  └────────────┬──────────────────────┘  │
│               │                          │
│  ┌────────────▼──────────────────────┐  │
│  │ Router (courses_router.py)       │  │
│  └────────────┬──────────────────────┘  │
│               │                          │
│  ┌────────────▼──────────────────────┐  │
│  │ Controller (course_controller.py)│  │
│  └────────────┬──────────────────────┘  │
│               │                          │
│  ┌────────────▼──────────────────────┐  │
│  │ Database (SQLModel)              │  │
│  └────────────┬──────────────────────┘  │
│               │                          │
│  ┌────────────▼──────────────────────┐  │
│  │ HTTP Response                     │  │
│  │ {"courses": [...]}               │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

---

## 🔧 TestClient de FastAPI

FastAPI proporciona `TestClient` que simula un cliente HTTP sin necesidad de levantar un servidor real.

### Configuración Básica

```python
from fastapi.testclient import TestClient
from src.main import app

# Crear cliente de prueba
client = TestClient(app)

# Hacer peticiones
response = client.get("/api/v1/courses")
assert response.status_code == 200
```

### Ventajas de TestClient

- ⚡ **Rápido**: No levanta servidor real
- 🔄 **Sincrónico**: Más fácil de testear
- 🎯 **Completo**: Prueba toda la pila HTTP
- 🛠️ **Fixture friendly**: Funciona con pytest

---

## 📁 Estructura de Tests

```
tests/
├── test_controllers/           # Tests unitarios
│   ├── test_course_controller.py
│   └── test_user_controller.py
│
└── test_routes/                # Tests de endpoints (NUEVO)
    ├── __init__.py
    ├── test_courses_router.py
    └── test_auth_router.py
```

---

## 🎨 Patrones Comunes

### 1. Test de Endpoint GET Básico

```python
def test_get_all_courses(client):
    """Test: GET /api/v1/courses"""
    # Act
    response = client.get("/api/v1/courses")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "courses" in data
    assert isinstance(data["courses"], list)
```

### 2. Test de Endpoint POST con Datos

```python
def test_create_course(client, auth_headers):
    """Test: POST /api/v1/courses"""
    # Arrange
    payload = {
        "title": "Nuevo Curso",
        "description": "Descripción"
    }
    
    # Act
    response = client.post(
        "/api/v1/courses",
        json=payload,
        headers=auth_headers
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "course_id" in data
```

### 3. Test de Endpoint con Parámetros Query

```python
def test_filter_courses(client):
    """Test: GET /api/v1/courses?category=Programación"""
    # Act
    response = client.get(
        "/api/v1/courses",
        params={"category": "Programación"}
    )
    
    # Assert
    assert response.status_code == 200
```

### 4. Test de Endpoint con Path Parameters

```python
def test_get_course_by_id(client):
    """Test: GET /api/v1/courses/{course_id}"""
    # Act
    response = client.get("/api/v1/courses/1")
    
    # Assert
    assert response.status_code in [200, 404]
```

### 5. Test de Endpoint DELETE

```python
def test_delete_course(client, auth_headers):
    """Test: DELETE /api/v1/courses/{course_id}"""
    # Act
    response = client.delete(
        "/api/v1/courses/1",
        headers=auth_headers
    )
    
    # Assert
    assert response.status_code in [200, 404]
```

### 6. Test de Validación de Datos

```python
def test_create_course_invalid_data(client, auth_headers):
    """Test: POST con datos inválidos"""
    # Arrange
    payload = {
        "title": "",  # Título vacío (inválido)
    }
    
    # Act
    response = client.post(
        "/api/v1/courses",
        json=payload,
        headers=auth_headers
    )
    
    # Assert
    assert response.status_code == 422  # Validation error
```

### 7. Test de Error 404

```python
def test_get_nonexistent_course(client):
    """Test: GET curso que no existe"""
    # Act
    response = client.get("/api/v1/courses/99999")
    
    # Assert
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
```

---

## 🔐 Testing de Autenticación

### Fixture para Token de Autenticación

```python
@pytest.fixture
def auth_token(session, sample_user_data):
    """Genera un token de autenticación válido"""
    from src.controllers.user_controller import UserController
    from src.utils.jwt_utils import encode_token
    
    # Crear usuario
    user = UserController.create_user(sample_user_data, db=session)
    
    # Generar token
    token = encode_token({
        "username": user.name,
        "email": user.email
    })
    return token

@pytest.fixture
def auth_headers(auth_token):
    """Headers con Bearer token"""
    return {"Authorization": f"Bearer {auth_token}"}
```

### Uso en Tests

```python
def test_protected_endpoint(client, auth_headers):
    """Test: Endpoint protegido con autenticación"""
    # Act
    response = client.get(
        "/api/v1/auth/profile",
        headers=auth_headers
    )
    
    # Assert
    assert response.status_code == 200

def test_protected_endpoint_without_auth(client):
    """Test: Endpoint protegido sin autenticación"""
    # Act
    response = client.get("/api/v1/auth/profile")
    
    # Assert
    assert response.status_code == 401
```

---

## 💡 Ejemplos Prácticos

### Ejemplo Completo: Test de Registro y Login

```python
class TestAuthFlow:
    """Test del flujo completo de autenticación"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_complete_auth_flow(self, client):
        """
        Test: Flujo completo de registro → login → acceso a perfil
        """
        # 1. Registrar usuario
        register_data = {
            "name": "Juan",
            "last_name": "Pérez",
            "email": "juan@test.com",
            "password": "password123"
        }
        register_response = client.post(
            "/api/v1/auth/register",
            json=register_data
        )
        assert register_response.status_code == 200
        
        # 2. Login
        login_response = client.post(
            "/api/v1/auth/token",
            data={
                "username": register_data["email"],
                "password": register_data["password"]
            }
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # 3. Acceder al perfil
        profile_response = client.get(
            "/api/v1/auth/profile",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert profile_response.status_code == 200
        profile = profile_response.json()
        assert profile["email"] == register_data["email"]
```

### Ejemplo: Test de CRUD Completo

```python
def test_course_crud_flow(client, auth_headers, session):
    """
    Test: Flujo completo CREATE → READ → UPDATE → DELETE
    """
    # 1. CREATE
    create_payload = {
        "course_data": {...},
        "requirements_data": {...},
        "contents_data": [...]
    }
    create_response = client.post(
        "/api/v1/courses",
        json=create_payload,
        headers=auth_headers
    )
    assert create_response.status_code == 200
    course_id = create_response.json()["course_id"]
    
    # 2. READ
    read_response = client.get(f"/api/v1/courses/{course_id}")
    assert read_response.status_code == 200
    course = read_response.json()
    assert course["id"] == course_id
    
    # 3. DELETE
    delete_response = client.delete(
        f"/api/v1/courses/{course_id}",
        headers=auth_headers
    )
    assert delete_response.status_code == 200
    
    # 4. Verificar eliminación
    verify_response = client.get(f"/api/v1/courses/{course_id}")
    assert verify_response.status_code == 404
```

---

## ✨ Mejores Prácticas

### 1. Usar Fixtures para Datos Comunes

```python
@pytest.fixture
def sample_course_payload():
    """Payload reutilizable para crear cursos"""
    return {
        "course_data": {...},
        "requirements_data": {...},
        "contents_data": [...]
    }

def test_1(client, sample_course_payload):
    response = client.post("/api/v1/courses", json=sample_course_payload)
    # ...

def test_2(client, sample_course_payload):
    response = client.post("/api/v1/courses", json=sample_course_payload)
    # ...
```

### 2. Testear Todos los Códigos HTTP

```python
def test_endpoint_status_codes(client):
    """Test: Verificar todos los códigos de estado posibles"""
    # 200 - Success
    response = client.get("/api/v1/courses")
    assert response.status_code == 200
    
    # 404 - Not Found
    response = client.get("/api/v1/courses/99999")
    assert response.status_code == 404
    
    # 401 - Unauthorized
    response = client.post("/api/v1/courses", json={})
    assert response.status_code == 401
    
    # 422 - Validation Error
    response = client.post("/api/v1/auth/register", json={})
    assert response.status_code == 422
```

### 3. Verificar Estructura de Respuestas

```python
def test_response_structure(client):
    """Test: Verificar que la respuesta tiene la estructura correcta"""
    # Act
    response = client.get("/api/v1/courses")
    data = response.json()
    
    # Assert estructura
    assert "courses" in data
    assert isinstance(data["courses"], list)
    
    if len(data["courses"]) > 0:
        course = data["courses"][0]
        assert "id" in course
        assert "title" in course
        assert "description" in course
```

### 4. Tests Parametrizados para Múltiples Casos

```python
@pytest.mark.parametrize("endpoint,expected_status", [
    ("/api/v1/courses", 200),
    ("/api/v1/courses/1", 404),
    ("/api/v1/courses/category/Programming", 200),
])
def test_multiple_endpoints(client, endpoint, expected_status):
    """Test: Múltiples endpoints con parametrize"""
    response = client.get(endpoint)
    assert response.status_code == expected_status
```

### 5. Testear Headers

```python
def test_response_headers(client):
    """Test: Verificar headers de respuesta"""
    # Act
    response = client.get("/api/v1/courses")
    
    # Assert
    assert response.headers["content-type"] == "application/json"
    assert "access-control-allow-origin" in response.headers  # CORS
```

---

## 🚀 Comandos para Ejecutar

```bash
# Todos los tests de routes
pytest tests/test_routes/ -v

# Solo test de courses router
pytest tests/test_routes/test_courses_router.py -v

# Solo test de auth router
pytest tests/test_routes/test_auth_router.py -v

# Con cobertura
pytest tests/test_routes/ --cov=src/routes --cov-report=html

# Un test específico
pytest tests/test_routes/test_auth_router.py::TestAuthEndpoints::test_login_success -v
```

---

## 📊 Diferencias Clave

### Tests de Controllers vs Tests de Routes

```python
# ❌ Test de Controller (Unitario)
def test_controller(session):
    result = CourseController.get_all_courses(session)
    assert isinstance(result, list)

# ✅ Test de Route (Integración)
def test_route(client):
    response = client.get("/api/v1/courses")
    assert response.status_code == 200
    assert "courses" in response.json()
```

---

## 🎯 Checklist para Tests de Endpoints

- [ ] **Happy path**: ¿Funciona cuando todo está bien?
- [ ] **Validaciones**: ¿Rechaza datos inválidos? (422)
- [ ] **Autenticación**: ¿Protege endpoints privados? (401)
- [ ] **Not found**: ¿Maneja recursos inexistentes? (404)
- [ ] **Errores**: ¿Maneja excepciones? (500)
- [ ] **Estructura JSON**: ¿Responde con el formato correcto?
- [ ] **Headers**: ¿Incluye headers necesarios?
- [ ] **CORS**: ¿Permite peticiones cross-origin?

---

## 📚 Recursos Adicionales

- [TestClient - FastAPI](https://fastapi.tiangolo.com/tutorial/testing/)
- [HTTP Status Codes](https://httpstatuses.com/)
- [REST API Testing Best Practices](https://restfulapi.net/rest-api-testing/)

---

**¡Ahora puedes testear tus APIs completas! 🎉**
