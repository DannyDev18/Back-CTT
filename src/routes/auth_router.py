import os
from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Annotated
from jose import jwt
from dotenv import load_dotenv
from src.controllers.user_controller import UserController
from src.dependencies.db_session import SessionDep
from src.models.user import User, UserBase

load_dotenv()

auth_router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY","sadfasdfsadfsadfsadf")

def encode_token(payload: dict):
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")
    return token

def decode_token(token: Annotated[str, Depends(oauth2_scheme)], db: SessionDep):
    data = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
    email = data.get("email")
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = UserController.get_user_by_email(email, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user

@auth_router.post("/register")
def register(user_data: UserBase, db: SessionDep):
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

@auth_router.get("/users/profile")
def profile(current_user: Annotated[User, Depends(decode_token)]):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "last_name": current_user.last_name,
        "email": current_user.email
    }