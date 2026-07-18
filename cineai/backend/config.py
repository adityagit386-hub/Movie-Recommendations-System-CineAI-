"""
config.py
Central place for environment-driven settings. In production, load these
from real environment variables (e.g. via python-dotenv) instead of
hard-coded defaults.
"""

import os

class Settings:
    APP_NAME: str = "CineAI Backend"

    # --- Database ---
    DATABASE_URL: str = os.getenv("CINEAI_DATABASE_URL", "sqlite:///./cineai.db")

    # --- Dataset ---
    MOVIES_CSV_PATH: str = os.getenv(
        "CINEAI_MOVIES_CSV", os.path.join(os.path.dirname(__file__), "data", "movies_sample.csv")
    )

    # --- TMDB API (https://www.themoviedb.org/documentation/api) ---
    TMDB_API_KEY: str = os.getenv("CINEAI_TMDB_API_KEY", "")
    TMDB_BASE_URL: str = "https://api.themoviedb.org/3"

    # --- CORS: browser extensions call the API from a chrome-extension:// origin ---
    ALLOWED_ORIGINS: list = ["*"]

    # --- Embedding model used for semantic / chatbot search ---
    SENTENCE_TRANSFORMER_MODEL: str = os.getenv(
        "CINEAI_ST_MODEL", "all-MiniLM-L6-v2"
    )


settings = Settings()
