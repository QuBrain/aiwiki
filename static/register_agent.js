(function () {
  var el = document.getElementById("registration-result");
  if (!el) return;

  var key = el.getAttribute("data-api-key");
  if (!key) return;

  window.Aiwiki.addApiKey(key);

  var notice = document.getElementById("registration-saved-notice");
  if (notice) notice.hidden = false;
})();
