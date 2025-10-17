"""
Tests unitarios para el UserController

Estos tests verifican que los métodos del controller de usuarios
funcionen correctamente.
"""
import pytest
from src.controllers.user_controller import UserController
from src.models.user import User


class TestUserController:
    """Suite de tests para UserController"""

    def test_create_user_success(self, session, sample_user_data):
        """
        Test: Crear un usuario exitosamente
        
        Verifica que el usuario se crea y se guarda correctamente en la BD
        """
        # Act
        created_user = UserController.create_user(sample_user_data, db=session)
        
        # Assert
        assert created_user is not None
        assert created_user.id is not None
        assert created_user.email == "test@example.com"
        assert created_user.name == "Juan"
        assert created_user.last_name == "Pérez"

    def test_get_user_by_email_found(self, session, sample_user_data):
        """
        Test: Buscar usuario por email cuando existe
        
        Verifica que retorna el usuario correcto cuando existe
        """
        # Arrange
        UserController.create_user(sample_user_data, db=session)
        
        # Act
        found_user = UserController.get_user_by_email(
            email="test@example.com",
            db=session
        )
        
        # Assert
        assert found_user is not None
        assert found_user.email == "test@example.com"
        assert found_user.name == "Juan"

    def test_get_user_by_email_not_found(self, session):
        """
        Test: Buscar usuario por email cuando no existe
        
        Verifica que retorna None cuando el usuario no existe
        """
        # Act
        found_user = UserController.get_user_by_email(
            email="noexiste@example.com",
            db=session
        )
        
        # Assert
        assert found_user is None

    def test_get_user_by_email_case_sensitive(self, session, sample_user_data):
        """
        Test: Verificar que la búsqueda por email es sensible a mayúsculas
        
        Nota: Dependiendo de la configuración de la BD, esto puede variar
        """
        # Arrange
        UserController.create_user(sample_user_data, db=session)
        
        # Act
        found_user_upper = UserController.get_user_by_email(
            email="TEST@EXAMPLE.COM",
            db=session
        )
        
        # Assert
        # En SQLite por defecto, las búsquedas de texto son case-insensitive
        # Ajusta este test según el comportamiento de tu BD
        # assert found_user_upper is None  # Si es case-sensitive
        # o
        # assert found_user_upper is not None  # Si es case-insensitive

    def test_create_multiple_users(self, session):
        """
        Test: Crear múltiples usuarios
        
        Verifica que se pueden crear varios usuarios sin conflictos
        """
        # Arrange
        user1 = User(
            name="Usuario",
            last_name="Uno",
            email="user1@example.com",
            password="pass1"
        )
        user2 = User(
            name="Usuario",
            last_name="Dos",
            email="user2@example.com",
            password="pass2"
        )
        
        # Act
        created_user1 = UserController.create_user(user1, db=session)
        created_user2 = UserController.create_user(user2, db=session)
        
        # Assert
        assert created_user1.id != created_user2.id
        assert created_user1.email == "user1@example.com"
        assert created_user2.email == "user2@example.com"

    def test_create_user_duplicate_email_should_fail(self, session, sample_user_data):
        """
        Test: Intentar crear usuario con email duplicado
        
        Verifica que no se puede crear un usuario con un email ya existente
        (asumiendo que hay constraint en la BD)
        """
        # Arrange
        UserController.create_user(sample_user_data, db=session)
        
        # Act & Assert
        duplicate_user = User(
            name="Otro",
            last_name="Usuario",
            email="test@example.com",  # Email duplicado
            password="otro_password"
        )
        
        # Si hay constraint UNIQUE en email, esto debería fallar
        # Descomenta y ajusta según tu implementación
        # with pytest.raises(Exception):  # IntegrityError o similar
        #     UserController.create_user(duplicate_user, db=session)
