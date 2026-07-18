/**
 * netflix.js
 * Detects the title of the movie/show currently open on netflix.com.
 * Netflix renders everything client-side, so we fall back to a
 * handful of selectors plus the document title.
 */

(function () {
  const PLATFORM = "netflix";

  function trySelectors() {
    const selectors = [
      '[data-uia="video-title"] h4',
      '[data-uia="video-title"]',
      ".video-title h4",
      ".title-info-header h1",
      ".previewModal--player-titleTreatment-logo img[alt]"
    ];

    for (const sel of selectors) {
      const el = document.querySelector(sel);
      if (el) {
        const text = el.getAttribute("alt") || el.textContent;
        if (text && text.trim().length > 1) {
          CineAIExtractor.sendTitle(text, { platform: PLATFORM });
          return true;
        }
      }
    }
    return false;
  }

  // Poll for the player/detail selectors (they mount async after route change)
  setInterval(trySelectors, 3000);

  // Always keep the document.title watcher running as a fallback
  CineAIExtractor.observeTitleTag(PLATFORM);
})();
