# 🚀 Comandos Rápidos de Testing

## Comandos Básicos

### Ejecutar Tests
```bash
# Todos los tests
pytest

# Con salida detallada
pytest -v

# Con salida muy detallada
pytest -vv

# Mostrar prints en la consola
pytest -s
```

### Tests Específicos
```bash
# Un archivo específico
pytest tests/test_controllers/test_course_controller.py

# Una clase específica
pytest tests/test_controllers/test_course_controller.py::TestCourseController

# Un test específico
pytest tests/test_controllers/test_course_controller.py::TestCourseController::test_create_course_with_requirements
```

### Filtrar Tests
```bash
# Tests que contengan "create" en el nombre
pytest -k "create"

# Tests que NO contengan "delete"
pytest -k "not delete"

# Múltiples condiciones
pytest -k "create or delete"
```

## Cobertura de Código

### Generar Reportes
```bash
# Reporte en terminal
pytest --cov=src/controllers

# Con líneas faltantes
pytest --cov=src/controllers --cov-report=term-missing

# Reporte HTML
pytest --cov=src/controllers --cov-report=html

# Múltiples reportes
pytest --cov=src/controllers --cov-report=html --cov-report=term
```

### Cobertura Específica
```bash
# Solo CourseController
pytest tests/test_controllers/test_course_controller.py --cov=src/controllers/course_controller

# Solo UserController
pytest tests/test_controllers/test_user_controller.py --cov=src/controllers/user_controller
```

## Control de Ejecución

### Manejo de Fallos
```bash
# Detener al primer fallo
pytest -x

# Detener después de N fallos
pytest --maxfail=3

# Ejecutar solo tests que fallaron la última vez
pytest --lf

# Ejecutar primero los que fallaron, luego el resto
pytest --ff
```

### Modo Debug
```bash
# Entrar en debugger al fallar un test
pytest --pdb

# Entrar en debugger al inicio de cada test
pytest --trace
```

## Opciones Avanzadas

### Performance
```bash
# Tests en paralelo (requiere pytest-xdist)
pytest -n auto

# Número específico de workers
pytest -n 4

# Mostrar los 10 tests más lentos
pytest --durations=10
```

### Información
```bash
# Ver fixtures disponibles
pytest --fixtures

# Ver marcadores disponibles
pytest --markers

# Recolectar tests sin ejecutarlos
pytest --collect-only
```

## Reportes y Salida

### Formato de Salida
```bash
# Salida corta (solo puntos)
pytest -q

# Sin capturar salida (ver prints inmediatamente)
pytest -s

# Mostrar variables locales en fallos
pytest -l

# Traceback más corto
pytest --tb=short

# Traceback en una línea
pytest --tb=line

# Sin traceback
pytest --tb=no
```

### Reportes HTML (requiere pytest-html)
```bash
# Generar reporte HTML de tests
pytest --html=report.html
```

## CI/CD

### Para Integración Continua
```bash
# Formato JUnit XML (para Jenkins, GitLab CI, etc.)
pytest --junitxml=junit.xml

# Con cobertura en formato XML (para SonarQube, Codecov)
pytest --cov=src --cov-report=xml
```

## Warnings

### Manejo de Advertencias
```bash
# Mostrar todas las advertencias
pytest -W all

# Convertir advertencias en errores
pytest -W error

# Ignorar advertencias
pytest --disable-warnings
```

## Aliases Útiles (agregar a tu PowerShell profile)

```powershell
# Windows PowerShell - Editar: $PROFILE

# Alias para tests
function Test-All { pytest -v }
function Test-Coverage { pytest --cov=src/controllers --cov-report=html }
function Test-Quick { pytest -x }
function Test-Course { pytest tests/test_controllers/test_course_controller.py -v }
function Test-User { pytest tests/test_controllers/test_user_controller.py -v }

# Uso:
# > Test-All
# > Test-Coverage
```

## Scripts Rápidos

### Script de PowerShell Inline
```powershell
# Ejecutar tests y abrir reporte si pasan
pytest --cov=src/controllers --cov-report=html && Start-Process htmlcov/index.html
```

### Bash (Git Bash, WSL)
```bash
# Ejecutar tests y abrir reporte si pasan
pytest --cov=src/controllers --cov-report=html && open htmlcov/index.html
```

## Configuración en pytest.ini

Ya está configurado en `pytest.ini`, pero puedes modificar:

```ini
[pytest]
# Agregar opciones por defecto
addopts = 
    -v
    --strict-markers
    --tb=short
    --disable-warnings
    # --cov=src  # Descomentar para siempre tener cobertura

# Directorios a ignorar
testpaths = tests
norecursedirs = .git .venv venv htmlcov
```

## Variables de Entorno

```bash
# Desactivar warnings de deprecación
set PYTHONWARNINGS=ignore::DeprecationWarning

# Modo debug de pytest
set PYTEST_DEBUG=1
```

## Ejemplos de Uso Común

### Desarrollo Diario
```bash
# Durante desarrollo: rápido, detener al primer fallo
pytest -x -v

# Antes de commit: todos los tests con cobertura
pytest --cov=src/controllers --cov-report=term-missing
```

### Debugging
```bash
# Ver qué está pasando en un test específico
pytest tests/test_controllers/test_course_controller.py::TestCourseController::test_create_course_with_requirements -vv -s

# Entrar en debugger
pytest tests/test_controllers/test_course_controller.py::TestCourseController::test_create_course_with_requirements --pdb
```

### Pre-commit Hooks
```bash
# Verificación rápida antes de commit
pytest -x --tb=short

# Verificación completa
pytest --cov=src/controllers --cov-fail-under=80
```

## Tips Pro 💡

1. **Uso de Watch Mode** (requiere pytest-watch)
```bash
pip install pytest-watch
ptw  # Ejecuta tests automáticamente al guardar archivos
```

2. **Tests Aleatorios** (requiere pytest-randomly)
```bash
pip install pytest-randomly
pytest  # Ejecuta tests en orden aleatorio
```

3. **BDD Style** (requiere pytest-bdd)
```bash
pip install pytest-bdd
# Escribir tests estilo Gherkin
```

4. **Cobertura Incremental**
```bash
# Ver solo archivos modificados
pytest --cov=src/controllers --cov-report=term:skip-covered
```

---

## Atajos del Script PowerShell

Si usas `run_tests.ps1`:

```powershell
.\run_tests.ps1
```

Luego selecciona:
- `1` - Todos los tests
- `2` - Con cobertura
- `3` - Solo CourseController
- `4` - Solo UserController
- `5` - Modo verbose
- `6` - Ver reporte HTML

---

**Tip**: Guarda este archivo como referencia rápida 📌
