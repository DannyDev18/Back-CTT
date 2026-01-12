from datetime import date, time
from unicodedata import category
from sqlmodel import Session
from src.config.db import engine
from src.models.course import (
    CourseCreate,
    CourseRequirementCreate,
    CourseContentCreate,
    CourseContentTopicRead,
    CourseStatus
)
from src.controllers.course_controller import CourseController

def seed_courses():
    with Session(engine) as session:
        print("Seeding courses...")

        # Verifica si el curso ya existe para evitar duplicados
        from sqlmodel import select
        from src.models.course import Course
        
        existing_course = session.exec(select(Course).where(Course.id == 1)).first()
        if existing_course:
            print("Course already exists, skipping seed.")
            return
        from src.models.category import Category
        category = session.exec(select(Category).where(Category.name == "TICS")).first()
        if not category:
            raise ValueError("La categoría 'TICS' no existe. Debes ejecutar seed_categories primero.")
        try:
            # Preparar datos del curso
            course_data = CourseCreate(
                title="Arduino desde cero: Electrónica, Programación y Automatización",
                description="El curso \"Arduino desde cero: Electrónica, Programación y Automatización\" ofrece una formación integral en el uso de Arduino para el desarrollo de proyectos de electrónica, programación",
                place="LUGAR DE CELEBRACIÓN\nTALLERES TECNOLÓGICOS.\n\nCentro de Transferencia y Desarrollo de Tecnologías CTT-FISEI.\nAvda. Los Chasquis entre Río Payamino y Río Guayllabamba\nCampus Huachi, Ambato-Ecuador.",
                course_image="https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Arduino_Logo.svg/720px-Arduino_Logo.svg.png",
                course_image_detail="https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Arduino_Logo.svg/720px-Arduino_Logo.svg.png",
                category_id=category.id,
                status=CourseStatus.ACTIVO,
                objectives=[
                    "Capacitar en el diseño, programación y ejecución de proyectos con Arduino, desde configuraciones básicas (entradas/salidas digitales, estructuras de control) hasta aplicaciones avanzadas (control de motores, comunicación serial/I2C y automatización).",
                    "Desarrollar habilidades prácticas en electrónica y sistemas integrados, incluyendo el manejo de sensores analógicos/digitales, modulación PWM, integración con herramientas como LabVIEW, y optimización de recursos mediante interrupciones y técnicas de bajo consumo.",
                    "Fomentar la creación de soluciones innovadoras y eficientes en automatización, prototipado y adquisición de datos, aplicables en contextos educativos, industriales o de desarrollo tecnológico."
                ],
                organizers=[
                    "Ing. Luis Pomaquero",
                    "Ing. Carlos Luis Vargas Guevara",
                    "Ing. Jesús Israel Guamán Molina"
                ],
                materials=[
                    "Sensores (analógicos y digitales: temperatura, presión, botones, etc.)",
                    "Módulos de comunicación (USB, Bluetooth, WiFi, etc.)",
                    "Módulos de control (PWM, I2C, SPI, etc.)",
                    "Módulos de potencia (motores, relés, etc.)",
                    "Módulos de alimentación (baterías, paneles solares, etc.)",
                    "Módulos de sensores (temperatura, presión, botones, etc.)",
                    "Módulos de comunicación (USB, Bluetooth, WiFi, etc.)",
                    "Internet",
                    "Proyector"
                ],
                target_audience=[
                    "Estudiantes",
                    "Graduados",
                    "Docentes",
                    "Público en general"
                ]
            )

            # Preparar requisitos del curso
            requirements_data = CourseRequirementCreate(
                start_date_registration=date(2025, 5, 19),
                end_date_registration=date(2025, 6, 4),
                start_date_course=date(2025, 6, 7),
                end_date_course=date(2025, 6, 30),
                days=["Sábado"],
                start_time=time(8, 0, 0),
                end_time=time(14, 0, 0),
                location="Laboratorio asignado - FISEI",
                min_quota=15,
                max_quota=25,
                in_person_hours=24,
                autonomous_hours=16,
                modality="Presencial",
                certification="Certificado digital de asistencia y aprobación con validación QR",
                prerequisites=["Ninguno"],
                prices=[
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
                ]
            )

            # Preparar contenidos del curso
            contents_data = [
                CourseContentCreate(
                    unit="Módulo 1",
                    title="Defensa de la Red",
                    topics=[
                        CourseContentTopicRead(unit="Capítulo 1", title="Comprendiendo la Defensa"),
                        CourseContentTopicRead(unit="Capítulo 2", title="Defensa de Sistemas y Redes"),
                        CourseContentTopicRead(unit="Capítulo 3", title="Control de Acceso"),
                        CourseContentTopicRead(unit="Capítulo 4", title="Listas de Control de Acceso"),
                        CourseContentTopicRead(unit="Capítulo 5", title="Tecnologías de Firewall")
                    ]
                ),
                CourseContentCreate(
                    unit="Módulo 2",
                    title="Administración de Amenazas Cibernéticas",
                    topics=[
                        CourseContentTopicRead(unit="Capítulo 1", title="Gobernanza y Cumplimiento"),
                        CourseContentTopicRead(unit="Capítulo 2", title="Pruebas de seguridad de red"),
                        CourseContentTopicRead(unit="Capítulo 3", title="Inteligencia de amenazas")
                    ]
                )
            ]

            # Crear el curso usando el controlador
            result = CourseController.create_course_with_requirements(
                course_data,
                requirements_data,
                contents_data,
                session
            )

            print(f"Course seeded successfully with ID: {result.get('id')}")

        except Exception as e:
            session.rollback()
            print(f"Error seeding course: {e}")
            raise


if __name__ == "__main__":
    seed_courses()