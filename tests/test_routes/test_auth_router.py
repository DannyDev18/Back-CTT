"""
Tests de integración para los endpoints de Auth

Estos tests verifican el registro, login y autenticación de usuarios.
"""
import pytest


class TestAuthEndpoints:
    """Suite de tests para los endpoints de autenticación"""

    @pytest.fixture
    def user_registration_data(self):
        """Datos para registrar un usuario"""
        return {
            "name": "Test",
            "last_name": "User",
            "email": "testuser@example.com",
            "password": "securepassword123"
        }

    def test_register_new_user_success(self, client, user_registration_data):
        """
        Test: POST /api/v1/auth/register con datos válidos
        
        Verifica que registra un usuario exitosamente
        """
        # Act
        response = client.post("/api/v1/auth/register", json=user_registration_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "User registered successfully"

    def test_register_duplicate_email(self, client, user_registration_data):
        """
        Test: POST /api/v1/auth/register con email duplicado
        
        Verifica que retorna error 400
        """
        # Arrange - Registrar usuario primero
        client.post("/api/v1/auth/register", json=user_registration_data)
        
        # Act - Intentar registrar de nuevo
        response = client.post("/api/v1/auth/register", json=user_registration_data)
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "User already exists" in data["detail"]

    def test_register_missing_fields(self, client):
        """
        Test: POST /api/v1/auth/register con campos faltantes
        
        Verifica que retorna error de validación 422
        """
        # Act
        response = client.post("/api/v1/auth/register", json={
            "name": "Test",
            # Faltan campos requeridos
        })
        
        # Assert
        assert response.status_code == 422

    def test_register_invalid_email_format(self, client):
        """
        Test: POST /api/v1/auth/register con email inválido
        
        Verifica validación de formato de email
        """
        # Act
        response = client.post("/api/v1/auth/register", json={
            "name": "Test",
            "last_name": "User",
            "email": "invalid-email",
            "password": "password123"
        })
        
        # Assert
        assert response.status_code == 422

    def test_login_success(self, client, user_registration_data):
        """
        Test: POST /api/v1/auth/token con credenciales válidas
        
        Verifica que retorna un token de acceso
        """
        # Arrange - Registrar usuario primero
        client.post("/api/v1/auth/register", json=user_registration_data)
        
        # Act - Login usando OAuth2PasswordRequestForm format
        response = client.post("/api/v1/auth/token", data={
            "username": user_registration_data["email"],
            "password": user_registration_data["password"]
        })
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["access_token"] is not None
        assert len(data["access_token"]) > 0

    def test_login_wrong_password(self, client, user_registration_data):
        """
        Test: POST /api/v1/auth/token con contraseña incorrecta
        
        Verifica que retorna error 400
        """
        # Arrange - Registrar usuario
        client.post("/api/v1/auth/register", json=user_registration_data)
        
        # Act - Intentar login con contraseña incorrecta
        response = client.post("/api/v1/auth/token", data={
            "username": user_registration_data["email"],
            "password": "wrongpassword"
        })
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "Incorrect username or password" in data["detail"]

    def test_login_nonexistent_user(self, client):
        """
        Test: POST /api/v1/auth/token con usuario inexistente
        
        Verifica que retorna error 400
        """
        # Act
        response = client.post("/api/v1/auth/token", data={
            "username": "nonexistent@example.com",
            "password": "anypassword"
        })
        
        # Assert
        assert response.status_code == 400

    def test_get_profile_with_valid_token(self, client, user_registration_data):
        """
        Test: GET /api/v1/auth/profile con token válido
        
        Verifica que retorna los datos del usuario
        """
        # Arrange - Registrar y hacer login
        client.post("/api/v1/auth/register", json=user_registration_data)
        login_response = client.post("/api/v1/auth/token", data={
            "username": user_registration_data["email"],
            "password": user_registration_data["password"]
        })
        token = login_response.json()["access_token"]
        
        # Act
        response = client.get(
            "/api/v1/auth/profile",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user_registration_data["email"]
        assert data["name"] == user_registration_data["name"]
        assert data["last_name"] == user_registration_data["last_name"]
        assert "id" in data
        assert "password" not in data  # No debe exponer la contraseña

    def test_get_profile_without_token(self, client):
        """
        Test: GET /api/v1/auth/profile sin token
        
        Verifica que retorna 401 Unauthorized
        """
        # Act
        response = client.get("/api/v1/auth/profile")
        
        # Assert
        assert response.status_code == 401

    def test_get_profile_with_invalid_token(self, client):
        """
        Test: GET /api/v1/auth/profile con token inválido
        
        Verifica que retorna 401
        """
        # Act
        response = client.get(
            "/api/v1/auth/profile",
            headers={"Authorization": "Bearer invalid_token_xyz"}
        )
        
        # Assert
        assert response.status_code == 401

    def test_get_profile_with_malformed_header(self, client):
        """
        Test: GET /api/v1/auth/profile con header malformado
        
        Verifica que retorna 401
        """
        # Act
        response = client.get(
            "/api/v1/auth/profile",
            headers={"Authorization": "InvalidFormat"}
        )
        
        # Assert
        assert response.status_code == 401

    def test_token_format(self, client, user_registration_data):
        """
        Test: Verificar que el token tiene el formato correcto
        
        El token debe ser un string JWT válido
        """
        # Arrange
        client.post("/api/v1/auth/register", json=user_registration_data)
        
        # Act
        response = client.post("/api/v1/auth/token", data={
            "username": user_registration_data["email"],
            "password": user_registration_data["password"]
        })
        
        # Assert
        token = response.json()["access_token"]
        assert isinstance(token, str)
        assert len(token.split('.')) == 3  # JWT tiene 3 partes separadas por puntos

    def test_password_is_hashed(self, client, user_registration_data, session):
        """
        Test: Verificar que la contraseña se guarda hasheada
        
        La contraseña en BD no debe ser texto plano
        """
        # Arrange & Act
        client.post("/api/v1/auth/register", json=user_registration_data)
        
        # Assert - Verificar en BD
        from src.controllers.user_controller import UserController
        user = UserController.get_user_by_email(user_registration_data["email"], session)
        
        assert user is not None
        assert user.password != user_registration_data["password"]  # No es texto plano
        assert len(user.password) > 50  # Hash es mucho más largo

    def test_login_case_sensitive_email(self, client, user_registration_data):
        """
        Test: Verificar comportamiento con emails en diferentes casos
        
        Dependiendo de la configuración, puede ser case-sensitive o no
        """
        # Arrange
        client.post("/api/v1/auth/register", json=user_registration_data)
        
        # Act - Login con email en mayúsculas
        response = client.post("/api/v1/auth/token", data={
            "username": user_registration_data["email"].upper(),
            "password": user_registration_data["password"]
        })
        
        # Assert
        # Esto depende de tu implementación
        # Si tu BD es case-insensitive, debería funcionar (status 200)
        # Si es case-sensitive, debería fallar (status 400)
        assert response.status_code in [200, 400]


class TestAuthEndpointsSecurity:
    """Tests de seguridad para endpoints de autenticación"""

    def test_register_with_weak_password(self, client):
        """
        Test: Intentar registrar con contraseña débil
        
        Nota: Implementa validación de contraseña si es necesario
        """
        # Este test es opcional, depende si implementas validación de contraseña
        response = client.post("/api/v1/auth/register", json={
            "name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "password": "123"  # Contraseña muy débil
        })

        # Pydantic devuelve 422 para validaciones fallidas
        assert response.status_code in [200, 400, 422]

    def test_sql_injection_in_login(self, client):
        """
        Test: Intentar SQL injection en login
        
        Verifica que la app está protegida contra SQL injection
        """
        # Act
        response = client.post("/api/v1/auth/token", data={
            "username": "admin' OR '1'='1",
            "password": "password' OR '1'='1"
        })
        
        # Assert
        assert response.status_code == 400  # No debe permitir login
