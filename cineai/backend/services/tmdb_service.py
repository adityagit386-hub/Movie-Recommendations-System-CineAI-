"""
services/tmdb_service.py
Thin wrapper around the TMDB API (proposal §7 "APIs"). Requires a free
API key from https://www.themoviedb.org/settings/api set as the
CINEAI_TMDB_API_KEY environment variable. Every function fails soft
(returns an empty list/dict) when no key is configured, so the rest of
the app keeps working against the local dataset alone.
"""

from typing import Dict, List, Optional
import httpx

from config import settings


def _has_key() -> bool:
    return bool(settings.TMDB_API_KEY)


def search_movie(title: str) -> Optional[Dict]:
    if not _has_key():
        return None

    try:
        resp = httpx.get(
            f"{settings.TMDB_BASE_URL}/search/movie",
            params={"api_key": settings.TMDB_API_KEY, "query": title},
            timeout=6,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        return results[0] if results else None
    except httpx.HTTPError:
        return None


def get_trending(time_window: str = "week") -> List[Dict]:
    if not _has_key():
        return []

    try:
        resp = httpx.get(
            f"{settings.TMDB_BASE_URL}/trending/movie/{time_window}",
            params={"api_key": settings.TMDB_API_KEY},
            timeout=6,
        )
        resp.raise_for_status()
        return resp.json().get("results", [])
    except httpx.HTTPError:
        return []


def tmdb_result_to_movie_out(result: Dict) -> Dict:
    """Map a TMDB API result onto the same shape used by the local recommendation engine."""
    return {
        "title": result.get("title") or result.get("name"),
        "genre": None,
        "language": result.get("original_language"),
        "runtime": None,
        "rating": result.get("vote_average"),
        "similarity_score": None,
        "reason": "Trending now on TMDB.",
        "release_year": (result.get("release_date") or "")[:4] or None,
    }
