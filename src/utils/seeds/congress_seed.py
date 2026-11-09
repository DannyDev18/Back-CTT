from sqlmodel import Session, select
from src.config.db import engine
from src.models.congress_model import Congress
from datetime import date

def seed_congresses():
    """
    Seed de congresos oficiales para el sistema CTT de la FISEI UTA.
    Registra exclusivamente los congresos institucionales reales de la facultad:
    - VII CSEI 2026 (vigente)
    - VI CSEI 2024 (pasado / legalidad y memorias)
    - V CSEI 2023 (pasado / legalidad y memorias)
    - I Jornadas de Investigación CISED 2025 (vigente)
    """
    with Session(engine) as session:
        print("Seeding official FISEI UTA congresses...")

        fisei_congresses = [
            {
                "nombre": "VII Congreso Internacional de Ciencia de la Computación, Electrónica e Ingeniería Industrial (CSEI 2026)",
                "edicion": "VII-2026",
                "anio": 2026,
                "fecha_inicio": date(2026, 10, 21),
                "fecha_fin": date(2026, 10, 23),
                "descripcion_general": "El VII Congreso Internacional de Ciencia de la Computación, Electrónica e Ingeniería Industrial (CSEI 2026) es el evento científico insignia de la FISEI - UTA, indexado en Scopus/IEEE, reuniendo a investigadores nacionales e internacionales.",
                "poster_cover_url": "https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=1200&auto=format&fit=crop&q=80",
                "lugar_sede": "Universidad Técnica de Ambato - Campus Huachi, FISEI",
                "modalidad": "Presencial",
                "duracion_horas": 40,
                "sitio_web_oficial": "https://csei.uta.edu.ec",
                "cupo_maximo": 300,
                "costo_estudiante_uta": 20.00,
                "costo_profesional": 50.00,
                "costo_ponente": 80.00
            },
            {
                "nombre": "VI Congreso Internacional de Ciencia de la Computación, Electrónica e Ingeniería Industrial (CSEI 2024)",
                "edicion": "VI-2024",
                "anio": 2024,
                "fecha_inicio": date(2024, 10, 23),
                "fecha_fin": date(2024, 10, 25),
                "descripcion_general": "Sexta edición del Congreso Internacional CSEI de la FISEI, con memorias científicas publicadas en Springer y ponencias en Inteligencia Artificial, Redes de Datos y Automatización Industrial.",
                "poster_cover_url": "https://images.unsplash.com/photo-1505373877841-8d25f7d46678?w=1200&auto=format&fit=crop&q=80",
                "lugar_sede": "Universidad Técnica de Ambato - Campus Huachi, FISEI",
                "modalidad": "Presencial",
                "duracion_horas": 40,
                "sitio_web_oficial": "https://csei2024.uta.edu.ec",
                "cupo_maximo": 250,
                "costo_estudiante_uta": 20.00,
                "costo_profesional": 50.00,
                "costo_ponente": 80.00
            },
            {
                "nombre": "V Congreso Internacional de Ciencia de la Computación, Electrónica e Ingeniería Industrial (CSEI 2023)",
                "edicion": "V-2023",
                "anio": 2023,
                "fecha_inicio": date(2023, 10, 25),
                "fecha_fin": date(2023, 10, 27),
                "descripcion_general": "Quinta edición del congreso científico insignia de la FISEI con foco en Robótica Aplicada, Ciberseguridad y Tecnologías Emergentes para la Industria.",
                "poster_cover_url": "https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?w=1200&auto=format&fit=crop&q=80",
                "lugar_sede": "Universidad Técnica de Ambato - Campus Huachi, FISEI",
                "modalidad": "Presencial",
                "duracion_horas": 40,
                "sitio_web_oficial": "https://csei2023.uta.edu.ec",
                "cupo_maximo": 200,
                "costo_estudiante_uta": 20.00,
                "costo_profesional": 50.00,
                "costo_ponente": 80.00
            },
            {
                "nombre": "I Jornadas de Investigación y Transferencia Tecnológica FISEI (CISED 2025)",
                "edicion": "CISED-2025",
                "anio": 2025,
                "fecha_inicio": date(2025, 11, 12),
                "fecha_fin": date(2025, 11, 14),
                "descripcion_general": "Espacio multidisciplinario de divulgación de semilleros de investigación, prototipos de ingeniería de software, hardware y vinculación tecnológica con la sociedad de la FISEI UTA.",
                "poster_cover_url": "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=1200&auto=format&fit=crop&q=80",
                "lugar_sede": "Auditorio Central FISEI - Campus Huachi",
                "modalidad": "Presencial",
                "duracion_horas": 30,
                "sitio_web_oficial": "https://fisei.uta.edu.ec/cised",
                "cupo_maximo": 180,
                "costo_estudiante_uta": 15.00,
                "costo_profesional": 35.00,
                "costo_ponente": 50.00
            }
        ]

        created_count = 0
        existing_count = 0

        for congress_data in fisei_congresses:
            existing = session.exec(
                select(Congress).where(
                    Congress.edicion == congress_data["edicion"],
                    Congress.anio == congress_data["anio"]
                )
            ).first()

            if not existing:
                new_congress = Congress(**congress_data)
                session.add(new_congress)
                created_count += 1
                print(f"  ✓ Created FISEI congress: {congress_data['nombre']}")
            else:
                existing_count += 1
                # Actualizar datos si cambiaron
                for key, val in congress_data.items():
                    setattr(existing, key, val)
                session.add(existing)
                print(f"  ~ Updated FISEI congress: {congress_data['nombre']}")

        session.commit()
        print(f"\nFISEI UTA Congresses seeded successfully! ✅")
        print(f"   - Created: {created_count}")
        print(f"   - Updated/Existing: {existing_count}")

if __name__ == "__main__":
    seed_congresses()
