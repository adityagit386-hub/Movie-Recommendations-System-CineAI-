/**
 * primevideo.js
 * Detects the title of the movie/show currently open on primevideo.com.
 */

(function () {
  const PLATFORM = "primevideo";

  function trySelectors() {
    const selectors = [
      '[data-automation-id="title"]',
      ".dv-node-dp-title h1",
      "h1.av-tv-title",
      ".atvwebplayersdk-title-text"
    ];

    for (const sel of selectors) {
      const el = document.querySelector(sel);
      if (el && el.textContent.trim().length > 1) {
        CineAIExtractor.sendTitle(el.textContent, { platform: PLATFORM });
        return true;
      }
    }
    return false;
  }

  setInterval(trySelectors, 3000);
  CineAIExtractor.observeTitleTag(PLATFORM);
})();
