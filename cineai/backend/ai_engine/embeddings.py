"""
ai_engine/embeddings.py
Sentence-Transformer based semantic similarity (proposal §10). Used for:
  - mood-based recommendations ("relaxing", "intense", ...)
  - the natural-language AI chatbot, where a free-text query is embedded
    and matched against every movie's overview/keyword embedding.

Falls back gracefully to a lightweight TF-IDF-based cosine similarity if
sentence-transformers / a downloaded model isn't available in the
current environment (e.g. no internet access to fetch model weights),
so the rest of the app keeps working.
"""

from typing import List, Dict
import numpy as np

from ai_engine.preprocess import MOVIES_DF
from config import settings

_MOOD_QUERY_MAP = {
    "feel_good": "uplifting heartwarming feel-good happy comedy family",
    "intense": "intense gripping tense thriller high-stakes action",
    "relaxing": "light easy relaxing calm comfort watch",
    "thought_provoking": "thought-provoking philosophical deep meaningful drama",
    "scary": "scary horror frightening tense supernatural",
}

_backend = None
_movie_embeddings = None


def _load_backend():
    """Lazily load sentence-transformers; fall back to TF-IDF on failure."""
    global _backend, _movie_embeddings

    if _backend is not None:
        return

    try:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer(settings.SENTENCE_TRANSFORMER_MODEL)
        embeddings = model.encode(MOVIES_DF["soup"].tolist(), convert_to_numpy=True, normalize_embeddings=True)

        _backend = ("sentence_transformers", model)
        _movie_embeddings = embeddings

    except Exception:
        # Fallback: reuse a TF-IDF vectorizer as a cheap embedding space.
        from sklearn.feature_extraction.text import TfidfVectorizer

        vectorizer = TfidfVectorizer(stop_words="english")
        matrix = vectorizer.fit_transform(MOVIES_DF["soup"]).toarray()
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1
        matrix = matrix / norms

        _backend = ("tfidf_fallback", vectorizer)
        _movie_embeddings = matrix


def _embed_query(query: str) -> np.ndarray:
    _load_backend()
    kind, model = _backend

    if kind == "sentence_transformers":
        vec = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)[0]
    else:
        vec = model.transform([query]).toarray()[0]
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm

    return vec


def semantic_search(query: str, top_n: int = 8) -> List[Dict]:
    """Free-text semantic search over the dataset, used by the chatbot and mood filter."""
    _load_backend()
    query_vec = _embed_query(query)

    # Cosine similarity against every movie embedding (vectors already normalized).
    dim = min(len(query_vec), _movie_embeddings.shape[1])
    scores = _movie_embeddings[:, :dim] @ query_vec[:dim]

    top_indices = np.argsort(scores)[::-1][:top_n]

    results = []
    for idx in top_indices:
        row = MOVIES_DF.iloc[idx]
        results.append({
            "title": row["title"],
            "genre": row["genre"],
            "language": row["language"],
            "runtime": int(row["runtime"]) if str(row["runtime"]).strip() else None,
            "rating": float(row["rating"]) if str(row["rating"]).strip() else None,
            "similarity_score": round(float(scores[idx]), 3),
            "reason": f"Matched your query \u2018{query}\u2019.",
            "release_year": int(row["release_year"]) if str(row["release_year"]).strip() else None,
        })
    return results


def recommend_by_mood(mood: str, top_n: int = 8) -> List[Dict]:
    query = _MOOD_QUERY_MAP.get(mood, mood)
    return semantic_search(query, top_n=top_n)
