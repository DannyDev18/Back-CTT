from fastapi import FastAPI
from contextlib import asynccontextmanager
from sqlmodel import SQLModel
from src.config.db import engine
from src.routes.auth_router import auth_router
from src.models.user import User
from src.utils.seeds.user_seed import seed_users

SQLModel.metadata.create_all(engine)


@asynccontextmanager # type: ignore
async def lifespan(app: FastAPI):
    seed_users()  
    yield# Llama a la función de seed al iniciar la aplicación

app = FastAPI(lifespan=lifespan)

app.include_router(auth_router)

@app.get("/")
def read_root():
    return {"Hello": "World"}