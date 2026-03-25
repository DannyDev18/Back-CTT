from sqlmodel import Session, select
from src.config.db import engine
from src.models.congreso_sponsor_model import CongresoSponsor
from src.models.sponsor_model import Sponsor
from src.models.congress_model import Congress
from decimal import Decimal
import random

def seed_congreso_sponsor():
    """
    Seed de asociaciones congreso-sponsor para el sistema CTT
    Crea relaciones realistas entre sponsors y congresos con categorías y aportes
    """
    with Session(engine) as session:
        print("Seeding congreso-sponsor associations...")

        # Obtener todos los congresos y sponsors existentes
        congresses = session.exec(select(Congress)).all()
        sponsors = session.exec(select(Sponsor)).all()

        if not congresses:
            print("  ❌ No congresses found. Please run congress seed first.")
            return

        if not sponsors:
            print("  ❌ No sponsors found. Please run sponsors seed first.")
            return

        created_count = 0
        existing_count = 0

        # Categorías de sponsorship con rangos de aporte típicos (en USD)
        sponsorship_categories = {
            "oro": {
                "min_amount": Decimal("15000.00"),
                "max_amount": Decimal("50000.00"),
                "probability": 0.15  # 15% de probabilidad por congreso
            },
            "plata": {
                "min_amount": Decimal("8000.00"),
                "max_amount": Decimal("14999.00"),
                "probability": 0.25  # 25% de probabilidad por congreso
            },
            "bronce": {
                "min_amount": Decimal("3000.00"),
                "max_amount": Decimal("7999.00"),
                "probability": 0.35  # 35% de probabilidad por congreso
            },
            "colaborador": {
                "min_amount": Decimal("500.00"),
                "max_amount": Decimal("2999.00"),
                "probability": 0.50  # 50% de probabilidad por congreso
            }
        }

        for congress in congresses:
            print(f"\n  Creating sponsorships for: {congress.nombre}")

            # Cada congreso puede tener múltiples sponsors, pero no todos los sponsors patrocinarán cada congreso
            # Seleccionar un subconjunto aleatorio de sponsors para este congreso
            num_sponsors_for_congress = random.randint(2, min(8, len(sponsors)))
            selected_sponsors = random.sample(sponsors, num_sponsors_for_congress)

            for sponsor in selected_sponsors:
                # Verificar si ya existe esta asociación
                existing_association = session.exec(
                    select(CongresoSponsor).where(
                        CongresoSponsor.id_congreso == congress.id_congreso,
                        CongresoSponsor.id_sponsor == sponsor.id_sponsor
                    )
                ).first()

                if existing_association:
                    existing_count += 1
                    print(f"    - Association already exists: {sponsor.nombre}")
                    continue

                # Determinar aleatoriamente la categoría de sponsorship
                # Los sponsors más establecidos tienen más probabilidad de categorías altas
                category_weights = []
                categories = list(sponsorship_categories.keys())

                # Lógica para determinar categoría basada en el tipo de sponsor
                if any(word in sponsor.nombre.lower() for word in ["editorial", "universidad", "seminario"]):
                    # Instituciones educativas y editoriales tienden a ser sponsors de categoría alta
                    category_weights = [0.3, 0.4, 0.2, 0.1]  # oro, plata, bronce, colaborador
                elif any(word in sponsor.nombre.lower() for word in ["fundación", "ministerios", "asociación"]):
                    # Organizaciones ministeriales tienden a ser sponsors medianos
                    category_weights = [0.1, 0.3, 0.4, 0.2]
                else:
                    # Otros sponsors tienen distribución más uniforme
                    category_weights = [0.15, 0.25, 0.35, 0.25]

                # Seleccionar categoría basada en los pesos
                selected_category = random.choices(categories, weights=category_weights)[0]

                # Generar monto de aporte dentro del rango de la categoría
                category_info = sponsorship_categories[selected_category]
                min_amount = category_info["min_amount"]
                max_amount = category_info["max_amount"]

                # Generar monto aleatorio en el rango, redondeado a múltiplos de 100
                amount_range = float(max_amount - min_amount)
                random_amount = min_amount + Decimal(str(random.randint(0, int(amount_range / 100)) * 100))

                # Crear la asociación
                new_association = CongresoSponsor(
                    id_congreso=congress.id_congreso,
                    id_sponsor=sponsor.id_sponsor,
                    categoria=selected_category,
                    aporte=random_amount
                )

                session.add(new_association)
                created_count += 1
                print(f"    ✓ Created {selected_category} sponsorship: {sponsor.nombre} - ${random_amount}")

        # Algunos sponsors especiales que patrocinan múltiples congresos
        premium_sponsors = [
            sponsor for sponsor in sponsors
            if any(word in sponsor.nombre.lower() for word in ["editorial", "universidad", "seminario teológico"])
        ]

        if premium_sponsors and len(congresses) > 1:
            print(f"\n  Creating premium multi-congress sponsorships...")

            for sponsor in premium_sponsors[:3]:  # Tomar los primeros 3 sponsors premium
                # Este sponsor patrocinará múltiples congresos
                num_congresses_to_sponsor = random.randint(2, min(4, len(congresses)))
                selected_congresses = random.sample(congresses, num_congresses_to_sponsor)

                for congress in selected_congresses:
                    # Verificar que no exista ya
                    existing = session.exec(
                        select(CongresoSponsor).where(
                            CongresoSponsor.id_congreso == congress.id_congreso,
                            CongresoSponsor.id_sponsor == sponsor.id_sponsor
                        )
                    ).first()

                    if not existing:
                        # Sponsors premium tienden a tener categorías altas
                        premium_category = random.choices(
                            ["oro", "plata", "bronce"],
                            weights=[0.5, 0.3, 0.2]
                        )[0]

                        category_info = sponsorship_categories[premium_category]
                        premium_amount = category_info["min_amount"] + Decimal(str(
                            random.randint(0, int((category_info["max_amount"] - category_info["min_amount"]) / 100)) * 100
                        ))

                        new_premium_association = CongresoSponsor(
                            id_congreso=congress.id_congreso,
                            id_sponsor=sponsor.id_sponsor,
                            categoria=premium_category,
                            aporte=premium_amount
                        )

                        session.add(new_premium_association)
                        created_count += 1
                        print(f"    ✓ Premium {premium_category}: {sponsor.nombre} -> {congress.nombre[:50]}... - ${premium_amount}")

        session.commit()
        print(f"\nCongreso-Sponsor associations seeded successfully! ✅")
        print(f"   - Created: {created_count} new associations")
        print(f"   - Skipped: {existing_count} existing associations")
        print(f"   - Total congresses: {len(congresses)}")
        print(f"   - Total sponsors: {len(sponsors)}")

        # Mostrar estadísticas de categorías
        print(f"\n   📊 Category Statistics:")
        category_counts = session.exec(
            select(CongresoSponsor.categoria).group_by(CongresoSponsor.categoria)
        ).all()

if __name__ == "__main__":
    seed_congreso_sponsor()