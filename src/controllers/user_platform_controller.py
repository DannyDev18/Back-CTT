from src.models.user_platform import UserPlatform
from src.dependencies.db_session import SessionDep
from sqlmodel import select

class UserPlatformController:

    @staticmethod
    def get_user_by_email(email: str, db: SessionDep):
        statement = select(UserPlatform).where(UserPlatform.email == email)
        user = db.exec(statement).first()
        return user

    @staticmethod
    def get_user_by_identification(identification: str, db: SessionDep):
        statement = select(UserPlatform).where(UserPlatform.identification == identification)
        user = db.exec(statement).first()
        return user

    @staticmethod
    def create_user(user: UserPlatform, db: SessionDep):
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
