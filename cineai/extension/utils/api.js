/**
 * api.js
 * Thin wrapper around fetch() for talking to the CineAI FastAPI backend.
 * Change BASE_URL when you deploy the backend somewhere other than localhost.
 */

const CineAIConfig = {
  BASE_URL: "http://localhost:8000"
};

async function apiRequest(path, { method = "GET", body = null } = {}) {
  const res = await fetch(`${CineAIConfig.BASE_URL}${path}`, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : null
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${method} ${path} failed: ${res.status} ${text}`);
  }
  return res.json();
}

const CineAIApi = {
  recommendByTitle: (title, { language = null, mood = null, genre = null } = {}) =>
    apiRequest("/recommend", { method: "POST", body: { title, language, mood, genre } }),

  recommendByGenre: (genre) => apiRequest(`/recommend/genre/${encodeURIComponent(genre)}`),

  recommendByMood: (mood) => apiRequest(`/recommend/mood/${encodeURIComponent(mood)}`),

  trending: () => apiRequest("/trending"),

  chatbotQuery: (message, history = []) =>
    apiRequest("/chatbot/query", { method: "POST", body: { message, history } }),

  getWatchlist: (userId = "local_user") => apiRequest(`/watchlist/${userId}`),

  addToWatchlist: (userId, movieTitle) =>
    apiRequest(`/watchlist/${userId}`, { method: "POST", body: { movie_title: movieTitle } }),

  removeFromWatchlist: (userId, movieTitle) =>
    apiRequest(`/watchlist/${userId}/${encodeURIComponent(movieTitle)}`, { method: "DELETE" }),

  addFavorite: (userId, movieTitle) =>
    apiRequest(`/watchlist/${userId}/favorite`, { method: "POST", body: { movie_title: movieTitle } }),

  getHistory: (userId = "local_user") => apiRequest(`/watchlist/${userId}/history`)
};
