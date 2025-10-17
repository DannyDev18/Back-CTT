from sqlmodel import SQLModel, Field
from passlib.context import CryptContext
from pydantic import EmailStr

pwd_context = CryptContext(schemes=["bcrypt"])

class UserBase(SQLModel):
    name: str = Field()
    last_name: str = Field()
    email: EmailStr = Field(index=True, unique=True, nullable=False)
    password: str = Field()

class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

    def verify_password(self, plain_password: str) -> bool:
        return pwd_context.verify(plain_password, self.password)

    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password) 