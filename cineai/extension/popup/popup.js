/**
 * popup.js
 * Wires up the popup UI: tab switching, dark mode, pulling the
 * currently-detected movie from storage, requesting recommendations
 * from the FastAPI backend, and the natural-language chatbot.
 */

const els = {
  currentTitle: document.getElementById("currentTitle"),
  currentPlatform: document.getElementById("currentPlatform"),
  tabs: document.querySelectorAll(".tab"),
  panels: document.querySelectorAll(".panel"),
  recList: document.getElementById("recList"),
  watchlistList: document.getElementById("watchlistList"),
  trendingList: document.getElementById("trendingList"),
  refreshRecs: document.getElementById("refreshRecs"),
  filterGenre: document.getElementById("filterGenre"),
  filterMood: document.getElementById("filterMood"),
  filterLanguage: document.getElementById("filterLanguage"),
  filterRuntime: document.getElementById("filterRuntime"),
  darkModeToggle: document.getElementById("darkModeToggle"),
  statusBar: document.getElementById("statusBar"),
  chatLog: document.getElementById("chatLog"),
  chatForm: document.getElementById("chatForm"),
  chatInput: document.getElementById("chatInput")
};

let currentMovie = null;
let chatHistory = [];

// ---------------------------------------------------------------
// Init
// ---------------------------------------------------------------
init();

async function init() {
  await loadDarkMode();
  await loadCurrentMovie();
  wireTabs();
  wireEvents();
  await refreshRecommendations();
  setStatus("Ready");
}

function wireTabs() {
  els.tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      els.tabs.forEach((t) => t.classList.remove("active"));
      els.panels.forEach((p) => p.classList.remove("active"));
      tab.classList.add("active");
      document.getElementById(`panel-${tab.dataset.tab}`).classList.add("active");

      if (tab.dataset.tab === "watchlist") loadWatchlist();
      if (tab.dataset.tab === "trending") loadTrending();
    });
  });
}

function wireEvents() {
  els.refreshRecs.addEventListener("click", refreshRecommendations);
  els.darkModeToggle.addEventListener("click", toggleDarkMode);
  els.chatForm.addEventListener("submit", handleChatSubmit);
}

// ---------------------------------------------------------------
// Current movie
// ---------------------------------------------------------------
async function loadCurrentMovie() {
  const { currentMovie: stored } = await chrome.storage.local.get("currentMovie");
  currentMovie = stored || null;

  if (currentMovie) {
    els.currentTitle.textContent = currentMovie.title;
    els.currentPlatform.textContent = currentMovie.platform;
  } else {
    els.currentTitle.textContent = "Open Netflix, Prime Video or YouTube to get started";
    els.currentPlatform.textContent = "";
  }
}

// ---------------------------------------------------------------
// Recommendations
// ---------------------------------------------------------------
async function refreshRecommendations() {
  els.recList.innerHTML = renderLoading();
  try {
    const filters = {
      genre: els.filterGenre.value || null,
      mood: els.filterMood.value || null,
      language: els.filterLanguage.value || null
    };

    let results;
    if (currentMovie) {
      results = await CineAIApi.recommendByTitle(currentMovie.title, filters);
    } else if (filters.mood) {
      results = await CineAIApi.recommendByMood(filters.mood);
    } else if (filters.genre) {
      results = await CineAIApi.recommendByGenre(filters.genre);
    } else {
      results = await CineAIApi.trending();
    }

    renderMovieCards(els.recList, results.recommendations || results, { showActions: true });
    setStatus(`${(results.recommendations || results).length} recommendations loaded`);
  } catch (err) {
    console.error(err);
    els.recList.innerHTML = renderEmpty(
      "Couldn't reach the CineAI backend. Make sure the FastAPI server is running on localhost:8000."
    );
    setStatus("Backend unreachable");
  }
}

// ---------------------------------------------------------------
// Watchlist
// ---------------------------------------------------------------
async function loadWatchlist() {
  els.watchlistList.innerHTML = renderLoading();
  try {
    const userId = await getUserId();
    const data = await CineAIApi.getWatchlist(userId);
    if (!data.items || data.items.length === 0) {
      els.watchlistList.innerHTML = renderEmpty("Your watchlist is empty. Add movies from the For You tab.");
      return;
    }
    renderMovieCards(els.watchlistList, data.items, { showActions: false, showRemove: true });
  } catch (err) {
    console.error(err);
    els.watchlistList.innerHTML = renderEmpty("Couldn't load your watchlist.");
  }
}

// ---------------------------------------------------------------
// Trending
// ---------------------------------------------------------------
async function loadTrending() {
  els.trendingList.innerHTML = renderLoading();
  try {
    const data = await CineAIApi.trending();
    renderMovieCards(els.trendingList, data.recommendations || data, { showActions: true });
  } catch (err) {
    console.error(err);
    els.trendingList.innerHTML = renderEmpty("Couldn't load trending titles.");
  }
}

