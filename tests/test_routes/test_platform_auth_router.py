"""
Tests de integración para los endpoints de Platform Auth

Estos tests verifican el registro, login y autenticación de usuarios de plataforma.
"""
import pytest


class TestPlatformAuthEndpoints:
    """Suite de tests para los endpoints de autenticación de plataforma"""

    @pytest.fixture
    def user_platform_registration_data(self):
        """Datos para registrar un usuario de plataforma"""
        return {
            "identification": "1234567890",
            "first_name": "Juan",
            "second_name": "Carlos",
            "first_last_name": "Pérez",
            "second_last_name": "García",
            "cellphone": "0998765432",
            "email": "juan.perez@example.com",
            "address": "Av. Principal 123",
            "type": "Estudiante",
            "password": "securepassword123"
        }

    @pytest.fixture
    def minimal_user_registration_data(self):
        """Datos mínimos para registrar un usuario (campos opcionales vacíos)"""
        return {
            "identification": "9876543210",
            "first_name": "María",
            "first_last_name": "López",
            "cellphone": "0987654321",
            "email": "maria.lopez@example.com",
            "type": "Externo",
            "password": "password123"
        }

    def test_register_new_platform_user_success(self, client, user_platform_registration_data):
        """
        Test: POST /api/v1/platform-auth/register con datos válidos
        
        Verifica que registra un usuario de plataforma exitosamente
        """
        # Act
        response = client.post("/api/v1/platform-auth/register", json=user_platform_registration_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Platform user registered successfully"

    def test_register_platform_user_with_minimal_fields(self, client, minimal_user_registration_data):
        """
        Test: POST /api/v1/platform-auth/register con campos mínimos
        
        Verifica que puede registrar sin campos opcionales
        """
        # Act
        response = client.post("/api/v1/platform-auth/register", json=minimal_user_registration_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Platform user registered successfully"

    def test_register_duplicate_email(self, client, user_platform_registration_data):
        """
        Test: POST /api/v1/platform-auth/register con email duplicado
        
        Verifica que retorna error 400
        """
        # Arrange - Registrar usuario primero
        client.post("/api/v1/platform-auth/register", json=user_platform_registration_data)
        
        # Act - Intentar registrar de nuevo con mismo email
        duplicate_data = user_platform_registration_data.copy()
        duplicate_data["identification"] = "0000000000"  # Diferente identificación
        response = client.post("/api/v1/platform-auth/register", json=duplicate_data)
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "email already exists" in data["detail"]

    def test_register_duplicate_identification(self, client, user_platform_registration_data):
        """
        Test: POST /api/v1/platform-auth/register con identificación duplicada
        
        Verifica que retorna error 400
        """
        # Arrange - Registrar usuario primero
        client.post("/api/v1/platform-auth/register", json=user_platform_registration_data)
        
        # Act - Intentar registrar de nuevo con misma identificación
        duplicate_data = user_platform_registration_data.copy()
        duplicate_data["email"] = "otro@example.com"  # Diferente email
        response = client.post("/api/v1/platform-auth/register", json=duplicate_data)
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "identification already exists" in data["detail"]

    def test_register_missing_required_fields(self, client):
        """
        Test: POST /api/v1/platform-auth/register con campos requeridos faltantes
        
        Verifica que retorna error de validación 422
        """
        # Act - Faltan campos requeridos
        response = client.post("/api/v1/platform-auth/register", json={
            "first_name": "Test",
            # Faltan campos requeridos
        })
        
        # Assert
        assert response.status_code == 422

    def test_register_invalid_email_format(self, client):
        """
        Test: POST /api/v1/platform-auth/register con email inválido
        
        Verifica validación de formato de email
        """
        # Act
        response = client.post("/api/v1/platform-auth/register", json={
            "identification": "1234567890",
            "first_name": "Test",
            "first_last_name": "User",
            "cellphone": "0987654321",
            "email": "invalid-email",
            "type": "Estudiante",
            "password": "password123"
        })
        
        # Assert
        assert response.status_code == 422

    def test_register_invalid_user_type(self, client):
        """
        Test: POST /api/v1/platform-auth/register con tipo de usuario inválido
        
        Verifica validación del enum de tipo de usuario
        """
        # Act
        response = client.post("/api/v1/platform-auth/register", json={
            "identification": "1234567890",
            "first_name": "Test",
            "first_last_name": "User",
            "cellphone": "0987654321",
            "email": "test@example.com",
            "type": "InvalidType",
            "password": "password123"
        })
        
        # Assert
        assert response.status_code == 422

    def test_register_all_user_types(self, client):
        """
        Test: Registrar usuarios con todos los tipos válidos
        
        Verifica que acepta: Estudiante, Externo, Administrativo
        """
        user_types = ["Estudiante", "Externo", "Administrativo"]
        
        for i, user_type in enumerate(user_types):
            # Act
            response = client.post("/api/v1/platform-auth/register", json={
                "identification": f"123456789{i}",
                "first_name": "Test",
                "first_last_name": "User",
                "cellphone": f"098765432{i}",
                "email": f"test{i}@example.com",
                "type": user_type,
                "password": "password123"
            })
            
            # Assert
            assert response.status_code == 200, f"Failed for type: {user_type}"

    def test_login_success(self, client, user_platform_registration_data):
        """
        Test: POST /api/v1/platform-auth/token con credenciales válidas
        
        Verifica que retorna un token de acceso
        """
        # Arrange - Registrar usuario primero
        client.post("/api/v1/platform-auth/register", json=user_platform_registration_data)
        
        # Act - Login usando OAuth2PasswordRequestForm format
        response = client.post("/api/v1/platform-auth/token", data={
            "username": user_platform_registration_data["email"],
            "password": user_platform_registration_data["password"]
        })
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert data["access_token"] is not None
        assert len(data["access_token"]) > 0

    def test_login_wrong_password(self, client, user_platform_registration_data):
        """
        Test: POST /api/v1/platform-auth/token con contraseña incorrecta
        
        Verifica que retorna error 400
        """
        # Arrange - Registrar usuario
        client.post("/api/v1/platform-auth/register", json=user_platform_registration_data)
        
        # Act - Intentar login con contraseña incorrecta
        response = client.post("/api/v1/platform-auth/token", data={
            "username": user_platform_registration_data["email"],
            "password": "wrongpassword"
        })
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "Incorrect username or password" in data["detail"]

    def test_login_nonexistent_user(self, client):
        """
        Test: POST /api/v1/platform-auth/token con usuario inexistente
        
        Verifica que retorna error 400
        """
        # Act
        response = client.post("/api/v1/platform-auth/token", data={
            "username": "nonexistent@example.com",
            "password": "anypassword"
        })
        
        # Assert
        assert response.status_code == 400

    def test_get_profile_with_valid_token(self, client, user_platform_registration_data):
        """
        Test: GET /api/v1/platform-auth/profile con token válido
        
        Verifica que retorna los datos completos del usuario
        """
        # Arrange - Registrar y hacer login
        client.post("/api/v1/platform-auth/register", json=user_platform_registration_data)
        login_response = client.post("/api/v1/platform-auth/token", data={
            "username": user_platform_registration_data["email"],
            "password": user_platform_registration_data["password"]
        })
        token = login_response.json()["access_token"]
        
        # Act
        response = client.get(
            "/api/v1/platform-auth/profile",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user_platform_registration_data["email"]
        assert data["identification"] == user_platform_registration_data["identification"]
        assert data["first_name"] == user_platform_registration_data["first_name"]
        assert data["second_name"] == user_platform_registration_data["second_name"]
        assert data["first_last_name"] == user_platform_registration_data["first_last_name"]
        assert data["second_last_name"] == user_platform_registration_data["second_last_name"]
        assert data["cellphone"] == user_platform_registration_data["cellphone"]
        assert data["address"] == user_platform_registration_data["address"]
        assert data["type"] == user_platform_registration_data["type"]
        assert "id" in data
        assert "password" not in data  # No debe exponer la contraseña

    def test_get_profile_without_token(self, client):
        """
        Test: GET /api/v1/platform-auth/profile sin token
        
        Verifica que retorna 401 Unauthorized
        """
        # Act
        response = client.get("/api/v1/platform-auth/profile")
        
        # Assert
        assert response.status_code == 401

    def test_get_profile_with_invalid_token(self, client):
        """
        Test: GET /api/v1/platform-auth/profile con token inválido
        
        Verifica que retorna 401
        """
        # Act
        response = client.get(
            "/api/v1/platform-auth/profile",
            headers={"Authorization": "Bearer invalid_token_xyz"}
        )
        
        # Assert
        assert response.status_code == 401

    def test_get_profile_with_malformed_header(self, client):
        """
        Test: GET /api/v1/platform-auth/profile con header malformado
        
        Verifica que retorna 401
        """
        # Act
        response = client.get(
            "/api/v1/platform-auth/profile",
            headers={"Authorization": "InvalidFormat"}
        )
        
        # Assert
        assert response.status_code == 401

    def test_token_format(self, client, user_platform_registration_data):
        """
        Test: Verificar que el token tiene el formato correcto
        
        El token debe ser un string JWT válido
        """
        # Arrange
        client.post("/api/v1/platform-auth/register", json=user_platform_registration_data)
        
        # Act
        response = client.post("/api/v1/platform-auth/token", data={
            "username": user_platform_registration_data["email"],
            "password": user_platform_registration_data["password"]
        })
        
        # Assert
        token = response.json()["access_token"]
        assert isinstance(token, str)
        assert len(token.split('.')) == 3  # JWT tiene 3 partes separadas por puntos

    def test_password_is_hashed(self, client, user_platform_registration_data, session):
        """
        Test: Verificar que la contraseña se guarda hasheada
        
        La contraseña en BD no debe ser texto plano
        """
        # Arrange & Act
        client.post("/api/v1/platform-auth/register", json=user_platform_registration_data)
        
        # Assert - Verificar en BD
        from src.controllers.user_platform_controller import UserPlatformController
        user = UserPlatformController.get_user_by_email(
            user_platform_registration_data["email"], 
            session
        )
        
        assert user is not None
        assert user.password != user_platform_registration_data["password"]  # No es texto plano
        assert len(user.password) > 50  # Hash es mucho más largo
        assert user.password.startswith("$2b$")  # bcrypt hash

    def test_profile_returns_correct_user_type(self, client):
        """
        Test: Verificar que el perfil retorna el tipo de usuario correcto
        
        Verifica que el enum se serializa correctamente
        """
        user_types = ["Estudiante", "Externo", "Administrativo"]
        
        for i, user_type in enumerate(user_types):
            # Arrange - Registrar usuario
            registration_data = {
                "identification": f"999999999{i}",
                "first_name": "Test",
                "first_last_name": "User",
                "cellphone": f"099999999{i}",
                "email": f"type_test{i}@example.com",
                "type": user_type,
                "password": "password123"
            }
            client.post("/api/v1/platform-auth/register", json=registration_data)
            
            # Act - Login y obtener perfil
            login_response = client.post("/api/v1/platform-auth/token", data={
                "username": registration_data["email"],
                "password": registration_data["password"]
            })
            token = login_response.json()["access_token"]
            
            profile_response = client.get(
                "/api/v1/platform-auth/profile",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            # Assert
            assert profile_response.status_code == 200
            profile_data = profile_response.json()
            assert profile_data["type"] == user_type


class TestPlatformAuthEndpointsSecurity:
    """Tests de seguridad para endpoints de autenticación de plataforma"""

    def test_sql_injection_in_login(self, client):
        """
        Test: Intentar SQL injection en login
        
        Verifica que la app está protegida contra SQL injection
        """
        # Act
        response = client.post("/api/v1/platform-auth/token", data={
            "username": "admin' OR '1'='1",
            "password": "password' OR '1'='1"
        })
        
        # Assert
        assert response.status_code == 400  # No debe permitir login

    def test_sql_injection_in_identification(self, client):
        """
        Test: Intentar SQL injection en el campo identification
        
        Verifica protección contra SQL injection en registro
        """
        # Act
        response = client.post("/api/v1/platform-auth/register", json={
            "identification": "1234'; DROP TABLE users_platform; --",
            "first_name": "Test",
            "first_last_name": "User",
            "cellphone": "0987654321",
            "email": "test@example.com",
            "type": "Estudiante",
            "password": "password123"
        })
        
        # Assert - Debería registrarse como string normal o fallar por validación
        assert response.status_code in [200, 400, 422]

    def test_xss_in_name_fields(self, client):
        """
        Test: Verificar que los campos de nombre manejan caracteres especiales
        
        Prevención de XSS
        """
        # Act
        response = client.post("/api/v1/platform-auth/register", json={
            "identification": "1234567890",
            "first_name": "<script>alert('xss')</script>",
            "first_last_name": "User",
            "cellphone": "0987654321",
            "email": "xss.test@example.com",
            "type": "Estudiante",
            "password": "password123"
        })
        
        # Assert - Debería aceptarlo como string o fallar por validación
        # La protección XSS debe ser en el frontend al renderizar
        assert response.status_code in [200, 400, 422]
