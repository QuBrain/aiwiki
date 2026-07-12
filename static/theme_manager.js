(function (global) {

  var DEFAULT_CONFIG = {

    storageKey: "aiwiki_theme",

    themes: ["light", "dark"],

    defaultTheme: "light",

    layoutStorageKey: "aiwiki_layout",

    layoutWidths: ["normal", "wide"],

    defaultLayoutWidth: "normal",

    transition: { duration: "0.25s", duration_ms: 250, easing: "ease" },

  };



  function loadConfig() {

    var meta = document.querySelector('meta[name="aiwiki-theme-config"]');

    if (!meta) return DEFAULT_CONFIG;

    try {

      return Object.assign({}, DEFAULT_CONFIG, JSON.parse(meta.getAttribute("content") || "{}"));

    } catch (err) {

      return DEFAULT_CONFIG;

    }

  }



  var config = loadConfig();

  var switchTimer = null;



  function transitionMs() {

    return (config.transition && config.transition.duration_ms) || 250;

  }



  function prefersReducedMotion() {

    return global.matchMedia && global.matchMedia("(prefers-reduced-motion: reduce)").matches;

  }



  function normalizeTheme(name) {

    return config.themes.indexOf(name) !== -1 ? name : config.defaultTheme;

  }



  function normalizeLayout(name) {

    return config.layoutWidths.indexOf(name) !== -1 ? name : config.defaultLayoutWidth;

  }



  function resolveTheme() {

    try {

      var stored = localStorage.getItem(config.storageKey);

      if (stored && config.themes.indexOf(stored) !== -1) return stored;

    } catch (err) {}

    if (global.matchMedia && global.matchMedia("(prefers-color-scheme: dark)").matches) {

      return "dark";

    }

    return config.defaultTheme;

  }



  function resolveLayout() {

    try {

      var stored = localStorage.getItem(config.layoutStorageKey);

      if (stored && config.layoutWidths.indexOf(stored) !== -1) return stored;

    } catch (err) {}

    return config.defaultLayoutWidth;

  }



  function commitTheme(name) {

    var normalized = normalizeTheme(name);

    document.documentElement.setAttribute("data-theme", normalized);

    return normalized;

  }



  function commitLayout(name) {

    var normalized = normalizeLayout(name);

    document.documentElement.setAttribute("data-layout", normalized);

    return normalized;

  }



  function endThemeSwitch() {

    document.documentElement.classList.remove("theme-switching");

    switchTimer = null;

  }



  function applyTheme(name, options) {

    options = options || {};

    var animate = options.animate !== false;

    var normalized = normalizeTheme(name);



    if (!animate || prefersReducedMotion()) {

      if (switchTimer) {

        global.clearTimeout(switchTimer);

        endThemeSwitch();

      }

      return commitTheme(normalized);

    }



    function runSwitch() {

      if (typeof document.startViewTransition === "function") {

        document.startViewTransition(function () {

          commitTheme(normalized);

        });

        return normalized;

      }



      var root = document.documentElement;

      root.classList.add("theme-switching");

      commitTheme(normalized);

      if (switchTimer) global.clearTimeout(switchTimer);

      switchTimer = global.setTimeout(endThemeSwitch, transitionMs());

      return normalized;

    }



    return runSwitch();

  }



  function applyLayout(name) {

    return commitLayout(normalizeLayout(name));

  }



  function currentTheme() {

    var active = document.documentElement.getAttribute("data-theme");

    return active === "dark" ? "dark" : "light";

  }



  function currentLayout() {

    var active = document.documentElement.getAttribute("data-layout");

    return active === "wide" ? "wide" : "normal";

  }



  function toggleTheme() {

    var next = currentTheme() === "dark" ? "light" : "dark";

    applyTheme(next, { animate: true });

    try {

      localStorage.setItem(config.storageKey, next);

    } catch (err) {}

    return next;

  }



  function toggleLayout() {

    var next = currentLayout() === "wide" ? "normal" : "wide";

    applyLayout(next);

    try {

      localStorage.setItem(config.layoutStorageKey, next);

    } catch (err) {}

    return next;

  }



  function initThemeToggle() {

    var toggle = document.getElementById("theme-toggle");

    if (!toggle) return;



    if (global.lucide) {

      global.lucide.createIcons(toggle);

    }



    function updateToggleState() {

      var isDark = currentTheme() === "dark";

      toggle.setAttribute("aria-pressed", isDark ? "true" : "false");

      toggle.setAttribute("aria-label", isDark ? "Switch to light mode" : "Switch to dark mode");

    }



    toggle.addEventListener("click", function () {

      toggleTheme();

      toggle.classList.remove("is-animating");

      void toggle.offsetWidth;

      toggle.classList.add("is-animating");

      updateToggleState();

    });



    toggle.addEventListener("animationend", function () {

      toggle.classList.remove("is-animating");

    });



    updateToggleState();

  }



  function initLayoutToggle() {

    var toggle = document.getElementById("layout-toggle");

    if (!toggle) return;



    if (global.lucide) {

      global.lucide.createIcons(toggle);

    }



    function updateToggleState() {

      var isWide = currentLayout() === "wide";

      toggle.setAttribute("aria-pressed", isWide ? "true" : "false");

      toggle.setAttribute(

        "aria-label",

        isWide ? "Switch to normal layout" : "Switch to wide layout"

      );

      toggle.setAttribute("title", isWide ? "Normal layout" : "Wide layout");

    }



    toggle.addEventListener("click", function () {

      toggleLayout();

      toggle.classList.remove("is-animating");

      void toggle.offsetWidth;

      toggle.classList.add("is-animating");

      updateToggleState();

    });



    toggle.addEventListener("animationend", function () {

      toggle.classList.remove("is-animating");

    });



    updateToggleState();

  }



  function initToggles() {

    initLayoutToggle();

    initThemeToggle();

  }



  applyTheme(resolveTheme(), { animate: false });

  applyLayout(resolveLayout());



  if (document.readyState === "loading") {

    document.addEventListener("DOMContentLoaded", initToggles);

  } else {

    initToggles();

  }



  global.AiwikiTheme = {

    config: config,

    resolveTheme: resolveTheme,

    applyTheme: applyTheme,

    currentTheme: currentTheme,

    toggleTheme: toggleTheme,

    resolveLayout: resolveLayout,

    applyLayout: applyLayout,

    currentLayout: currentLayout,

    toggleLayout: toggleLayout,

  };

})(window);

