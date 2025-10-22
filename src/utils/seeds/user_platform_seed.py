from sqlmodel import Session
from src.config.db import engine
from src.models.user_platform import UserPlatform, UserPlatformType

def seed_users_platform():
    with Session(engine) as session:
        print("Seeding platform users...")
        
        # Usuario 1: Estudiante
        existing_user1 = session.get(UserPlatform, 1)
        hashed_password1 = UserPlatform.hash_password("estudiante123")
        if not existing_user1:
            session.add(UserPlatform(
                id=1,
                identification="1234567890",
                first_name="María",
                second_name="Isabel",
                first_last_name="González",
                second_last_name="Pérez",
                cellphone="0998765432",
                email="maria.gonzalez@example.com",
                address="Av. Simón Bolívar 123",
                type=UserPlatformType.ESTUDIANTE,
                password=hashed_password1
            ))
        else:
            if not existing_user1.password.startswith("$2b$"):
                existing_user1.password = hashed_password1
        
        # Usuario 2: Externo
        existing_user2 = session.get(UserPlatform, 2)
        hashed_password2 = UserPlatform.hash_password("externo123")
        if not existing_user2:
            session.add(UserPlatform(
                id=2,
                identification="9876543210",
                first_name="Carlos",
                second_name=None,
                first_last_name="Ramírez",
                second_last_name="Torres",
                cellphone="0987654321",
                email="carlos.ramirez@example.com",
                address="Calle 10 de Agosto 456",
                type=UserPlatformType.EXTERNO,
                password=hashed_password2
            ))
        else:
            if not existing_user2.password.startswith("$2b$"):
                existing_user2.password = hashed_password2
        
        # Usuario 3: Administrativo
        existing_user3 = session.get(UserPlatform, 3)
        hashed_password3 = UserPlatform.hash_password("admin123")
        if not existing_user3:
            session.add(UserPlatform(
                id=3,
                identification="1726543890",
                first_name="Ana",
                second_name="Lucía",
                first_last_name="Morales",
                second_last_name=None,
                cellphone="0991234567",
                email="ana.morales@example.com",
                address=None,
                type=UserPlatformType.ADMINISTRATIVO,
                password=hashed_password3
            ))
        else:
            if not existing_user3.password.startswith("$2b$"):
                existing_user3.password = hashed_password3
        
        session.commit()
        print("Platform users seeded successfully.")
