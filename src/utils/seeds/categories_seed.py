from sqlmodel import Session, select
from src.config.db import engine
from src.models.category import Category, CategoryStatus

def seed_categories():
    with Session(engine) as session:
        # Lista de categorías que quieres crear
        categories = [
            {"name": "TICS", "description": "Tecnologías de la información y comunicación"},
            {"name": "Electrónica", "description": "Cursos de electrónica y hardware"},
            {"name": "Programación", "description": "Cursos de desarrollo de software"}
        ]

        for cat in categories:
            # Verificar si ya existe
            existing = session.exec(select(Category).where(Category.name == cat["name"])).first()
            if not existing:
                new_cat = Category(
                    name=cat["name"],
                    description=cat["description"],
                    svgurl="",
                    status=CategoryStatus.ACTIVO,
                    created_by=1  
                )
                session.add(new_cat)
        
        session.commit()
        print("Categories seeded successfully.")
