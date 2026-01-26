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
from src.routes.pdf_router import pdf_router
from src.models.user import User
from src.models.course import Course
from src.models.user_platform import UserPlatform
from src.models.post import Post
from src.models.enrollment import Enrollment
from src.models.category import Category
from src.utils.seeds.categories_seed import seed_categories
from src.utils.seeds.user_seed import seed_users
from src.utils.seeds.courses_seed import seed_courses
#from src.utils.seeds.courses_bulk_seed import seed_courses_bulk
from src.utils.seeds.user_platform_seed import seed_users_platform
from src.utils.svg_utils import init_svg_directory
from src.utils.image_utils import init_upload_directory
from src.utils.pdf_utils import init_pdf_directory
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from src.middleware.error_handler import error_handler_middleware
from starlette.middleware.base import BaseHTTPMiddleware
from src.config.logging_config import setup_logging

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
    seed_courses()
   #seed_courses_bulk()
    seed_users_platform()
    yield

app = FastAPI(lifespan=lifespan)

# Montar directorio estático para servir imágenes, SVGs y PDFs
app.mount("/static", StaticFiles(directory="static"), name="static")

# Agregar middleware de manejo de errores (debe ir primero)
app.middleware("http")(error_handler_middleware)

origins = ["*"]

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
app.include_router(svg_router)
app.include_router(pdf_router)
@app.get("/")
def read_root():
    return {"Hello": "World"}