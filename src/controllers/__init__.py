# Controllers package
"""
Controladores para el sistema CTT (Congreso Trinitario de Teología).

Este paquete contiene todos los controladores que manejan la lógica de negocio
y las operaciones CRUD para las diferentes entidades del sistema.

Arquitectura de controladores:
- BaseController: Clase base con operaciones CRUD genéricas
- Controladores específicos: Implementan lógica de negocio particular para cada entidad
- Manejo de errores unificado con decoradores
- Validaciones personalizadas mediante hooks
- Serialización consistente de datos

Patrones implementados:
- Repository Pattern: Los controladores utilizan repositorios para acceso a datos
- Generic Programming: Uso de TypeVar para reutilización de código
- Dependency Injection: Inyección de dependencias de repositorios
- Error Handling: Manejo centralizado de excepciones
"""

# Importar el controlador base
from .base_controller import (
    BaseController,
    ControllerError,
    ValidationError,
    NotFoundError,
    handle_controller_errors,
    ControllerUtils
)

# Importar controladores específicos
from .congress_controller import (
    CongressController,
    congress_controller
)

from .sponsor_controller import (
    SponsorController,
    sponsor_controller
)

from .speaker_controller import (
    SpeakerController,
    speaker_controller
)

from .sesion_cronograma_controller import (
    SesionCronogramaController,
    sesion_cronograma_controller
)

from .congreso_sponsor_controller import (
    CongresoSponsorController,
    congreso_sponsor_controller
)

# Exportar las instancias de controladores para uso directo
__all__ = [
    # Clases base
    "BaseController",
    "ControllerError",
    "ValidationError",
    "NotFoundError",
    "handle_controller_errors",
    "ControllerUtils",

    # Clases de controladores
    "CongressController",
    "SponsorController",
    "SpeakerController",
    "SesionCronogramaController",
    "CongresoSponsorController",

    # Instancias de controladores (recomendado para uso)
    "congress_controller",
    "sponsor_controller",
    "speaker_controller",
    "sesion_cronograma_controller",
    "congreso_sponsor_controller"
]

# Diccionario de controladores para acceso dinámico
CONTROLLERS = {
    'congress': congress_controller,
    'sponsor': sponsor_controller,
    'speaker': speaker_controller,
    'sesion_cronograma': sesion_cronograma_controller,
    'congreso_sponsor': congreso_sponsor_controller,
}

# Funciones de utilidad
def get_controller(name: str):
    """
    Obtener controlador por nombre.

    Args:
        name: Nombre del controlador ('congress', 'sponsor', etc.)

    Returns:
        Instancia del controlador correspondiente

    Raises:
        KeyError: Si el controlador no existe
    """
    if name not in CONTROLLERS:
        available = ', '.join(CONTROLLERS.keys())
        raise KeyError(f"Controller '{name}' not found. Available: {available}")

    return CONTROLLERS[name]

def list_controllers():
    """
    Listar todos los controladores disponibles.

    Returns:
        Lista con los nombres de controladores disponibles
    """
    return list(CONTROLLERS.keys())

# Metadata del paquete
__version__ = "1.0.0"
__author__ = "CTT Development Team"
__description__ = "Controladores para el sistema CTT"