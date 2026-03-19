from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List, Optional, Union
from src.models.user import User
from src.controllers.enrollment_controller import EnrollmentController
from src.dependencies.db_session import SessionDep
from src.models.enrollment import (
    EnrollmentCreate,
    EnrollmentUpdate,
    EnrollmentResponse,
    EnrollmentStatus,
)
from src.utils.platform_jwt_utils import decode_platform_token
from src.models.user_platform import UserPlatform
from src.utils.jwt_utils import decode_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

enrollments_router = APIRouter(prefix="/api/v1/enrollments", tags=["enrollments"])

# ============= Dependencies de autenticación =============

async def get_current_platform_user(token: str = Depends(decode_platform_token)) -> UserPlatform:
    return token


async def get_current_admin_user(token: str = Depends(decode_token)) -> User:
    return token


security = HTTPBearer()


async def get_current_user_any_type(
    db: SessionDep,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> tuple[Union[User, UserPlatform], str]:
    """
    Autentica como admin (User) o usuario de plataforma (UserPlatform).
    Retorna (usuario, tipo) donde tipo es 'admin' o 'platform'.
    """
    token = credentials.credentials

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
    except Exception:
        pass

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
    except Exception:
        pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
    )


# ============= Endpoints =============

@enrollments_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Crear inscripción",
    description=(
        "Inscribe a un usuario en un **curso** o en un **congreso**. "
        "Se debe enviar exactamente uno de `id_course` o `id_congress`."
    ),
)
def create_enrollment(
    enrollment_data: EnrollmentCreate,
    db: SessionDep,
    current_user: UserPlatform = Depends(get_current_platform_user),
):
    if enrollment_data.id_user_platform != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para inscribir a otro usuario.",
        )
    try:
        return EnrollmentController.create_enrollment(enrollment_data, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear la inscripción: {str(e)}",
        )


@enrollments_router.get(
    "/",
    summary="Listar inscripciones paginadas",
    description=(
        "Admins ven todas; usuarios de plataforma solo las propias. "
        "Filtros opcionales: estado, usuario, curso, congreso."
    ),
)
def list_enrollments(
    db: SessionDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    enrollment_status: Optional[EnrollmentStatus] = Query(None, description="Filtrar por estado"),
    filter_user_id: Optional[int] = Query(None, description="Filtrar por usuario (solo admin)"),
    course_id: Optional[int] = Query(None, description="Filtrar por curso"),
    congress_id: Optional[int] = Query(None, description="Filtrar por congreso"),
    user_data: tuple[Union[User, UserPlatform], str] = Depends(get_current_user_any_type),
):
    try:
        current_user, user_type = user_data
        actual_user_id = current_user.id if user_type == "platform" else filter_user_id
        return EnrollmentController.get_enrollments_paginated(
            db, page, page_size, enrollment_status, actual_user_id, course_id, congress_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener inscripciones: {str(e)}",
        )


@enrollments_router.get(
    "/user/{user_id}",
    summary="Inscripciones de un usuario",
    description="Admin puede consultar cualquier usuario; usuario de plataforma solo las propias.",
)
def get_user_enrollments(
    user_id: int,
    db: SessionDep,
    enrollment_status: Optional[EnrollmentStatus] = Query(None),
    user_data: tuple[Union[User, UserPlatform], str] = Depends(get_current_user_any_type),
):
    current_user, user_type = user_data
    if user_type == "platform" and user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver inscripciones de otro usuario.",
        )
    try:
        enrollments = EnrollmentController.get_enrollments_by_user(user_id, db, enrollment_status)
        return {"user_id": user_id, "total": len(enrollments), "enrollments": enrollments}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener inscripciones del usuario: {str(e)}",
        )


# ---- Estadísticas ----

@enrollments_router.get(
    "/stats/course/{course_id}",
    summary="Estadísticas de inscripciones por curso (admin)",
)
def get_course_stats(
    course_id: int,
    db: SessionDep,
    current_user: User = Depends(get_current_admin_user),
):
    try:
        return EnrollmentController.get_course_enrollment_stats(course_id, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener estadísticas: {str(e)}",
        )