// ---------------------------------------------------------------
// Chatbot
// ---------------------------------------------------------------
async function handleChatSubmit(e) {
  e.preventDefault();
  const message = els.chatInput.value.trim();
  if (!message) return;

  appendChatBubble("user", message);
  els.chatInput.value = "";
  chatHistory.push({ role: "user", content: message });

  const loadingBubble = appendChatBubble("assistant", "Thinking\u2026");

  try {
    const data = await CineAIApi.chatbotQuery(message, chatHistory);
    loadingBubble.textContent = data.reply;
    chatHistory.push({ role: "assistant", content: data.reply });

    if (data.recommendations && data.recommendations.length) {
      const list = document.createElement("div");
      list.className = "card-list";
      renderMovieCards(list, data.recommendations, { showActions: true });
      els.chatLog.appendChild(list);
      els.chatLog.scrollTop = els.chatLog.scrollHeight;
    }
  } catch (err) {
    console.error(err);
    loadingBubble.textContent = "Sorry, I couldn't reach the CineAI backend.";
  }
}

function appendChatBubble(role, text) {
  const bubble = document.createElement("div");
  bubble.className = `chat-bubble ${role}`;
  bubble.textContent = text;
  els.chatLog.appendChild(bubble);
  els.chatLog.scrollTop = els.chatLog.scrollHeight;
  return bubble;
}

// ---------------------------------------------------------------
// Rendering helpers
// ---------------------------------------------------------------
function renderMovieCards(container, movies, { showActions, showRemove } = {}) {
  container.innerHTML = "";
  if (!movies || movies.length === 0) {
    container.innerHTML = renderEmpty("No results yet.");
    return;
  }

  movies.forEach((movie) => {
    const card = document.createElement("div");
    card.className = "movie-card";
    card.innerHTML = `
      <div class="movie-card-top">
        <div>
          <p class="movie-title">${escapeHtml(movie.title)}</p>
          <p class="movie-meta">${escapeHtml(movie.genre || "")} \u2022 ${escapeHtml(
      movie.language || ""
    )} \u2022 ${movie.runtime ? movie.runtime + " min" : ""} \u2022 \u2605 ${movie.rating ?? "N/A"}</p>
        </div>
        ${
          movie.similarity_score != null
            ? `<span class="similarity-badge">${Math.round(movie.similarity_score * 100)}% match</span>`
            : ""
        }
      </div>
      ${movie.reason ? `<p class="reason">${escapeHtml(movie.reason)}</p>` : ""}
      <div class="card-actions"></div>
    `;

    const actions = card.querySelector(".card-actions");

    if (showActions) {
      const addBtn = document.createElement("button");
      addBtn.className = "ghost-btn";
      addBtn.textContent = "+ Watchlist";
      addBtn.addEventListener("click", () => handleAddToWatchlist(movie.title));
      actions.appendChild(addBtn);

      const favBtn = document.createElement("button");
      favBtn.className = "ghost-btn";
      favBtn.textContent = "\u2605 Favorite";
      favBtn.addEventListener("click", () => handleAddFavorite(movie.title));
      actions.appendChild(favBtn);
    }

    if (showRemove) {
      const removeBtn = document.createElement("button");
      removeBtn.className = "ghost-btn danger";
      removeBtn.textContent = "Remove";
      removeBtn.addEventListener("click", () => handleRemoveFromWatchlist(movie.title));
      actions.appendChild(removeBtn);
    }

    container.appendChild(card);
  });
}

function renderLoading() {
  return `<div class="empty-state">Loading\u2026</div>`;
}

function renderEmpty(message) {
  return `<div class="empty-state">${escapeHtml(message)}</div>`;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

// ---------------------------------------------------------------
// Watchlist actions
// ---------------------------------------------------------------
async function handleAddToWatchlist(title) {
  const userId = await getUserId();
  try {
    await CineAIApi.addToWatchlist(userId, title);
    setStatus(`Added "${title}" to watchlist`);
  } catch (err) {
    console.error(err);
    setStatus("Couldn't add to watchlist");
  }
}

async function handleAddFavorite(title) {
  const userId = await getUserId();
  try {
    await CineAIApi.addFavorite(userId, title);
    setStatus(`Added "${title}" to favorites`);
  } catch (err) {
    console.error(err);
    setStatus("Couldn't add to favorites");
  }
}

async function handleRemoveFromWatchlist(title) {
  const userId = await getUserId();
  try {
    await CineAIApi.removeFromWatchlist(userId, title);
    loadWatchlist();
  } catch (err) {
    console.error(err);
    setStatus("Couldn't remove from watchlist");
  }
}

// ---------------------------------------------------------------
// Dark mode
// ---------------------------------------------------------------
async function loadDarkMode() {
  const { darkMode } = await chrome.storage.local.get("darkMode");
  document.body.classList.toggle("light-mode", !darkMode);
  document.getElementById("darkModeIcon").textContent = darkMode ? "\u2600" : "\u263D";
}

async function toggleDarkMode() {
  const { darkMode } = await chrome.storage.local.get("darkMode");
  const next = !darkMode;
  await chrome.storage.local.set({ darkMode: next });
  document.body.classList.toggle("light-mode", !next);
  document.getElementById("darkModeIcon").textContent = next ? "\u2600" : "\u263D";
}

// ---------------------------------------------------------------
// Misc
// ---------------------------------------------------------------
async function getUserId() {
  let { userId } = await chrome.storage.local.get("userId");
  if (!userId) {
    userId = "user_" + Math.random().toString(36).slice(2, 10);
    await chrome.storage.local.set({ userId });
  }
  return userId;
}

function setStatus(text) {
  els.statusBar.textContent = text;
}
