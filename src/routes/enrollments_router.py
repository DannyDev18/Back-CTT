from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List, Optional, Union
from src.models.user import User
from src.controllers.enrollment_controller import EnrollmentController
from src.dependencies.db_session import SessionDep
from src.models.enrollment import (
    EnrollmentCreate,
    EnrollmentUpdate,
    EnrollmentResponse,
    EnrollmentStatus
)
from src.utils.platform_jwt_utils import decode_platform_token
from src.models.user_platform import UserPlatform
from src.utils.jwt_utils import decode_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

enrollments_router = APIRouter(prefix="/api/v1/enrollments", tags=["enrollments"])

# ============= Dependency para autenticación ============= 

async def get_current_platform_user(token: str = Depends(decode_platform_token)) -> UserPlatform:
    """Obtiene el usuario actual de la plataforma desde el token"""
    return token

async def get_current_admin_user(
    token: str = Depends(decode_token)
) -> User:
    """Obtiene el usuario actual y verifica que sea el token de un administrador"""
    return token

security = HTTPBearer()

async def get_current_user_any_type(
    db: SessionDep,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> tuple[Union[User, UserPlatform], str]:
    """
    Intenta autenticar primero como admin, luego como usuario de plataforma.
    Retorna una tupla con el usuario y el tipo ('admin' o 'platform')
    """
    token = credentials.credentials
    
    # Primero intentar como admin
    try:
        from jose import jwt
        from src.utils.jwt_utils import JWT_SECRET_KEY
        from src.controllers.user_controller import UserController
        
        data = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        email = data.get("email")
        if email:
            user = UserController.get_user_by_email(email, db)
            if user:
                return user, "admin"
    except:
        pass
    
    # Si no es admin, intentar como usuario de plataforma
    try:
        from jose import jwt
        from src.utils.platform_jwt_utils import JWT_SECRET_KEY
        from src.controllers.user_platform_controller import UserPlatformController
        
        data = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        email = data.get("email")
        if email:
            user = UserPlatformController.get_user_by_email(email, db)
            if user:
                return user, "platform"
    except:
        pass
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado"
    )

# ============= Endpoints ============= 

@enrollments_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Crear una nueva inscripción",
    description="Permite a un usuario de la plataforma inscribirse en un curso"
)
def create_enrollment(
    enrollment_data: EnrollmentCreate,
    db: SessionDep,
    current_user: UserPlatform = Depends(get_current_platform_user)
):
    """
    Crea una nueva inscripción en un curso.
    
    - **id_user_platform**: ID del usuario de la plataforma
    - **id_course**: ID del curso
    - **status**: Estado inicial (por defecto: Interesado)
    - **payment_order_url**: URL de la orden de pago (opcional)
    """
    # Validar que el usuario solo pueda inscribirse a sí mismo
    if enrollment_data.id_user_platform != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para inscribir a otro usuario"
        )
    
    try:
        result = EnrollmentController.create_enrollment(enrollment_data, db)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear la inscripción: {str(e)}"
        )


@enrollments_router.get(
    "/{enrollment_id}",
    summary="Obtener inscripción por ID",
    description="Obtiene los detalles de una inscripción específica. Admins pueden ver cualquiera, usuarios solo las suyas."
)
def get_enrollment(
    enrollment_id: int,
    db: SessionDep,
    user_data: tuple[Union[User, UserPlatform], str] = Depends(get_current_user_any_type)
):
    """
    Obtiene una inscripción por su ID con detalles del usuario y curso.
    
    - **Admin (User)**: Puede ver cualquier inscripción
    - **Usuario Plataforma (UserPlatform)**: Solo puede ver sus propias inscripciones
    """
    try:
        result = EnrollmentController.get_enrollment_by_id(enrollment_id, db)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener la inscripción: {str(e)}"
        )
    
    current_user, user_type = user_data
    
    # Si es usuario de plataforma, validar que solo pueda ver sus propias inscripciones
    if user_type == "platform" and result["id_user_platform"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver esta inscripción"
        )
    
    return result


@enrollments_router.put(
    "/{enrollment_id}",
    summary="Actualizar inscripción",
    description="Actualiza una inscripción. Admin puede cambiar status y payment_order_url. Usuario plataforma solo payment_order_url."
)
def update_enrollment(
    enrollment_id: int,
    enrollment_data: EnrollmentUpdate,
    db: SessionDep,
    user_data: tuple[Union[User, UserPlatform], str] = Depends(get_current_user_any_type)
):
    """
    Actualiza una inscripción existente.
    
    - **Admin (User)**: Puede actualizar cualquier inscripción (status y payment_order_url)
    - **Usuario Plataforma (UserPlatform)**: Solo puede actualizar payment_order_url de sus propias inscripciones
    """
    try:
        # Obtener la inscripción para validar permisos
        existing = EnrollmentController.get_enrollment_by_id(enrollment_id, db)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener la inscripción: {str(e)}"
        )
    
    current_user, user_type = user_data
    
    # Si es usuario de plataforma, aplicar restricciones
    if user_type == "platform":
        # Solo puede actualizar sus propias inscripciones
        if existing["id_user_platform"] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para actualizar esta inscripción"
            )
        
        # No puede cambiar el status
        if enrollment_data.status is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Los usuarios de plataforma no pueden cambiar el estado de la inscripción"
            )
    
    try:
        result = EnrollmentController.update_enrollment(enrollment_id, enrollment_data, db)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar la inscripción: {str(e)}"
        )