@enrollments_router.get(
    "/stats/congress/{congress_id}",
    summary="Estadísticas de inscripciones por congreso (admin)",
)
def get_congress_stats(
    congress_id: int,
    db: SessionDep,
    current_user: User = Depends(get_current_admin_user),
):
    try:
        return EnrollmentController.get_congress_enrollment_stats(congress_id, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener estadísticas: {str(e)}",
        )


# ---- Listados por recurso ----

@enrollments_router.get(
    "/course/{course_id}",
    summary="Inscripciones de un curso (admin)",
    description="Lista paginada de usuarios inscritos en un curso.",
)
def get_course_enrollments(
    course_id: int,
    db: SessionDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    enrollment_status: Optional[EnrollmentStatus] = Query(None),
    search_term: Optional[str] = Query(None),
    current_user: User = Depends(get_current_admin_user),
):
    try:
        return EnrollmentController.get_enrollments_by_course(
            course_id, db, page, page_size, enrollment_status, search_term
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener inscripciones del curso: {str(e)}",
        )


@enrollments_router.get(
    "/congress/{congress_id}",
    summary="Inscripciones de un congreso (admin)",
    description="Lista paginada de usuarios inscritos en un congreso.",
)
def get_congress_enrollments(
    congress_id: int,
    db: SessionDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    enrollment_status: Optional[EnrollmentStatus] = Query(None),
    search_term: Optional[str] = Query(None),
    current_user: User = Depends(get_current_admin_user),
):
    try:
        return EnrollmentController.get_enrollments_by_congress(
            congress_id, db, page, page_size, enrollment_status, search_term
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener inscripciones del congreso: {str(e)}",
        )


# ---- CRUD individual ----

@enrollments_router.get(
    "/{enrollment_id}",
    summary="Obtener inscripción por ID",
    description="Admin puede ver cualquiera; usuario de plataforma solo las propias.",
)
def get_enrollment(
    enrollment_id: int,
    db: SessionDep,
    user_data: tuple[Union[User, UserPlatform], str] = Depends(get_current_user_any_type),
):
    try:
        result = EnrollmentController.get_enrollment_by_id(enrollment_id, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener la inscripción: {str(e)}",
        )

    current_user, user_type = user_data
    if user_type == "platform" and result["id_user_platform"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver esta inscripción.",
        )
    return result


@enrollments_router.put(
    "/{enrollment_id}",
    summary="Actualizar inscripción",
    description="Admin puede cambiar estado y URL de pago; usuario de plataforma solo URL de pago.",
)
def update_enrollment(
    enrollment_id: int,
    enrollment_data: EnrollmentUpdate,
    db: SessionDep,
    user_data: tuple[Union[User, UserPlatform], str] = Depends(get_current_user_any_type),
):
    try:
        existing = EnrollmentController.get_enrollment_by_id(enrollment_id, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener la inscripción: {str(e)}",
        )

    current_user, user_type = user_data
    if user_type == "platform":
        if existing["id_user_platform"] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para actualizar esta inscripción.",
            )
        if enrollment_data.status is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Los usuarios de plataforma no pueden cambiar el estado de la inscripción.",
            )

    try:
        return EnrollmentController.update_enrollment(enrollment_id, enrollment_data, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar la inscripción: {str(e)}",
        )


@enrollments_router.delete(
    "/{enrollment_id}",
    summary="Anular inscripción (admin)",
    description="Soft delete — cambia el estado a ANULADO. Solo administradores.",
)
def delete_enrollment(
    enrollment_id: int,
    db: SessionDep,
    user_data: tuple[Union[User, UserPlatform], str] = Depends(get_current_user_any_type),
):
    try:
        existing = EnrollmentController.get_enrollment_by_id(enrollment_id, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener la inscripción: {str(e)}",
        )

    _, user_type = user_data
    if user_type != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo un administrador puede anular inscripciones.",
        )

    try:
        return EnrollmentController.delete_enrollment(enrollment_id, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al anular la inscripción: {str(e)}",
        )
