/**
 * extractor.js
 * Shared helpers used by every platform-specific content script.
 * Responsible for: watching the DOM for title changes and pushing
 * the detected title to the background service worker.
 */

const CineAIExtractor = (() => {
  let lastSentTitle = null;

  function cleanTitle(raw) {
    if (!raw) return null;
    return raw
      .replace(/\s*[-|]\s*Netflix.*$/i, "")
      .replace(/\s*[-|]\s*Prime Video.*$/i, "")
      .replace(/\s*[-|]\s*YouTube.*$/i, "")
      .replace(/\(\d{4}\)\s*$/, "")
      .trim();
  }

  function sendTitle(title, meta = {}) {
    const clean = cleanTitle(title);
    if (!clean || clean === lastSentTitle) return;
    lastSentTitle = clean;

    chrome.runtime.sendMessage({
      type: "MOVIE_DETECTED",
      payload: {
        title: clean,
        platform: meta.platform || "unknown",
        url: window.location.href,
        detectedAt: Date.now()
      }
    });
  }

  function observeTitleTag(platform) {
    sendTitle(document.title, { platform });

    const observer = new MutationObserver(() => {
      sendTitle(document.title, { platform });
    });

    const titleEl = document.querySelector("title");
    if (titleEl) {
      observer.observe(titleEl, { childList: true, subtree: true, characterData: true });
    }

    // SPA route changes don't always trigger a mutation on <title>,
    // so also poll gently as a fallback.
    setInterval(() => sendTitle(document.title, { platform }), 4000);
  }

  return { sendTitle, cleanTitle, observeTitleTag };
})();
