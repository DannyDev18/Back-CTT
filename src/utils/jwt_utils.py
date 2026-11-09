import os
from typing import Annotated, Union
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError, ExpiredSignatureError
from dotenv import load_dotenv

from src.controllers.user_controller import UserController
from src.dependencies.db_session import SessionDep

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
security_bearer = HTTPBearer()
load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY","sadfasdfsadfsadfsadf")

def encode_token(payload: dict):
    payload["exp"] = datetime.now(timezone.utc) + timedelta(hours=9)  
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


async def get_current_user_any_type(
    db: SessionDep,
    credentials: HTTPAuthorizationCredentials = Depends(security_bearer),
):
    """
    Autentica como admin (User) o usuario de plataforma (UserPlatform).
    Retorna (usuario, tipo) donde tipo es 'admin' o 'platform'.
    """
    token = credentials.credentials

    # Intentar como Admin
    try:
        data = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        email = data.get("email")
        if email:
            user = UserController.get_user_by_email(email, db)
            if user:
                return user, "admin"
    except Exception:
        pass

    # Intentar como Platform User (Estudiante / Participante)
    try:
        from src.utils.platform_jwt_utils import JWT_SECRET_KEY as PLATFORM_JWT_SECRET_KEY
        from src.controllers.user_platform_controller import UserPlatformController

        data = jwt.decode(token, PLATFORM_JWT_SECRET_KEY, algorithms=["HS256"])
        email = data.get("email")
        if email:
            user = UserPlatformController.get_user_by_email(email, db)
            if user:
                return user, "platform"
    except Exception:
        pass

    raise HTTPException(status_code=401, detail="Credenciales inválidas o token expirado")
