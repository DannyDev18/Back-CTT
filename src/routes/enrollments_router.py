from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List, Optional
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

enrollments_router = APIRouter(prefix="/api/v1/enrollments", tags=["enrollments"])

# ============= Dependency para autenticación ============= 

async def get_current_platform_user(token: str = Depends(decode_platform_token)) -> UserPlatform:
    """Obtiene el usuario actual de la plataforma desde el token"""
    return token

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
    description="Obtiene los detalles de una inscripción específica"
)
def get_enrollment(
    enrollment_id: int,
    db: SessionDep,
    current_user: UserPlatform = Depends(get_current_platform_user)
):
    """
    Obtiene una inscripción por su ID con detalles del usuario y curso.
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
    
    # Validar que el usuario solo pueda ver sus propias inscripciones
    # (a menos que implementes roles de admin)
    if result["id_user_platform"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver esta inscripción"
        )
    
    return result


@enrollments_router.put(
    "/{enrollment_id}",
    summary="Actualizar inscripción",
    description="Actualiza el estado o la URL de pago de una inscripción"
)
def update_enrollment(
    enrollment_id: int,
    enrollment_data: EnrollmentUpdate,
    db: SessionDep,
    current_user: UserPlatform = Depends(get_current_platform_user)
):
    """
    Actualiza una inscripción existente.
    
    - **status**: Nuevo estado de la inscripción
    - **payment_order_url**: Nueva URL de la orden de pago
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
    
    if existing["id_user_platform"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para actualizar esta inscripción"
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
    description="Anula una inscripción (soft delete)"
)
def delete_enrollment(
    enrollment_id: int,
    db: SessionDep,
    current_user: UserPlatform = Depends(get_current_platform_user)
):
    """
    Anula una inscripción cambiando su estado a ANULADO.
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
    
    if existing["id_user_platform"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para anular esta inscripción"
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
    description="Obtiene todas las inscripciones de un usuario específico"
)
def get_user_enrollments(
    user_id: int,
    db: SessionDep,
    enrollment_status: Optional[EnrollmentStatus] = Query(None, description="Filtrar por estado"),
    current_user: UserPlatform = Depends(get_current_platform_user)
):
    """
    Obtiene todas las inscripciones de un usuario con detalles de los cursos.
    """
    # Validar que el usuario solo pueda ver sus propias inscripciones
    if user_id != current_user.id:
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
    current_user: UserPlatform = Depends(get_current_platform_user)
):
    """
    Obtiene todas las inscripciones de un curso con detalles de los usuarios.
    
    **Nota:** Este endpoint debería estar restringido solo para administradores.
    """
    try:
        # TODO: Implementar validación de rol de administrador
        # Por ahora, cualquier usuario autenticado puede ver esto
        # if current_user.type != UserPlatformType.ADMINISTRATIVO:
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail="Solo administradores pueden ver inscripciones de cursos"
        #     )
        
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
    description="Obtiene un listado paginado de inscripciones con filtros opcionales"
)
def list_enrollments(
    db: SessionDep,
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(10, ge=1, le=100, description="Tamaño de página"),
    enrollment_status: Optional[EnrollmentStatus] = Query(None, description="Filtrar por estado"),
    user_id: Optional[int] = Query(None, description="Filtrar por usuario"),
    course_id: Optional[int] = Query(None, description="Filtrar por curso"),
    current_user: UserPlatform = Depends(get_current_platform_user)
):
    """
    Obtiene un listado paginado de inscripciones con filtros opcionales.
    
    Los usuarios normales solo verán sus propias inscripciones.
    """
    try:
        # Si no es admin, forzar el filtro por user_id del usuario actual
        # TODO: Implementar validación de rol de administrador
        # if current_user.type != UserPlatformType.ADMINISTRATIVO:
        #     user_id = current_user.id
        
        # Por ahora, forzar siempre que vea solo sus inscripciones
        user_id = current_user.id
        
        result = EnrollmentController.get_enrollments_paginated(
            db, page, page_size, enrollment_status, user_id, course_id
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
    current_user: UserPlatform = Depends(get_current_platform_user)
):
    """
    Obtiene estadísticas de inscripciones de un curso agrupadas por estado.
    
    **Nota:** Este endpoint debería estar restringido solo para administradores.
    """
    try:
        # TODO: Implementar validación de rol de administrador
        # if current_user.type != UserPlatformType.ADMINISTRATIVO:
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail="Solo administradores pueden ver estadísticas"
        #     )
        
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
