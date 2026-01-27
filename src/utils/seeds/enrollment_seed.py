from sqlmodel import Session, select, func
from src.config.db import engine
from src.models.enrollment import Enrollment, EnrollmentStatus
from src.models.course import Course
from src.models.user_platform import UserPlatform
from datetime import datetime, timedelta
import random

def seed_enrollments():
    """
    Crea inscripciones de prueba de forma automática.
    - Verifica que existan cursos y usuarios
    - Inscribe al menos 15 usuarios a diferentes cursos
    - Distribuye diferentes estados de inscripción
    """
    with Session(engine) as session:
        print("Seeding enrollments...")
        
        # Obtener todos los cursos disponibles
        courses = session.exec(select(Course)).all()
        if not courses:
            print("No hay cursos disponibles. Ejecuta primero el seed de cursos.")
            return
        
        # Obtener todos los usuarios de plataforma disponibles
        users = session.exec(select(UserPlatform)).all()
        if not users:
            print("No hay usuarios disponibles. Ejecuta primero el seed de usuarios.")
            return
        
        print(f"✓ Encontrados {len(courses)} cursos y {len(users)} usuarios")
        
        # Obtener el último ID de enrollment existente
        max_id = session.exec(select(func.max(Enrollment.id))).first()
        enrollment_id = (max_id or 0) + 1
        print(f"✓ Comenzando desde ID: {enrollment_id}")
        
        # Estados posibles para las inscripciones
        statuses = [
            EnrollmentStatus.INTERESADO,
            EnrollmentStatus.ORDEN_GENERADA,
            EnrollmentStatus.PAGADO,
            EnrollmentStatus.FACTURADO,
            EnrollmentStatus.ANULADO
        ]
        
        created_count = 0
        skipped_count = 0
        
        for course in courses[:5]:  # Primeros 5 cursos
            # Para cada curso, inscribir entre 3-100 usuarios aleatorios
            num_enrollments = random.randint(3, 100)
            selected_users = random.sample(users, min(num_enrollments, len(users)))
            
            for user in selected_users:
                # Verificar si ya existe esta inscripción
                existing = session.exec(
                    select(Enrollment).where(
                        Enrollment.id_user_platform == user.id,
                        Enrollment.id_course == course.id
                    )
                ).first()
                
                if existing:
                    skipped_count += 1
                    continue
                
                # Seleccionar estado con ponderación (más comunes: PAGADO e INTERESADO)
                status_weights = [0.25, 0.15, 0.40, 0.15, 0.05]  # Probabilidades
                status = random.choices(statuses, weights=status_weights)[0]
                
                # Generar fecha de inscripción (últimos 30 días)
                days_ago = random.randint(0, 30)
                enrollment_date = datetime.utcnow() - timedelta(days=days_ago)
                
                # URL de pago solo para estados ORDEN_GENERADA, PAGADO o FACTURADO
                payment_url = None
                if status in [EnrollmentStatus.ORDEN_GENERADA, EnrollmentStatus.PAGADO, EnrollmentStatus.FACTURADO]:
                    payment_url = f"https://payment.example.com/order/ORD-2025-{enrollment_id:03d}"
                
                # Crear la inscripción
                enrollment = Enrollment(
                    id=enrollment_id,
                    id_user_platform=user.id,
                    id_course=course.id,
                    enrollment_date=enrollment_date,
                    status=status,
                    payment_order_url=payment_url
                )
                
                session.add(enrollment)
                created_count += 1
                enrollment_id += 1
        
        # Asegurar que tenemos al menos 20 inscripciones
        # Si no alcanzamos, inscribir más usuarios a cursos adicionales
        if created_count < 20 and len(courses) > 5:
            remaining_courses = courses[5:]
            remaining_needed = 20 - created_count
            
            for i in range(remaining_needed):
                course = random.choice(remaining_courses)
                user = random.choice(users)
                
                # Verificar si ya existe
                existing = session.exec(
                    select(Enrollment).where(
                        Enrollment.id_user_platform == user.id,
                        Enrollment.id_course == course.id
                    )
                ).first()
                
                if existing:
                    continue
                
                status = random.choice(statuses)
                days_ago = random.randint(0, 30)
                enrollment_date = datetime.utcnow() - timedelta(days=days_ago)
                
                payment_url = None
                if status in [EnrollmentStatus.ORDEN_GENERADA, EnrollmentStatus.PAGADO, EnrollmentStatus.FACTURADO]:
                    payment_url = f"https://payment.example.com/order/ORD-2025-{enrollment_id:03d}"
                
                enrollment = Enrollment(
                    id=enrollment_id,
                    id_user_platform=user.id,
                    id_course=course.id,
                    enrollment_date=enrollment_date,
                    status=status,
                    payment_order_url=payment_url
                )
                
                session.add(enrollment)
                created_count += 1
                enrollment_id += 1
        
        session.commit()
        
        print("Enrollments seeded successfully.")
        print(f"  → Created: {created_count} enrollments")
        print(f"  → Skipped (duplicates): {skipped_count}")
        print(f"  → Total: {created_count} new enrollments")

if __name__ == "__main__":
    seed_enrollments()
