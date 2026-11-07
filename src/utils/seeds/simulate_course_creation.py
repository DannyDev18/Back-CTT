"""
Script para simular el flujo real de creación de cursos con subida de imágenes.
Simula exactamente lo que ocurre en la aplicación cuando un administrador crea un curso:
1. Se sube la imagen al backend (/api/v1/images/upload o función save_image)
2. Se almacena localmente en static/images/courses/
3. Se obtiene la URL estática (ej: http://localhost:3002/static/images/courses/...)
4. Se crea/actualiza el curso asociando la URL de banner y detalle.
"""

import os
import shutil
import uuid
from pathlib import Path
from sqlmodel import Session, select
from src.config.db import engine
from src.models.course import Course, CourseCreate, CourseStatus
from src.models.category import Category
from src.controllers.course_controller import CourseController

UPLOAD_DIR = Path("static/images/courses")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:3002")

def simulate_image_upload(source_image_path: str, base_url: str = BACKEND_URL) -> str:
    """
    Simula la subida de una imagen al endpoint /api/v1/images/upload
    Copia el archivo al directorio UPLOAD_DIR generando un identificador único
    y retorna la URL accesible.
    """
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    src = Path(source_image_path)
    if not src.exists():
        raise FileNotFoundError(f"No se encontró la imagen fuente: {source_image_path}")

    ext = src.suffix.lower() or ".jpg"
    unique_name = f"{uuid.uuid4().hex[:12]}_{src.name}"
    dest = UPLOAD_DIR / unique_name
    shutil.copy2(src, dest)
    
    image_url = f"{base_url}/static/images/courses/{unique_name}"
    print(f"  [Upload Simulado] {src.name} -> {image_url}")
    return image_url

def sync_existing_courses_with_real_images():
    """
    Sincroniza y actualiza todos los cursos existentes en la base de datos
    con sus imágenes reales correspondientes.
    """
    print("\n>> Sincronizando cursos en BD con imágenes locales reales...")
    
    mapping = {
        1: "course-1-arduino.jpg",
        2: "course-2-python-data-science.jpg",
        3: "course-3-fullstack-react-node.jpg",
        4: "course-4-cybersecurity.jpg",
        5: "course-5-ux-ui-design.jpg",
        6: "course-6-devops-docker.jpg",
        7: "course-7-ai-deep-learning.jpg",
        8: "course-8-blockchain-crypto.jpg",
        9: "course-9-iot-esp32.jpg",
        10: "course-10-unity-gamedev.jpg",
        11: "course-11-big-data-spark.jpg",
        12: "course-12-quantum-computing.jpg",
        13: "course-13-cloud-aws.jpg",
        14: "course-14-vr-ar.jpg",
        15: "course-15-software-testing.jpg",
        16: "course-16-mobile-flutter.jpg",
        17: "course-17-robotica-ros.jpg",
        18: "course-18-graphql-apis.jpg",
        19: "course-19-microservicios-spring.jpg",
        20: "course-20-computer-vision.jpg",
        21: "course-21-power-bi-analytics.jpg",
        22: "course-22-git-github.jpg",
        23: "course-23-nlp-spacy.jpg",
        24: "course-24-seguridad-owasp.jpg",
        25: "course-25-typescript-js.jpg",
        26: "course-26-serverless-lambda.jpg",
        27: "course-27-scrum-master-agile.jpg",
    }
    
    with Session(engine) as session:
        courses = session.exec(select(Course)).all()
        updated_count = 0
        for course in courses:
            filename = mapping.get(course.id)
            if filename:
                img_path = UPLOAD_DIR / filename
                if img_path.exists():
                    url = f"{BACKEND_URL}/static/images/courses/{filename}"
                    course.course_image = url
                    course.course_image_detail = url
                    session.add(course)
                    updated_count += 1
        
        session.commit()
        print(f"✓ {updated_count} cursos sincronizados exitosamente con imágenes reales.\n")

if __name__ == "__main__":
    sync_existing_courses_with_real_images()

