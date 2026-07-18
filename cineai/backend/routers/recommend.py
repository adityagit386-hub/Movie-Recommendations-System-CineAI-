"""
routers/recommend.py
Core recommendation endpoints described in proposal §5/§9:
  POST /recommend            -> hybrid recommendation from a detected title
  GET  /recommend/genre/{g}  -> genre-based recommendation
  GET  /recommend/mood/{m}   -> mood-based recommendation (semantic search)
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from schemas.schemas import RecommendRequest, RecommendationResponse, MovieOut
from ai_engine import hybrid, content_based, embeddings

router = APIRouter(prefix="/recommend", tags=["recommendations"])


@router.post("", response_model=RecommendationResponse)
def recommend(payload: RecommendRequest, db: Session = Depends(get_db)):
    result = hybrid.recommend_hybrid(
        db,
        payload.title,
        top_n=payload.top_n,
        language=payload.language,
        genre=payload.genre,
    )

    if payload.mood and result["recommendations"]:
        mood_titles = {m["title"] for m in embeddings.recommend_by_mood(payload.mood, top_n=50)}
        filtered = [r for r in result["recommendations"] if r["title"] in mood_titles]
        result["recommendations"] = filtered or result["recommendations"]

    return result


@router.get("/genre/{genre}", response_model=RecommendationResponse)
def recommend_by_genre(genre: str, top_n: int = 8):
    recs = content_based.recommend_by_genre(genre, top_n=top_n)
    return {"source_title": None, "recommendations": recs}


@router.get("/mood/{mood}", response_model=RecommendationResponse)
def recommend_by_mood(mood: str, top_n: int = 8):
    recs = embeddings.recommend_by_mood(mood, top_n=top_n)
    return {"source_title": None, "recommendations": recs}