@enrollments_router.delete(
    "/{enrollment_id}",
    summary="Anular inscripción",
    description="Anula una inscripción (soft delete). Solo administradores."
)
def delete_enrollment(
    enrollment_id: int,
    db: SessionDep,
    user_data: tuple[Union[User, UserPlatform], str] = Depends(get_current_user_any_type)
):
    """
    Anula una inscripción cambiando su estado a ANULADO.
    
    - **Solo Admin (User)**: Puede anular cualquier inscripción
    """
    try:
        # Primero obtener la inscripción para validar permisos
        existing = EnrollmentController.get_enrollment_by_id(enrollment_id, db)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener la inscripción: {str(e)}"
        )
    
    _, user_type = user_data

    if user_type != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo un administrador puede anular inscripciones"
        )
    
    try:
        result = EnrollmentController.delete_enrollment(enrollment_id, db)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al anular la inscripción: {str(e)}"
        )


@enrollments_router.get(
    "/user/{user_id}",
    summary="Obtener inscripciones por usuario",
    description="Obtiene todas las inscripciones de un usuario específico. Admins pueden ver cualquier usuario, usuarios solo los suyos."
)
def get_user_enrollments(
    user_id: int,
    db: SessionDep,
    enrollment_status: Optional[EnrollmentStatus] = Query(None, description="Filtrar por estado"),
    user_data: tuple[Union[User, UserPlatform], str] = Depends(get_current_user_any_type)
):
    """
    Obtiene todas las inscripciones de un usuario con detalles de los cursos.
    
    - **Admin (User)**: Puede ver inscripciones de cualquier usuario
    - **Usuario Plataforma (UserPlatform)**: Solo puede ver sus propias inscripciones
    """
    current_user, user_type = user_data
    
    # Si es usuario de plataforma, validar que solo pueda ver sus propias inscripciones
    if user_type == "platform" and user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver inscripciones de otro usuario"
        )
    
    try:
        enrollments = EnrollmentController.get_enrollments_by_user(user_id, db, enrollment_status)
        return {
            "user_id": user_id,
            "total": len(enrollments),
            "enrollments": enrollments
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener inscripciones del usuario: {str(e)}"
        )


@enrollments_router.get(
    "/course/{course_id}",
    summary="Obtener inscripciones por curso",
    description="Obtiene todas las inscripciones de un curso específico (solo admin)"
)
def get_course_enrollments(
    course_id: int,
    db: SessionDep,
    enrollment_status: Optional[EnrollmentStatus] = Query(None, description="Filtrar por estado"),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Obtiene todas las inscripciones de un curso con detalles de los usuarios.
    """
    try:
        enrollments = EnrollmentController.get_enrollments_by_course(course_id, db, enrollment_status)
        return {
            "course_id": course_id,
            "total": len(enrollments),
            "enrollments": enrollments
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener inscripciones del curso: {str(e)}"
        )


@enrollments_router.get(
    "/",
    summary="Listar inscripciones paginadas",
    description="Obtiene un listado paginado de inscripciones. Admins ven todas, usuarios de plataforma solo las suyas."
)
def list_enrollments(
    db: SessionDep,
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(10, ge=1, le=100, description="Tamaño de página"),
    enrollment_status: Optional[EnrollmentStatus] = Query(None, description="Filtrar por estado"),
    filter_user_id: Optional[int] = Query(None, description="Filtrar por usuario (solo admin)"),
    course_id: Optional[int] = Query(None, description="Filtrar por curso"),
    user_data: tuple[Union[User, UserPlatform], str] = Depends(get_current_user_any_type)
):
    """
    Obtiene un listado paginado de inscripciones con filtros opcionales.
    
    - **Admin (User)**: Puede ver todas las inscripciones y aplicar filtros opcionales
    - **Usuario Plataforma (UserPlatform)**: Solo puede ver sus propias inscripciones
    """
    try:
        current_user, user_type = user_data
        
        # Si es usuario de plataforma, SIEMPRE filtrar por su propio ID
        if user_type == "platform":
            actual_user_id = current_user.id
        # Si es admin, puede ver todas o filtrar si lo especifica
        else:
            actual_user_id = filter_user_id
        
        result = EnrollmentController.get_enrollments_paginated(
            db, page, page_size, enrollment_status, actual_user_id, course_id
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener el listado de inscripciones: {str(e)}"
        )


@enrollments_router.get(
    "/stats/course/{course_id}",
    summary="Obtener estadísticas de inscripciones por curso",
    description="Obtiene estadísticas detalladas de inscripciones de un curso (solo admin)"
)
def get_course_stats(
    course_id: int,
    db: SessionDep,
    current_user: User = Depends(get_current_admin_user)
):
    """
    Obtiene estadísticas de inscripciones de un curso agrupadas por estado.
    """
    try:
        stats = EnrollmentController.get_course_enrollment_stats(course_id, db)
        return stats
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener estadísticas: {str(e)}"
        )
