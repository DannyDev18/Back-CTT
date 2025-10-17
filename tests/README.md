# Tests - CTT Backend

Este directorio contiene todos los tests del proyecto.

## Estructura

```
tests/
├── __init__.py
├── conftest.py              # Fixtures compartidos
├── README.md               # Este archivo
└── test_controllers/       # Tests de la capa de controllers
    ├── __init__.py
    ├── test_course_controller.py
    └── test_user_controller.py
```

## Ejecutar Tests

### Ejecutar todos los tests
```bash
pytest
```

### Ejecutar tests específicos
```bash
# Solo tests de course_controller
pytest tests/test_controllers/test_course_controller.py

# Solo tests de user_controller
pytest tests/test_controllers/test_user_controller.py

# Ejecutar un test específico
pytest tests/test_controllers/test_course_controller.py::TestCourseController::test_create_course_with_requirements
```

### Ejecutar tests con cobertura
```bash
pytest --cov=src --cov-report=html --cov-report=term-missing
```

El reporte HTML se generará en `htmlcov/index.html`

### Ejecutar tests en modo verbose
```bash
pytest -v
```

### Ejecutar tests mostrando prints
```bash
pytest -s
```

## Fixtures Disponibles

Los fixtures están definidos en `conftest.py` y están disponibles para todos los tests:

- **session**: Sesión de base de datos en memoria (SQLite)
- **sample_course_data**: Datos de ejemplo para crear un curso
- **sample_requirements_data**: Datos de ejemplo para requisitos de curso
- **sample_contents_data**: Datos de ejemplo para contenidos de curso
- **sample_user_data**: Datos de ejemplo para crear un usuario

## Buenas Prácticas

1. **Nomenclatura**: Los archivos de test deben empezar con `test_`
2. **Aislamiento**: Cada test debe ser independiente
3. **Arrange-Act-Assert**: Sigue el patrón AAA en tus tests
4. **Documentación**: Incluye docstrings explicando qué verifica cada test
5. **Fixtures**: Reutiliza fixtures para evitar código duplicado

## Agregar Nuevos Tests

1. Crea un nuevo archivo `test_*.py` en el directorio correspondiente
2. Crea una clase `Test*` para agrupar tests relacionados
3. Define métodos `test_*` para cada caso de prueba
4. Usa fixtures para datos de prueba
5. Documenta qué verifica cada test

## Ejemplo de Test

```python
def test_example(session, sample_data):
    """
    Test: Descripción breve del test
    
    Verifica que: [lo que verifica el test]
    """
    # Arrange (preparar)
    controller = MyController()
    
    # Act (ejecutar)
    result = controller.some_method(sample_data, session)
    
    # Assert (verificar)
    assert result is not None
    assert result.id is not None
```

## Troubleshooting

### Error: "No module named 'src'"
Asegúrate de ejecutar pytest desde la raíz del proyecto.

### Error de importación de modelos
Verifica que el archivo `__init__.py` exista en cada directorio del paquete.

### Tests fallan con error de BD
Los tests usan SQLite en memoria. Si fallan, verifica que las importaciones de modelos sean correctas.
