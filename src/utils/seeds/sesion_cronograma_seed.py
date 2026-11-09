from sqlmodel import Session, select
from src.config.db import engine
from src.models.sesion_cronograma_model import SesionCronograma
from src.models.speaker_model import Speaker
from src.models.congress_model import Congress
from datetime import date, time

def seed_sesion_cronograma():
    """
    Seed de cronograma académico para el Congreso CSEI de la FISEI UTA.
    """
    with Session(engine) as session:
        print("Seeding academic agenda for FISEI congresses...")

        csei_congress = session.exec(select(Congress).where(Congress.anio == 2026)).first()
        if not csei_congress:
            print("  ❌ No CSEI congress found.")
            return

        speakers = session.exec(select(Speaker).where(Speaker.id_congreso == csei_congress.id_congreso)).all()
        speaker_id = speakers[0].id_speaker if speakers else None

        sessions = [
            {
                "id_congreso": csei_congress.id_congreso,
                "id_speaker": speaker_id,
                "fecha": date(2026, 10, 21),
                "hora_inicio": time(9, 0),
                "hora_fin": time(10, 30),
                "titulo_sesion": "Conferencia Magistral: Modelos Fundacionales y Edge Computing en la Industria",
                "jornada": "mañana",
                "lugar": "Auditorio Central FISEI - Campus Huachi"
            },
            {
                "id_congreso": csei_congress.id_congreso,
                "id_speaker": speaker_id,
                "fecha": date(2026, 10, 21),
                "hora_inicio": time(11, 0),
                "hora_fin": time(12, 30),
                "titulo_sesion": "Track Científico: Ciberseguridad Ofensiva y Detección de Amenazas en Redes de Potencia",
                "jornada": "mañana",
                "lugar": "Sala de Grados 1 - FISEI"
            },
            {
                "id_congreso": csei_congress.id_congreso,
                "id_speaker": speaker_id,
                "fecha": date(2026, 10, 22),
                "hora_inicio": time(14, 30),
                "hora_fin": time(16, 0),
                "titulo_sesion": "Taller Especializado: Implementación de Controladores Lógicos Programables en Gemelos Digitales",
                "jornada": "tarde",
                "lugar": "Laboratorio de Automatización y Control"
            }
        ]

        created = 0
        for s_data in sessions:
            existing = session.exec(
                select(SesionCronograma).where(
                    SesionCronograma.id_congreso == s_data["id_congreso"],
                    SesionCronograma.titulo_sesion == s_data["titulo_sesion"]
                )
            ).first()
            if not existing:
                session_obj = SesionCronograma(**s_data)
                session.add(session_obj)
                created += 1

        session.commit()
        print(f"Agenda seeded: {created} new engineering sessions ✅")

if __name__ == "__main__":
    seed_sesion_cronograma()
