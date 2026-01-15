"""
Tests unitarios para el CategoriesController

Estos tests verifican que los métodos del controller de categorías
funcionen correctamente utilizando una base de datos en memoria.
"""
import pytest
from fastapi import HTTPException
from src.controllers.categories_controller import CategoriesController
from src.models.category import Category, CategoryStatus
from src.models.user import User


class TestCategoriesController:
    """Suite de tests para CategoriesController"""

    @pytest.fixture
    def sample_user(self, session):
        """Crea un usuario de prueba para asignar como creador"""
        user = User(
            name="Admin",
            last_name="Test",
            email="admin@test.com",
            password="hashed_password"
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    @pytest.fixture
    def sample_category_data(self):
        """Datos de ejemplo para crear una categoría"""
        return Category.CategoryCreate(
            name="Programación",
            description="Cursos de programación y desarrollo de software",
            svgurl="https://example.com/icons/programming.svg",
            status=CategoryStatus.ACTIVO
        )

    def test_create_category_success(self, session, sample_category_data, sample_user):
        """
        Test: Crear una categoría exitosamente
        
        Verifica que la categoría se crea y se guarda correctamente en la BD
        """
        # Act
        created_category = CategoriesController.create_category(
            db=session,
            category_data=sample_category_data,
            created_by=sample_user.id
        )
        
        # Assert
        assert created_category is not None
        assert created_category.id is not None
        assert created_category.name == "Programación"
        assert created_category.description == "Cursos de programación y desarrollo de software"
        assert created_category.status == CategoryStatus.ACTIVO
        assert created_category.created_by == sample_user.id

    def test_create_category_duplicate_name_should_fail(
        self,
        session,
        sample_category_data,
        sample_user
    ):
        """
        Test: Intentar crear categoría con nombre duplicado
        
        Verifica que no se puede crear una categoría con un nombre ya existente
        """
        # Arrange
        CategoriesController.create_category(
            db=session,
            category_data=sample_category_data,
            created_by=sample_user.id
        )
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            CategoriesController.create_category(
                db=session,
                category_data=sample_category_data,
                created_by=sample_user.id
            )
        
        assert exc_info.value.status_code == 400
        assert "Ya existe una categoría con ese nombre" in str(exc_info.value.detail)

    def test_get_all_categories_empty(self, session):
        """
        Test: Obtener todas las categorías cuando no hay ninguna
        
        Verifica que retorna una respuesta paginada vacía
        """
        # Act
        result = CategoriesController.get_all_categories(db=session)
        
        # Assert
        assert isinstance(result, dict)
        assert result["total"] == 0
        assert result["page"] == 1
        assert result["page_size"] == 10
        assert isinstance(result["items"], list)
        assert len(result["items"]) == 0

    def test_get_all_categories_with_data(
        self,
        session,
        sample_category_data,
        sample_user
    ):
        """
        Test: Obtener todas las categorías cuando existen datos
        
        Verifica que retorna la lista correcta de categorías con paginación
        """
        # Arrange
        CategoriesController.create_category(
            db=session,
            category_data=sample_category_data,
            created_by=sample_user.id
        )
        
        category_data_2 = Category.CategoryCreate(
            name="Electrónica",
            description="Cursos de electrónica y circuitos",
            svgurl="https://example.com/icons/electronics.svg",
            status=CategoryStatus.ACTIVO
        )
        CategoriesController.create_category(
            db=session,
            category_data=category_data_2,
            created_by=sample_user.id
        )
        
        # Act
        result = CategoriesController.get_all_categories(db=session)
        
        # Assert
        assert result["total"] == 2
        assert len(result["items"]) == 2

    def test_get_all_categories_pagination(self, session, sample_user):
        """
        Test: Verificar que la paginación funciona correctamente
        
        Crea varias categorías y verifica que la paginación retorna
        el número correcto de items por página
        """
        # Arrange: Crear 5 categorías
        for i in range(1, 6):
            category_data = Category.CategoryCreate(
                name=f"Categoría {i}",
                description=f"Descripción de categoría {i}",
                status=CategoryStatus.ACTIVO
            )
            CategoriesController.create_category(
                db=session,
                category_data=category_data,
                created_by=sample_user.id
            )
        
        # Act: Obtener primera página con 3 items
        result_page1 = CategoriesController.get_all_categories(
            db=session,
            page=1,
            page_size=3
        )
        
        # Assert: Primera página
        assert result_page1["total"] == 5
        assert len(result_page1["items"]) == 3
        assert result_page1["page"] == 1
        assert result_page1["page_size"] == 3
        
        # Act: Obtener segunda página
        result_page2 = CategoriesController.get_all_categories(
            db=session,
            page=2,
            page_size=3
        )
        
        # Assert: Segunda página
        assert result_page2["total"] == 5
        assert len(result_page2["items"]) == 2  # Solo quedan 2

    def test_get_all_categories_filter_by_status(self, session, sample_user):
        """
        Test: Filtrar categorías por estado
        
        Verifica que se pueden filtrar categorías activas/inactivas
        """
        # Arrange: Crear categorías con diferentes estados
        active_category = Category.CategoryCreate(
            name="Activa",
            description="Categoría activa",
            status=CategoryStatus.ACTIVO
        )
        CategoriesController.create_category(
            db=session,
            category_data=active_category,
            created_by=sample_user.id
        )
        
        inactive_category = Category.CategoryCreate(
            name="Inactiva",
            description="Categoría inactiva",
            status=CategoryStatus.INACTIVO
        )
        CategoriesController.create_category(
            db=session,
            category_data=inactive_category,
            created_by=sample_user.id
        )
        
        # Act: Filtrar solo activas
        result_active = CategoriesController.get_all_categories(
            db=session,
            status=CategoryStatus.ACTIVO
        )
        
        # Assert
        assert result_active["total"] == 1
        assert result_active["items"][0]["name"] == "Activa"

    def test_get_category_by_id_found(
        self,
        session,
        sample_category_data,
        sample_user
    ):
        """
        Test: Buscar categoría por ID cuando existe
        
        Verifica que retorna la categoría correcta
        """
        # Arrange
        created = CategoriesController.create_category(
            db=session,
            category_data=sample_category_data,
            created_by=sample_user.id
        )
        
        # Act
        found_category = CategoriesController.get_category_by_id(
            db=session,
            category_id=created.id
        )
        
        # Assert
        assert found_category is not None
        assert found_category.id == created.id
        assert found_category.name == "Programación"

    def test_get_category_by_id_not_found(self, session):
        """
        Test: Buscar categoría por ID cuando no existe
        
        Verifica que lanza HTTPException 404
        """
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            CategoriesController.get_category_by_id(
                db=session,
                category_id=9999
            )
        
        assert exc_info.value.status_code == 404

    def test_get_category_by_name_found(
        self,
        session,
        sample_category_data,
        sample_user
    ):
        """
        Test: Buscar categoría por nombre cuando existe
        """
        # Arrange
        CategoriesController.create_category(
            db=session,
            category_data=sample_category_data,
            created_by=sample_user.id
        )
        
        # Act
        found_category = CategoriesController.get_category_by_name(
            db=session,
            name="Programación"
        )
        
        # Assert
        assert found_category is not None
        assert found_category.name == "Programación"

    def test_get_category_by_name_not_found(self, session):
        """
        Test: Buscar categoría por nombre cuando no existe
        """
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            CategoriesController.get_category_by_name(
                db=session,
                name="Categoría Inexistente"
            )
        
        assert exc_info.value.status_code == 404

    def test_update_category_success(
        self,
        session,
        sample_category_data,
        sample_user
    ):
        """
        Test: Actualizar una categoría exitosamente
        """
        # Arrange
        created = CategoriesController.create_category(
            db=session,
            category_data=sample_category_data,
            created_by=sample_user.id
        )
        
        update_data = Category.CategoryUpdate(
            name="Programación Avanzada",
            description="Cursos avanzados de programación"
        )
        
        # Act
        updated = CategoriesController.update_category(
            db=session,
            category_id=created.id,
            category_data=update_data
        )
        
        # Assert
        assert updated.id == created.id
        assert updated.name == "Programación Avanzada"
        assert updated.description == "Cursos avanzados de programación"

    def test_update_category_not_found(self, session):
        """
        Test: Intentar actualizar categoría que no existe
        """
        # Arrange
        update_data = Category.CategoryUpdate(
            name="Nuevo Nombre"
        )
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            CategoriesController.update_category(
                db=session,
                category_id=9999,
                category_data=update_data
            )
        
        assert exc_info.value.status_code == 404

    def test_delete_category_success(
        self,
        session,
        sample_category_data,
        sample_user
    ):
        """
        Test: Soft delete de una categoría
        
        Verifica que la categoría se marca como inactiva
        """
        # Arrange
        created = CategoriesController.create_category(
            db=session,
            category_data=sample_category_data,
            created_by=sample_user.id
        )
        
        # Act
        CategoriesController.delete_category(
            db=session,
            category_id=created.id,
            current_user_id=sample_user.id
        )
        
        # Assert: La categoría debería estar inactiva
        deleted_category = CategoriesController.get_category_by_id(
            db=session,
            category_id=created.id
        )
        assert deleted_category.status == CategoryStatus.INACTIVO

    def test_delete_category_not_found(self, session, sample_user):
        """
        Test: Intentar eliminar categoría que no existe
        """
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            CategoriesController.delete_category(
                db=session,
                category_id=9999,
                current_user_id=sample_user.id
            )
        
        assert exc_info.value.status_code == 404

    def test_get_category_enable_only_active(self, session, sample_user):
        """
        Test: Obtener solo categorías activas
        
        Verifica que get_category_enable retorna solo las activas
        """
        # Arrange: Crear categorías activas e inactivas
        active1 = Category.CategoryCreate(
            name="Activa 1",
            status=CategoryStatus.ACTIVO
        )
        active2 = Category.CategoryCreate(
            name="Activa 2",
            status=CategoryStatus.ACTIVO
        )
        inactive = Category.CategoryCreate(
            name="Inactiva",
            status=CategoryStatus.INACTIVO
        )
        
        CategoriesController.create_category(session, active1, sample_user.id)
        CategoriesController.create_category(session, active2, sample_user.id)
        CategoriesController.create_category(session, inactive, sample_user.id)
        
        # Act
        enabled_categories = CategoriesController.get_category_enable(db=session)
        
        # Assert
        assert len(enabled_categories) == 2
        # Como get_category_enable retorna una lista de diccionarios
        assert isinstance(enabled_categories, list)
        for category in enabled_categories:
            assert isinstance(category, dict)
            assert category["status"] == CategoryStatus.ACTIVO.value
            assert category["name"] in ["Activa 1", "Activa 2"]
