"""
ai_engine/content_based.py
Content-based filtering (proposal §9): recommends movies with similar
genres, cast, director and keywords using TF-IDF + cosine similarity.
"""

from typing import List, Dict, Optional
from difflib import get_close_matches

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from ai_engine.preprocess import MOVIES_DF

_vectorizer = TfidfVectorizer(stop_words="english")
_tfidf_matrix = _vectorizer.fit_transform(MOVIES_DF["soup"])
_similarity_matrix = cosine_similarity(_tfidf_matrix, _tfidf_matrix)

_TITLE_INDEX = {title.lower(): idx for idx, title in enumerate(MOVIES_DF["title"])}


def _resolve_title(title: str) -> Optional[int]:
    """Fuzzy-match a free-text title (as extracted from the browser DOM) to a dataset row."""
    key = title.lower().strip()
    if key in _TITLE_INDEX:
        return _TITLE_INDEX[key]

    close = get_close_matches(key, _TITLE_INDEX.keys(), n=1, cutoff=0.6)
    if close:
        return _TITLE_INDEX[close[0]]
    return None


def _explain(base_idx: int, rec_idx: int) -> str:
    base = MOVIES_DF.iloc[base_idx]
    rec = MOVIES_DF.iloc[rec_idx]

    shared_genre = set(str(base["genre"]).split()) & set(str(rec["genre"]).split())
    if shared_genre:
        return f"Shares the {', '.join(shared_genre).lower()} genre with {base['title']}."
    if base["director"] == rec["director"] and base["director"]:
        return f"Directed by {rec['director']}, like {base['title']}."
    return f"Similar tone and themes to {base['title']}."


def recommend_similar(
    title: str,
    top_n: int = 8,
    language: Optional[str] = None,
    genre: Optional[str] = None,
) -> Dict:
    """Return the top-N most similar movies to `title`."""
    idx = _resolve_title(title)
    if idx is None:
        return {"source_title": title, "recommendations": []}

    scores = list(enumerate(_similarity_matrix[idx]))
    scores = [s for s in scores if s[0] != idx]
    scores.sort(key=lambda x: x[1], reverse=True)

    results = []
    for rec_idx, score in scores:
        row = MOVIES_DF.iloc[rec_idx]

        if language and language.lower() not in str(row["language"]).lower():
            continue
        if genre and genre.lower() not in str(row["genre"]).lower():
            continue

        results.append(_row_to_dict(row, score, _explain(idx, rec_idx)))
        if len(results) >= top_n:
            break

    return {"source_title": MOVIES_DF.iloc[idx]["title"], "recommendations": results}


def recommend_by_genre(genre: str, top_n: int = 8) -> List[Dict]:
    matches = MOVIES_DF[MOVIES_DF["genre"].str.contains(genre, case=False, na=False)]
    matches = matches.sort_values("rating", ascending=False).head(top_n)
    return [_row_to_dict(row, None, f"Popular pick in {genre}.") for _, row in matches.iterrows()]


def _row_to_dict(row, score: Optional[float], reason: str) -> Dict:
    return {
        "title": row["title"],
        "genre": row["genre"],
        "language": row["language"],
        "runtime": int(row["runtime"]) if str(row["runtime"]).strip() else None,
        "rating": float(row["rating"]) if str(row["rating"]).strip() else None,
        "similarity_score": round(float(score), 3) if score is not None else None,
        "reason": reason,
        "release_year": int(row["release_year"]) if str(row["release_year"]).strip() else None,
    }
