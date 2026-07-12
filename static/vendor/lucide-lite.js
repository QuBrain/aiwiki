/**
 * Minimal Lucide subset (sun, moon) — https://lucide.dev (ISC)
 */
(function (global) {
  var ICONS = {
    sun:
      '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
      '<circle cx="12" cy="12" r="4"></circle>' +
      '<path d="M12 2v2"></path><path d="M12 20v2"></path>' +
      '<path d="m4.93 4.93 1.41 1.41"></path><path d="m17.66 17.66 1.41 1.41"></path>' +
      '<path d="M2 12h2"></path><path d="M20 12h2"></path>' +
      '<path d="m6.34 17.66-1.41 1.41"></path><path d="m19.07 4.93-1.41 1.41"></path>' +
      "</svg>",
    moon:
      '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
      '<path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"></path>' +
      "</svg>",
  };

  function createIcons(root) {
    var scope = root || document;
    scope.querySelectorAll("[data-lucide]").forEach(function (el) {
      var name = el.getAttribute("data-lucide");
      var markup = ICONS[name];
      if (!markup) return;
      el.innerHTML = markup;
      var svg = el.querySelector("svg");
      if (svg) {
        svg.setAttribute("width", "22");
        svg.setAttribute("height", "22");
      }
    });
  }

  global.lucide = { createIcons: createIcons };
})(window);
