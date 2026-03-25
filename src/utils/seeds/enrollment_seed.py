from sqlmodel import Session, select, func
from src.config.db import engine
from src.models.enrollment import Enrollment, EnrollmentStatus
from src.models.course import Course
from src.models.congress_model import Congress  # Usar el nuevo modelo Congress
from src.models.user_platform import UserPlatform
from datetime import datetime, timedelta
import random


def seed_enrollments():
    """
    Crea inscripciones de prueba para cursos y congresos (usando nuevo modelo Congress).
    - Distribuye usuarios entre cursos y congresos teológicos
    - Asigna estados con ponderación realista
    - Omite inscripciones duplicadas
    - Genera fechas de inscripción lógicas según las fechas de los congresos
    """
    with Session(engine) as session:
        print("Seeding enrollments...")

        courses = session.exec(select(Course)).all()
        congresses = session.exec(select(Congress)).all()  # Nuevo modelo Congress
        users = session.exec(select(UserPlatform)).all()

        if not courses and not congresses:
            print("  ❌ No hay cursos ni congresos. Ejecuta primero esos seeds.")
            return
        if not users:
            print("  ❌ No hay usuarios. Ejecuta primero el seed de usuarios de plataforma.")
            return

        print(f"  ✓ {len(courses)} cursos, {len(congresses)} congresos, {len(users)} usuarios")

        max_id = session.exec(select(func.max(Enrollment.id))).first()
        enrollment_id = (max_id or 0) + 1

        statuses = [
            EnrollmentStatus.INTERESADO,
            EnrollmentStatus.ORDEN_GENERADA,
            EnrollmentStatus.PAGADO,
            EnrollmentStatus.FACTURADO,
            EnrollmentStatus.ANULADO,
        ]
        # Ponderación realista para congresos teológicos: muchos interesados, buenos pagos
        status_weights = [0.30, 0.15, 0.35, 0.15, 0.05]

        created_count = 0
        skipped_count = 0

        # ── Inscripciones a cursos (conservar lógica existente) ──────────
        print(f"\n  Creating course enrollments...")
        for course in courses[:5]:
            num = random.randint(3, min(100, len(users)))
            selected_users = random.sample(users, num)

            for user in selected_users:
                existing = session.exec(
                    select(Enrollment).where(
                        Enrollment.id_user_platform == user.id,
                        Enrollment.id_course == course.id,
                    )
                ).first()
                if existing:
                    skipped_count += 1
                    continue

                status = random.choices(statuses, weights=status_weights)[0]
                days_ago = random.randint(0, 30)
                enrollment_date = datetime.utcnow() - timedelta(days=days_ago)
                payment_url = None
                if status in (
                    EnrollmentStatus.ORDEN_GENERADA,
                    EnrollmentStatus.PAGADO,
                    EnrollmentStatus.FACTURADO,
                ):
                    payment_url = f"https://payment.cttecuador.com/order/ORD-2025-{enrollment_id:04d}"

                session.add(Enrollment(
                    id=enrollment_id,
                    id_user_platform=user.id,
                    id_course=course.id,
                    enrollment_date=enrollment_date,
                    status=status,
                    payment_order_url=payment_url,
                ))
                created_count += 1
                enrollment_id += 1

        # ── Inscripciones a congresos (MEJORADA con nuevo modelo) ──────
        print(f"\n  Creating congress enrollments...")
        current_date = datetime.now()

        for congress in congresses:
            print(f"    Processing: {congress.nombre[:50]}...")

            # Determinar número de inscripciones basado en el perfil del congreso
            # Congresos futuros tienen más inscripciones activas
            if congress.fecha_inicio > current_date.date():
                # Congress futuro: más inscripciones, menos anulados
                num_enrollments = random.randint(10, min(150, len(users) // 2))
                future_weights = [0.40, 0.20, 0.25, 0.10, 0.05]  # Más interesados
            else:
                # Congress pasado: distribución normal
                num_enrollments = random.randint(5, min(80, len(users) // 3))
                future_weights = status_weights

            selected_users = random.sample(users, min(num_enrollments, len(users)))

            for user in selected_users:
                existing = session.exec(
                    select(Enrollment).where(
                        Enrollment.id_user_platform == user.id,
                        Enrollment.id_congress == congress.id_congreso,  # Usar id_congreso del nuevo modelo
                    )
                ).first()
                if existing:
                    skipped_count += 1
                    continue

                status = random.choices(statuses, weights=future_weights)[0]

                # Generar fecha de inscripción lógica
                if congress.fecha_inicio > current_date.date():
                    # Congress futuro: inscripciones desde hace 3 meses hasta ahora
                    max_days_ago = min(90, (current_date.date() - congress.fecha_inicio).days + 90)
                    days_ago = random.randint(0, max(1, max_days_ago))
                else:
                    # Congress pasado: inscripciones desde 3 meses antes hasta 1 semana después
                    congress_start = datetime.combine(congress.fecha_inicio, datetime.min.time())
                    days_before_congress = random.randint(1, 90)
                    enrollment_date = congress_start - timedelta(days=days_before_congress)

                    # Algunos se inscriben después del congress (hasta 7 días)
                    if random.random() < 0.1:  # 10% se inscriben después
                        enrollment_date = congress_start + timedelta(days=random.randint(1, 7))

                if 'enrollment_date' not in locals():
                    enrollment_date = current_date - timedelta(days=days_ago)

                # Generar URL de pago para estados que la requieren
                payment_url = None
                if status in (
                    EnrollmentStatus.ORDEN_GENERADA,
                    EnrollmentStatus.PAGADO,
                    EnrollmentStatus.FACTURADO,
                ):
                    congress_code = congress.edicion.replace('-', '').upper()
                    payment_url = f"https://payment.cttecuador.com/congress/{congress_code}/order/{enrollment_id:06d}"

                session.add(Enrollment(
                    id=enrollment_id,
                    id_user_platform=user.id,
                    id_congress=congress.id_congreso,  # Usar id_congreso del nuevo modelo
                    enrollment_date=enrollment_date,
                    status=status,
                    payment_order_url=payment_url,
                ))
                created_count += 1
                enrollment_id += 1

        # ── Completar inscripciones adicionales si es necesario ─────────
        if created_count < 50 and congresses:  # Aumentar mínimo a 50 para mejor testing
            print(f"\n  Adding additional enrollments to reach minimum...")
            remaining = 50 - created_count

            for _ in range(remaining):
                if not congresses:
                    break

                congress = random.choice(congresses)
                user = random.choice(users)

                existing = session.exec(
                    select(Enrollment).where(
                        Enrollment.id_user_platform == user.id,
                        Enrollment.id_congress == congress.id_congreso,
                    )
                ).first()

                if existing:
                    continue

                status = random.choices(statuses, weights=status_weights)[0]
                days_ago = random.randint(1, 60)
                enrollment_date = datetime.utcnow() - timedelta(days=days_ago)

                payment_url = None
                if status in (
                    EnrollmentStatus.ORDEN_GENERADA,
                    EnrollmentStatus.PAGADO,
                    EnrollmentStatus.FACTURADO,
                ):
                    congress_code = congress.edicion.replace('-', '').upper()
                    payment_url = f"https://payment.cttecuador.com/congress/{congress_code}/order/{enrollment_id:06d}"

                session.add(Enrollment(
                    id=enrollment_id,
                    id_user_platform=user.id,
                    id_congress=congress.id_congreso,
                    enrollment_date=enrollment_date,
                    status=status,
                    payment_order_url=payment_url,
                ))
                created_count += 1
                enrollment_id += 1

        session.commit()

        print(f"\nEnrollments seeded successfully! ✅")
        print(f"   - Created: {created_count} enrollments")
        print(f"   - Skipped: {skipped_count} duplicates")

        # Mostrar estadísticas por estado
        print(f"\n   📊 Enrollment Status Distribution:")
        for status in EnrollmentStatus:
            count_query = select(Enrollment).where(Enrollment.status == status)
            count = len(session.exec(count_query).all())
            if count > 0:
                percentage = (count / created_count) * 100 if created_count > 0 else 0
                print(f"    - {status.value}: {count} ({percentage:.1f}%)")

        # Estadísticas por congreso
        print(f"\n   📊 Top Congress Enrollments:")
        congress_enrollments = []
        for congress in congresses[:5]:
            count_query = select(Enrollment).where(Enrollment.id_congress == congress.id_congreso)
            count = len(session.exec(count_query).all())
            congress_enrollments.append((congress.nombre, count))

        congress_enrollments.sort(key=lambda x: x[1], reverse=True)
        for name, count in congress_enrollments[:5]:
            display_name = name[:50] + '...' if len(name) > 50 else name
            print(f"    - {display_name}: {count} enrollments")


if __name__ == "__main__":
    seed_enrollments()
