"""
Tests unitarios para el UserPlatformController

Estos tests verifican que los métodos del controller de usuarios de plataforma
funcionen correctamente.
"""
import pytest
from src.controllers.user_platform_controller import UserPlatformController
from src.models.user_platform import UserPlatform, UserPlatformType


class TestUserPlatformController:
    """Suite de tests para UserPlatformController"""

    def test_create_user_success(self, session, sample_user_platform_data):
        """
        Test: Crear un usuario de plataforma exitosamente
        
        Verifica que el usuario se crea y se guarda correctamente en la BD
        """
        # Act
        created_user = UserPlatformController.create_user(sample_user_platform_data, db=session)
        
        # Assert
        assert created_user is not None
        assert created_user.id is not None
        assert created_user.email == "pedro.martinez@example.com"
        assert created_user.identification == "1234567890"
        assert created_user.first_name == "Pedro"
        assert created_user.second_name == "Luis"
        assert created_user.first_last_name == "Martínez"
        assert created_user.second_last_name == "López"
        assert created_user.cellphone == "0987654321"
        assert created_user.address == "Calle Test 123"
        assert created_user.type == UserPlatformType.ESTUDIANTE

    def test_get_user_by_email_found(self, session, sample_user_platform_data):
        """
        Test: Buscar usuario por email cuando existe
        
        Verifica que retorna el usuario correcto cuando existe
        """
        # Arrange
        UserPlatformController.create_user(sample_user_platform_data, db=session)
        
        # Act
        found_user = UserPlatformController.get_user_by_email(
            email="pedro.martinez@example.com",
            db=session
        )
        
        # Assert
        assert found_user is not None
        assert found_user.email == "pedro.martinez@example.com"
        assert found_user.first_name == "Pedro"
        assert found_user.identification == "1234567890"

    def test_get_user_by_email_not_found(self, session):
        """
        Test: Buscar usuario por email cuando no existe
        
        Verifica que retorna None cuando el usuario no existe
        """
        # Act
        found_user = UserPlatformController.get_user_by_email(
            email="noexiste@example.com",
            db=session
        )
        
        # Assert
        assert found_user is None

    def test_get_user_by_identification_found(self, session, sample_user_platform_data):
        """
        Test: Buscar usuario por identificación cuando existe
        
        Verifica que retorna el usuario correcto cuando existe
        """
        # Arrange
        UserPlatformController.create_user(sample_user_platform_data, db=session)
        
        # Act
        found_user = UserPlatformController.get_user_by_identification(
            identification="1234567890",
            db=session
        )
        
        # Assert
        assert found_user is not None
        assert found_user.identification == "1234567890"
        assert found_user.email == "pedro.martinez@example.com"
        assert found_user.first_name == "Pedro"

    def test_get_user_by_identification_not_found(self, session):
        """
        Test: Buscar usuario por identificación cuando no existe
        
        Verifica que retorna None cuando el usuario no existe
        """
        # Act
        found_user = UserPlatformController.get_user_by_identification(
            identification="9999999999",
            db=session
        )
        
        # Assert
        assert found_user is None

    def test_create_multiple_users(self, session):
        """
        Test: Crear múltiples usuarios
        
        Verifica que se pueden crear varios usuarios sin conflictos
        """
        # Arrange
        user1 = UserPlatform(
            identification="1111111111",
            first_name="Usuario",
            first_last_name="Uno",
            cellphone="0991111111",
            email="user1@example.com",
            type=UserPlatformType.ESTUDIANTE,
            password="pass1"
        )
        user2 = UserPlatform(
            identification="2222222222",
            first_name="Usuario",
            first_last_name="Dos",
            cellphone="0992222222",
            email="user2@example.com",
            type=UserPlatformType.EXTERNO,
            password="pass2"
        )
        
        # Act
        created_user1 = UserPlatformController.create_user(user1, db=session)
        created_user2 = UserPlatformController.create_user(user2, db=session)
        
        # Assert
        assert created_user1.id != created_user2.id
        assert created_user1.email == "user1@example.com"
        assert created_user1.identification == "1111111111"
        assert created_user2.email == "user2@example.com"
        assert created_user2.identification == "2222222222"

    def test_create_users_with_different_types(self, session):
        """
        Test: Crear usuarios con diferentes tipos
        
        Verifica que se pueden crear usuarios con todos los tipos válidos
        """
        # Arrange
        estudiante = UserPlatform(
            identification="1111111111",
            first_name="Estudiante",
            first_last_name="Test",
            cellphone="0991111111",
            email="estudiante@example.com",
            type=UserPlatformType.ESTUDIANTE,
            password="pass1"
        )
        externo = UserPlatform(
            identification="2222222222",
            first_name="Externo",
            first_last_name="Test",
            cellphone="0992222222",
            email="externo@example.com",
            type=UserPlatformType.EXTERNO,
            password="pass2"
        )
        administrativo = UserPlatform(
            identification="3333333333",
            first_name="Administrativo",
            first_last_name="Test",
            cellphone="0993333333",
            email="administrativo@example.com",
            type=UserPlatformType.ADMINISTRATIVO,
            password="pass3"
        )
        
        # Act
        created_estudiante = UserPlatformController.create_user(estudiante, db=session)
        created_externo = UserPlatformController.create_user(externo, db=session)
        created_administrativo = UserPlatformController.create_user(administrativo, db=session)
        
        # Assert
        assert created_estudiante.type == UserPlatformType.ESTUDIANTE
        assert created_externo.type == UserPlatformType.EXTERNO
        assert created_administrativo.type == UserPlatformType.ADMINISTRATIVO

    def test_create_user_with_minimal_fields(self, session):
        """
        Test: Crear usuario con campos mínimos (sin opcionales)
        
        Verifica que se puede crear un usuario sin los campos opcionales
        """
        # Arrange
        user = UserPlatform(
            identification="1234567890",
            first_name="Test",
            second_name=None,  # Opcional
            first_last_name="User",
            second_last_name=None,  # Opcional
            cellphone="0987654321",
            email="minimal@example.com",
            address=None,  # Opcional
            type=UserPlatformType.ESTUDIANTE,
            password="password123"
        )
        
        # Act
        created_user = UserPlatformController.create_user(user, db=session)
        
        # Assert
        assert created_user is not None
        assert created_user.identification == "1234567890"
        assert created_user.first_name == "Test"
        assert created_user.second_name is None
        assert created_user.second_last_name is None
        assert created_user.address is None

    def test_create_user_with_all_fields(self, session):
        """
        Test: Crear usuario con todos los campos incluyendo opcionales
        
        Verifica que se puede crear un usuario con todos los campos
        """
        # Arrange
        user = UserPlatform(
            identification="9876543210",
            first_name="Juan",
            second_name="Carlos",
            first_last_name="Pérez",
            second_last_name="García",
            cellphone="0998765432",
            email="full@example.com",
            address="Av. Principal 456",
            type=UserPlatformType.ADMINISTRATIVO,
            password="password456"
        )
        
        # Act
        created_user = UserPlatformController.create_user(user, db=session)
        
        # Assert
        assert created_user is not None
        assert created_user.identification == "9876543210"
        assert created_user.first_name == "Juan"
        assert created_user.second_name == "Carlos"
        assert created_user.first_last_name == "Pérez"
        assert created_user.second_last_name == "García"
        assert created_user.cellphone == "0998765432"
        assert created_user.email == "full@example.com"
        assert created_user.address == "Av. Principal 456"
        assert created_user.type == UserPlatformType.ADMINISTRATIVO

    def test_search_by_email_is_exact_match(self, session):
        """
        Test: Verificar que la búsqueda por email es exacta
        
        Verifica que solo retorna coincidencias exactas
        """
        # Arrange
        user = UserPlatform(
            identification="1234567890",
            first_name="Test",
            first_last_name="User",
            cellphone="0987654321",
            email="test@example.com",
            type=UserPlatformType.ESTUDIANTE,
            password="password123"
        )
        UserPlatformController.create_user(user, db=session)
        
        # Act
        found_exact = UserPlatformController.get_user_by_email("test@example.com", session)
        found_partial = UserPlatformController.get_user_by_email("test@", session)
        
        # Assert
        assert found_exact is not None
        assert found_partial is None  # Búsqueda parcial no debe funcionar

    def test_search_by_identification_is_exact_match(self, session):
        """
        Test: Verificar que la búsqueda por identificación es exacta
        
        Verifica que solo retorna coincidencias exactas
        """
        # Arrange
        user = UserPlatform(
            identification="1234567890",
            first_name="Test",
            first_last_name="User",
            cellphone="0987654321",
            email="test@example.com",
            type=UserPlatformType.ESTUDIANTE,
            password="password123"
        )
        UserPlatformController.create_user(user, db=session)
        
        # Act
        found_exact = UserPlatformController.get_user_by_identification("1234567890", session)
        found_partial = UserPlatformController.get_user_by_identification("12345", session)
        
        # Assert
        assert found_exact is not None
        assert found_partial is None  # Búsqueda parcial no debe funcionar
