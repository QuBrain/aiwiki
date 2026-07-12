(function () {
  var KEY = "aiwiki_theme";
  var stored = localStorage.getItem(KEY);
  var theme = stored === "dark" || stored === "light" ? stored : null;
  if (!theme) {
    theme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }
  document.documentElement.setAttribute("data-theme", theme);
})();
