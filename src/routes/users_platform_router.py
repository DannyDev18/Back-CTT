from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from src.controllers.user_platform_controller import UserPlatformController
from src.dependencies.db_session import SessionDep

users_platform_router = APIRouter(prefix="/api/v1/users", tags=["users"])

@users_platform_router.get("")
def get_all_users(
    db: SessionDep,
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(10, ge=1, le=100, description="Tamaño de página"),
    type: Optional[str] = Query(None, description="Tipo de usuario (Estudiante/Externo/Administrativo)")
):
    """
    Obtiene todos los usuarios de la plataforma con paginación.
    - **page**: número de página (por defecto 1)
    - **page_size**: cantidad de usuarios por página (por defecto 10, máximo 100)
    - **type**: tipo de usuario (opcional)
    """
    try:
        result = UserPlatformController.get_all_users(
            db, page=page, page_size=page_size, type=type
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")
