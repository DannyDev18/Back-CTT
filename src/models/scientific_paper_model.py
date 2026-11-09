from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from sqlalchemy import Column, DateTime, Text
from pydantic import BaseModel
import src.models.congress_model  # Ensures congresos table is registered in SQLModel.metadata
import src.models.user_platform   # Ensures users_platform table is registered in SQLModel.metadata


class ScientificPaper(SQLModel, table=True):
    __tablename__ = "scientific_papers"

    id: Optional[int] = Field(default=None, primary_key=True)
    id_congress: int = Field(foreign_key="congresos.id_congreso", nullable=False)
    id_user_platform: int = Field(foreign_key="users_platform.id", nullable=False)
    title: str = Field(max_length=300, nullable=False)
    abstract: str = Field(sa_column=Column(Text, nullable=False))
    track: str = Field(max_length=100, nullable=False)
    keywords: Optional[str] = Field(default=None, max_length=255, nullable=True)
    file_url: str = Field(max_length=500, nullable=False)
    status: str = Field(default="ENVIADO", max_length=50, nullable=False)
    reviewer_comments: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    submitted_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, nullable=False, default=datetime.utcnow),
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, nullable=False, default=datetime.utcnow),
    )


class ScientificPaperCreate(BaseModel):
    title: str
    abstract: str
    track: str
    keywords: Optional[str] = None
    file_url: str
    id_user_platform: Optional[int] = None


class ScientificPaperReview(BaseModel):
    status: str
    reviewer_comments: Optional[str] = None


class ScientificPaperRead(BaseModel):
    id: int
    id_congress: int
    id_user_platform: int
    title: str
    abstract: str
    track: str
    keywords: Optional[str] = None
    file_url: str
    status: str
    reviewer_comments: Optional[str] = None
    submitted_at: datetime
    updated_at: datetime
    author_name: Optional[str] = None
    author_email: Optional[str] = None
    author_identification: Optional[str] = None

    class Config:
        from_attributes = True
