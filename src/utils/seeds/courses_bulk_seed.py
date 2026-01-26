from datetime import date, time
from sqlmodel import Session, select
from src.config.db import engine
from src.models.course import (
    CourseCreate,
    CourseRequirementCreate,
    CourseContentCreate,
    CourseContentTopicRead,
    CourseStatus,
    Course
)
from src.models.category import Category
from src.controllers.course_controller import CourseController


def get_courses_data(category_id: int):
    """Retorna una lista con datos de más de 20 cursos variados"""
    return [
        {
            "course": CourseCreate(
                title="Python para Ciencia de Datos y Machine Learning",
                description="Aprende a utilizar Python para análisis de datos, visualización y construcción de modelos de machine learning desde cero.",
                place="LABORATORIO DE COMPUTACIÓN.\n\nCentro de Transferencia y Desarrollo de Tecnologías CTT-FISEI.\nCampus Huachi, Ambato-Ecuador.",
                course_image="https://example.com/python-ml.png",
                course_image_detail="https://example.com/python-ml-detail.png",
                category_id=category_id,
                status=CourseStatus.ACTIVO,
                objectives=[
                    "Dominar Python para análisis de datos con Pandas y NumPy",
                    "Crear visualizaciones efectivas con Matplotlib y Seaborn",
                    "Implementar modelos de Machine Learning con scikit-learn"
                ],
                organizers=["Dr. María González", "Ing. Roberto Silva"],
                materials=["Computadora", "Software Python", "Jupyter Notebook", "Internet"],
                target_audience=["Estudiantes", "Profesionales", "Investigadores"]
            ),
            "requirements": CourseRequirementCreate(
                start_date_registration=date(2026, 2, 1),
                end_date_registration=date(2026, 2, 28),
                start_date_course=date(2026, 3, 1),
                end_date_course=date(2026, 4, 15),
                days=["Lunes", "Miércoles"],
                start_time=time(18, 0, 0),
                end_time=time(21, 0, 0),
                location="Laboratorio 101 - FISEI",
                min_quota=15,
                max_quota=30,
                in_person_hours=36,
                autonomous_hours=24,
                modality="Presencial",
                certification="Certificado digital de asistencia y aprobación",
                prerequisites=["Programación básica"],
                prices=[
                    {"amount": 60, "category": "Estudiantes UTA"},
                    {"amount": 80, "category": "Graduados y Docentes UTA"},
                    {"amount": 100, "category": "Público en general"}
                ]
            ),
            "contents": [
                CourseContentCreate(
                    unit="Módulo 1",
                    title="Fundamentos de Python",
                    topics=[
                        CourseContentTopicRead(unit="1.1", title="Sintaxis básica"),
                        CourseContentTopicRead(unit="1.2", title="Estructuras de datos"),
                        CourseContentTopicRead(unit="1.3", title="Funciones y módulos")
                    ]
                ),
                CourseContentCreate(
                    unit="Módulo 2",
                    title="Machine Learning",
                    topics=[
                        CourseContentTopicRead(unit="2.1", title="Algoritmos supervisados"),
                        CourseContentTopicRead(unit="2.2", title="Algoritmos no supervisados")
                    ]
                )
            ]
        },
    
        {
            "course": CourseCreate(
                title="Desarrollo Web Full Stack con React y Node.js",
                description="Conviértete en desarrollador full stack dominando React para el frontend y Node.js para el backend.",
                place="LABORATORIO DE DESARROLLO.\n\nCentro de Transferencia y Desarrollo de Tecnologías CTT-FISEI.",
                course_image="https://example.com/fullstack.png",
                course_image_detail="https://example.com/fullstack-detail.png",
                category_id=category_id,
                status=CourseStatus.ACTIVO,
                objectives=[
                    "Desarrollar aplicaciones web modernas con React",
                    "Crear APIs RESTful con Node.js y Express",
                    "Implementar bases de datos con MongoDB"
                ],
                organizers=["Ing. Carlos Mendoza", "Ing. Ana Pérez"],
                materials=["Computadora", "Editor de código", "Node.js", "Internet"],
                target_audience=["Estudiantes", "Desarrolladores junior", "Emprendedores"]
            ),
            "requirements": CourseRequirementCreate(
                start_date_registration=date(2026, 2, 10),
                end_date_registration=date(2026, 3, 10),
                start_date_course=date(2026, 3, 15),
                end_date_course=date(2026, 5, 30),
                days=["Martes", "Jueves"],
                start_time=time(19, 0, 0),
                end_time=time(22, 0, 0),
                location="Laboratorio 102 - FISEI",
                min_quota=12,
                max_quota=25,
                in_person_hours=48,
                autonomous_hours=32,
                modality="Híbrido",
                certification="Certificado digital con validación QR",
                prerequisites=["HTML, CSS, JavaScript básico"],
                prices=[
                    {"amount": 70, "category": "Estudiantes UTA"},
                    {"amount": 90, "category": "Graduados y Docentes UTA"},
                    {"amount": 120, "category": "Público en general"}
                ]
            ),
            "contents": [
                CourseContentCreate(
                    unit="Módulo 1",
                    title="React Fundamentals",
                    topics=[
                        CourseContentTopicRead(unit="1.1", title="Componentes y Props"),
                        CourseContentTopicRead(unit="1.2", title="State y Hooks"),
                        CourseContentTopicRead(unit="1.3", title="React Router")
                    ]
                ),
                CourseContentCreate(
                    unit="Módulo 2",
                    title="Backend con Node.js",
                    topics=[
                        CourseContentTopicRead(unit="2.1", title="Express.js"),
                        CourseContentTopicRead(unit="2.2", title="MongoDB y Mongoose")
                    ]
                )
            ]
        },
        {
            "course": CourseCreate(
                title="Ciberseguridad y Ethical Hacking",
                description="Aprende técnicas de hacking ético y ciberseguridad para proteger sistemas y redes.",
                place="LABORATORIO DE SEGURIDAD.\n\nCentro CTT-FISEI, Campus Huachi.",
                course_image="https://example.com/cybersec.png",
                course_image_detail="https://example.com/cybersec-detail.png",
                category_id=category_id,
                status=CourseStatus.ACTIVO,
                objectives=[
                    "Identificar vulnerabilidades en sistemas",
                    "Realizar pruebas de penetración",
                    "Implementar medidas de seguridad efectivas"
                ],
                organizers=["Ing. Diego Mora", "MSc. Laura Castillo"],
                materials=["Computadora", "Kali Linux", "Herramientas de pentesting", "Internet"],
                target_audience=["Estudiantes de TI", "Profesionales de seguridad", "Administradores de sistemas"]
            ),
            "requirements": CourseRequirementCreate(
                start_date_registration=date(2026, 3, 1),
                end_date_registration=date(2026, 3, 25),
                start_date_course=date(2026, 4, 1),
                end_date_course=date(2026, 5, 15),
                days=["Viernes", "Sábado"],
                start_time=time(14, 0, 0),
                end_time=time(18, 0, 0),
                location="Laboratorio de Seguridad - FISEI",
                min_quota=10,
                max_quota=20,
                in_person_hours=40,
                autonomous_hours=30,
                modality="Presencial",
                certification="Certificado de Ethical Hacker",
                prerequisites=["Redes básicas", "Sistemas operativos"],
                prices=[
                    {"amount": 80, "category": "Estudiantes UTA"},
                    {"amount": 100, "category": "Graduados y Docentes UTA"},
                    {"amount": 150, "category": "Público en general"}
                ]
            ),
            "contents": [
                CourseContentCreate(
                    unit="Módulo 1",
                    title="Fundamentos de Seguridad",
                    topics=[
                        CourseContentTopicRead(unit="1.1", title="Tipos de amenazas"),
                        CourseContentTopicRead(unit="1.2", title="Criptografía"),
                        CourseContentTopicRead(unit="1.3", title="Seguridad de redes")
                    ]
                ),
                CourseContentCreate(
                    unit="Módulo 2",
                    title="Pentesting Avanzado",
                    topics=[
                        CourseContentTopicRead(unit="2.1", title="Explotación de vulnerabilidades"),
                        CourseContentTopicRead(unit="2.2", title="Post-explotación")
                    ]
                )
            ]
        },
        {
            "course": CourseCreate(
                title="Diseño UX/UI para Aplicaciones Móviles",
                description="Aprende a diseñar experiencias de usuario excepcionales para aplicaciones móviles.",
                place="AULA MULTIMEDIA.\n\nCentro CTT-FISEI, Campus Huachi, Ambato-Ecuador.",
                course_image="https://example.com/uxui.png",
                course_image_detail="https://example.com/uxui-detail.png",
                category_id=category_id,
                status=CourseStatus.ACTIVO,
                objectives=[
                    "Comprender principios de diseño UX/UI",
                    "Utilizar herramientas de prototipado como Figma",
                    "Realizar investigación de usuarios"
                ],
                organizers=["Dis. Patricia Ruiz", "Ing. Javier Torres"],
                materials=["Computadora", "Figma", "Adobe XD", "Internet"],
                target_audience=["Diseñadores", "Desarrolladores", "Product Managers"]
            ),
            "requirements": CourseRequirementCreate(
                start_date_registration=date(2026, 2, 15),
                end_date_registration=date(2026, 3, 5),
                start_date_course=date(2026, 3, 10),
                end_date_course=date(2026, 4, 20),
                days=["Lunes", "Miércoles", "Viernes"],
                start_time=time(17, 0, 0),
                end_time=time(20, 0, 0),
                location="Aula Multimedia - FISEI",
                min_quota=15,
                max_quota=30,
                in_person_hours=30,
                autonomous_hours=20,
                modality="Híbrido",
                certification="Certificado UX/UI Designer",
                prerequisites=["Ninguno"],
                prices=[
                    {"amount": 50, "category": "Estudiantes UTA"},
                    {"amount": 70, "category": "Graduados y Docentes UTA"},
                    {"amount": 90, "category": "Público en general"}
                ]
            ),
            "contents": [
                CourseContentCreate(
                    unit="Módulo 1",
                    title="Fundamentos de UX",
                    topics=[
                        CourseContentTopicRead(unit="1.1", title="Investigación de usuarios"),
                        CourseContentTopicRead(unit="1.2", title="Wireframing"),
                        CourseContentTopicRead(unit="1.3", title="Arquitectura de información")
                    ]
                ),
                CourseContentCreate(
                    unit="Módulo 2",
                    title="UI Design",
                    topics=[
                        CourseContentTopicRead(unit="2.1", title="Sistemas de diseño"),
                        CourseContentTopicRead(unit="2.2", title="Prototipado")
                    ]
                )
            ]
        },
        {
            "course": CourseCreate(
                title="DevOps: CI/CD con Docker y Kubernetes",
                description="Domina las prácticas DevOps modernas con contenedores y orquestación.",
                place="LABORATORIO CLOUD.\n\nCentro CTT-FISEI.",
                course_image="https://example.com/devops.png",
                course_image_detail="https://example.com/devops-detail.png",
                category_id=category_id,
                status=CourseStatus.ACTIVO,
                objectives=[
                    "Implementar pipelines CI/CD",
                    "Gestionar contenedores con Docker",
                    "Orquestar aplicaciones con Kubernetes"
                ],
                organizers=["Ing. Fernando López", "Ing. Sandra Jiménez"],
                materials=["Computadora", "Docker Desktop", "kubectl", "Internet"],
                target_audience=["DevOps Engineers", "Desarrolladores", "SysAdmins"]
            ),
            "requirements": CourseRequirementCreate(
                start_date_registration=date(2026, 3, 10),
                end_date_registration=date(2026, 4, 5),
                start_date_course=date(2026, 4, 10),
                end_date_course=date(2026, 6, 5),
                days=["Sábado"],
                start_time=time(8, 0, 0),
                end_time=time(13, 0, 0),
                location="Laboratorio Cloud - FISEI",
                min_quota=12,
                max_quota=22,
                in_person_hours=40,
                autonomous_hours=30,
                modality="Presencial",
                certification="Certificado DevOps Professional",
                prerequisites=["Linux básico", "Git"],
                prices=[
                    {"amount": 75, "category": "Estudiantes UTA"},
                    {"amount": 95, "category": "Graduados y Docentes UTA"},
                    {"amount": 130, "category": "Público en general"}
                ]
            ),
            "contents": [
                CourseContentCreate(
                    unit="Módulo 1",
                    title="Docker Fundamentals",
                    topics=[
                        CourseContentTopicRead(unit="1.1", title="Contenedores"),
                        CourseContentTopicRead(unit="1.2", title="Imágenes"),
                        CourseContentTopicRead(unit="1.3", title="Docker Compose")
                    ]
                ),
                CourseContentCreate(
                    unit="Módulo 2",
                    title="Kubernetes",
                    topics=[
                        CourseContentTopicRead(unit="2.1", title="Pods y Deployments"),
                        CourseContentTopicRead(unit="2.2", title="Services y Networking")
                    ]
                )
            ]
        },
        {
            "course": CourseCreate(
                title="Inteligencia Artificial con TensorFlow y PyTorch",
                description="Desarrolla modelos de IA y Deep Learning con las frameworks más populares.",
                place="LABORATORIO IA.\n\nCentro CTT-FISEI, Campus Huachi.",
                course_image="https://example.com/ai.png",
                course_image_detail="https://example.com/ai-detail.png",
                category_id=category_id,
                status=CourseStatus.ACTIVO,
                objectives=[
                    "Construir redes neuronales profundas",
                    "Implementar modelos de visión por computadora",
                    "Desarrollar modelos de procesamiento de lenguaje natural"
                ],
                organizers=["PhD. Alberto Sánchez", "MSc. Cristina Vega"],
                materials=["GPU Computing", "Python", "Jupyter", "Datasets"],
                target_audience=["Investigadores", "Data Scientists", "Estudiantes avanzados"]
            ),
            "requirements": CourseRequirementCreate(
                start_date_registration=date(2026, 4, 1),
                end_date_registration=date(2026, 4, 25),
                start_date_course=date(2026, 5, 1),
                end_date_course=date(2026, 7, 15),
                days=["Martes", "Jueves"],
                start_time=time(18, 30, 0),
                end_time=time(21, 30, 0),
                location="Laboratorio IA - FISEI",
                min_quota=10,
                max_quota=18,
                in_person_hours=48,
                autonomous_hours=40,
                modality="Presencial",
                certification="Certificado AI Specialist",
                prerequisites=["Python avanzado", "Matemáticas", "Machine Learning básico"],
                prices=[
                    {"amount": 90, "category": "Estudiantes UTA"},
                    {"amount": 120, "category": "Graduados y Docentes UTA"},
                    {"amount": 180, "category": "Público en general"}
                ]
            ),
            "contents": [
                CourseContentCreate(
                    unit="Módulo 1",
                    title="Deep Learning Fundamentals",
                    topics=[
                        CourseContentTopicRead(unit="1.1", title="Redes neuronales"),
                        CourseContentTopicRead(unit="1.2", title="Backpropagation"),
                        CourseContentTopicRead(unit="1.3", title="CNNs y RNNs")
                    ]
                ),
                CourseContentCreate(
                    unit="Módulo 2",
                    title="Aplicaciones Avanzadas",
                    topics=[
                        CourseContentTopicRead(unit="2.1", title="Computer Vision"),
                        CourseContentTopicRead(unit="2.2", title="NLP")
                    ]
                )
            ]
        },
        {
            "course": CourseCreate(
                title="Blockchain y Criptomonedas",
                description="Entiende la tecnología blockchain y desarrolla smart contracts.",
                place="AULA TECNOLÓGICA.\n\nCentro CTT-FISEI.",
                course_image="https://example.com/blockchain.png",
                course_image_detail="https://example.com/blockchain-detail.png",
                category_id=category_id,
                status=CourseStatus.ACTIVO,
                objectives=[
                    "Comprender la tecnología blockchain",
                    "Desarrollar smart contracts con Solidity",
                    "Crear aplicaciones descentralizadas (DApps)"
                ],
                organizers=["Ing. Marco Ramírez", "Ing. Sofía Cordero"],
                materials=["Computadora", "MetaMask", "Remix IDE", "Internet"],
                target_audience=["Desarrolladores", "Inversionistas tech", "Emprendedores"]
            ),
            "requirements": CourseRequirementCreate(
                start_date_registration=date(2026, 2, 20),
                end_date_registration=date(2026, 3, 15),
                start_date_course=date(2026, 3, 20),
                end_date_course=date(2026, 5, 10),
                days=["Miércoles", "Viernes"],
                start_time=time(19, 0, 0),
                end_time=time(22, 0, 0),
                location="Aula 201 - FISEI",
                min_quota=15,
                max_quota=25,
                in_person_hours=36,
                autonomous_hours=24,
                modality="Híbrido",
                certification="Certificado Blockchain Developer",
                prerequisites=["Programación básica"],
                prices=[
                    {"amount": 65, "category": "Estudiantes UTA"},
                    {"amount": 85, "category": "Graduados y Docentes UTA"},
                    {"amount": 110, "category": "Público en general"}
                ]
            ),
            "contents": [
                CourseContentCreate(
                    unit="Módulo 1",
                    title="Blockchain Basics",
                    topics=[
                        CourseContentTopicRead(unit="1.1", title="Criptografía"),
                        CourseContentTopicRead(unit="1.2", title="Consenso"),
                        CourseContentTopicRead(unit="1.3", title="Bitcoin y Ethereum")
                    ]
                ),
                CourseContentCreate(
                    unit="Módulo 2",
                    title="Smart Contracts",
                    topics=[
                        CourseContentTopicRead(unit="2.1", title="Solidity"),
                        CourseContentTopicRead(unit="2.2", title="DApps")
                    ]
                )
            ]
        },
        {
            "course": CourseCreate(
                title="IoT: Internet de las Cosas con ESP32",
                description="Desarrolla proyectos IoT conectando sensores y actuadores a la nube.",
                place="LABORATORIO IoT.\n\nCentro CTT-FISEI, Campus Huachi.",
                course_image="https://example.com/iot.png",
                course_image_detail="https://example.com/iot-detail.png",
                category_id=category_id,
                status=CourseStatus.ACTIVO,
                objectives=[
                    "Programar microcontroladores ESP32",
                    "Conectar dispositivos a la nube",
                    "Desarrollar dashboards IoT"
                ],
                organizers=["Ing. Luis Pomaquero", "Ing. Miguel Herrera"],
                materials=["ESP32", "Sensores", "Actuadores", "Plataformas cloud"],
                target_audience=["Estudiantes", "Makers", "Ingenieros"]
            ),
            "requirements": CourseRequirementCreate(
                start_date_registration=date(2026, 3, 5),
                end_date_registration=date(2026, 3, 30),
                start_date_course=date(2026, 4, 5),
                end_date_course=date(2026, 5, 25),
                days=["Sábado", "Domingo"],
                start_time=time(9, 0, 0),
                end_time=time(13, 0, 0),
                location="Laboratorio IoT - FISEI",
                min_quota=12,
                max_quota=20,
                in_person_hours=32,
                autonomous_hours=20,
                modality="Presencial",
                certification="Certificado IoT Developer",
                prerequisites=["Programación básica", "Electrónica básica"],
                prices=[
                    {"amount": 55, "category": "Estudiantes UTA"},
                    {"amount": 75, "category": "Graduados y Docentes UTA"},
                    {"amount": 95, "category": "Público en general"}
                ]
            ),
            "contents": [
                CourseContentCreate(
                    unit="Módulo 1",
                    title="ESP32 Programming",
                    topics=[
                        CourseContentTopicRead(unit="1.1", title="Setup y GPIO"),
                        CourseContentTopicRead(unit="1.2", title="WiFi y Bluetooth"),
                        CourseContentTopicRead(unit="1.3", title="Protocolos de comunicación")
                    ]
                ),
                CourseContentCreate(
                    unit="Módulo 2",
                    title="Cloud Integration",
                    topics=[
                        CourseContentTopicRead(unit="2.1", title="MQTT"),
                        CourseContentTopicRead(unit="2.2", title="AWS IoT Core")
                    ]
                )
            ]
        },
        {
            "course": CourseCreate(
                title="Desarrollo de Videojuegos con Unity",
                description="Crea tus propios videojuegos 2D y 3D con Unity y C#.",
                place="LABORATORIO GAMING.\n\nCentro CTT-FISEI.",
                course_image="https://example.com/unity.png",
                course_image_detail="https://example.com/unity-detail.png",
                category_id=category_id,
                status=CourseStatus.ACTIVO,
                objectives=[
                    "Desarrollar juegos 2D y 3D",
                    "Programar mecánicas de juego",
                    "Optimizar rendimiento de juegos"
                ],
                organizers=["Ing. Gabriel Moreno", "Dis. Andrea Núñez"],
                materials=["Computadora", "Unity Hub", "Visual Studio", "Assets"],
                target_audience=["Estudiantes", "Desarrolladores", "Diseñadores"]
            ),
            "requirements": CourseRequirementCreate(
                start_date_registration=date(2026, 2, 25),
                end_date_registration=date(2026, 3, 20),
                start_date_course=date(2026, 3, 25),
                end_date_course=date(2026, 6, 10),
                days=["Lunes", "Miércoles"],
                start_time=time(18, 0, 0),
                end_time=time(21, 0, 0),
                location="Laboratorio Gaming - FISEI",
                min_quota=15,
                max_quota=25,
                in_person_hours=48,
                autonomous_hours=36,
                modality="Presencial",
                certification="Certificado Unity Developer",
                prerequisites=["C# básico o programación orientada a objetos"],
                prices=[
                    {"amount": 70, "category": "Estudiantes UTA"},
                    {"amount": 90, "category": "Graduados y Docentes UTA"},
                    {"amount": 120, "category": "Público en general"}
                ]
            ),
            "contents": [
                CourseContentCreate(
                    unit="Módulo 1",
                    title="Unity Basics",
                    topics=[
                        CourseContentTopicRead(unit="1.1", title="Interfaz Unity"),
                        CourseContentTopicRead(unit="1.2", title="GameObjects y Components"),
                        CourseContentTopicRead(unit="1.3", title="Scripting C#")
                    ]
                ),
                CourseContentCreate(
                    unit="Módulo 2",
                    title="Game Development",
                    topics=[
                        CourseContentTopicRead(unit="2.1", title="Physics y Collisions"),
                        CourseContentTopicRead(unit="2.2", title="UI y Audio")
                    ]
                )
            ]
        },
        {
            "course": CourseCreate(
                title="Análisis de Big Data con Apache Spark",
                description="Procesa y analiza grandes volúmenes de datos con Apache Spark.",
                place="LABORATORIO BIG DATA.\n\nCentro CTT-FISEI.",
                course_image="https://example.com/spark.png",
                course_image_detail="https://example.com/spark-detail.png",
                category_id=category_id,
                status=CourseStatus.ACTIVO,
                objectives=[
                    "Procesar grandes volúmenes de datos",
                    "Utilizar Spark SQL y DataFrames",
                    "Implementar pipelines de datos"
                ],
                organizers=["Dr. Ricardo Palacios", "Ing. Daniela Ortiz"],
                materials=["Cluster Hadoop", "Spark", "Python/Scala", "Datasets"],
                target_audience=["Data Engineers", "Data Scientists", "Analistas"]
            ),
            "requirements": CourseRequirementCreate(
                start_date_registration=date(2026, 4, 5),
                end_date_registration=date(2026, 4, 28),
                start_date_course=date(2026, 5, 5),
                end_date_course=date(2026, 6, 20),
                days=["Martes", "Jueves"],
                start_time=time(19, 0, 0),
                end_time=time(22, 0, 0),
                location="Laboratorio Big Data - FISEI",
                min_quota=10,
                max_quota=20,
                in_person_hours=36,
                autonomous_hours=28,
                modality="Presencial",
                certification="Certificado Big Data Analyst",
                prerequisites=["Python", "SQL básico"],
                prices=[
                    {"amount": 85, "category": "Estudiantes UTA"},
                    {"amount": 110, "category": "Graduados y Docentes UTA"},
                    {"amount": 150, "category": "Público en general"}
                ]
            ),
            "contents": [
                CourseContentCreate(
                    unit="Módulo 1",
                    title="Spark Fundamentals",
                    topics=[
                        CourseContentTopicRead(unit="1.1", title="RDDs"),
                        CourseContentTopicRead(unit="1.2", title="DataFrames"),
                        CourseContentTopicRead(unit="1.3", title="Spark SQL")
                    ]
                ),
                CourseContentCreate(
                    unit="Módulo 2",
                    title="Advanced Analytics",
                    topics=[
                        CourseContentTopicRead(unit="2.1", title="MLlib"),
                        CourseContentTopicRead(unit="2.2", title="Streaming")
                    ]
                )
            ]
        },
        {
            "course": CourseCreate(
                title="Computación Cuántica: Introducción con Qiskit",
                description="Explora el fascinante mundo de la computación cuántica.",
                place="AULA VIRTUAL.\n\nCentro CTT-FISEI.",
                course_image="https://example.com/quantum.png",
                course_image_detail="https://example.com/quantum-detail.png",
                category_id=category_id,
                status=CourseStatus.ACTIVO,
                objectives=[
                    "Comprender principios de computación cuántica",
                    "Programar circuitos cuánticos con Qiskit",
                    "Explorar algoritmos cuánticos"
                ],
                organizers=["PhD. Elena Vargas", "MSc. Pablo Rojas"],
                materials=["Computadora", "Qiskit", "IBM Quantum Lab", "Internet"],
                target_audience=["Físicos", "Matemáticos", "Computer Scientists"]
            ),
            "requirements": CourseRequirementCreate(
                start_date_registration=date(2026, 5, 1),
                end_date_registration=date(2026, 5, 25),
                start_date_course=date(2026, 6, 1),
                end_date_course=date(2026, 7, 20),
                days=["Viernes"],
                start_time=time(17, 0, 0),
                end_time=time(21, 0, 0),
                location="Online - Zoom",
                min_quota=8,
                max_quota=15,
                in_person_hours=32,
                autonomous_hours=28,
                modality="Virtual",
                certification="Certificado Quantum Computing",
                prerequisites=["Álgebra lineal", "Python básico"],
                prices=[
                    {"amount": 75, "category": "Estudiantes UTA"},
                    {"amount": 100, "category": "Graduados y Docentes UTA"},
                    {"amount": 140, "category": "Público en general"}
                ]
            ),
            "contents": [
                CourseContentCreate(
                    unit="Módulo 1",
                    title="Quantum Basics",
                    topics=[
                        CourseContentTopicRead(unit="1.1", title="Qubits y superposición"),
                        CourseContentTopicRead(unit="1.2", title="Entrelazamiento"),
                        CourseContentTopicRead(unit="1.3", title="Puertas cuánticas")
                    ]
                ),
                CourseContentCreate(
                    unit="Módulo 2",
                    title="Quantum Algorithms",
                    topics=[
                        CourseContentTopicRead(unit="2.1", title="Deutsch-Jozsa"),
                        CourseContentTopicRead(unit="2.2", title="Grover")
                    ]
                )
            ]
        },
        {
            "course": CourseCreate(
                title="Cloud Computing con AWS",
                description="Domina Amazon Web Services y arquitecturas cloud.",
                place="LABORATORIO CLOUD.\n\nCentro CTT-FISEI.",
                course_image="https://example.com/aws.png",
                course_image_detail="https://example.com/aws-detail.png",
                category_id=category_id,
                status=CourseStatus.ACTIVO,
                objectives=[
                    "Diseñar arquitecturas cloud",
                    "Gestionar servicios AWS",
                    "Implementar soluciones serverless"
                ],
                organizers=["Ing. Rodrigo Campos", "Ing. Mónica Salazar"],
                materials=["Cuenta AWS", "Computadora", "Internet", "AWS CLI"],
                target_audience=["Cloud Engineers", "DevOps", "Arquitectos de soluciones"]
            ),
            "requirements": CourseRequirementCreate(
                start_date_registration=date(2026, 3, 15),
                end_date_registration=date(2026, 4, 10),
                start_date_course=date(2026, 4, 15),
                end_date_course=date(2026, 6, 15),
                days=["Sábado"],
                start_time=time(14, 0, 0),
                end_time=time(18, 0, 0),
                location="Laboratorio Cloud - FISEI",
                min_quota=12,
                max_quota=24,
                in_person_hours=40,
                autonomous_hours=32,
                modality="Presencial",
                certification="Certificado AWS Practitioner",
                prerequisites=["Redes básicas", "Linux básico"],
                prices=[
                    {"amount": 80, "category": "Estudiantes UTA"},
                    {"amount": 105, "category": "Graduados y Docentes UTA"},
                    {"amount": 145, "category": "Público en general"}
                ]
            ),
            "contents": [
                CourseContentCreate(
                    unit="Módulo 1",
                    title="AWS Fundamentals",
                    topics=[
                        CourseContentTopicRead(unit="1.1", title="EC2 y S3"),
                        CourseContentTopicRead(unit="1.2", title="VPC y Networking"),
                        CourseContentTopicRead(unit="1.3", title="IAM y Security")
                    ]
                ),
                CourseContentCreate(
                    unit="Módulo 2",
                    title="Advanced Services",
                    topics=[
                        CourseContentTopicRead(unit="2.1", title="Lambda y Serverless"),
                        CourseContentTopicRead(unit="2.2", title="RDS y DynamoDB")
                    ]
                )
            ]
        },
        {
            "course": CourseCreate(
                title="Realidad Virtual y Aumentada",
                description="Desarrolla experiencias inmersivas con VR/AR.",
                place="LABORATORIO VR/AR.\n\nCentro CTT-FISEI.",
                course_image="https://example.com/vr.png",
                course_image_detail="https://example.com/vr-detail.png",
                category_id=category_id,
                status=CourseStatus.ACTIVO,
                objectives=[
                    "Crear aplicaciones de Realidad Virtual",
                    "Desarrollar apps de Realidad Aumentada",
                    "Optimizar experiencias inmersivas"
                ],
                organizers=["Ing. Esteban Delgado", "Dis. Valentina Cruz"],
                materials=["VR Headset", "Unity", "ARCore/ARKit", "Computadora"],
                target_audience=["Desarrolladores", "Diseñadores", "Creativos"]
            ),
            "requirements": CourseRequirementCreate(
                start_date_registration=date(2026, 4, 10),
                end_date_registration=date(2026, 5, 5),
                start_date_course=date(2026, 5, 10),
                end_date_course=date(2026, 7, 10),
                days=["Miércoles", "Viernes"],
                start_time=time(18, 30, 0),
                end_time=time(21, 30, 0),
                location="Laboratorio VR - FISEI",
                min_quota=10,
                max_quota=18,
                in_person_hours=36,
                autonomous_hours=30,
                modality="Presencial",
                certification="Certificado VR/AR Developer",
                prerequisites=["Unity básico", "C#"],
                prices=[
                    {"amount": 90, "category": "Estudiantes UTA"},
                    {"amount": 115, "category": "Graduados y Docentes UTA"},
                    {"amount": 160, "category": "Público en general"}
                ]
            ),
            "contents": [
                CourseContentCreate(
                    unit="Módulo 1",
                    title="Virtual Reality",
                    topics=[
                        CourseContentTopicRead(unit="1.1", title="VR Fundamentals"),
                        CourseContentTopicRead(unit="1.2", title="Interacción VR"),
                        CourseContentTopicRead(unit="1.3", title="Optimización VR")
                    ]
                ),
                CourseContentCreate(
                    unit="Módulo 2",
                    title="Augmented Reality",
                    topics=[
                        CourseContentTopicRead(unit="2.1", title="ARCore/ARKit"),
                        CourseContentTopicRead(unit="2.2", title="Marker-based AR")
                    ]
                )
            ]
        },
        {
            "course": CourseCreate(
                title="Automatización de Testing con Selenium y Cypress",
                description="Automatiza pruebas de software para garantizar calidad.",
                place="LABORATORIO QA.\n\nCentro CTT-FISEI.",
                course_image="https://example.com/testing.png",
                course_image_detail="https://example.com/testing-detail.png",
                category_id=category_id,
                status=CourseStatus.ACTIVO,
                objectives=[
                    "Automatizar pruebas web con Selenium",
                    "Implementar testing con Cypress",
                    "Crear frameworks de testing"
                ],
                organizers=["Ing. Claudia Mendoza", "Ing. Alejandro Suárez"],
                materials=["Computadora", "IDE", "Selenium WebDriver", "Cypress"],
                target_audience=["QA Engineers", "Desarrolladores", "Testers"]
            ),
            "requirements": CourseRequirementCreate(
                start_date_registration=date(2026, 3, 20),
                end_date_registration=date(2026, 4, 15),
                start_date_course=date(2026, 4, 20),
                end_date_course=date(2026, 6, 5),
                days=["Martes", "Jueves"],
                start_time=time(19, 0, 0),
                end_time=time(22, 0, 0),
                location="Laboratorio QA - FISEI",
                min_quota=12,
                max_quota=22,
                in_person_hours=36,
                autonomous_hours=24,
                modality="Híbrido",
                certification="Certificado Test Automation",
                prerequisites=["Programación básica", "Testing manual"],
                prices=[
                    {"amount": 60, "category": "Estudiantes UTA"},
                    {"amount": 80, "category": "Graduados y Docentes UTA"},
                    {"amount": 105, "category": "Público en general"}
                ]
            ),
            "contents": [
                CourseContentCreate(
                    unit="Módulo 1",
                    title="Selenium Automation",
                    topics=[
                        CourseContentTopicRead(unit="1.1", title="WebDriver"),
                        CourseContentTopicRead(unit="1.2", title="Page Object Model"),
                        CourseContentTopicRead(unit="1.3", title="Test Frameworks")
                    ]
                ),
                CourseContentCreate(
                    unit="Módulo 2",
                    title="Cypress Testing",
                    topics=[
                        CourseContentTopicRead(unit="2.1", title="Cypress basics"),
                        CourseContentTopicRead(unit="2.2", title="API Testing")
                    ]
                )
            ]
        },
        {
            "course": CourseCreate(
                title="Desarrollo Mobile con Flutter",
                description="Crea aplicaciones móviles multiplataforma con Flutter.",
                place="LABORATORIO MOBILE.\n\nCentro CTT-FISEI.",
                course_image="https://example.com/flutter.png",
                course_image_detail="https://example.com/flutter-detail.png",
                category_id=category_id,
                status=CourseStatus.ACTIVO,
                objectives=[
                    "Desarrollar apps con Flutter",
                    "Gestionar estado con Provider/Bloc",
                    "Integrar APIs y bases de datos"
                ],
                organizers=["Ing. Natalia Ramos", "Ing. Sebastián Flores"],
                materials=["Computadora", "Android Studio", "Flutter SDK", "Emuladores"],
                target_audience=["Desarrolladores", "Estudiantes", "Freelancers"]
            ),
            "requirements": CourseRequirementCreate(
                start_date_registration=date(2026, 2, 28),
                end_date_registration=date(2026, 3, 25),
                start_date_course=date(2026, 3, 28),
                end_date_course=date(2026, 6, 15),
                days=["Lunes", "Miércoles"],
                start_time=time(18, 0, 0),
                end_time=time(21, 0, 0),
                location="Laboratorio Mobile - FISEI",
                min_quota=15,
                max_quota=28,
                in_person_hours=48,
                autonomous_hours=32,
                modality="Presencial",
                certification="Certificado Flutter Developer",
                prerequisites=["Programación orientada a objetos"],
                prices=[
                    {"amount": 70, "category": "Estudiantes UTA"},
                    {"amount": 90, "category": "Graduados y Docentes UTA"},
                    {"amount": 125, "category": "Público en general"}
                ]
            ),
            "contents": [
                CourseContentCreate(
                    unit="Módulo 1",
                    title="Flutter Basics",
                    topics=[
                        CourseContentTopicRead(unit="1.1", title="Widgets"),
                        CourseContentTopicRead(unit="1.2", title="Layouts"),
                        CourseContentTopicRead(unit="1.3", title="Navigation")
                    ]
                ),
                CourseContentCreate(
                    unit="Módulo 2",
                    title="Advanced Flutter",
                    topics=[
                        CourseContentTopicRead(unit="2.1", title="State Management"),
                        CourseContentTopicRead(unit="2.2", title="API Integration")
                    ]
                )
            ]
        },
        {
            "course": CourseCreate(
                title="Robótica con ROS (Robot Operating System)",
                description="Programa robots autónomos con ROS.",
                place="LABORATORIO ROBÓTICA.\n\nCentro CTT-FISEI.",
                course_image="https://example.com/ros.png",
                course_image_detail="https://example.com/ros-detail.png",
                category_id=category_id,
                status=CourseStatus.ACTIVO,
                objectives=[
                    "Programar robots con ROS",
                    "Implementar navegación autónoma",
                    "Integrar sensores y actuadores"
                ],
                organizers=["Dr. Ismael Paredes", "Ing. Carla Benítez"],
                materials=["Robot kit", "Sensores", "ROS", "Gazebo Simulator"],
                target_audience=["Ingenieros", "Estudiantes", "Investigadores"]
            ),
            "requirements": CourseRequirementCreate(
                start_date_registration=date(2026, 4, 15),
                end_date_registration=date(2026, 5, 10),
                start_date_course=date(2026, 5, 15),
                end_date_course=date(2026, 7, 30),
                days=["Sábado"],
                start_time=time(8, 0, 0),
                end_time=time(14, 0, 0),
                location="Laboratorio Robótica - FISEI",
                min_quota=10,
                max_quota=16,
                in_person_hours=48,
                autonomous_hours=36,
                modality="Presencial",
                certification="Certificado ROS Developer",
                prerequisites=["Python", "Linux básico"],
                prices=[
                    {"amount": 95, "category": "Estudiantes UTA"},
                    {"amount": 125, "category": "Graduados y Docentes UTA"},
                    {"amount": 170, "category": "Público en general"}
                ]
            ),
            "contents": [
                CourseContentCreate(
                    unit="Módulo 1",
                    title="ROS Fundamentals",
                    topics=[
                        CourseContentTopicRead(unit="1.1", title="Nodes y Topics"),
                        CourseContentTopicRead(unit="1.2", title="Services y Actions"),
                        CourseContentTopicRead(unit="1.3", title="TF y URDF")
                    ]
                ),
                CourseContentCreate(
                    unit="Módulo 2",
                    title="Robot Navigation",
                    topics=[
                        CourseContentTopicRead(unit="2.1", title="SLAM"),
                        CourseContentTopicRead(unit="2.2", title="Path Planning")
                    ]
                )
            ]
        },
        {
            "course": CourseCreate(
                title="GraphQL: APIs Modernas",
                description="Desarrolla APIs eficientes con GraphQL.",
                place="AULA DESARROLLO.\n\nCentro CTT-FISEI.",
                course_image="https://example.com/graphql.png",
                course_image_detail="https://example.com/graphql-detail.png",
                category_id=category_id,
                status=CourseStatus.ACTIVO,
                objectives=[
                    "Diseñar schemas GraphQL",
                    "Implementar resolvers",
                    "Optimizar queries con DataLoader"
                ],
                organizers=["Ing. Víctor Luna", "Ing. Isabel Carrasco"],
                materials=["Computadora", "Node.js", "Apollo Server", "Internet"],
                target_audience=["Backend Developers", "Full Stack", "Arquitectos"]
            ),
            "requirements": CourseRequirementCreate(
                start_date_registration=date(2026, 3, 25),
                end_date_registration=date(2026, 4, 18),
                start_date_course=date(2026, 4, 22),
                end_date_course=date(2026, 5, 30),
                days=["Lunes", "Miércoles", "Viernes"],
                start_time=time(19, 0, 0),
                end_time=time(21, 30, 0),
                location="Aula 301 - FISEI",
                min_quota=12,
                max_quota=24,
                in_person_hours=30,
                autonomous_hours=20,
                modality="Híbrido",
                certification="Certificado GraphQL Developer",
                prerequisites=["JavaScript", "Node.js básico"],
                prices=[
                    {"amount": 55, "category": "Estudiantes UTA"},
                    {"amount": 75, "category": "Graduados y Docentes UTA"},
                    {"amount": 100, "category": "Público en general"}
                ]
            ),
            "contents": [
                CourseContentCreate(
                    unit="Módulo 1",
                    title="GraphQL Basics",
                    topics=[
                        CourseContentTopicRead(unit="1.1", title="Schema Definition"),
                        CourseContentTopicRead(unit="1.2", title="Queries y Mutations"),
                        CourseContentTopicRead(unit="1.3", title="Subscriptions")
                    ]
                ),
                CourseContentCreate(
                    unit="Módulo 2",
                    title="Advanced GraphQL",
                    topics=[
                        CourseContentTopicRead(unit="2.1", title="Resolvers"),
                        CourseContentTopicRead(unit="2.2", title="DataLoader")
                    ]
                )
            ]
        },
        {
            "course": CourseCreate(
                title="Microservicios con Spring Boot",
                description="Arquitectura de microservicios con Java y Spring.",
                place="LABORATORIO JAVA.\n\nCentro CTT-FISEI.",
                course_image="https://example.com/springboot.png",
                course_image_detail="https://example.com/springboot-detail.png",
                category_id=category_id,
                status=CourseStatus.ACTIVO,
                objectives=[
                    "Diseñar arquitecturas de microservicios",
                    "Implementar servicios con Spring Boot",
                    "Gestionar comunicación entre servicios"
                ],
                organizers=["Ing. Héctor Molina", "Ing. Beatriz Aguirre"],
                materials=["JDK", "IntelliJ IDEA", "Docker", "Postman"],
                target_audience=["Java Developers", "Arquitectos", "Backend Engineers"]
            ),
            "requirements": CourseRequirementCreate(
                start_date_registration=date(2026, 5, 5),
                end_date_registration=date(2026, 5, 28),
                start_date_course=date(2026, 6, 2),
                end_date_course=date(2026, 8, 15),
                days=["Martes", "Jueves"],
                start_time=time(18, 30, 0),
                end_time=time(21, 30, 0),
                location="Laboratorio Java - FISEI",
                min_quota=12,
                max_quota=20,
                in_person_hours=48,
                autonomous_hours=36,
                modality="Presencial",
                certification="Certificado Spring Boot Developer",
                prerequisites=["Java", "Spring Framework básico"],
                prices=[
                    {"amount": 85, "category": "Estudiantes UTA"},
                    {"amount": 110, "category": "Graduados y Docentes UTA"},
                    {"amount": 155, "category": "Público en general"}
                ]
            ),
            "contents": [
                CourseContentCreate(
                    unit="Módulo 1",
                    title="Spring Boot Essentials",
                    topics=[
                        CourseContentTopicRead(unit="1.1", title="Spring Boot Setup"),
                        CourseContentTopicRead(unit="1.2", title="REST APIs"),
                        CourseContentTopicRead(unit="1.3", title="Spring Data JPA")
                    ]
                ),
                CourseContentCreate(
                    unit="Módulo 2",
                    title="Microservices Architecture",
                    topics=[
                        CourseContentTopicRead(unit="2.1", title="Service Discovery"),
                        CourseContentTopicRead(unit="2.2", title="API Gateway")
                    ]
                )
            ]
        },
        {
            "course": CourseCreate(
                title="Computer Vision con OpenCV",
                description="Procesamiento de imágenes y visión artificial.",
                place="LABORATORIO VISIÓN.\n\nCentro CTT-FISEI.",
                course_image="https://example.com/opencv.png",
                course_image_detail="https://example.com/opencv-detail.png",
                category_id=category_id,
                status=CourseStatus.ACTIVO,
                objectives=[
                    "Procesar imágenes con OpenCV",
                    "Implementar detección de objetos",
                    "Desarrollar aplicaciones de visión artificial"
                ],
                organizers=["PhD. Ramiro Navarro", "Ing. Lucia Fernández"],
                materials=["Python", "OpenCV", "Cámaras", "Datasets de imágenes"],
                target_audience=["Investigadores", "Desarrolladores", "Ingenieros"]
            ),
            "requirements": CourseRequirementCreate(
                start_date_registration=date(2026, 4, 20),
                end_date_registration=date(2026, 5, 15),
                start_date_course=date(2026, 5, 20),
                end_date_course=date(2026, 7, 5),
                days=["Miércoles", "Viernes"],
                start_time=time(18, 0, 0),
                end_time=time(21, 0, 0),
                location="Laboratorio Visión - FISEI",
                min_quota=10,
                max_quota=18,
                in_person_hours=36,
                autonomous_hours=28,
                modality="Presencial",
                certification="Certificado Computer Vision",
                prerequisites=["Python", "Matemáticas"],
                prices=[
                    {"amount": 75, "category": "Estudiantes UTA"},
                    {"amount": 100, "category": "Graduados y Docentes UTA"},
                    {"amount": 135, "category": "Público en general"}
                ]
            ),
            "contents": [
                CourseContentCreate(
                    unit="Módulo 1",
                    title="Image Processing",
                    topics=[
                        CourseContentTopicRead(unit="1.1", title="Filtros y transformaciones"),
                        CourseContentTopicRead(unit="1.2", title="Detección de bordes"),
                        CourseContentTopicRead(unit="1.3", title="Segmentación")
                    ]
                ),
                CourseContentCreate(
                    unit="Módulo 2",
                    title="Object Detection",
                    topics=[
                        CourseContentTopicRead(unit="2.1", title="Haar Cascades"),
                        CourseContentTopicRead(unit="2.2", title="Deep Learning CV")
                    ]
                )
            ]
        },
        {
            "course": CourseCreate(
                title="Análisis de Datos con Power BI",
                description="Business Intelligence y visualización de datos con Power BI.",
                place="AULA ANÁLISIS.\n\nCentro CTT-FISEI.",
                course_image="https://example.com/powerbi.png",
                course_image_detail="https://example.com/powerbi-detail.png",
                category_id=category_id,
                status=CourseStatus.ACTIVO,
                objectives=[
                    "Crear dashboards interactivos",
                    "Modelar datos con DAX",
                    "Implementar soluciones BI"
                ],
                organizers=["Ing. Ernesto Guzmán", "Lic. Marina Soto"],
                materials=["Power BI Desktop", "Excel", "Fuentes de datos", "Computadora"],
                target_audience=["Analistas de datos", "Gerentes", "Business Analysts"]
            ),
            "requirements": CourseRequirementCreate(
                start_date_registration=date(2026, 3, 8),
                end_date_registration=date(2026, 4, 2),
                start_date_course=date(2026, 4, 7),
                end_date_course=date(2026, 5, 20),
                days=["Lunes", "Miércoles"],
                start_time=time(19, 0, 0),
                end_time=time(22, 0, 0),
                location="Aula 401 - FISEI",
                min_quota=15,
                max_quota=30,
                in_person_hours=30,
                autonomous_hours=20,
                modality="Híbrido",
                certification="Certificado Power BI Analyst",
                prerequisites=["Excel intermedio"],
                prices=[
                    {"amount": 50, "category": "Estudiantes UTA"},
                    {"amount": 70, "category": "Graduados y Docentes UTA"},
                    {"amount": 95, "category": "Público en general"}
                ]
            ),
            "contents": [
                CourseContentCreate(
                    unit="Módulo 1",
                    title="Power BI Basics",
                    topics=[
                        CourseContentTopicRead(unit="1.1", title="Importación de datos"),
                        CourseContentTopicRead(unit="1.2", title="Transformación ETL"),
                        CourseContentTopicRead(unit="1.3", title="Visualizaciones")
                    ]
                ),
                CourseContentCreate(
                    unit="Módulo 2",
                    title="Advanced Analytics",
                    topics=[
                        CourseContentTopicRead(unit="2.1", title="DAX"),
                        CourseContentTopicRead(unit="2.2", title="Modelado de datos")
                    ]
                )
            ]
        },
        {
            "course": CourseCreate(
                title="Git y GitHub Avanzado",
                description="Control de versiones profesional para equipos.",
                place="LABORATORIO DESARROLLO.\n\nCentro CTT-FISEI.",
                course_image="https://example.com/git.png",
                course_image_detail="https://example.com/git-detail.png",
                category_id=category_id,
                status=CourseStatus.ACTIVO,
                objectives=[
                    "Dominar Git workflows",
                    "Colaborar efectivamente con GitHub",
                    "Implementar CI/CD con GitHub Actions"
                ],
                organizers=["Ing. Oscar Reyes", "Ing. Camila Ibarra"],
                materials=["Git", "GitHub account", "Terminal", "VS Code"],
                target_audience=["Desarrolladores", "DevOps", "Teams"]
            ),
            "requirements": CourseRequirementCreate(
                start_date_registration=date(2026, 2, 5),
                end_date_registration=date(2026, 2, 26),
                start_date_course=date(2026, 3, 3),
                end_date_course=date(2026, 4, 5),
                days=["Martes", "Jueves"],
                start_time=time(19, 0, 0),
                end_time=time(21, 0, 0),
                location="Laboratorio 201 - FISEI",
                min_quota=15,
                max_quota=35,
                in_person_hours=24,
                autonomous_hours=16,
                modality="Híbrido",
                certification="Certificado Git Professional",
                prerequisites=["Git básico"],
                prices=[
                    {"amount": 35, "category": "Estudiantes UTA"},
                    {"amount": 50, "category": "Graduados y Docentes UTA"},
                    {"amount": 70, "category": "Público en general"}
                ]
            ),
            "contents": [
                CourseContentCreate(
                    unit="Módulo 1",
                    title="Git Advanced",
                    topics=[
                        CourseContentTopicRead(unit="1.1", title="Branching strategies"),
                        CourseContentTopicRead(unit="1.2", title="Rebase y Merge"),
                        CourseContentTopicRead(unit="1.3", title="Cherry-pick y Stash")
                    ]
                ),
                CourseContentCreate(
                    unit="Módulo 2",
                    title="GitHub Collaboration",
                    topics=[
                        CourseContentTopicRead(unit="2.1", title="Pull Requests"),
                        CourseContentTopicRead(unit="2.2", title="GitHub Actions")
                    ]
                )
            ]
        },
        {
            "course": CourseCreate(
                title="Procesamiento de Lenguaje Natural con spaCy",
                description="NLP y análisis de texto con Python.",
                place="LABORATORIO NLP.\n\nCentro CTT-FISEI.",
                course_image="https://example.com/nlp.png",
                course_image_detail="https://example.com/nlp-detail.png",
                category_id=category_id,
                status=CourseStatus.ACTIVO,
                objectives=[
                    "Procesar texto con spaCy",
                    "Implementar análisis de sentimientos",
                    "Crear modelos de NLP personalizados"
                ],
                organizers=["Dr. Arturo Velasco", "MSc. Diana Torres"],
                materials=["Python", "spaCy", "Jupyter", "Corpus de texto"],
                target_audience=["Data Scientists", "Lingüistas computacionales", "Investigadores"]
            ),
            "requirements": CourseRequirementCreate(
                start_date_registration=date(2026, 5, 10),
                end_date_registration=date(2026, 6, 5),
                start_date_course=date(2026, 6, 10),
                end_date_course=date(2026, 7, 25),
                days=["Lunes", "Miércoles"],
                start_time=time(18, 30, 0),
                end_time=time(21, 30, 0),
                location="Laboratorio NLP - FISEI",
                min_quota=10,
                max_quota=20,
                in_person_hours=36,
                autonomous_hours=28,
                modality="Presencial",
                certification="Certificado NLP Specialist",
                prerequisites=["Python", "Machine Learning básico"],
                prices=[
                    {"amount": 80, "category": "Estudiantes UTA"},
                    {"amount": 105, "category": "Graduados y Docentes UTA"},
                    {"amount": 145, "category": "Público en general"}
                ]
            ),
            "contents": [
                CourseContentCreate(
                    unit="Módulo 1",
                    title="NLP Fundamentals",
                    topics=[
                        CourseContentTopicRead(unit="1.1", title="Tokenización y POS"),
                        CourseContentTopicRead(unit="1.2", title="Named Entity Recognition"),
                        CourseContentTopicRead(unit="1.3", title="Dependency Parsing")
                    ]
                ),
                CourseContentCreate(
                    unit="Módulo 2",
                    title="Advanced NLP",
                    topics=[
                        CourseContentTopicRead(unit="2.1", title="Sentiment Analysis"),
                        CourseContentTopicRead(unit="2.2", title="Custom Models")
                    ]
                )
            ]
        },
        {
            "course": CourseCreate(
                title="Seguridad en Aplicaciones Web OWASP",
                description="Protege aplicaciones web contra vulnerabilidades comunes.",
                place="LABORATORIO SEGURIDAD WEB.\n\nCentro CTT-FISEI.",
                course_image="https://example.com/owasp.png",
                course_image_detail="https://example.com/owasp-detail.png",
                category_id=category_id,
                status=CourseStatus.ACTIVO,
                objectives=[
                    "Identificar OWASP Top 10",
                    "Implementar medidas de seguridad",
                    "Realizar auditorías de seguridad"
                ],
                organizers=["Ing. Federico Paredes", "Ing. Gabriela Serrano"],
                materials=["Burp Suite", "OWASP ZAP", "Navegador", "Computadora"],
                target_audience=["Desarrolladores web", "Security Engineers", "Pentesters"]
            ),
            "requirements": CourseRequirementCreate(
                start_date_registration=date(2026, 3, 12),
                end_date_registration=date(2026, 4, 8),
                start_date_course=date(2026, 4, 12),
                end_date_course=date(2026, 5, 28),
                days=["Sábado"],
                start_time=time(9, 0, 0),
                end_time=time(14, 0, 0),
                location="Laboratorio Seguridad - FISEI",
                min_quota=12,
                max_quota=20,
                in_person_hours=30,
                autonomous_hours=22,
                modality="Presencial",
                certification="Certificado Web Security",
                prerequisites=["Desarrollo web", "HTTP/HTTPS"],
                prices=[
                    {"amount": 70, "category": "Estudiantes UTA"},
                    {"amount": 90, "category": "Graduados y Docentes UTA"},
                    {"amount": 125, "category": "Público en general"}
                ]
            ),
            "contents": [
                CourseContentCreate(
                    unit="Módulo 1",
                    title="OWASP Top 10",
                    topics=[
                        CourseContentTopicRead(unit="1.1", title="Injection"),
                        CourseContentTopicRead(unit="1.2", title="XSS y CSRF"),
                        CourseContentTopicRead(unit="1.3", title="Authentication")
                    ]
                ),
                CourseContentCreate(
                    unit="Módulo 2",
                    title="Security Testing",
                    topics=[
                        CourseContentTopicRead(unit="2.1", title="Burp Suite"),
                        CourseContentTopicRead(unit="2.2", title="Security Headers")
                    ]
                )
            ]
        },
        {
            "course": CourseCreate(
                title="TypeScript para Desarrolladores JavaScript",
                description="Aprende TypeScript y mejora la calidad de tu código.",
                place="AULA PROGRAMACIÓN.\n\nCentro CTT-FISEI.",
                course_image="https://example.com/typescript.png",
                course_image_detail="https://example.com/typescript-detail.png",
                category_id=category_id,
                status=CourseStatus.ACTIVO,
                objectives=[
                    "Dominar TypeScript",
                    "Implementar tipos avanzados",
                    "Migrar proyectos a TypeScript"
                ],
                organizers=["Ing. Andrés Maldonado", "Ing. Silvia Ponce"],
                materials=["Node.js", "VS Code", "TypeScript compiler", "Internet"],
                target_audience=["JavaScript Developers", "Frontend", "Backend"]
            ),
            "requirements": CourseRequirementCreate(
                start_date_registration=date(2026, 2, 18),
                end_date_registration=date(2026, 3, 12),
                start_date_course=date(2026, 3, 17),
                end_date_course=date(2026, 4, 25),
                days=["Lunes", "Miércoles", "Viernes"],
                start_time=time(19, 0, 0),
                end_time=time(21, 0, 0),
                location="Aula 501 - FISEI",
                min_quota=15,
                max_quota=30,
                in_person_hours=30,
                autonomous_hours=18,
                modality="Híbrido",
                certification="Certificado TypeScript Developer",
                prerequisites=["JavaScript ES6+"],
                prices=[
                    {"amount": 45, "category": "Estudiantes UTA"},
                    {"amount": 60, "category": "Graduados y Docentes UTA"},
                    {"amount": 85, "category": "Público en general"}
                ]
            ),
            "contents": [
                CourseContentCreate(
                    unit="Módulo 1",
                    title="TypeScript Basics",
                    topics=[
                        CourseContentTopicRead(unit="1.1", title="Tipos básicos"),
                        CourseContentTopicRead(unit="1.2", title="Interfaces y Types"),
                        CourseContentTopicRead(unit="1.3", title="Generics")
                    ]
                ),
                CourseContentCreate(
                    unit="Módulo 2",
                    title="Advanced TypeScript",
                    topics=[
                        CourseContentTopicRead(unit="2.1", title="Utility Types"),
                        CourseContentTopicRead(unit="2.2", title="Decorators")
                    ]
                )
            ]
        },
        {
            "course": CourseCreate(
                title="Serverless Architecture con AWS Lambda",
                description="Desarrolla aplicaciones serverless escalables.",
                place="LABORATORIO SERVERLESS.\n\nCentro CTT-FISEI.",
                course_image="https://example.com/lambda.png",
                course_image_detail="https://example.com/lambda-detail.png",
                category_id=category_id,
                status=CourseStatus.ACTIVO,
                objectives=[
                    "Crear funciones Lambda",
                    "Implementar arquitecturas serverless",
                    "Integrar servicios AWS serverless"
                ],
                organizers=["Ing. Mauricio Ríos", "Ing. Fernanda Castañeda"],
                materials=["AWS Account", "SAM CLI", "Serverless Framework", "Computadora"],
                target_audience=["Cloud Developers", "Backend Engineers", "DevOps"]
            ),
            "requirements": CourseRequirementCreate(
                start_date_registration=date(2026, 4, 25),
                end_date_registration=date(2026, 5, 18),
                start_date_course=date(2026, 5, 22),
                end_date_course=date(2026, 7, 8),
                days=["Jueves"],
                start_time=time(18, 0, 0),
                end_time=time(22, 0, 0),
                location="Laboratorio Cloud - FISEI",
                min_quota=12,
                max_quota=22,
                in_person_hours=32,
                autonomous_hours=24,
                modality="Presencial",
                certification="Certificado Serverless Developer",
                prerequisites=["AWS básico", "Node.js o Python"],
                prices=[
                    {"amount": 75, "category": "Estudiantes UTA"},
                    {"amount": 100, "category": "Graduados y Docentes UTA"},
                    {"amount": 140, "category": "Público en general"}
                ]
            ),
            "contents": [
                CourseContentCreate(
                    unit="Módulo 1",
                    title="Lambda Fundamentals",
                    topics=[
                        CourseContentTopicRead(unit="1.1", title="Lambda Functions"),
                        CourseContentTopicRead(unit="1.2", title="Event Sources"),
                        CourseContentTopicRead(unit="1.3", title="API Gateway")
                    ]
                ),
                CourseContentCreate(
                    unit="Módulo 2",
                    title="Serverless Patterns",
                    topics=[
                        CourseContentTopicRead(unit="2.1", title="Step Functions"),
                        CourseContentTopicRead(unit="2.2", title="EventBridge")
                    ]
                )
            ]
        },
        {
            "course": CourseCreate(
                title="Scrum Master Certification Prep",
                description="Prepárate para la certificación Scrum Master.",
                place="AULA AGILE.\n\nCentro CTT-FISEI.",
                course_image="https://example.com/scrum.png",
                course_image_detail="https://example.com/scrum-detail.png",
                category_id=category_id,
                status=CourseStatus.ACTIVO,
                objectives=[
                    "Dominar el framework Scrum",
                    "Facilitar eventos Scrum",
                    "Preparar examen de certificación"
                ],
                organizers=["Cert. Scrum Master Jorge Paredes", "Agile Coach María Solís"],
                materials=["Scrum Guide", "Material de estudio", "Exámenes de práctica"],
                target_audience=["Project Managers", "Team Leaders", "Desarrolladores"]
            ),
            "requirements": CourseRequirementCreate(
                start_date_registration=date(2026, 3, 1),
                end_date_registration=date(2026, 3, 22),
                start_date_course=date(2026, 3, 27),
                end_date_course=date(2026, 4, 18),
                days=["Viernes", "Sábado"],
                start_time=time(17, 0, 0),
                end_time=time(21, 0, 0),
                location="Aula Agile - FISEI",
                min_quota=15,
                max_quota=30,
                in_person_hours=28,
                autonomous_hours=20,
                modality="Híbrido",
                certification="Certificado preparación Scrum Master",
                prerequisites=["Ninguno"],
                prices=[
                    {"amount": 60, "category": "Estudiantes UTA"},
                    {"amount": 80, "category": "Graduados y Docentes UTA"},
                    {"amount": 110, "category": "Público en general"}
                ]
            ),
            "contents": [
                CourseContentCreate(
                    unit="Módulo 1",
                    title="Scrum Framework",
                    topics=[
                        CourseContentTopicRead(unit="1.1", title="Scrum Values y Pillars"),
                        CourseContentTopicRead(unit="1.2", title="Roles"),
                        CourseContentTopicRead(unit="1.3", title="Events")
                    ]
                ),
                CourseContentCreate(
                    unit="Módulo 2",
                    title="Scrum Master Role",
                    topics=[
                        CourseContentTopicRead(unit="2.1", title="Facilitation"),
                        CourseContentTopicRead(unit="2.2", title="Exam Prep")
                    ]
                )
            ]
        }
    ]



