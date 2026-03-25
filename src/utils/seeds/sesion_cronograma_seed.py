from sqlmodel import Session, select
from src.config.db import engine
from src.models.sesion_cronograma_model import SesionCronograma
from src.models.speaker_model import Speaker
from src.models.congress_model import Congress
from datetime import date, time
from typing import List, Dict

def seed_sesion_cronograma():
    """
    Seed de sesiones del cronograma para el sistema CTT
    Crea cronogramas realistas para congresos con speakers
    """
    with Session(engine) as session:
        print("Seeding sesion cronograma...")

        # Obtener congresos y sus speakers
        congresses_query = select(Congress)
        congresses = session.exec(congresses_query).all()

        if not congresses:
            print("  ❌ No congresses found. Please run congress and speakers seeds first.")
            return

        created_count = 0
        existing_count = 0

        # Templates de sesiones típicas para congresos teológicos
        session_templates = [
            {
                "titulo_sesion": "Conferencia Magistral de Apertura",
                "jornada": "mañana",
                "lugar": "Auditorio Principal",
                "hora_inicio": time(9, 0),
                "hora_fin": time(10, 30),
                "tipo_preferido": "keynote"
            },
            {
                "titulo_sesion": "Teología Sistemática: Fundamentos Bíblicos",
                "jornada": "mañana",
                "lugar": "Aula Magna",
                "hora_inicio": time(11, 0),
                "hora_fin": time(12, 30),
                "tipo_preferido": "conferencia"
            },
            {
                "titulo_sesion": "Taller de Hermenéutica Bíblica",
                "jornada": "tarde",
                "lugar": "Salón de Seminarios A",
                "hora_inicio": time(14, 0),
                "hora_fin": time(15, 30),
                "tipo_preferido": "taller"
            },
            {
                "titulo_sesion": "Historia de la Iglesia Primitiva",
                "jornada": "tarde",
                "lugar": "Aula de Conferencias",
                "hora_inicio": time(16, 0),
                "hora_fin": time(17, 30),
                "tipo_preferido": "conferencia"
            },
            {
                "titulo_sesion": "Panel: Desafíos Pastorales Contemporáneos",
                "jornada": "noche",
                "lugar": "Salón de Eventos",
                "hora_inicio": time(19, 0),
                "hora_fin": time(20, 30),
                "tipo_preferido": "panel"
            },
            # Día 2
            {
                "titulo_sesion": "Conferencia Magistral: Teología y Cultura",
                "jornada": "mañana",
                "lugar": "Auditorio Principal",
                "hora_inicio": time(9, 0),
                "hora_fin": time(10, 30),
                "tipo_preferido": "keynote"
            },
            {
                "titulo_sesion": "Exégesis del Nuevo Testamento",
                "jornada": "mañana",
                "lugar": "Aula Bíblica",
                "hora_inicio": time(11, 0),
                "hora_fin": time(12, 30),
                "tipo_preferido": "conferencia"
            },
            {
                "titulo_sesion": "Taller de Consejería Pastoral",
                "jornada": "tarde",
                "lugar": "Salón de Seminarios B",
                "hora_inicio": time(14, 0),
                "hora_fin": time(15, 30),
                "tipo_preferido": "taller"
            },
            {
                "titulo_sesion": "Ética Cristiana en el Siglo XXI",
                "jornada": "tarde",
                "lugar": "Aula de Ética",
                "hora_inicio": time(16, 0),
                "hora_fin": time(17, 30),
                "tipo_preferido": "conferencia"
            },
            # Día 3
            {
                "titulo_sesion": "Mesa Redonda: Educación Teológica",
                "jornada": "mañana",
                "lugar": "Centro de Convenciones",
                "hora_inicio": time(9, 0),
                "hora_fin": time(10, 30),
                "tipo_preferido": "panel"
            },
            {
                "titulo_sesion": "Ministerio Juvenil y Familia",
                "jornada": "mañana",
                "lugar": "Aula de Ministerios",
                "hora_inicio": time(11, 0),
                "hora_fin": time(12, 30),
                "tipo_preferido": "taller"
            },
            {
                "titulo_sesion": "Conferencia de Clausura: El Futuro de la Iglesia",
                "jornada": "tarde",
                "lugar": "Auditorio Principal",
                "hora_inicio": time(16, 0),
                "hora_fin": time(17, 30),
                "tipo_preferido": "keynote"
            }
        ]

        for congress in congresses:
            print(f"\n  Creating schedule for: {congress.nombre}")

            # Obtener speakers de este congreso
            speakers_query = select(Speaker).where(Speaker.id_congreso == congress.id_congreso)
            congress_speakers = session.exec(speakers_query).all()

            if not congress_speakers:
                print(f"    ❌ No speakers found for congress: {congress.nombre}")
                continue

            # Organizar speakers por tipo
            speakers_by_type = {}
            for speaker in congress_speakers:
                speaker_type = speaker.tipo_speaker
                if speaker_type not in speakers_by_type:
                    speakers_by_type[speaker_type] = []
                speakers_by_type[speaker_type].append(speaker)

            # Crear fechas del congreso (distribuir en los días del evento)
            congress_days = []
            current_date = congress.fecha_inicio
            while current_date <= congress.fecha_fin:
                congress_days.append(current_date)
                # Avanzar al siguiente día
                from datetime import timedelta
                current_date += timedelta(days=1)

            # Crear sesiones
            day_index = 0
            session_template_index = 0

            for template in session_templates:
                # Verificar si tenemos speakers del tipo preferido
                preferred_type = template["tipo_preferido"]
                available_speakers = speakers_by_type.get(preferred_type, [])

                # Si no hay del tipo preferido, usar cualquier speaker disponible
                if not available_speakers:
                    all_speakers = [s for speakers_list in speakers_by_type.values() for s in speakers_list]
                    if all_speakers:
                        available_speakers = [all_speakers[session_template_index % len(all_speakers)]]

                if not available_speakers:
                    print(f"    ❌ No speakers available for session: {template['titulo_sesion']}")
                    continue

                # Seleccionar speaker
                selected_speaker = available_speakers[session_template_index % len(available_speakers)]

                # Seleccionar fecha (distribuir entre los días del congreso)
                session_date = congress_days[day_index % len(congress_days)]

                # Verificar si la sesión ya existe
                existing_session = session.exec(
                    select(SesionCronograma).where(
                        SesionCronograma.id_congreso == congress.id_congreso,
                        SesionCronograma.id_speaker == selected_speaker.id_speaker,
                        SesionCronograma.fecha == session_date,
                        SesionCronograma.hora_inicio == template["hora_inicio"]
                    )
                ).first()

                if not existing_session:
                    new_session = SesionCronograma(
                        id_congreso=congress.id_congreso,
                        id_speaker=selected_speaker.id_speaker,
                        fecha=session_date,
                        hora_inicio=template["hora_inicio"],
                        hora_fin=template["hora_fin"],
                        titulo_sesion=template["titulo_sesion"],
                        jornada=template["jornada"],
                        lugar=template["lugar"]
                    )
                    session.add(new_session)
                    created_count += 1
                    print(f"    ✓ Created session: {template['titulo_sesion']} - {selected_speaker.nombres_completos}")
                else:
                    existing_count += 1
                    print(f"    - Session already exists: {template['titulo_sesion']}")

                session_template_index += 1

                # Cambiar de día cada 3-4 sesiones para simular múltiples días
                if session_template_index % 4 == 0:
                    day_index += 1

        session.commit()
        print(f"\nSesion Cronograma seeded successfully! ✅")
        print(f"   - Created: {created_count} new sessions")
        print(f"   - Skipped: {existing_count} existing sessions")
        print(f"   - Total templates used: {len(session_templates)}")
        print(f"   - Processed congresses: {len(congresses)}")

if __name__ == "__main__":
    seed_sesion_cronograma()