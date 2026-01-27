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
        
        # Crear usuarios adicionales automáticamente (IDs 4-20)
        first_names = [
            "Juan", "Laura", "Diego", "Carmen", "Luis", "Sofía", "Pedro", 
            "Isabel", "Miguel", "Patricia", "Roberto", "Lucía", "Fernando", 
            "Elena", "Andrés", "Daniela", "Jorge"
        ]
        
        last_names = [
            "López", "García", "Martínez", "Rodríguez", "Fernández", "Torres", 
            "Sánchez", "Díaz", "Vargas", "Castro", "Ortiz", "Ruiz", "Mendoza", 
            "Jiménez", "Herrera", "Silva", "Paredes", "Guzmán"
        ]
        
        created_count = 0
        updated_count = 0
        
        # Generar usuarios del 4 al 20
        for i in range(4, 21):
            existing_user = session.get(UserPlatform, i)
            
            idx = (i - 4) % len(first_names)
            first_name = first_names[idx]
            first_last_name = last_names[idx % len(last_names)]
            second_last_name = last_names[(idx + 3) % len(last_names)]
            
            # Segundo nombre: solo algunos usuarios lo tienen
            second_name = None if i % 3 == 0 else ["José", "María", "Antonio", "Teresa", "Luis", "Rosa"][idx % 6]
            
            # Generar datos únicos
            identification = f"{1200000000 + i:010d}"
            cellphone = f"099{7000000 + i:07d}"
            email = f"{first_name.lower()}.{first_last_name.lower()}{i}@example.com"
            address = None if i % 4 == 0 else f"Calle {i} y Av. Principal {i*10}"
            
            # Distribuir tipos: mayoría estudiantes
            if i <= 15:
                user_type = UserPlatformType.ESTUDIANTE
                password = f"estudiante{i}"
            elif i <= 18:
                user_type = UserPlatformType.EXTERNO
                password = f"externo{i}"
            else:
                user_type = UserPlatformType.ADMINISTRATIVO
                password = f"admin{i}"
            
            hashed_password = UserPlatform.hash_password(password)
            
            if not existing_user:
                session.add(UserPlatform(
                    id=i,
                    identification=identification,
                    first_name=first_name,
                    second_name=second_name,
                    first_last_name=first_last_name,
                    second_last_name=second_last_name,
                    cellphone=cellphone,
                    email=email,
                    address=address,
                    type=user_type,
                    password=hashed_password
                ))
                created_count += 1
            else:
                if not existing_user.password.startswith("$2b$"):
                    existing_user.password = hashed_password
                    updated_count += 1
        
        session.commit()
        print("Platform users seeded successfully.")
        print(f"  → Manual users (1-3): verified")
        print(f"  → Auto-generated users (4-20): {created_count} created, {updated_count} updated")

if __name__ == "__main__":
    seed_users_platform()
