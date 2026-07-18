/**
 * youtube.js
 * Detects the title of the video currently open on youtube.com.
 * Only fires on watch pages (?v=) since CineAI targets movie/show content.
 */

(function () {
  const PLATFORM = "youtube";

  function isWatchPage() {
    return window.location.pathname === "/watch";
  }

  function trySelectors() {
    if (!isWatchPage()) return false;

    const selectors = [
      "h1.ytd-watch-metadata yt-formatted-string",
      "#title h1",
      "meta[name='title']"
    ];

    for (const sel of selectors) {
      const el = document.querySelector(sel);
      if (el) {
        const text = el.getAttribute ? el.getAttribute("content") || el.textContent : el.textContent;
        if (text && text.trim().length > 1) {
          CineAIExtractor.sendTitle(text, { platform: PLATFORM });
          return true;
        }
      }
    }
    return false;
  }

  setInterval(trySelectors, 3000);
  CineAIExtractor.observeTitleTag(PLATFORM);
})();
