from src.models.user_platform import UserPlatform, UserPlatformType
from src.dependencies.db_session import SessionDep
from sqlmodel import select, Session

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

    @staticmethod
    def get_all_users(
        db: Session,
        page: int = 1,
        page_size: int = 10,
        type: str | None = None
    ) -> dict:
        from sqlalchemy import func
        statement = select(UserPlatform)
        
        if type:
            statement = statement.where(UserPlatform.type == type)
        
        statement = statement.order_by(UserPlatform.id)
        
        total_statement = select(func.count()).select_from(UserPlatform)
        
        if type:
            total_statement = total_statement.where(UserPlatform.type == type)
        
        total_row = db.exec(total_statement).first()
        offset = (page - 1) * page_size
        users = db.exec(statement.offset(offset).limit(page_size)).all()
        
        result = []
        for user in users:
            user_dict = {
                "id": user.id,
                "identification": user.identification,
                "first_name": user.first_name,
                "second_name": user.second_name,
                "first_last_name": user.first_last_name,
                "second_last_name": user.second_last_name,
                "cellphone": user.cellphone,
                "email": user.email,
                "address": user.address,
                "type": user.type
            }
            result.append(user_dict)
        
        if total_row is None:
            total = 0
        elif isinstance(total_row, (tuple, list)):
            total = int(total_row[0])
        else:
            try:
                total = int(total_row)
            except Exception:
                total = int(total_row[0])
        
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        has_next = page < total_pages
        has_prev = page > 1 and total_pages > 0
        base_path = "/api/v1/users"
        
        type_param = f"&type={type}" if type else ""
        
        links = {
            "self": f"{base_path}?page={page}&page_size={page_size}{type_param}",
            "next": f"{base_path}?page={page + 1}&page_size={page_size}{type_param}" if has_next else None,
            "prev": f"{base_path}?page={page - 1}&page_size={page_size}{type_param}" if has_prev else None,
        }
        
        return {
            "total": total,
            "total_pages": total_pages,
            "page": page,
            "page_size": page_size,
            "has_next": has_next,
            "has_prev": has_prev,
            "links": links,
            "users": result,
        }
