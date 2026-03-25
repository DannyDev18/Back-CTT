from sqlmodel import Session, select
from src.config.db import engine
from src.models.speaker_model import Speaker
from src.models.congress_model import Congress
from datetime import date

def seed_speakers():
    """
    Seed de speakers para el sistema CTT
    Crea speakers teológicos realistas asociados a congresos existentes
    """
    with Session(engine) as session:
        print("Seeding speakers...")

        # Obtener algunos congresos existentes para asociar speakers
        existing_congresses = session.exec(select(Congress)).all()

        if not existing_congresses:
            print("  ❌ No congresses found. Please run congress seed first.")
            return

        # Lista de speakers teológicos realistas
        speakers_data = [
            # Speakers para diferentes congresos
            {
                "nombres_completos": "Dr. Miguel Núñez Fernández",
                "titulo_academico": "Doctor en Teología Sistemática",
                "institucion": "Seminario Teológico Centroamericano",
                "pais": "Guatemala",
                "foto_url": "https://example.com/speakers/miguel-nunez.jpg",
                "tipo_speaker": "keynote"
            },
            {
                "nombres_completos": "Dra. Nancy Pineda de Demarco",
                "titulo_academico": "Doctora en Ministerio Cristiano",
                "institucion": "Seminario Teológico Bautista de Venezuela",
                "pais": "Venezuela",
                "foto_url": "https://example.com/speakers/nancy-pineda.jpg",
                "tipo_speaker": "conferencia"
            },
            {
                "nombres_completos": "Rev. Dr. Sugel Michelén",
                "titulo_academico": "Doctor en Ministerio Pastoral",
                "institucion": "Iglesia Bíblica del Señor Jesucristo",
                "pais": "República Dominicana",
                "foto_url": "https://example.com/speakers/sugel-michelen.jpg",
                "tipo_speaker": "keynote"
            },
            {
                "nombres_completos": "Dr. Paul David Washer",
                "titulo_academico": "Master en Divinidad",
                "institucion": "HeartCry Missionary Society",
                "pais": "Estados Unidos",
                "foto_url": "https://example.com/speakers/paul-washer.jpg",
                "tipo_speaker": "keynote"
            },
            {
                "nombres_completos": "Dra. Carmen Alicia Usuga",
                "titulo_academico": "Doctora en Teología Pastoral",
                "institucion": "Seminario Bíblico de Colombia",
                "pais": "Colombia",
                "foto_url": "https://example.com/speakers/carmen-usuga.jpg",
                "tipo_speaker": "taller"
            },
            {
                "nombres_completos": "Dr. John MacArthur Jr.",
                "titulo_academico": "Doctor en Divinidad",
                "institucion": "The Master's Seminary",
                "pais": "Estados Unidos",
                "foto_url": "https://example.com/speakers/john-macarthur.jpg",
                "tipo_speaker": "keynote"
            },
            {
                "nombres_completos": "Rev. Dr. R.C. Sproul",
                "titulo_academico": "Doctor en Teología",
                "institucion": "Ligonier Ministries",
                "pais": "Estados Unidos",
                "foto_url": "https://example.com/speakers/rc-sproul.jpg",
                "tipo_speaker": "conferencia"
            },
            {
                "nombres_completos": "Dr. Martyn Lloyd-Jones Memorial",
                "titulo_academico": "Doctor en Medicina y Teología",
                "institucion": "Westminster Chapel Historical Society",
                "pais": "Reino Unido",
                "foto_url": "https://example.com/speakers/lloyd-jones.jpg",
                "tipo_speaker": "conferencia"
            },
            {
                "nombres_completos": "Rev. Dr. Arturo Azurdia III",
                "titulo_academico": "Doctor en Ministerio",
                "institucion": "Western Seminary Portland",
                "pais": "Estados Unidos",
                "foto_url": "https://example.com/speakers/arturo-azurdia.jpg",
                "tipo_speaker": "taller"
            },
            {
                "nombres_completos": "Dr. Steven Lawson",
                "titulo_academico": "Doctor en Ministerio",
                "institucion": "OnePassion Ministries",
                "pais": "Estados Unidos",
                "foto_url": "https://example.com/speakers/steven-lawson.jpg",
                "tipo_speaker": "keynote"
            },
            {
                "nombres_completos": "Dra. Rebeca Manley Pippert",
                "titulo_academico": "Master en Estudios Teológicos",
                "institucion": "Salt Shaker Ministries",
                "pais": "Estados Unidos",
                "foto_url": "https://example.com/speakers/rebeca-pippert.jpg",
                "tipo_speaker": "taller"
            },
            {
                "nombres_completos": "Dr. Albert Mohler Jr.",
                "titulo_academico": "Doctor en Filosofía",
                "institucion": "Southern Baptist Theological Seminary",
                "pais": "Estados Unidos",
                "foto_url": "https://example.com/speakers/albert-mohler.jpg",
                "tipo_speaker": "keynote"
            },
            {
                "nombres_completos": "Rev. Dr. Iain Murray",
                "titulo_academico": "Master en Artes",
                "institucion": "Banner of Truth Trust",
                "pais": "Escocia",
                "foto_url": "https://example.com/speakers/iain-murray.jpg",
                "tipo_speaker": "conferencia"
            },
            {
                "nombres_completos": "Dr. Conrad Mbewe",
                "titulo_academico": "Doctor en Ministerio Pastoral",
                "institucion": "African Christian University",
                "pais": "Zambia",
                "foto_url": "https://example.com/speakers/conrad-mbewe.jpg",
                "tipo_speaker": "keynote"
            },
            {
                "nombres_completos": "Dra. Elizabeth Elliot Memorial",
                "titulo_academico": "Bachelor en Literatura Clásica",
                "institucion": "Back to the Bible Ministries",
                "pais": "Estados Unidos",
                "foto_url": "https://example.com/speakers/elizabeth-elliot.jpg",
                "tipo_speaker": "panel"
            },
            {
                "nombres_completos": "Dr. Joni Eareckson Tada",
                "titulo_academico": "Doctor Honoris Causa en Humanidades",
                "institucion": "Joni and Friends International",
                "pais": "Estados Unidos",
                "foto_url": "https://example.com/speakers/joni-eareckson.jpg",
                "tipo_speaker": "panel"
            },
            {
                "nombres_completos": "Rev. Dr. Sinclair Ferguson",
                "titulo_academico": "Doctor en Divinidad",
                "institucion": "Reformed Theological Seminary",
                "pais": "Estados Unidos",
                "foto_url": "https://example.com/speakers/sinclair-ferguson.jpg",
                "tipo_speaker": "keynote"
            },
            {
                "nombres_completos": "Dr. José Luis González",
                "titulo_academico": "Doctor en Historia del Cristianismo",
                "institucion": "Candler School of Theology",
                "pais": "México",
                "foto_url": "https://example.com/speakers/jose-gonzalez.jpg",
                "tipo_speaker": "conferencia"
            },
            {
                "nombres_completos": "Dra. Alejandra Kornblit",
                "titulo_academico": "Doctora en Psicología Pastoral",
                "institucion": "Instituto Bíblico Buenos Aires",
                "pais": "Argentina",
                "foto_url": "https://example.com/speakers/alejandra-kornblit.jpg",
                "tipo_speaker": "taller"
            },
            {
                "nombres_completos": "Rev. Dr. Hernandes Dias Lopes",
                "titulo_academico": "Doctor en Ministerio",
                "institucion": "Igreja Presbiteriana de Vitória",
                "pais": "Brasil",
                "foto_url": "https://example.com/speakers/hernandes-lopes.jpg",
                "tipo_speaker": "keynote"
            }
        ]

        created_count = 0
        existing_count = 0

        # Distribuir speakers entre los congresos existentes
        congress_index = 0

        for speaker_data in speakers_data:
            # Seleccionar congreso (rotar entre los disponibles)
            current_congress = existing_congresses[congress_index % len(existing_congresses)]

            # Verificar si el speaker ya existe en este congreso
            existing = session.exec(
                select(Speaker).where(
                    Speaker.nombres_completos == speaker_data["nombres_completos"],
                    Speaker.id_congreso == current_congress.id_congreso
                )
            ).first()

            if not existing:
                new_speaker = Speaker(
                    id_congreso=current_congress.id_congreso,
                    nombres_completos=speaker_data["nombres_completos"],
                    titulo_academico=speaker_data["titulo_academico"],
                    institucion=speaker_data["institucion"],
                    pais=speaker_data["pais"],
                    foto_url=speaker_data["foto_url"],
                    tipo_speaker=speaker_data["tipo_speaker"]
                )
                session.add(new_speaker)
                created_count += 1
                print(f"  ✓ Created speaker: {speaker_data['nombres_completos']} for {current_congress.nombre}")
            else:
                existing_count += 1
                print(f"  - Speaker already exists: {speaker_data['nombres_completos']}")

            congress_index += 1

        session.commit()
        print(f"\nSpeakers seeded successfully! ✅")
        print(f"   - Created: {created_count} new speakers")
        print(f"   - Skipped: {existing_count} existing speakers")
        print(f"   - Total: {len(speakers_data)} speakers")
        print(f"   - Distributed across: {len(existing_congresses)} congresses")

if __name__ == "__main__":
    seed_speakers()