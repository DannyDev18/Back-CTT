from sqlmodel import Session, select
from src.config.db import engine
from src.models.speaker_model import Speaker
from src.models.congress_model import Congress

def seed_speakers():
    """
    Seed de speakers oficiales de ingeniería para congresos de la FISEI UTA.
    Registra académicos e investigadores en Inteligencia Artificial, Ciberseguridad,
    Sistemas Embebidos y Automatización Industrial.
    """
    with Session(engine) as session:
        print("Seeding official FISEI engineering speakers...")

        existing_congresses = session.exec(select(Congress)).all()
        if not existing_congresses:
            print("  ❌ No congresses found.")
            return

        csei_congress = session.exec(select(Congress).where(Congress.anio == 2026)).first()
        if not csei_congress:
            csei_congress = existing_congresses[0]

        speakers_data = [
            {
                "nombres_completos": "Dr. Carlos Rodríguez Paredes",
                "titulo_academico": "PhD en Inteligencia Artificial y Robótica",
                "institucion": "Universidad Politécnica de Madrid / FISEI UTA",
                "pais": "España / Ecuador",
                "foto_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=500&auto=format&fit=crop&q=80",
                "tipo_speaker": "keynote",
                "id_congreso": csei_congress.id_congreso
            },
            {
                "nombres_completos": "Dra. Elena Villacís Mora",
                "titulo_academico": "PhD en Ciberseguridad y Redes de Alta Velocidad",
                "institucion": "Georgia Institute of Technology",
                "pais": "Estados Unidos",
                "foto_url": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=500&auto=format&fit=crop&q=80",
                "tipo_speaker": "keynote",
                "id_congreso": csei_congress.id_congreso
            },
            {
                "nombres_completos": "Ing. Roberto Silva Benítez, MSc",
                "titulo_academico": "Master en Automatización e Industria 4.0",
                "institucion": "Siemens Digital Industries",
                "pais": "Alemania",
                "foto_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=500&auto=format&fit=crop&q=80",
                "tipo_speaker": "conferencia",
                "id_congreso": csei_congress.id_congreso
            },
            {
                "nombres_completos": "Dra. Mónica Salazar Ortiz",
                "titulo_academico": "PhD en Ciencia de Datos y Machine Learning",
                "institucion": "Universidad Técnica de Ambato (FISEI)",
                "pais": "Ecuador",
                "foto_url": "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=500&auto=format&fit=crop&q=80",
                "tipo_speaker": "conferencia",
                "id_congreso": csei_congress.id_congreso
            }
        ]

        created = 0
        for sp in speakers_data:
            existing = session.exec(
                select(Speaker).where(Speaker.nombres_completos == sp["nombres_completos"])
            ).first()
            if not existing:
                speaker_obj = Speaker(**sp)
                session.add(speaker_obj)
                created += 1

        session.commit()
        print(f"Speakers seeded: {created} new engineering speakers ✅")

if __name__ == "__main__":
    seed_speakers()
