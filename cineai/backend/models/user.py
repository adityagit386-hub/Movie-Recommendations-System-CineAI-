"""
models/user.py
Persistence for the "User Module" described in the proposal:
watchlist, favorites and search history. Kept intentionally simple
(string user_id, no auth) since login is marked optional in the spec.
"""

from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint
from sqlalchemy.sql import func

from database import Base


class WatchlistItem(Base):
    __tablename__ = "watchlist"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    movie_title = Column(String, nullable=False)
    added_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("user_id", "movie_title", name="uq_watchlist_user_movie"),)


class FavoriteItem(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    movie_title = Column(String, nullable=False)
    added_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("user_id", "movie_title", name="uq_favorite_user_movie"),)


class SearchHistoryItem(Base):
    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    movie_title = Column(String, nullable=False)
    platform = Column(String, nullable=True)
    searched_at = Column(DateTime(timezone=True), server_default=func.now())
