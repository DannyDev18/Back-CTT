from sqlmodel import Session, select
from src.config.db import engine
from src.models.congress_model import Congress
from src.models.congress_category import CongressCategory
from datetime import date

def seed_congresses():
    """
    Seed de congresos para el sistema CTT
    Crea congresos teológicos realistas con fechas futuras
    """
    with Session(engine) as session:
        print("Seeding congresses...")

        # Obtener algunas categorías existentes para asociar
        teologia_categoria = session.exec(
            select(CongressCategory).where(CongressCategory.name.contains("Teología"))
        ).first()

        # Lista de congresos teológicos realistas
        congresses = [
            {
                "nombre": "Congreso Internacional de Teología Sistemática 2026",
                "edicion": "CITS-2026",
                "anio": 2026,
                "fecha_inicio": date(2026, 3, 15),
                "fecha_fin": date(2026, 3, 17),
                "descripcion_general": "Congreso internacional reuniendo a los principales teólogos sistemáticos de América Latina para discutir temas doctrinales contemporáneos y su relevancia para la iglesia del siglo XXI.",
                "poster_cover_url": "https://example.com/posters/cits-2026.jpg"
            },
            {
                "nombre": "Simposio de Hermenéutica Bíblica 2026",
                "edicion": "SHB-2026",
                "anio": 2026,
                "fecha_inicio": date(2026, 4, 22),
                "fecha_fin": date(2026, 4, 24),
                "descripcion_general": "Simposio especializado en métodos de interpretación bíblica contemporánea, exégesis y aplicación homilética. Dirigido a pastores, estudiantes de teología y académicos.",
                "poster_cover_url": "https://example.com/posters/shb-2026.jpg"
            },
            {
                "nombre": "Conferencia Latinoamericana de Misiones 2026",
                "edicion": "CLM-2026",
                "anio": 2026,
                "fecha_inicio": date(2026, 5, 10),
                "fecha_fin": date(2026, 5, 12),
                "descripcion_general": "Conferencia enfocada en la obra misionera en América Latina, estrategias de evangelización urbana y plantación de iglesias en contextos multiculturales.",
                "poster_cover_url": "https://example.com/posters/clm-2026.jpg"
            },
            {
                "nombre": "Congreso de Ética Cristiana y Bioética 2026",
                "edicion": "CECB-2026",
                "anio": 2026,
                "fecha_inicio": date(2026, 6, 5),
                "fecha_fin": date(2026, 6, 7),
                "descripcion_general": "Congreso que aborda los desafíos éticos contemporáneos desde una perspectiva cristiana, incluyendo bioética, ética médica y dilemas morales modernos.",
                "poster_cover_url": "https://example.com/posters/cecb-2026.jpg"
            },
            {
                "nombre": "Simposio de Historia del Cristianismo Primitivo",
                "edicion": "SHCP-2026",
                "anio": 2026,
                "fecha_inicio": date(2026, 7, 14),
                "fecha_fin": date(2026, 7, 16),
                "descripcion_general": "Simposio académico sobre los primeros siglos del cristianismo, desarrollo doctrinal, patrística y formación del canon bíblico.",
                "poster_cover_url": "https://example.com/posters/shcp-2026.jpg"
            },
            {
                "nombre": "Congreso de Liderazgo Pastoral y Eclesiástico",
                "edicion": "CLPE-2026",
                "anio": 2026,
                "fecha_inicio": date(2026, 8, 18),
                "fecha_fin": date(2026, 8, 20),
                "descripcion_general": "Congreso dirigido a pastores y líderes eclesiásticos, enfocado en desarrollo del liderazgo, administración pastoral y cuidado integral de la congregación.",
                "poster_cover_url": "https://example.com/posters/clpe-2026.jpg"
            },
            {
                "nombre": "Conferencia de Educación Cristiana y Pedagogía",
                "edicion": "CECP-2026",
                "anio": 2026,
                "fecha_inicio": date(2026, 9, 12),
                "fecha_fin": date(2026, 9, 14),
                "descripcion_general": "Conferencia sobre metodologías educativas cristianas, pedagogía bíblica y formación integral desde una cosmovisión cristiana.",
                "poster_cover_url": "https://example.com/posters/cecp-2026.jpg"
            },
            {
                "nombre": "Encuentro de Teología Contextual Latinoamericana",
                "edicion": "ETCL-2026",
                "anio": 2026,
                "fecha_inicio": date(2026, 10, 8),
                "fecha_fin": date(2026, 10, 10),
                "descripcion_general": "Encuentro académico sobre el desarrollo de una teología contextualizada para América Latina, considerando aspectos sociales, culturales y económicos.",
                "poster_cover_url": "https://example.com/posters/etcl-2026.jpg"
            },
            {
                "nombre": "Simposio de Apologética Cristiana Contemporánea",
                "edicion": "SACC-2026",
                "anio": 2026,
                "fecha_inicio": date(2026, 11, 15),
                "fecha_fin": date(2026, 11, 17),
                "descripcion_general": "Simposio dedicado a la defensa de la fe cristiana frente a desafíos contemporáneos: secularización, relativismo moral y nuevas religiosidades.",
                "poster_cover_url": "https://example.com/posters/sacc-2026.jpg"
            },
            {
                "nombre": "Congreso de Ministerios Juveniles y Familiares",
                "edicion": "CMJF-2026",
                "anio": 2026,
                "fecha_inicio": date(2026, 12, 3),
                "fecha_fin": date(2026, 12, 5),
                "descripcion_general": "Congreso enfocado en estrategias ministeriales para jóvenes y familias, abordando desafíos generacionales y fortalecimiento de la unidad familiar cristiana.",
                "poster_cover_url": "https://example.com/posters/cmjf-2026.jpg"
            },
            # Congresos para 2027
            {
                "nombre": "Congreso Mundial de Teología Reformada 2027",
                "edicion": "CMTR-2027",
                "anio": 2027,
                "fecha_inicio": date(2027, 2, 18),
                "fecha_fin": date(2027, 2, 21),
                "descripcion_general": "Congreso mundial que reúne a académicos y pastores de tradición reformada para discutir la relevancia de la teología reformada en el siglo XXI.",
                "poster_cover_url": "https://example.com/posters/cmtr-2027.jpg"
            },
            {
                "nombre": "Simposio de Teología Bíblica del Pentateuco",
                "edicion": "STBP-2027",
                "anio": 2027,
                "fecha_inicio": date(2027, 4, 10),
                "fecha_fin": date(2027, 4, 12),
                "descripcion_general": "Simposio especializado en el estudio del Pentateuco, su composición, teología y relevancia para la fe y práctica cristiana contemporánea.",
                "poster_cover_url": "https://example.com/posters/stbp-2027.jpg"
            },
            {
                "nombre": "Conferencia de Eclesiología y Gobierno de la Iglesia",
                "edicion": "CEGI-2027",
                "anio": 2027,
                "fecha_inicio": date(2027, 6, 25),
                "fecha_fin": date(2027, 6, 27),
                "descripcion_general": "Conferencia sobre diferentes modelos de gobierno eclesiástico, disciplina pastoral y organización de la iglesia local según principios bíblicos.",
                "poster_cover_url": "https://example.com/posters/cegi-2027.jpg"
            }
        ]

        created_count = 0
        existing_count = 0

        for congress_data in congresses:
            # Verificar si el congreso ya existe (por edición y año)
            existing = session.exec(
                select(Congress).where(
                    Congress.edicion == congress_data["edicion"],
                    Congress.anio == congress_data["anio"]
                )
            ).first()

            if not existing:
                new_congress = Congress(
                    nombre=congress_data["nombre"],
                    edicion=congress_data["edicion"],
                    anio=congress_data["anio"],
                    fecha_inicio=congress_data["fecha_inicio"],
                    fecha_fin=congress_data["fecha_fin"],
                    descripcion_general=congress_data["descripcion_general"],
                    poster_cover_url=congress_data["poster_cover_url"]
                )
                session.add(new_congress)
                created_count += 1
                print(f"  ✓ Created congress: {congress_data['nombre']}")
            else:
                existing_count += 1
                print(f"  - Congress already exists: {congress_data['nombre']}")

        session.commit()
        print(f"\nCongresses seeded successfully! ✅")
        print(f"   - Created: {created_count} new congresses")
        print(f"   - Skipped: {existing_count} existing congresses")
        print(f"   - Total: {len(congresses)} congresses")

if __name__ == "__main__":
    seed_congresses()