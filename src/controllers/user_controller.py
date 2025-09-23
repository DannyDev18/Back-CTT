from src.models.user import User
from src.dependencies.db_session import SessionDep
from sqlmodel import select

class UserController:

    @staticmethod
    def get_user_by_email(email: str, db: SessionDep):
        statement = select(User).where(User.email == email)
        user = db.exec(statement).first()
        return user

    @staticmethod
    def create_user(user: User, db: SessionDep):
        db.add(user)
        db.commit()
        db.refresh(user)
        return user