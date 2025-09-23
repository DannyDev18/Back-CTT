import os
from typing import Annotated
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError, ExpiredSignatureError
from dotenv import load_dotenv

from src.controllers.user_controller import UserController
from src.dependencies.db_session import SessionDep

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY","sadfasdfsadfsadfsadf")

def encode_token(payload: dict):
    payload["exp"] = datetime.now(timezone.utc) + timedelta(hours=1)  
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")
    return token

def decode_token(token: Annotated[str, Depends(oauth2_scheme)], db: SessionDep):
    try:
        data = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    email = data.get("email")
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = UserController.get_user_by_email(email, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user