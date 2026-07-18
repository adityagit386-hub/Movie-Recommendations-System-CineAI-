"""
ai_engine/collaborative.py
Collaborative filtering (proposal §9): "recommend movies based on users
with similar interests, if user data is available."

Implicit feedback (watchlist + favorites) from the SQLite tables is used
to build a user-item interaction matrix. Item-item similarity is then
computed so we can answer "users who liked X also liked Y". With very
little data (cold start / new deployment) this degrades gracefully to
an empty result, and the hybrid engine falls back to content-based.
"""

from typing import Dict, List
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import select

from models.user import WatchlistItem, FavoriteItem
from ai_engine.preprocess import MOVIES_DF

_TITLES = list(MOVIES_DF["title"])
_TITLE_TO_COL = {title: i for i, title in enumerate(_TITLES)}


def _build_interaction_matrix(db: Session) -> np.ndarray:
    """Rows = users, columns = dataset movies. Cell = 1 if the user engaged with it."""
    watch_rows = db.execute(select(WatchlistItem.user_id, WatchlistItem.movie_title)).all()
    fav_rows = db.execute(select(FavoriteItem.user_id, FavoriteItem.movie_title)).all()

    interactions = list(watch_rows) + list(fav_rows)
    if not interactions:
        return np.zeros((0, len(_TITLES)))

    user_ids = sorted({row[0] for row in interactions})
    user_to_row = {uid: i for i, uid in enumerate(user_ids)}

    matrix = np.zeros((len(user_ids), len(_TITLES)))
    for user_id, movie_title in interactions:
        col = _TITLE_TO_COL.get(movie_title)
        if col is not None:
            matrix[user_to_row[user_id], col] = 1

    return matrix


def recommend_collaborative(db: Session, title: str, top_n: int = 8) -> List[Dict]:
    """Movies favored by users who also engaged with `title`."""
    matrix = _build_interaction_matrix(db)
    col = _TITLE_TO_COL.get(title)

    if matrix.shape[0] < 2 or col is None:
        return []  # not enough signal yet -- caller should fall back to content-based

    # Item-item cosine similarity computed from the interaction matrix.
    item_vectors = matrix.T  # movies x users
    norms = np.linalg.norm(item_vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1
    normalized = item_vectors / norms

    target_vec = normalized[col]
    scores = normalized @ target_vec

    ranked = np.argsort(scores)[::-1]
    results = []
    for idx in ranked:
        if idx == col or scores[idx] <= 0:
            continue
        row = MOVIES_DF.iloc[idx]
        results.append({
            "title": row["title"],
            "genre": row["genre"],
            "language": row["language"],
            "runtime": int(row["runtime"]) if str(row["runtime"]).strip() else None,
            "rating": float(row["rating"]) if str(row["rating"]).strip() else None,
            "similarity_score": round(float(scores[idx]), 3),
            "reason": f"Viewers who liked {title} also liked this.",
            "release_year": int(row["release_year"]) if str(row["release_year"]).strip() else None,
        })
        if len(results) >= top_n:
            break

    return results
