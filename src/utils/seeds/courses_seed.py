import json
from datetime import datetime, date, time
from sqlmodel import Session
from src.config.db import engine
from src.models.course import Course, CourseRequirement, CourseContent, CourseContentTopic
from src.controllers.course_controller import CourseController

def seed_courses():
    with Session(engine) as session:
        print("Seeding courses...")

        # Verifica si el curso ya existe para evitar duplicados
        existing_course = session.get(Course, 1)
        if existing_course:
            print("Course already exists, skipping seed.")
            return

        try:
            # Crear el curso principal
            course = Course(
                id=1,
                title="Arduino desde cero: Electrónica, Programación y Automatización",
                description="El curso \"Arduino desde cero: Electrónica, Programación y Automatización\" ofrece una formación integral en el uso de Arduino para el desarrollo de proyectos de electrónica, programación",
                place="LUGAR DE CELEBRACIÓN\nTALLERES TECNOLÓGICOS.\n\nCentro de Transferencia y Desarrollo de Tecnologías CTT-FISEI.\nAvda. Los Chasquis entre Río Payamino y Río Guayllabamba\nCampus Huachi, Ambato-Ecuador.",
                course_image="https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Arduino_Logo.svg/720px-Arduino_Logo.svg.png",
                course_image_detail="https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Arduino_Logo.svg/720px-Arduino_Logo.svg.png",
                category="TICS",
                status="Activo",
                objectives=json.dumps([
                    "Capacitar en el diseño, programación y ejecución de proyectos con Arduino, desde configuraciones básicas (entradas/salidas digitales, estructuras de control) hasta aplicaciones avanzadas (control de motores, comunicación serial/I2C y automatización).",
                    "Desarrollar habilidades prácticas en electrónica y sistemas integrados, incluyendo el manejo de sensores analógicos/digitales, modulación PWM, integración con herramientas como LabVIEW, y optimización de recursos mediante interrupciones y técnicas de bajo consumo.",
                    "Fomentar la creación de soluciones innovadoras y eficientes en automatización, prototipado y adquisición de datos, aplicables en contextos educativos, industriales o de desarrollo tecnológico."
                ]),
                organizers=json.dumps([
                    "Ing. Luis Pomaquero",
                    "Ing. Carlos Luis Vargas Guevara",
                    "Ing. Jesús Israel Guamán Molina"
                ]),
                materials=json.dumps([
                    "Sensores (analógicos y digitales: temperatura, presión, botones, etc.)",
                    "Módulos de comunicación (USB, Bluetooth, WiFi, etc.)",
                    "Módulos de control (PWM, I2C, SPI, etc.)",
                    "Módulos de potencia (motores, relés, etc.)",
                    "Módulos de alimentación (baterías, paneles solares, etc.)",
                    "Módulos de sensores (temperatura, presión, botones, etc.)",
                    "Módulos de comunicación (USB, Bluetooth, WiFi, etc.)",
                    "Internet",
                    "Proyector"
                ]),
                target_audience=json.dumps([
                    "Estudiantes",
                    "Graduados",
                    "Docentes",
                    "Público en general"
                ]),
            )
            session.add(course)
            session.flush()  # Para obtener el ID del curso

            # Crear los requisitos del curso
            requirements = CourseRequirement(
                course_id=course.id,
                start_date_registration=date(2025, 5, 19),
                end_date_registration=date(2025, 6, 4),
                start_date_course=date(2025, 6, 7),
                end_date_course=date(2025, 6, 30),
                days=json.dumps(["Sábado"]),
                start_time="08:00:00",
                end_time="14:00:00",
                location="Laboratorio asignado - FISEI",
                min_quota=15,
                max_quota=25,
                total_hours=40,
                in_person_hours=24,
                autonomous_hours=16,
                modality="Presencial",
                certification="Certificado digital de asistencia y aprobación con validación QR",
                prerequisites=json.dumps(["Ninguno"]),
                prices=json.dumps([
                    {
                        "amount": 40,
                        "category": "Estudiantes UTA (Último periodo)"
                    },
                    {
                        "amount": 50,
                        "category": "Graduados, Docentes y Administrativos UTA"
                    },
                    {
                        "amount": 60,
                        "category": "Público en general"
                    }
                ])
            )
            session.add(requirements)

            # Crear los contenidos del curso
            contents_data = [
                {
                    "unit": "Módulo 1",
                    "title": "Defensa de la Red",
                    "topics": [
                        {"unit": "Capítulo 1", "title": "Comprendiendo la Defensa"},
                        {"unit": "Capítulo 2", "title": "Defensa de Sistemas y Redes"},
                        {"unit": "Capítulo 3", "title": "Control de Acceso"},
                        {"unit": "Capítulo 4", "title": "Listas de Control de Acceso"},
                        {"unit": "Capítulo 5", "title": "Tecnologías de Firewall"}
                    ]
                },
                {
                    "unit": "Módulo 2",
                    "title": "Administración de Amenazas Cibernéticas",
                    "topics": [
                        {"unit": "Capítulo 1", "title": "Gobernanza y Cumplimiento"},
                        {"unit": "Capítulo 2", "title": "Pruebas de seguridad de red"},
                        {"unit": "Capítulo 3", "title": "Inteligencia de amenazas"}
                    ]
                }
            ]

            for content_data in contents_data:
                content = CourseContent(
                    course_id=course.id,
                    unit=content_data["unit"],
                    title=content_data["title"],
                    topics_data=json.dumps(content_data["topics"])
                )
                session.add(content)
                session.flush()  # Para obtener el ID del contenido

                # Crear los topics del contenido
                for topic_data in content_data["topics"]:
                    topic = CourseContentTopic(
                        course_id=course.id,
                        content_id=content.id,
                        unit=topic_data["unit"],
                        title=topic_data["title"]
                    )
                    session.add(topic)

            session.commit()
            print("Course seeded successfully.")

        except Exception as e:
            session.rollback()
            print(f"Error seeding course: {e}")
            raise
