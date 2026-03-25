#!/usr/bin/env python3
"""
Debug sponsor controller get_by_id with congresses method
"""
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

def debug_sponsor_get_by_id():
    """Debug sponsor get by id with congresses method"""
    # Setup database
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Import models
    from src.models.base import Base
    from src.models.sponsor_model import Sponsor, SponsorCreate
    from src.controllers.sponsor_controller import sponsor_controller

    try:
        # Create all tables
        SQLModel.metadata.create_all(engine)
        print("[OK] Tables created successfully")

        with Session(engine) as session:
            # Create a test sponsor directly
            sponsor = Sponsor(
                nombre="Test Sponsor",
                logo_url="https://test.jpg",
                sitio_web="https://test.com",
                descripcion="Test description"
            )
            session.add(sponsor)
            session.commit()
            session.refresh(sponsor)
            print(f"[OK] Created sponsor directly: {sponsor}")
            print(f"[INFO] Sponsor type: {type(sponsor)}")
            print(f"[INFO] Sponsor id_sponsor: {sponsor.id_sponsor}")

            # Test controller method with include_congresses=True
            try:
                result = sponsor_controller.get_sponsor_by_id(
                    session, sponsor.id_sponsor, include_congresses=True
                )
                print(f"[OK] Got sponsor with congresses: {result}")
            except Exception as e:
                print(f"[ERROR] Getting sponsor with congresses failed: {e}")
                import traceback
                traceback.print_exc()

            # Test repository method directly
            try:
                from src.repositories.sponsor_repository import sponsor_repository
                repo_result = sponsor_repository.get_sponsor_with_congresses(
                    session, sponsor.id_sponsor
                )
                print(f"[INFO] Repository result type: {type(repo_result)}")
                print(f"[INFO] Repository result: {repo_result}")
                if hasattr(repo_result, 'id_sponsor'):
                    print(f"[INFO] Repository result id_sponsor: {repo_result.id_sponsor}")
                else:
                    print(f"[INFO] Repository result dir: {[attr for attr in dir(repo_result) if not attr.startswith('_')]}")
            except Exception as e:
                print(f"[ERROR] Repository method failed: {e}")
                import traceback
                traceback.print_exc()

    except Exception as e:
        print(f"[ERROR] Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_sponsor_get_by_id()