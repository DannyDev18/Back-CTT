from sqlmodel import Session, select, func
from src.config.db import engine
from src.models.enrollment import Enrollment, EnrollmentStatus
from src.models.course import Course
from src.models.congress import Congress
from src.models.user_platform import UserPlatform
from datetime import datetime, timedelta
import random


def seed_enrollments():
    """
    Crea inscripciones de prueba para cursos y congresos.
    - Distribuye usuarios entre cursos (primeros 5) y congresos (primeros 3)
    - Asigna estados con ponderación realista
    - Omite inscripciones duplicadas
    - Garantiza al menos 20 inscripciones en total
    """
    with Session(engine) as session:
        print("Seeding enrollments...")

        courses = session.exec(select(Course)).all()
        congresses = session.exec(select(Congress)).all()
        users = session.exec(select(UserPlatform)).all()

        if not courses and not congresses:
            print("No hay cursos ni congresos. Ejecuta primero esos seeds.")
            return
        if not users:
            print("No hay usuarios. Ejecuta primero el seed de usuarios.")
            return

        print(f"✓ {len(courses)} cursos, {len(congresses)} congresos, {len(users)} usuarios")

        max_id = session.exec(select(func.max(Enrollment.id))).first()
        enrollment_id = (max_id or 0) + 1

        statuses = [
            EnrollmentStatus.INTERESADO,
            EnrollmentStatus.ORDEN_GENERADA,
            EnrollmentStatus.PAGADO,
            EnrollmentStatus.FACTURADO,
            EnrollmentStatus.ANULADO,
        ]
        # Ponderación: PAGADO e INTERESADO son los más frecuentes
        status_weights = [0.25, 0.15, 0.40, 0.15, 0.05]

        created_count = 0
        skipped_count = 0

        # ── Inscripciones a cursos ────────────────────────────────────
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
                    payment_url = f"https://payment.example.com/order/ORD-2025-{enrollment_id:04d}"

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

        # ── Inscripciones a congresos ─────────────────────────────────
        for congress in congresses[:3]:
            num = random.randint(3, min(80, len(users)))
            selected_users = random.sample(users, num)

            for user in selected_users:
                existing = session.exec(
                    select(Enrollment).where(
                        Enrollment.id_user_platform == user.id,
                        Enrollment.id_congress == congress.id,
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
                    payment_url = f"https://payment.example.com/order/ORD-2025-{enrollment_id:04d}"

                session.add(Enrollment(
                    id=enrollment_id,
                    id_user_platform=user.id,
                    id_congress=congress.id,
                    enrollment_date=enrollment_date,
                    status=status,
                    payment_order_url=payment_url,
                ))
                created_count += 1
                enrollment_id += 1

        # ── Completar hasta 20 si hicieron falta recursos ────────────
        if created_count < 20:
            remaining = 20 - created_count
            all_resources = (
                [("course", c) for c in courses[5:]]
                + [("congress", g) for g in congresses[3:]]
            )
            if all_resources:
                for _ in range(remaining):
                    kind, resource = random.choice(all_resources)
                    user = random.choice(users)

                    if kind == "course":
                        existing = session.exec(
                            select(Enrollment).where(
                                Enrollment.id_user_platform == user.id,
                                Enrollment.id_course == resource.id,
                            )
                        ).first()
                    else:
                        existing = session.exec(
                            select(Enrollment).where(
                                Enrollment.id_user_platform == user.id,
                                Enrollment.id_congress == resource.id,
                            )
                        ).first()

                    if existing:
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
                        payment_url = f"https://payment.example.com/order/ORD-2025-{enrollment_id:04d}"

                    enrollment_kwargs = dict(
                        id=enrollment_id,
                        id_user_platform=user.id,
                        enrollment_date=enrollment_date,
                        status=status,
                        payment_order_url=payment_url,
                    )
                    if kind == "course":
                        enrollment_kwargs["id_course"] = resource.id
                    else:
                        enrollment_kwargs["id_congress"] = resource.id

                    session.add(Enrollment(**enrollment_kwargs))
                    created_count += 1
                    enrollment_id += 1

        session.commit()

        print("Enrollments seeded successfully.")
        print(f"  → Created : {created_count} enrollments")
        print(f"  → Skipped : {skipped_count} duplicates")


if __name__ == "__main__":
    seed_enrollments()
