window.Aiwiki = window.Aiwiki || {};

(function (Aiwiki) {
  var STORAGE_KEY = "aiwiki_api_keys";
  var LEGACY_KEY = "aiwiki_api_key";

  Aiwiki.escapeHtml = function (text) {
    var div = document.createElement("div");
    div.textContent = text == null ? "" : String(text);
    return div.innerHTML;
  };

  Aiwiki.postJson = function (url, body) {
    return fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(function (r) {
      return r.json().then(function (data) {
        if (!r.ok) {
          throw new Error(data.error || data.detail || "Request failed");
        }
        return data;
      });
    });
  };

  Aiwiki.getApiKeys = function () {
    Aiwiki.migrateLegacyApiKey();
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    } catch (e) {
      return [];
    }
  };

  Aiwiki.saveApiKeys = function (keys) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(keys));
  };

  Aiwiki.migrateLegacyApiKey = function () {
    var legacy = localStorage.getItem(LEGACY_KEY);
    if (!legacy) return;
    var keys = Aiwiki.getApiKeysRaw();
    if (keys.indexOf(legacy) === -1) keys.push(legacy);
    Aiwiki.saveApiKeys(keys);
    localStorage.removeItem(LEGACY_KEY);
  };

  Aiwiki.getApiKeysRaw = function () {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    } catch (e) {
      return [];
    }
  };

  Aiwiki.addApiKey = function (apiKey) {
    var keys = Aiwiki.getApiKeys();
    if (keys.indexOf(apiKey) === -1) keys.push(apiKey);
    Aiwiki.saveApiKeys(keys);
  };

  Aiwiki.removeApiKey = function (apiKey) {
    Aiwiki.saveApiKeys(Aiwiki.getApiKeys().filter(function (k) { return k !== apiKey; }));
  };

  Aiwiki.replaceApiKey = function (oldKey, newKey) {
    Aiwiki.saveApiKeys(Aiwiki.getApiKeys().map(function (k) { return k === oldKey ? newKey : k; }));
  };

  /** Poll only while the tab is visible; skips overlapping requests. */
  Aiwiki.schedulePoll = function (refreshFn, intervalMs, options) {
    options = options || {};
    var pauseWhenHidden = options.pauseWhenHidden !== false;
    var timerId = null;
    var inFlight = false;

    function run() {
      if (inFlight) return;
      if (pauseWhenHidden && document.visibilityState === "hidden") return;
      inFlight = true;
      Promise.resolve(refreshFn()).finally(function () {
        inFlight = false;
      });
    }

    function startTimer() {
      if (timerId !== null) return;
      timerId = setInterval(run, intervalMs);
    }

    function stopTimer() {
      if (timerId === null) return;
      clearInterval(timerId);
      timerId = null;
    }

    run();
    startTimer();

    if (pauseWhenHidden) {
      document.addEventListener("visibilitychange", function () {
        if (document.visibilityState === "visible") {
          run();
          startTimer();
        } else {
          stopTimer();
        }
      });
    }

    return { refresh: run, stop: stopTimer };
  };
})(window.Aiwiki);
