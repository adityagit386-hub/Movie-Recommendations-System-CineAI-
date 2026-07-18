"""
main.py
FastAPI application entrypoint (proposal §7/§8).

Run locally:
    uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import engine, Base
from routers import recommend, watchlist, chatbot, trending

# Create SQLite tables on first run.
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.APP_NAME, version="1.0.0")

# The Chrome extension calls this API from a chrome-extension:// origin,
# so CORS is wide open here; tighten ALLOWED_ORIGINS in config.py for prod.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(recommend.router)
app.include_router(trending.router)
app.include_router(watchlist.router)
app.include_router(chatbot.router)


@app.get("/")
def root():
    return {"status": "ok", "service": settings.APP_NAME}


@app.get("/health")
def health():
    return {"status": "healthy"}
