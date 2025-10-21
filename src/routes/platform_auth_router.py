from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from pydantic import BaseModel
from src.controllers.user_platform_controller import UserPlatformController
from src.dependencies.db_session import SessionDep
from src.models.user_platform import UserPlatformBase, UserPlatformType, UserPlatform
from src.utils.platform_jwt_utils import decode_platform_token, encode_platform_token

platform_auth_router = APIRouter(prefix="/api/v1/platform-auth", tags=["platform-auth"])

class UserPlatformProfile(BaseModel):
    id: int
    identification: str
    first_name: str
    second_name: str | None
    first_last_name: str
    second_last_name: str | None
    cellphone: str
    email: str
    address: str | None
    type: UserPlatformType

@platform_auth_router.post("/register")
def register(user_data: UserPlatformBase, db: SessionDep):
    # Verificar si el usuario ya existe por email
    existing_user = UserPlatformController.get_user_by_email(user_data.email, db)
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    # Verificar si el usuario ya existe por identificación
    existing_identification = UserPlatformController.get_user_by_identification(user_data.identification, db)
    if existing_identification:
        raise HTTPException(status_code=400, detail="User with this identification already exists")
    
    # Hash password
    hashed_password = UserPlatform.hash_password(user_data.password)
    
    # Crear usuario
    new_user = UserPlatform(
        identification=user_data.identification,
        first_name=user_data.first_name,
        second_name=user_data.second_name,
        first_last_name=user_data.first_last_name,
        second_last_name=user_data.second_last_name,
        cellphone=user_data.cellphone,
        email=user_data.email,
        address=user_data.address,
        type=user_data.type,
        password=hashed_password
    )
    UserPlatformController.create_user(new_user, db)
    return {"message": "Platform user registered successfully"}

@platform_auth_router.post("/token")
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: SessionDep):
    user = UserPlatformController.get_user_by_email(form_data.username, db)
    if not user or not user.verify_password(form_data.password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    token = encode_platform_token(
        {
            "user_id": user.id,
            "email": user.email,
            "type": user.type.value
        }
    )
    return {"access_token": token, "token_type": "bearer"}

@platform_auth_router.get("/profile", response_model=UserPlatformProfile)
def profile(current_user: Annotated[UserPlatformBase, Depends(decode_platform_token)]):
    return UserPlatformProfile(
        id=current_user.id,
        identification=current_user.identification,
        first_name=current_user.first_name,
        second_name=current_user.second_name,
        first_last_name=current_user.first_last_name,
        second_last_name=current_user.second_last_name,
        cellphone=current_user.cellphone,
        email=current_user.email,
        address=current_user.address,
        type=current_user.type
    )
