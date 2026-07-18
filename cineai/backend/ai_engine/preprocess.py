"""
ai_engine/preprocess.py
Loads the movie dataset and builds the combined text "soup" (genre +
cast + director + keywords + overview) that both the TF-IDF model and
the Sentence-Transformer model are built on.
"""

import pandas as pd

from config import settings

_REQUIRED_COLUMNS = [
    "movie_id", "title", "genre", "language", "cast", "director",
    "runtime", "rating", "keywords", "release_year", "overview"
]


def load_movies() -> pd.DataFrame:
    """Load the CSV dataset (MovieLens/TMDB/IMDb-style fields, see proposal §12)."""
    df = pd.read_csv(settings.MOVIES_CSV_PATH)

    for col in _REQUIRED_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    df = df.fillna("")
    df["soup"] = df.apply(_build_soup, axis=1)
    return df


def _build_soup(row) -> str:
    """Concatenate the fields that matter for similarity into one text blob."""
    parts = [
        str(row.get("genre", "")),
        str(row.get("cast", "")),
        str(row.get("director", "")),
        str(row.get("keywords", "")),
        str(row.get("overview", "")),
    ]
    return " ".join(parts).lower()


# Loaded once at import time and reused by every request (small demo dataset).
MOVIES_DF = load_movies()
