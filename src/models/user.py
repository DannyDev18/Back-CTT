from typing import Annotated, List
from sqlmodel import Relationship, SQLModel, Field
from sqlalchemy import Column, String
from passlib.context import CryptContext
from pydantic import EmailStr

pwd_context = CryptContext(schemes=["bcrypt"])

EmailStrDB = Annotated[EmailStr, Field(max_length=320)]

class UserBase(SQLModel):
    name: str = Field(max_length=100, nullable=False)
    last_name: str = Field(max_length=100, nullable=False)
    # Forzamos VARCHAR(320) y el índice único en SQL Server:
    email: EmailStrDB = Field(
        sa_column=Column(String(320), unique=True, index=True, nullable=False)
    )
    password: str = Field(max_length=255, nullable=False)

class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

    #relaciones
    categories: List["Category"] = Relationship(back_populates="creator")
    congress_categories: List["CongressCategory"] = Relationship(back_populates="creator")
    def verify_password(self, plain_password: str) -> bool:
        return pwd_context.verify(plain_password, self.password)

    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password) 
User.update_forward_refs()
from src.models.category import Category
from src.models.congress_category import CongressCategory
