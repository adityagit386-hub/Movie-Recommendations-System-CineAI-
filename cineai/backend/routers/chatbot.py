"""
routers/chatbot.py
"AI Chatbot" feature from proposal §6: lets the user ask for
recommendations in natural language, e.g.
  "Suggest a light-hearted Korean movie under 2 hours"
  "Something like Inception but shorter"

Approach: lightweight rule-based slot extraction (genre / mood /
runtime / language / "similar to X") layered on top of the semantic
search + content-based engines, so no external LLM call is required.
Swap `generate_reply()` for a call to the Anthropic API if you want
richer conversational responses.
"""

import re
from fastapi import APIRouter

from schemas.schemas import ChatbotRequest, ChatbotResponse
from ai_engine import embeddings, content_based

router = APIRouter(prefix="/chatbot", tags=["chatbot"])

_GENRES = ["action", "comedy", "drama", "sci-fi", "thriller", "romance", "animation", "horror", "crime", "fantasy"]
_LANGUAGES = ["english", "hindi", "korean", "spanish", "japanese", "italian"]
_MOOD_KEYWORDS = {
    "feel_good": ["feel-good", "feel good", "light-hearted", "lighthearted", "uplifting", "happy", "wholesome"],
    "intense": ["intense", "gripping", "edge of my seat", "action-packed"],
    "relaxing": ["relaxing", "easy watch", "chill", "calm"],
    "thought_provoking": ["thought-provoking", "thought provoking", "deep", "philosophical"],
    "scary": ["scary", "horror", "spooky", "frightening"],
}


@router.post("/query", response_model=ChatbotResponse)
def chatbot_query(payload: ChatbotRequest):
    message = payload.message.strip()
    lower = message.lower()

    similar_to = _extract_similar_to(message)
    genre = next((g for g in _GENRES if g in lower), None)
    language = next((l for l in _LANGUAGES if l in lower), None)
    mood = _extract_mood(lower)
    max_runtime = _extract_runtime(lower)

    if similar_to:
        result = content_based.recommend_similar(similar_to, top_n=6, language=language, genre=genre)
        recs = result["recommendations"]
        reply = (
            f"Here are picks similar to \u201c{result['source_title'] or similar_to}\u201d."
            if recs
            else f"I couldn't find \u201c{similar_to}\u201d in the catalogue yet -- try another title."
        )
    else:
        query_text = " ".join(filter(None, [mood, genre, language, message]))
        recs = embeddings.semantic_search(query_text, top_n=6)
        reply = "Here's what I'd suggest based on what you're in the mood for." if recs else \
            "I couldn't find a good match -- try mentioning a genre, mood, or a movie you liked."

    if max_runtime:
        recs = [r for r in recs if not r.get("runtime") or r["runtime"] <= max_runtime]

    return {"reply": reply, "recommendations": recs}


_STOP_PHRASES = [" but ", " that ", " under ", " with ", " and ", ", "]


def _extract_similar_to(message: str):
    match = re.search(r"(?:like|similar to)\s+([A-Za-z0-9:'\- ]+)", message, re.IGNORECASE)
    if not match:
        return None

    title = match.group(1).strip(" .!?")
    lower_title = title.lower()

    cut_at = len(title)
    for phrase in _STOP_PHRASES:
        pos = lower_title.find(phrase)
        if pos != -1:
            cut_at = min(cut_at, pos)

    return title[:cut_at].strip(" .!?")


def _extract_mood(lower_message: str):
    for mood, keywords in _MOOD_KEYWORDS.items():
        if any(kw in lower_message for kw in keywords):
            return mood
    return None


def _extract_runtime(lower_message: str):
    match = re.search(r"under\s+(\d+)\s*(?:min|minutes)", lower_message)
    if match:
        return int(match.group(1))

    match = re.search(r"under\s+(\d+)\s*hours?", lower_message)
    if match:
        return int(match.group(1)) * 60

    if "under 2 hours" in lower_message:
        return 120

    return None
