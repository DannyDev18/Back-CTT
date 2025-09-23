import os
from sqlmodel import create_engine
from dotenv import load_dotenv

load_dotenv()

SQL_SERVER = os.getenv("SQL_SERVER")
SQL_PORT = os.getenv("SQL_PORT")
SQL_DB = os.getenv("SQL_DB")
SQL_USER = os.getenv("SQL_USER")
SQL_PASSWORD = os.getenv("SQL_PASSWORD")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"


DATABASE_URL = f"mssql+pyodbc://{SQL_USER}:{SQL_PASSWORD}@{SQL_SERVER}:{SQL_PORT}/{SQL_DB}?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"

engine = create_engine(DATABASE_URL, echo=DEBUG)