from sqlmodel import Session, select
from src.config.db import engine
from src.models.congress_category import CongressCategory, CongressCategoryStatus


def seed_congress_categories():
    """Seed para crear 25 categorías de congresos de ejemplo"""
    with Session(engine) as session:
        # Lista de 25 categorías de congresos
        congress_categories = [
            {
                "name": "Inteligencia Artificial",
                "description": "Congresos sobre IA, Machine Learning y Deep Learning",
                "svgurl": "https://example.com/icons/ai.svg"
            },
            {
                "name": "Ciberseguridad",
                "description": "Eventos sobre seguridad informática y protección de datos",
                "svgurl": "https://example.com/icons/security.svg"
            },
            {
                "name": "Desarrollo de Software",
                "description": "Congresos de ingeniería de software y metodologías ágiles",
                "svgurl": "https://example.com/icons/software.svg"
            },
            {
                "name": "Ciencia de Datos",
                "description": "Eventos sobre Big Data, Analytics y Data Science",
                "svgurl": "https://example.com/icons/data-science.svg"
            },
            {
                "name": "Internet de las Cosas (IoT)",
                "description": "Congresos sobre dispositivos conectados y sistemas embebidos",
                "svgurl": "https://example.com/icons/iot.svg"
            },
            {
                "name": "Cloud Computing",
                "description": "Eventos sobre computación en la nube y arquitecturas distribuidas",
                "svgurl": "https://example.com/icons/cloud.svg"
            },
            {
                "name": "Blockchain y Criptomonedas",
                "description": "Congresos sobre tecnología blockchain y activos digitales",
                "svgurl": "https://example.com/icons/blockchain.svg"
            },
            {
                "name": "Realidad Virtual y Aumentada",
                "description": "Eventos sobre VR, AR y tecnologías inmersivas",
                "svgurl": "https://example.com/icons/vr.svg"
            },
            {
                "name": "Robótica e Automatización",
                "description": "Congresos sobre robótica, automatización industrial y sistemas autónomos",
                "svgurl": "https://example.com/icons/robotics.svg"
            },
            {
                "name": "Energías Renovables",
                "description": "Eventos sobre energía solar, eólica y sostenibilidad energética",
                "svgurl": "https://example.com/icons/renewable.svg"
            },
            {
                "name": "Biotecnología",
                "description": "Congresos sobre biotecnología, genética y biología molecular",
                "svgurl": "https://example.com/icons/biotech.svg"
            },
            {
                "name": "Medicina y Salud Digital",
                "description": "Eventos sobre telemedicina, e-health y tecnologías médicas",
                "svgurl": "https://example.com/icons/health.svg"
            },
            {
                "name": "Educación y Tecnología",
                "description": "Congresos sobre e-learning, edtech y nuevas metodologías educativas",
                "svgurl": "https://example.com/icons/education.svg"
            },
            {
                "name": "Emprendimiento e Innovación",
                "description": "Eventos sobre startups, innovación y ecosistemas empresariales",
                "svgurl": "https://example.com/icons/innovation.svg"
            },
            {
                "name": "Marketing Digital",
                "description": "Congresos sobre marketing digital, redes sociales y publicidad online",
                "svgurl": "https://example.com/icons/marketing.svg"
            },
            {
                "name": "Arquitectura y Diseño",
                "description": "Eventos sobre arquitectura sostenible, urbanismo y diseño",
                "svgurl": "https://example.com/icons/architecture.svg"
            },
            {
                "name": "Medio Ambiente y Cambio Climático",
                "description": "Congresos sobre sostenibilidad ambiental y cambio climático",
                "svgurl": "https://example.com/icons/environment.svg"
            },
            {
                "name": "Agricultura y Agroindustria",
                "description": "Eventos sobre agricultura de precisión, agroindustria y tecnología agrícola",
                "svgurl": "https://example.com/icons/agriculture.svg"
            },
            {
                "name": "Derechos Humanos",
                "description": "Congresos sobre derechos humanos, justicia social e inclusión",
                "svgurl": "https://example.com/icons/human-rights.svg"
            },
            {
                "name": "Ingeniería Civil",
                "description": "Eventos sobre ingeniería civil, construcción e infraestructura",
                "svgurl": "https://example.com/icons/civil-engineering.svg"
            },
            {
                "name": "Física y Astronomía",
                "description": "Congresos sobre física, astrofísica y ciencias del espacio",
                "svgurl": "https://example.com/icons/physics.svg"
            },
            {
                "name": "Química y Ciencias de Materiales",
                "description": "Eventos sobre química, nanotecnología y nuevos materiales",
                "svgurl": "https://example.com/icons/chemistry.svg"
            },
            {
                "name": "Psicología y Neurociencias",
                "description": "Congresos sobre psicología, neurociencia y salud mental",
                "svgurl": "https://example.com/icons/psychology.svg"
            },
            {
                "name": "Economía y Finanzas",
                "description": "Eventos sobre economía, finanzas y mercados financieros",
                "svgurl": "https://example.com/icons/finance.svg"
            },
            {
                "name": "Turismo y Hospitalidad",
                "description": "Congresos sobre turismo sostenible, hotelería y gestión turística",
                "svgurl": "https://example.com/icons/tourism.svg"
            }
        ]

        created_count = 0
        existing_count = 0

        for cat in congress_categories:
            # Verificar si ya existe
            existing = session.exec(
                select(CongressCategory).where(CongressCategory.name == cat["name"])
            ).first()

            if not existing:
                new_cat = CongressCategory(
                    name=cat["name"],
                    description=cat["description"],
                    svgurl=cat.get("svgurl", ""),
                    status=CongressCategoryStatus.ACTIVO,
                    created_by=1  # Usuario admin por defecto
                )
                session.add(new_cat)
                created_count += 1
            else:
                existing_count += 1

        session.commit()
        print(f"Congress Categories seeded successfully!")
        print(f"   - Created: {created_count} new categories")
        print(f"   - Skipped: {existing_count} existing categories")
        print(f"   - Total: {len(congress_categories)} categories")
