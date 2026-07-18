"""
routers/trending.py
GET /trending -> highest-rated titles from the local dataset, enriched
with live TMDB trending data when an API key is configured.
"""

from fastapi import APIRouter

from ai_engine.preprocess import MOVIES_DF
from services import tmdb_service
from schemas.schemas import RecommendationResponse

router = APIRouter(prefix="/trending", tags=["trending"])


@router.get("", response_model=RecommendationResponse)
def trending(top_n: int = 8):
    local_top = MOVIES_DF.sort_values("rating", ascending=False).head(top_n)

    recommendations = [
        {
            "title": row["title"],
            "genre": row["genre"],
            "language": row["language"],
            "runtime": int(row["runtime"]) if str(row["runtime"]).strip() else None,
            "rating": float(row["rating"]) if str(row["rating"]).strip() else None,
            "similarity_score": None,
            "reason": "Highly rated in the CineAI catalogue.",
            "release_year": int(row["release_year"]) if str(row["release_year"]).strip() else None,
        }
        for _, row in local_top.iterrows()
    ]

    tmdb_trending = tmdb_service.get_trending()
    if tmdb_trending:
        recommendations = [tmdb_service.tmdb_result_to_movie_out(r) for r in tmdb_trending[:top_n]]

    return {"source_title": None, "recommendations": recommendations}
