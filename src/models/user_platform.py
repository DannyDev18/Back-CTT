from typing import Annotated
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, String, Enum as SQLEnum
from passlib.context import CryptContext
from pydantic import EmailStr
from enum import Enum

pwd_context = CryptContext(schemes=["bcrypt"])

EmailStrDB = Annotated[EmailStr, Field(max_length=320)]

class UserPlatformType(str, Enum):
    ESTUDIANTE = "Estudiante"
    EXTERNO = "Externo"
    ADMINISTRATIVO = "Administrativo"

class UserPlatformBase(SQLModel):
    identification: str = Field(max_length=20, nullable=False, description="Cédula o RUC")
    first_name: str = Field(max_length=100, nullable=False)
    second_name: str | None = Field(default=None, max_length=100)
    first_last_name: str = Field(max_length=100, nullable=False)
    second_last_name: str | None = Field(default=None, max_length=100)
    cellphone: str = Field(max_length=15, nullable=False)
    email: EmailStrDB = Field(
        sa_column=Column(String(320), unique=True, index=True, nullable=False)
    )
    address: str | None = Field(default=None, max_length=255)
    type: UserPlatformType = Field(
        sa_column=Column(SQLEnum(UserPlatformType), nullable=False)
    )
    password: str = Field(max_length=255, nullable=False)

class UserPlatform(UserPlatformBase, table=True):
    __tablename__ = "users_platform"
    
    id: int | None = Field(default=None, primary_key=True)

    def verify_password(self, plain_password: str) -> bool:
        return pwd_context.verify(plain_password, self.password)

    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)
