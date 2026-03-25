"""
Main seed file para el sistema CTT - Ecuador
Ejecuta todos los seeds en el orden correcto respetando dependencias
"""

from sqlmodel import Session
from src.config.db import engine

# Import all seed functions
from src.utils.seeds.user_seed import seed_users
from src.utils.seeds.user_platform_seed import seed_users_platform
from src.utils.seeds.categories_seed import seed_categories
from src.utils.seeds.congress_categories_seed import seed_congress_categories
from src.utils.seeds.courses_seed import seed_courses
from src.utils.seeds.congress_seed import seed_congresses
from src.utils.seeds.sponsors_seed import seed_sponsors
from src.utils.seeds.speakers_seed import seed_speakers
from src.utils.seeds.sesion_cronograma_seed import seed_sesion_cronograma
from src.utils.seeds.congreso_sponsor_seed import seed_congreso_sponsor
from src.utils.seeds.enrollment_seed import seed_enrollments


def run_all_seeds():
    """
    Ejecuta todos los seeds en el orden correcto

    Orden de dependencias:
    1. Usuarios del sistema (admin)
    2. Usuarios de plataforma
    3. Categorías (para cursos y congresos)
    4. Cursos
    5. Congresos
    6. Sponsors
    7. Speakers (dependen de congresos)
    8. Sesiones del cronograma (dependen de congresos y speakers)
    9. Asociaciones congreso-sponsor (dependen de congresos y sponsors)
    10. Inscripciones (dependen de usuarios, cursos y congresos)
    """

    print(">> Starting CTT Ecuador Database Seeding Process...")
    print("="*70)

    try:
        # Verificar conectividad de base de datos
        with Session(engine) as session:
            print("✓ Database connection successful")

        # STEP 1: Usuarios del sistema (administradores)
        print("\n>> STEP 1: System Users (Administrators)")
        print("-" * 50)
        seed_users()

        # STEP 2: Usuarios de plataforma (estudiantes, externos, administrativos)
        print("\n>> STEP 2: Platform Users")
        print("-" * 50)
        seed_users_platform()

        # STEP 3: Categorías de cursos
        print("\n>> STEP 3: Course Categories")
        print("-" * 50)
        seed_categories()

        # STEP 4: Categorías de congresos
        print("\n>> STEP 4: Congress Categories")
        print("-" * 50)
        seed_congress_categories()

        # STEP 5: Cursos
        print("\n>> STEP 5: Courses")
        print("-" * 50)
        try:
            seed_courses()
        except Exception as e:
            print(f"  WARNING: Course seeding failed: {str(e)}")
            print("  Continuing with congress-only seeding...")

        # STEP 6: Congresos
        print("\n>> STEP 6: Congresses")
        print("-" * 50)
        seed_congresses()

        # STEP 7: Sponsors
        print("\n>> STEP 7: Sponsors")
        print("-" * 50)
        seed_sponsors()

        # STEP 8: Speakers
        print("\n>> STEP 8: Speakers")
        print("-" * 50)
        seed_speakers()

        # STEP 9: Sesiones del Cronograma
        print("\n>> STEP 9: Session Schedule")
        print("-" * 50)
        seed_sesion_cronograma()

        # STEP 10: Asociaciones Congreso-Sponsor
        print("\n>> STEP 10: Congress-Sponsor Associations")
        print("-" * 50)
        seed_congreso_sponsor()

        # STEP 11: Inscripciones (Enrollments)
        print("\n>> STEP 11: Enrollments")
        print("-" * 50)
        seed_enrollments()

        print("\n" + "="*70)
        print(">> ALL SEEDS COMPLETED SUCCESSFULLY!")
        print("="*70)

        # Mostrar resumen final
        show_seeding_summary()

    except Exception as e:
        print(f"\nERROR: Seeding process failed: {str(e)}")
        print("Please check the error and fix any issues before running again.")
        raise


def show_seeding_summary():
    """
    Muestra un resumen de los datos creados
    """
    from sqlmodel import select, func
    from src.models.user import User
    from src.models.user_platform import UserPlatform
    from src.models.category import Category
    from src.models.congress_category import CongressCategory
    from src.models.congress_model import Congress
    from src.models.sponsor_model import Sponsor
    from src.models.speaker_model import Speaker
    from src.models.sesion_cronograma_model import SesionCronograma
    from src.models.congreso_sponsor_model import CongresoSponsor
    from src.models.enrollment import Enrollment

    print("\n>> SEEDING SUMMARY")
    print("-" * 50)

    try:
        with Session(engine) as session:
            # Contar registros en cada tabla
            users_count = len(session.exec(select(User)).all())
            platform_users_count = len(session.exec(select(UserPlatform)).all())
            categories_count = len(session.exec(select(Category)).all())
            congress_categories_count = len(session.exec(select(CongressCategory)).all())
            congresses_count = len(session.exec(select(Congress)).all())
            sponsors_count = len(session.exec(select(Sponsor)).all())
            speakers_count = len(session.exec(select(Speaker)).all())
            sessions_count = len(session.exec(select(SesionCronograma)).all())
            associations_count = len(session.exec(select(CongresoSponsor)).all())
            enrollments_count = len(session.exec(select(Enrollment)).all())

            print(f"System Users: {users_count}")
            print(f"Platform Users: {platform_users_count}")
            print(f"Course Categories: {categories_count}")
            print(f"Congress Categories: {congress_categories_count}")
            print(f"Congresses: {congresses_count}")
            print(f"Sponsors: {sponsors_count}")
            print(f"Speakers: {speakers_count}")
            print(f"Schedule Sessions: {sessions_count}")
            print(f"Congress-Sponsor Associations: {associations_count}")
            print(f"Enrollments: {enrollments_count}")

            print("-" * 50)
            total_records = users_count + platform_users_count + categories_count + congress_categories_count + congresses_count + sponsors_count + speakers_count + sessions_count + associations_count + enrollments_count
            print(f"Total Records Created: {total_records}")

            # Información adicional útil
            print(f"\n>> Next Steps:")
            print(f"   - API Server: Run 'uvicorn src.main:app --reload'")
            print(f"   - Test Suite: Run 'pytest tests/'")
            print(f"   - Admin Panel: Access via admin endpoints")

    except Exception as e:
        print(f"  WARNING: Could not generate summary: {str(e)}")


def seed_congress_only():
    """
    Ejecuta solo los seeds relacionados con congresos
    Útil para desarrollo y testing específico de congresos
    """
    print(">> Starting Congress-Only Seeding Process...")
    print("="*50)

    try:
        print("\n>> System Users...")
        seed_users()

        print("\n>> Platform Users...")
        seed_users_platform()

        print("\n>> Congress Categories...")
        seed_congress_categories()

        print("\n>> Congresses...")
        seed_congresses()

        print("\n>> Sponsors...")
        seed_sponsors()

        print("\n>> Speakers...")
        seed_speakers()

        print("\n>> Session Schedule...")
        seed_sesion_cronograma()

        print("\n>> Congress-Sponsor Associations...")
        seed_congreso_sponsor()

        print("\n>> Congress Enrollments...")
        seed_enrollments()

        print("\n>> CONGRESS SEEDING COMPLETED!")

    except Exception as e:
        print(f"\nERROR: Congress seeding failed: {str(e)}")
        raise


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "congress-only":
        seed_congress_only()
    else:
        run_all_seeds()