from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from fastapi.security import  OAuth2PasswordRequestForm
from typing import Annotated
from src.controllers.user_controller import UserController
from src.dependencies.db_session import SessionDep
from src.models.user import User, UserCreate
from src.utils.jwt_utils import decode_token, encode_token

auth_router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

@auth_router.post("/register")
def register(user_data: UserCreate, db: SessionDep):
    # Check if user already exists
    existing_user = UserController.get_user_by_email(user_data.email, db)
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Hash password
    hashed_password = User.hash_password(user_data.password)
    
    # Create user
    new_user = User(
        name=user_data.name,
        last_name=user_data.last_name,
        email=user_data.email,
        password=hashed_password
    )
    UserController.create_user(new_user, db)
    return {"message": "User registered successfully"}

@auth_router.post("/token")
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: SessionDep):
    user = UserController.get_user_by_email(form_data.username, db)
    if not user or not user.verify_password(form_data.password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    token = encode_token(
        {
            "username": user.name,
            "email": user.email
        }
    )
    return {"access_token": token}

@auth_router.get("/profile")
def profile(current_user: Annotated[User, Depends(decode_token)]):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "last_name": current_user.last_name,
        "email": current_user.email
    }