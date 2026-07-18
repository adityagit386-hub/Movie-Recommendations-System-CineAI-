/**
 * background.js (Manifest V3 service worker)
 * Receives MOVIE_DETECTED messages from content scripts, stores the
 * current movie + a rolling watch history in chrome.storage.local,
 * and lights up the extension badge so the user knows a recommendation
 * is ready to view.
 */

const HISTORY_LIMIT = 50;

chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.set({
    currentMovie: null,
    searchHistory: [],
    darkMode: false
  });
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "MOVIE_DETECTED") {
    handleMovieDetected(message.payload);
    sendResponse({ ok: true });
  }
  return true; // keep the message channel open for async sendResponse
});

async function handleMovieDetected(payload) {
  const { currentMovie, searchHistory = [] } = await chrome.storage.local.get([
    "currentMovie",
    "searchHistory"
  ]);

  if (currentMovie && currentMovie.title === payload.title) return;

  const updatedHistory = [payload, ...searchHistory.filter((h) => h.title !== payload.title)].slice(
    0,
    HISTORY_LIMIT
  );

  await chrome.storage.local.set({
    currentMovie: payload,
    searchHistory: updatedHistory
  });

  chrome.action.setBadgeText({ text: "AI" });
  chrome.action.setBadgeBackgroundColor({ color: "#E0A93E" });
}
