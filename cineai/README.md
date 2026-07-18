# CineAI — AI Movie Recommendation Browser Extension

## Folder structure

```
cineai/
├── extension/                     # Chrome Extension (Manifest V3)
│   ├── manifest.json
│   ├── background/
│   │   └── background.js          # service worker: stores detected movie + history
│   ├── content_scripts/
│   │   ├── extractor.js           # shared DOM-watching helper
│   │   ├── netflix.js
│   │   ├── primevideo.js
│   │   └── youtube.js
│   ├── popup/
│   │   ├── popup.html             # tabs: For You / Watchlist / Trending / Ask AI
│   │   ├── popup.css
│   │   └── popup.js
│   ├── utils/
│   │   └── api.js                 # fetch wrapper around the FastAPI backend
│   └── icons/
│       ├── icon16.png
│       ├── icon48.png
│       └── icon128.png
│
├── backend/                       # FastAPI backend
│   ├── main.py                    # app entrypoint
│   ├── config.py
│   ├── database.py                # SQLAlchemy engine/session (SQLite)
│   ├── requirements.txt
│   ├── models/
│   │   └── user.py                # Watchlist / Favorite / SearchHistory tables
│   ├── schemas/
│   │   └── schemas.py             # Pydantic request/response models
│   ├── routers/
│   │   ├── recommend.py           # POST /recommend, GET /recommend/genre|mood
│   │   ├── trending.py            # GET /trending
│   │   ├── watchlist.py           # watchlist / favorites / history CRUD
│   │   └── chatbot.py             # POST /chatbot/query (NL recommendations)
│   ├── ai_engine/
│   │   ├── preprocess.py          # dataset loading + feature "soup"
│   │   ├── content_based.py       # TF-IDF + cosine similarity
│   │   ├── collaborative.py       # implicit-feedback item-item CF
│   │   ├── hybrid.py              # blends content-based + collaborative
│   │   └── embeddings.py          # Sentence-Transformers semantic search (mood/chat)
│   ├── services/
│   │   └── tmdb_service.py        # optional TMDB API integration
│   └── data/
│       └── movies_sample.csv      # sample dataset (title, genre, cast, keywords, ...)
│
└── README.md
```

## Run the backend

```bash
cd backend
python -m venv venv && source venv/bin/activate     # optional
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

The API is now live at `http://localhost:8000` (interactive docs at `/docs`).

Optional environment variables:
- `CINEAI_TMDB_API_KEY` — enables live TMDB metadata/trending
- `CINEAI_DATABASE_URL` — defaults to local `sqlite:///./cineai.db`
- `CINEAI_ST_MODEL` — Sentence-Transformers model name (falls back to a TF-IDF
  embedding automatically if the model can't be downloaded)

## Load the extension

1. Go to `chrome://extensions`
2. Enable **Developer mode**
3. Click **Load unpacked** → select the `extension/` folder
4. Open Netflix, Prime Video, or a YouTube video, then click the CineAI icon

## Swap in your own dataset

Replace `backend/data/movies_sample.csv` with a larger export from
MovieLens / TMDB / IMDb using the same columns — the AI engine re-derives
everything from that file automatically.