def seed_courses_bulk():
    """Función principal para sembrar múltiples cursos"""
    with Session(engine) as session:
        print("Iniciando seed de múltiples cursos...")
        
        # Obtener la categoría TICS primero
        category = session.exec(
            select(Category).where(Category.name == "TICS")
        ).first()
        
        if not category:
            print("ERROR: La categoría 'TICS' no existe. Debes ejecutar seed_categories primero.")
            return
        
        print(f"Usando categoría: {category.name} (ID: {category.id})")
        
        courses_data = get_courses_data(category.id)
        courses_created = 0
        courses_skipped = 0
        
        for idx, course_info in enumerate(courses_data, 1):
            try:
                # Verificar si el curso ya existe por título
                existing_course = session.exec(
                    select(Course).where(Course.title == course_info["course"].title)
                ).first()
                
                if existing_course:
                    print(f"[{idx}/{len(courses_data)}] Curso '{course_info['course'].title}' ya existe, omitiendo...")
                    courses_skipped += 1
                    continue
                
                # Crear el curso
                result = CourseController.create_course_with_requirements(
                    course_info["course"],
                    course_info["requirements"],
                    course_info["contents"],
                    session,
                    current_user_id=1  # User ID para seeds
                )
                
                print(f"[{idx}/{len(courses_data)}] ✓ Curso '{course_info['course'].title}' creado exitosamente (ID: {result.get('id')})")
                courses_created += 1
                
            except Exception as e:
                print(f"[{idx}/{len(courses_data)}] ✗ Error al crear curso '{course_info['course'].title}': {e}")
                session.rollback()
                courses_skipped += 1
                continue
        
        print(f"\n{'='*80}")
        print(f"Resumen de creación de cursos:")
        print(f"  - Total de cursos en seed: {len(courses_data)}")
        print(f"  - Cursos creados exitosamente: {courses_created}")
        print(f"  - Cursos omitidos/fallidos: {courses_skipped}")
        print(f"{'='*80}\n")


if __name__ == "__main__":
    seed_courses_bulk()
