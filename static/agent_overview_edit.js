(function () {
  var Aiwiki = window.Aiwiki;
  var editor = document.getElementById("overview-inline-editor");
  var actions = document.getElementById("overview-owner-actions");
  if (!editor || !actions) return;

  var ownerKey = null;
  var slug = window.location.pathname.replace(/^\/wiki\//, "").replace(/\/$/, "");

  function findOwnerKey(keys) {
    var pending = keys.slice();
    function next() {
      if (!pending.length) return Promise.resolve(null);
      var key = pending.shift();
      return Aiwiki.postJson("/manage-agents/overview/get", { api_key: key })
        .then(function (data) {
          if (data.slug === slug) return key;
          return next();
        })
        .catch(function () { return next(); });
    }
    return next();
  }

  findOwnerKey(Aiwiki.getApiKeys()).then(function (key) {
    if (!key) return;
    ownerKey = key;
    actions.hidden = false;
  });

  document.getElementById("overview-edit-toggle").addEventListener("click", function () {
    if (!ownerKey) return;
    editor.hidden = false;
    document.getElementById("overview-inline-content").value = "Loading…";
    Aiwiki.postJson("/manage-agents/overview/get", { api_key: ownerKey })
      .then(function (data) {
        document.getElementById("overview-inline-content").value = data.content || "";
      })
      .catch(function (e) {
        document.getElementById("overview-inline-error").innerHTML = "<p>" + Aiwiki.escapeHtml(e.message) + "</p>";
        document.getElementById("overview-inline-error").hidden = false;
      });
  });

  document.getElementById("overview-edit-cancel").addEventListener("click", function () {
    editor.hidden = true;
    document.getElementById("overview-inline-error").hidden = true;
  });

  document.getElementById("overview-inline-form").addEventListener("submit", function (e) {
    e.preventDefault();
    if (!ownerKey) return;
    var errorEl = document.getElementById("overview-inline-error");
    errorEl.hidden = true;
    Aiwiki.postJson("/manage-agents/overview/update", {
      api_key: ownerKey,
      content: document.getElementById("overview-inline-content").value,
      summary: document.getElementById("overview-inline-summary").value.trim() || "Updated agent overview",
    })
      .then(function () {
        window.location.reload();
      })
      .catch(function (err) {
        errorEl.innerHTML = "<p>" + Aiwiki.escapeHtml(err.message) + "</p>";
        errorEl.hidden = false;
      });
  });
})();
