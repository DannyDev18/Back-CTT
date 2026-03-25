import os
from fastapi import FastAPI
from contextlib import asynccontextmanager
from sqlmodel import SQLModel
from src.routes.svg_router import svg_router
from src.config.db import engine
from src.routes.auth_router import auth_router
from src.routes.courses_router import courses_router
from src.routes.images_router import images_router
from src.routes.platform_auth_router import platform_auth_router
from src.routes.users_platform_router import users_platform_router
from src.routes.posts_router import posts_router
from src.routes.enrollments_router import enrollments_router
from src.routes.categories_router import categories_router
from src.routes.congress_categories_router import congress_categories_router
from src.routes.pdf_router import pdf_router
from src.routes.congress_router import congress_router
from src.routes.sponsor_router import sponsor_router
from src.routes.speaker_router import speaker_router
from src.routes.sesion_cronograma_router import sesion_cronograma_router
from src.routes.congreso_sponsor_router import congreso_sponsor_router
from src.models.user import User
from src.models.course import Course
from src.models.user_platform import UserPlatform
from src.models.post import Post
from src.models.enrollment import Enrollment
from src.models.category import Category
from src.models.congress_category import CongressCategory
from src.utils.seeds.categories_seed import seed_categories
from src.utils.seeds.congress_categories_seed import seed_congress_categories
from src.utils.seeds.user_seed import seed_users
from src.utils.seeds.courses_seed import seed_courses
from src.utils.seeds.courses_bulk_seed import seed_courses_bulk
from src.utils.seeds.enrollment_seed import seed_enrollments
from src.utils.seeds.user_platform_seed import seed_users_platform
from src.utils.svg_utils import init_svg_directory
from src.utils.image_utils import init_upload_directory
from src.utils.pdf_utils import init_pdf_directory
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from src.middleware.error_handler import error_handler_middleware
from starlette.middleware.base import BaseHTTPMiddleware
from src.config.logging_config import setup_logging
from src.utils.seeds.congress_seed import seed_congresses
from src.utils.seeds.sponsors_seed import seed_sponsors
from src.utils.seeds.congreso_sponsor_seed import seed_congreso_sponsor
from src.utils.seeds.speakers_seed import seed_speakers
from src.utils.seeds.sesion_cronograma_seed import seed_sesion_cronograma


# Configurar logging
setup_logging()

SQLModel.metadata.create_all(engine)


@asynccontextmanager # type: ignore
async def lifespan(app: FastAPI):
    # Inicializar directorio de imágenes
    init_svg_directory()
    init_upload_directory()
    init_pdf_directory()
    # Ejecutar seeds
    seed_users()
    seed_categories()
    seed_congress_categories()
    #seed_courses()
    seed_courses_bulk()
    seed_users_platform()
    seed_enrollments()
    seed_congresses()
    seed_sponsors()
    seed_congreso_sponsor()
    seed_speakers()
    seed_sesion_cronograma()
    yield

app = FastAPI(
    lifespan=lifespan,
    title="CTT API",
    description="API para el sistema CTT con autenticación JWT",
    version="1.0.0",
    swagger_ui_parameters={
        "persistAuthorization": True  # Mantiene el token después de refrescar
    }
)
security_scheme = {
    "BearerAuth": {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "Autenticación con token JWT"
    },
    "PlatformBearerAuth": {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "Autenticación con token JWT para plataforma"
    }
}
app.openapi_schema = None  

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    from fastapi.openapi.utils import get_openapi
    
    openapi_schema = get_openapi(
        title="CTT API",
        version="1.0.0",
        description="API para el sistema CTT con autenticación JWT",
        routes=app.routes,
    )
    
    # Agregar esquemas de seguridad
    openapi_schema["components"]["securitySchemes"] = security_scheme
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Montar directorio estático para servir imágenes, SVGs y PDFs
app.mount("/static", StaticFiles(directory="static"), name="static")

# Agregar middleware de manejo de errores (debe ir primero)
app.middleware("http")(error_handler_middleware)

origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(courses_router)
app.include_router(images_router)
app.include_router(platform_auth_router)
app.include_router(users_platform_router)
app.include_router(posts_router)
app.include_router(enrollments_router)
app.include_router(categories_router)
app.include_router(congress_categories_router)
app.include_router(svg_router)
app.include_router(pdf_router)
app.include_router(congress_router)
app.include_router(sponsor_router)
app.include_router(speaker_router)
app.include_router(sesion_cronograma_router)
app.include_router(congreso_sponsor_router)
@app.get("/")
def read_root():
    return {"Hello": "World"}