from fastapi import FastAPI
from contextlib import asynccontextmanager
from sqlmodel import SQLModel
from src.config.db import engine
from src.routes.auth_router import auth_router
from src.routes.courses_router import courses_router
from src.models.user import User
from src.models.course import Course
from src.utils.seeds.user_seed import seed_users
from src.utils.seeds.courses_seed import seed_courses
from fastapi.middleware.cors import CORSMiddleware

SQLModel.metadata.create_all(engine)


@asynccontextmanager # type: ignore
async def lifespan(app: FastAPI):
    seed_users()
    seed_courses()
    yield# Llama a las funciones de seed al iniciar la aplicación

app = FastAPI(lifespan=lifespan)

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

@app.get("/")
def read_root():
    return {"Hello": "World"}