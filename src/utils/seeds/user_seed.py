from sqlmodel import Session
from src.config.db import engine
from src.models.user import User

def seed_users():
    with Session(engine) as session:
        print("Seeding users...")
        # Verifica si el usuario ya existe para evitar duplicados
        existing_user = session.get(User,1)
        hashed_password = User.hash_password("securepassword")
        if not existing_user:
            session.add(User(name="Daniel", last_name="Jerez", email="daniel.jerez@example.com", password=hashed_password, id=1))
            session.commit()
        else:
            # Update password if it's not hashed
            if not existing_user.password.startswith("$2b$"):
                existing_user.password = hashed_password
                session.commit()
            print("User already exists, password updated if needed.")