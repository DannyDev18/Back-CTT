"""
Seeds package for CTT Ecuador
Contains all database seeding functions for development and testing
"""

# Import all seed functions for easy access
from .user_seed import seed_users
from .user_platform_seed import seed_users_platform
from .categories_seed import seed_categories
from .congress_categories_seed import seed_congress_categories
from .congress_seed import seed_congresses
from .sponsors_seed import seed_sponsors
from .speakers_seed import seed_speakers
from .sesion_cronograma_seed import seed_sesion_cronograma
from .congreso_sponsor_seed import seed_congreso_sponsor
from .enrollment_seed import seed_enrollments
from .main_seed import run_all_seeds, seed_congress_only

# For courses (if available)
try:
    from .courses_seed import seed_courses
    from .courses_bulk_seed import seed_courses_bulk
except ImportError:
    # Course seeds might not be available in all environments
    seed_courses = None
    seed_courses_bulk = None

__all__ = [
    # Individual seeds
    "seed_users",
    "seed_users_platform",
    "seed_categories",
    "seed_congress_categories",
    "seed_congresses",
    "seed_sponsors",
    "seed_speakers",
    "seed_sesion_cronograma",
    "seed_congreso_sponsor",
    "seed_enrollments",

    # Course seeds (optional)
    "seed_courses",
    "seed_courses_bulk",

    # Main orchestration functions
    "run_all_seeds",
    "seed_congress_only",
]