from fastapi import APIRouter, HTTPException, Query, Depends, Header, status
from typing import Optional, Union, Annotated
from pydantic import BaseModel
from jose import jwt
from src.controllers.user_platform_controller import UserPlatformController
from src.controllers.user_controller import UserController
from src.dependencies.db_session import SessionDep
from src.utils.jwt_utils import JWT_SECRET_KEY, decode_token, get_current_user_any_type
from src.utils.platform_jwt_utils import JWT_SECRET_KEY as PLATFORM_JWT_SECRET_KEY
from src.models.user import User
from src.models.user_platform import UserPlatform

users_platform_router = APIRouter(prefix="/api/v1/users", tags=["users"])


def get_optional_current_user_any_type(
    db: SessionDep,
    authorization: Optional[str] = Header(None)
) -> Optional[tuple[Union[User, UserPlatform], str]]:
    """Obtiene el usuario actual de forma opcional si el header Authorization está presente."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ", 1)[1]
    # Intentar como Admin
    try:
        data = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        email = data.get("email")
        if email:
            admin = UserController.get_user_by_email(email, db)
            if admin:
                return admin, "admin"
    except Exception:
        pass
    # Intentar como Platform User
    try:
        data = jwt.decode(token, PLATFORM_JWT_SECRET_KEY, algorithms=["HS256"])
        email = data.get("email")
        if email:
            plat_user = UserPlatformController.get_user_by_email(email, db)
            if plat_user:
                return plat_user, "platform"
    except Exception:
        pass
    return None


class UserBillingUpdate(BaseModel):
    billing_identification: str
    billing_name: str
    billing_address: str
    billing_phone: str
    billing_email: str


class UserProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    first_last_name: Optional[str] = None
    second_name: Optional[str] = None
    second_last_name: Optional[str] = None
    phone: Optional[str] = None
    cellphone: Optional[str] = None
    address: Optional[str] = None
    identification: Optional[str] = None  # Intencionalmente ignorado: la cédula es inmutable


class UserPasswordUpdate(BaseModel):
    current_password: str
    new_password: str


@users_platform_router.put("/{user_id}/billing")
def update_user_billing(
    user_id: int,
    data: UserBillingUpdate,
    db: SessionDep,
    user_data: tuple[Union[User, UserPlatform], str] = Depends(get_current_user_any_type)
):
    current_user, user_type = user_data
    if user_type == "platform" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para actualizar los datos de otro usuario."
        )

    user = db.get(UserPlatform, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    user.billing_identification = data.billing_identification.strip()
    user.billing_name = data.billing_name.strip()
    user.billing_address = data.billing_address.strip()
    user.billing_phone = data.billing_phone.strip()
    user.billing_email = data.billing_email.strip()

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "message": "Datos de facturación actualizados correctamente",
        "data": {
            "billing_identification": user.billing_identification,
            "billing_name": user.billing_name,
            "billing_address": user.billing_address,
            "billing_phone": user.billing_phone,
            "billing_email": user.billing_email,
        }
    }


@users_platform_router.put("/{user_id}/profile")
def update_user_profile(
    user_id: int,
    data: UserProfileUpdate,
    db: SessionDep,
    user_data: Optional[tuple[Union[User, UserPlatform], str]] = Depends(get_optional_current_user_any_type)
):
    """
    Actualiza la información personal de un usuario (nombres, apellidos, teléfono, dirección).
    Regla estricta: NO se permite modificar la identificación (cédula o RUC).
    """
    if user_data:
        current_user, user_type = user_data
        if user_type == "platform" and current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para actualizar los datos de otro usuario."
            )

    user = db.get(UserPlatform, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    if data.first_name is not None and data.first_name.strip():
        user.first_name = data.first_name.strip()
    if data.second_name is not None:
        user.second_name = data.second_name.strip() if data.second_name else None

    # Manejar last_name / first_last_name
    if data.last_name is not None and data.last_name.strip():
        parts = data.last_name.strip().split(None, 1)
        user.first_last_name = parts[0]
        if len(parts) > 1 and data.second_last_name is None:
            user.second_last_name = parts[1]
    elif data.first_last_name is not None and data.first_last_name.strip():
        user.first_last_name = data.first_last_name.strip()

    if data.second_last_name is not None:
        user.second_last_name = data.second_last_name.strip() if data.second_last_name else None

    # Manejar phone / cellphone
    if data.phone is not None and data.phone.strip():
        user.cellphone = data.phone.strip()
    elif data.cellphone is not None and data.cellphone.strip():
        user.cellphone = data.cellphone.strip()

    if data.address is not None:
        user.address = data.address.strip() if data.address else None

    # Regla estricta: NO se modifica user.identification bajo ninguna circunstancia

    db.add(user)
    db.commit()
    db.refresh(user)

    last_name_display = user.first_last_name
    if user.second_last_name:
        last_name_display = f"{user.first_last_name} {user.second_last_name}".strip()

    return {
        "message": "Perfil actualizado correctamente",
        "data": {
            "id": user.id,
            "identification": user.identification,
            "first_name": user.first_name,
            "last_name": last_name_display,
            "first_last_name": user.first_last_name,
            "second_name": user.second_name,
            "second_last_name": user.second_last_name,
            "phone": user.cellphone,
            "cellphone": user.cellphone,
            "address": user.address,
            "email": user.email,
        }
    }


@users_platform_router.put("/{user_id}/password")
def update_user_password(
    user_id: int,
    payload: UserPasswordUpdate,
    db: SessionDep,
    user_data: Optional[tuple[Union[User, UserPlatform], str]] = Depends(get_optional_current_user_any_type)
):
    """
    Actualiza la contraseña de un usuario verificando la contraseña actual y hasheando con bcrypt.
    """
    if user_data:
        current_user, user_type = user_data
        if user_type == "platform" and current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para actualizar la contraseña de otro usuario."
            )

    user = db.get(UserPlatform, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    try:
        is_valid_pwd = user.verify_password(payload.current_password)
    except Exception:
        is_valid_pwd = False

    if not is_valid_pwd:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contraseña actual incorrecta"
        )

    if not payload.new_password or len(payload.new_password.strip()) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La nueva contraseña debe tener al menos 6 caracteres"
        )

    user.password = UserPlatform.hash_password(payload.new_password)
    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "message": "Contraseña actualizada exitosamente"
    }


@users_platform_router.get("/{user_id}")
@users_platform_router.get("/{user_id}/profile")
def get_user_profile(
    user_id: int,
    db: SessionDep,
):
    """Obtiene los detalles del perfil y datos de facturación de un usuario."""
    user = db.get(UserPlatform, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    last_name_display = user.first_last_name
    if user.second_last_name:
        last_name_display = f"{user.first_last_name} {user.second_last_name}".strip()

    return {
        "id": user.id,
        "identification": user.identification,
        "first_name": user.first_name,
        "last_name": last_name_display,
        "first_last_name": user.first_last_name,
        "second_name": user.second_name,
        "second_last_name": user.second_last_name,
        "phone": user.cellphone,
        "cellphone": user.cellphone,
        "address": user.address,
        "email": user.email,
        "type": user.type.value if hasattr(user.type, "value") else str(user.type),
        "billing_identification": user.billing_identification,
        "billing_name": user.billing_name,
        "billing_address": user.billing_address,
        "billing_phone": user.billing_phone,
        "billing_email": user.billing_email,
    }


@users_platform_router.get("")
def get_all_users(
    current_user: Annotated[User, Depends(decode_token)],
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
