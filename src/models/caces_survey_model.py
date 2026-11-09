from sqlmodel import SQLModel, Field
from typing import Optional, List, Any
from datetime import datetime
from sqlalchemy import Column, DateTime, Text
from pydantic import BaseModel, Field as PydanticField, model_validator
import src.models.congress_model  # Ensures congresos table is registered in SQLModel.metadata
import src.models.user_platform   # Ensures users_platform table is registered in SQLModel.metadata


class CacesSurvey(SQLModel, table=True):
    __tablename__ = "caces_surveys"

    id: Optional[int] = Field(default=None, primary_key=True)
    id_congress: Optional[int] = Field(default=None, foreign_key="congresos.id_congreso", nullable=True)
    id_course: Optional[int] = Field(default=None, foreign_key="course.id", nullable=True)
    id_user_platform: int = Field(foreign_key="users_platform.id", nullable=False)
    q1_rating: int = Field(nullable=False)
    q2_rating: int = Field(nullable=False)
    q3_rating: int = Field(nullable=False)
    comments: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    submitted_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, nullable=False, default=datetime.utcnow),
    )


class CacesSurveyCreate(BaseModel):
    q1_rating: Optional[int] = None
    q2_rating: Optional[int] = None
    q3_rating: Optional[int] = None
    q1_score: Optional[int] = None
    q2_score: Optional[int] = None
    q3_score: Optional[int] = None
    comments: Optional[str] = None
    id_user_platform: Optional[int] = None

    @model_validator(mode="before")
    @classmethod
    def map_scores_to_ratings(cls, data: Any) -> Any:
        if isinstance(data, dict):
            data = dict(data)
            for i in range(1, 4):
                score_key = f"q{i}_score"
                rating_key = f"q{i}_rating"
                score_val = data.get(score_key)
                rating_val = data.get(rating_key)
                if rating_val is None and score_val is not None:
                    data[rating_key] = score_val
                elif score_val is None and rating_val is not None:
                    data[score_key] = rating_val
        return data

    @model_validator(mode="after")
    def validate_ratings_present(self) -> "CacesSurveyCreate":
        for i in range(1, 4):
            val = getattr(self, f"q{i}_rating")
            if val is None:
                raise ValueError(f"Campo q{i}_rating (o q{i}_score) es requerido.")
        return self


class CacesSurveyRead(BaseModel):
    id: int
    id_congress: int
    id_user_platform: int
    q1_rating: int
    q2_rating: int
    q3_rating: int
    comments: Optional[str] = None
    submitted_at: datetime

    class Config:
        from_attributes = True


class CacesSurveyStats(BaseModel):
    id_congress: int
    total_responses: int
    avg_q1: float
    avg_q2: float
    avg_q3: float
    overall_average: float
    recent_comments: List[str] = []
