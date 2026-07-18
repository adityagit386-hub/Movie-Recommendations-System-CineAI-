"""
schemas/schemas.py
Pydantic models describing every request body and response payload
served by the FastAPI routers.
"""

from typing import List, Optional
from pydantic import BaseModel


class MovieOut(BaseModel):
    title: str
    genre: Optional[str] = None
    language: Optional[str] = None
    runtime: Optional[int] = None
    rating: Optional[float] = None
    similarity_score: Optional[float] = None
    reason: Optional[str] = None
    release_year: Optional[int] = None


class RecommendationResponse(BaseModel):
    source_title: Optional[str] = None
    recommendations: List[MovieOut]


class RecommendRequest(BaseModel):
    title: str
    language: Optional[str] = None
    mood: Optional[str] = None
    genre: Optional[str] = None
    top_n: int = 8


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatbotRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []


class ChatbotResponse(BaseModel):
    reply: str
    recommendations: List[MovieOut] = []


class WatchlistAddRequest(BaseModel):
    movie_title: str


class WatchlistResponse(BaseModel):
    user_id: str
    items: List[MovieOut]
