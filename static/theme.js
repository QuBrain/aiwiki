(function () {
  var KEY = "aiwiki_theme";
  var toggle = document.getElementById("theme-toggle");
  if (!toggle) return;

  if (window.lucide) {
    window.lucide.createIcons(toggle);
  }

  function currentTheme() {
    return document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";
  }

  function updateToggleState() {
    var isDark = currentTheme() === "dark";
    toggle.setAttribute("aria-pressed", isDark ? "true" : "false");
    toggle.setAttribute("aria-label", isDark ? "Switch to light mode" : "Switch to dark mode");
  }

  toggle.addEventListener("click", function () {
    var next = currentTheme() === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem(KEY, next);
    toggle.classList.remove("is-animating");
    void toggle.offsetWidth;
    toggle.classList.add("is-animating");
    updateToggleState();
  });

  toggle.addEventListener("animationend", function () {
    toggle.classList.remove("is-animating");
  });

  updateToggleState();
})();
