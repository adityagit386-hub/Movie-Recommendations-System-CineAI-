"""
routers/watchlist.py
"Personalized Watchlist", "Favorite Movies" and "Search History"
features from proposal §6. Simple per-user_id persistence, no auth --
the extension generates and stores a random user_id in chrome.storage.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from database import get_db
from models.user import WatchlistItem, FavoriteItem, SearchHistoryItem
from ai_engine.preprocess import MOVIES_DF
from schemas.schemas import WatchlistAddRequest, WatchlistResponse

router = APIRouter(prefix="/watchlist", tags=["watchlist"])

_TITLE_LOOKUP = {row["title"]: row for _, row in MOVIES_DF.iterrows()}


def _movie_out(title: str) -> dict:
    row = _TITLE_LOOKUP.get(title)
    if row is None:
        return {"title": title}
    return {
        "title": row["title"],
        "genre": row["genre"],
        "language": row["language"],
        "runtime": int(row["runtime"]) if str(row["runtime"]).strip() else None,
        "rating": float(row["rating"]) if str(row["rating"]).strip() else None,
        "release_year": int(row["release_year"]) if str(row["release_year"]).strip() else None,
    }


@router.get("/{user_id}", response_model=WatchlistResponse)
def get_watchlist(user_id: str, db: Session = Depends(get_db)):
    rows = db.execute(select(WatchlistItem).where(WatchlistItem.user_id == user_id)).scalars().all()
    return {"user_id": user_id, "items": [_movie_out(r.movie_title) for r in rows]}


@router.post("/{user_id}")
def add_to_watchlist(user_id: str, payload: WatchlistAddRequest, db: Session = Depends(get_db)):
    exists = db.execute(
        select(WatchlistItem).where(
            WatchlistItem.user_id == user_id, WatchlistItem.movie_title == payload.movie_title
        )
    ).scalar_one_or_none()

    if not exists:
        db.add(WatchlistItem(user_id=user_id, movie_title=payload.movie_title))
        db.commit()

    return {"ok": True}


@router.delete("/{user_id}/{movie_title}")
def remove_from_watchlist(user_id: str, movie_title: str, db: Session = Depends(get_db)):
    item = db.execute(
        select(WatchlistItem).where(
            WatchlistItem.user_id == user_id, WatchlistItem.movie_title == movie_title
        )
    ).scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Not in watchlist")

    db.delete(item)
    db.commit()
    return {"ok": True}


@router.post("/{user_id}/favorite")
def add_favorite(user_id: str, payload: WatchlistAddRequest, db: Session = Depends(get_db)):
    exists = db.execute(
        select(FavoriteItem).where(
            FavoriteItem.user_id == user_id, FavoriteItem.movie_title == payload.movie_title
        )
    ).scalar_one_or_none()

    if not exists:
        db.add(FavoriteItem(user_id=user_id, movie_title=payload.movie_title))
        db.commit()

    return {"ok": True}


@router.get("/{user_id}/history")
def get_history(user_id: str, db: Session = Depends(get_db)):
    rows = (
        db.execute(
            select(SearchHistoryItem)
            .where(SearchHistoryItem.user_id == user_id)
            .order_by(SearchHistoryItem.searched_at.desc())
            .limit(50)
        )
        .scalars()
        .all()
    )
    return {
        "user_id": user_id,
        "history": [
            {"title": r.movie_title, "platform": r.platform, "searched_at": r.searched_at} for r in rows
        ],
    }


@router.post("/{user_id}/history")
def log_history(user_id: str, payload: dict, db: Session = Depends(get_db)):
    db.add(
        SearchHistoryItem(
            user_id=user_id,
            movie_title=payload.get("movie_title", ""),
            platform=payload.get("platform"),
        )
    )
    db.commit()
    return {"ok": True}
