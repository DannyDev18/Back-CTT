import os
from urllib.parse import quote_plus

from sqlmodel import create_engine
from dotenv import load_dotenv

load_dotenv()

POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"


# quote_plus: usuario/contraseña con caracteres especiales (@, :, /, #...) no rompen la URL
DATABASE_URL = (
    f"postgresql+psycopg2://{quote_plus(POSTGRES_USER or '')}:{quote_plus(POSTGRES_PASSWORD or '')}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

engine = create_engine(DATABASE_URL, echo=DEBUG)
