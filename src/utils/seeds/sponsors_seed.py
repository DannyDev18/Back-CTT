from sqlmodel import Session, select
from src.config.db import engine
from src.models.sponsor_model import Sponsor

def seed_sponsors():
    """
    Seed de sponsors para el sistema CTT
    Crea sponsors realistas para congresos teológicos
    """
    with Session(engine) as session:
        print("Seeding sponsors...")

        # Lista de sponsors realistas para congresos teológicos
        sponsors = [
            {
                "nombre": "Editorial Teológica Vida",
                "logo_url": "https://example.com/logos/editorial-vida.png",
                "sitio_web": "https://editorialvida.com",
                "descripcion": "Editorial líder en literatura cristiana y recursos teológicos en español. Publicamos libros de reconocidos autores cristianos y materiales de estudio bíblico."
            },
            {
                "nombre": "Seminario Teológico Bautista Internacional",
                "logo_url": "https://example.com/logos/stbi.png",
                "sitio_web": "https://stbi.edu",
                "descripcion": "Institución educativa superior dedicada a la formación integral de líderes cristianos y ministros del evangelio en América Latina."
            },
            {
                "nombre": "Fundación Cristiana para la Educación",
                "logo_url": "https://example.com/logos/fundacion-cristiana.png",
                "sitio_web": "https://fundacioncristianaeducacion.org",
                "descripcion": "Fundación sin fines de lucro que promueve la educación cristiana y apoya eventos académicos teológicos en la región."
            },
            {
                "nombre": "Editorial Portavoz",
                "logo_url": "https://example.com/logos/portavoz.png",
                "sitio_web": "https://editorialportavoz.com",
                "descripcion": "Casa editorial especializada en teología reformada, comentarios bíblicos y obras de grandes teólogos históricos."
            },
            {
                "nombre": "Librería y Distribuidora Cristiana Emanuel",
                "logo_url": "https://example.com/logos/emanuel.png",
                "sitio_web": "https://libreriacristianaemauel.com",
                "descripcion": "Distribuidora líder de literatura cristiana, materiales educativos y recursos ministeriales en Ecuador y la región andina."
            },
            {
                "nombre": "Universidad Cristiana Latinoamericana",
                "logo_url": "https://example.com/logos/ucl.png",
                "sitio_web": "https://ucl.edu.ec",
                "descripcion": "Universidad cristiana comprometida con la excelencia académica y la formación integral desde una cosmovisión bíblica."
            },
            {
                "nombre": "Ministerios RBC Internacional",
                "logo_url": "https://example.com/logos/rbc.png",
                "sitio_web": "https://rbclatino.org",
                "descripcion": "Red de ministerios dedicada a la enseñanza bíblica profunda y la edificación de la iglesia a través de recursos multimedia."
            },
            {
                "nombre": "Editorial CLIE",
                "logo_url": "https://example.com/logos/clie.png",
                "sitio_web": "https://clie.es",
                "descripcion": "Editorial cristiana con más de 40 años de experiencia, especializada en teología, comentarios bíblicos y literatura devocional."
            },
            {
                "nombre": "Asociación Bíblica Ecuatoriana",
                "logo_url": "https://example.com/logos/abe.png",
                "sitio_web": "https://biblicaecuador.org",
                "descripcion": "Organización dedicada a la promoción del estudio bíblico, traducción de las Escrituras y educación teológica popular."
            },
            {
                "nombre": "Editorial Mundo Hispano",
                "logo_url": "https://example.com/logos/mundo-hispano.png",
                "sitio_web": "https://editorialmundohispano.org",
                "descripción": "Casa editora cristiana con amplia tradición en la publicación de materiales teológicos, educativos y devocionales para la iglesia hispana."
            },
            {
                "nombre": "Instituto Bíblico y Teológico del Ecuador",
                "logo_url": "https://example.com/logos/ibte.png",
                "sitio_web": "https://ibte.edu.ec",
                "descripcion": "Instituto superior especializado en formación bíblica y teológica, ofreciendo programas presenciales y a distancia."
            },
            {
                "nombre": "Confesión de Fe Westminster - Ecuador",
                "logo_url": "https://example.com/logos/westminster-ec.png",
                "sitio_web": "https://westminsterecuador.org",
                "descripcion": "Organización reformada dedicada a la promoción de la sana doctrina y la educación teológica conforme a los estándares de Westminster."
            },
            {
                "nombre": "Sociedad Bíblica del Ecuador",
                "logo_url": "https://example.com/logos/sbe.png",
                "sitio_web": "https://sociedadbiblica.ec",
                "descripcion": "Organización sin fines de lucro dedicada a la traducción, publicación y distribución de las Sagradas Escrituras."
            },
            {
                "nombre": "Red de Pastores Evangélicos del Ecuador",
                "logo_url": "https://example.com/logos/rpee.png",
                "sitio_web": "https://redpastores.ec",
                "descripcion": "Red nacional que reúne a pastores evangélicos para promover la unidad, formación continua y fortalecimiento del liderazgo pastoral."
            },
            {
                "nombre": "Editorial Herder Teológica",
                "logo_url": "https://example.com/logos/herder.png",
                "sitio_web": "https://herder.com",
                "descripcion": "Editorial de prestigio internacional especializada en obras teológicas académicas, patrística y estudios bíblicos especializados."
            },
            {
                "nombre": "Fundación Teológica Ecuménica",
                "logo_url": "https://example.com/logos/fte.png",
                "sitio_web": "https://fundacionecumenica.org",
                "descripcion": "Fundación que promueve el diálogo ecuménico, la investigación teológica y la cooperación entre diferentes tradiciones cristianas."
            },
            {
                "nombre": "Centro de Estudios Pastorales Latinoamericanos",
                "logo_url": "https://example.com/logos/cepal.png",
                "sitio_web": "https://cepal-teologia.org",
                "descripcion": "Centro especializado en investigación pastoral, formación de líderes eclesiásticos y desarrollo de estrategias ministeriales contextuales."
            },
            {
                "nombre": "Editorial Concordia Teológica",
                "logo_url": "https://example.com/logos/concordia.png",
                "sitio_web": "https://concordiateologica.com",
                "descripcion": "Casa editorial luterana especializada en teología sistemática, historia de la Reforma y literatura confesional."
            }
        ]

        created_count = 0
        existing_count = 0

        for sponsor_data in sponsors:
            # Verificar si el sponsor ya existe (por nombre)
            existing = session.exec(
                select(Sponsor).where(Sponsor.nombre == sponsor_data["nombre"])
            ).first()

            if not existing:
                new_sponsor = Sponsor(
                    nombre=sponsor_data["nombre"],
                    logo_url=sponsor_data["logo_url"],
                    sitio_web=sponsor_data["sitio_web"],
                    descripcion=sponsor_data["descripcion"]
                )
                session.add(new_sponsor)
                created_count += 1
                print(f"  ✓ Created sponsor: {sponsor_data['nombre']}")
            else:
                existing_count += 1
                print(f"  - Sponsor already exists: {sponsor_data['nombre']}")

        session.commit()
        print(f"\nSponsors seeded successfully! ✅")
        print(f"   - Created: {created_count} new sponsors")
        print(f"   - Skipped: {existing_count} existing sponsors")
        print(f"   - Total: {len(sponsors)} sponsors")

if __name__ == "__main__":
    seed_sponsors()