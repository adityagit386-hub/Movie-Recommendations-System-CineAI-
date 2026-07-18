"""
ai_engine/hybrid.py
Hybrid recommendation (proposal §9): blends content-based similarity
(always available) with collaborative signal (only once enough users
have interacted with the catalogue) for better accuracy over time.
"""

from typing import Dict, Optional
from sqlalchemy.orm import Session

from ai_engine import content_based, collaborative

CONTENT_WEIGHT = 0.7
COLLAB_WEIGHT = 0.3


def recommend_hybrid(
    db: Session,
    title: str,
    top_n: int = 8,
    language: Optional[str] = None,
    genre: Optional[str] = None,
) -> Dict:
    content_result = content_based.recommend_similar(title, top_n=top_n * 2, language=language, genre=genre)
    collab_list = collaborative.recommend_collaborative(db, title, top_n=top_n * 2)

    if not collab_list:
        # Cold start: not enough cross-user data yet, content-based only.
        content_result["recommendations"] = content_result["recommendations"][:top_n]
        return content_result

    collab_scores = {item["title"]: item["similarity_score"] for item in collab_list}

    blended = []
    for item in content_result["recommendations"]:
        content_score = item["similarity_score"] or 0
        collab_score = collab_scores.get(item["title"], 0)
        item = dict(item)
        item["similarity_score"] = round(CONTENT_WEIGHT * content_score + COLLAB_WEIGHT * collab_score, 3)
        blended.append(item)

    # Include strong collaborative-only picks that content-based missed.
    existing_titles = {item["title"] for item in blended}
    for item in collab_list:
        if item["title"] not in existing_titles:
            item = dict(item)
            item["similarity_score"] = round(COLLAB_WEIGHT * item["similarity_score"], 3)
            blended.append(item)

    blended.sort(key=lambda x: x["similarity_score"] or 0, reverse=True)

    return {"source_title": content_result["source_title"], "recommendations": blended[:top_n]}
