from fastapi import Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError, OperationalError, IntegrityError, DatabaseError
import logging
from typing import Callable

# Configurar logging
logger = logging.getLogger(__name__)

async def error_handler_middleware(request: Request, call_next: Callable):
    """
    Middleware para manejar errores de base de datos y otros errores del servidor.
    Oculta los detalles técnicos y retorna mensajes genéricos al usuario.
    """
    try:
        response = await call_next(request)
        return response
    except SQLAlchemyError as e:
        # Loguear el error completo para los desarrolladores
        logger.error(f"Database error: {str(e)}", exc_info=True)
        
        # Determinar el tipo de error de base de datos
        if isinstance(e, OperationalError):
            error_message = "Error de conexión con la base de datos. Por favor, intente nuevamente."
        elif isinstance(e, IntegrityError):
            error_message = "Error de integridad de datos. Verifique que los datos sean correctos."
        elif isinstance(e, DatabaseError):
            error_message = "Error al procesar la operación en la base de datos."
        else:
            error_message = "Ha ocurrido un error con la base de datos."
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Database Error",
                "message": error_message,
                "detail": "Por favor, contacte al administrador si el problema persiste."
            }
        )
    except Exception as e:
        # Loguear cualquier otro error
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "message": "Ha ocurrido un error inesperado.",
                "detail": "Por favor, contacte al administrador si el problema persiste."
            }
        )
