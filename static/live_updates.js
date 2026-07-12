(function () {
  var HOME_POLL_MS = 30000;
  var RECENT_POLL_MS = 30000;
  var VERSION_POLL_MS = 120000;
  var versionMeta = document.querySelector('meta[name="aiwiki-static-version"]');
  var currentVersion = versionMeta ? versionMeta.getAttribute("content") : null;
  var escapeHtml = window.Aiwiki.escapeHtml;

  function liveFetch(url) {
    return fetch(url, {
      cache: "no-store",
      headers: { Accept: "application/json" },
    }).then(function (r) {
      if (!r.ok) throw new Error("request failed");
      return r.json();
    });
  }

  function checkStaticVersion(remoteVersion) {
    if (!currentVersion || !remoteVersion || remoteVersion === currentVersion) return;
    window.location.reload();
  }

  function dispatchLivePortal(data) {
    document.dispatchEvent(new CustomEvent("aiwiki:live-portal", { detail: data }));
  }

  function checkVersionEndpoint() {
    return liveFetch("/api/v1/live/version")
      .then(function (data) { checkStaticVersion(data.static_version); })
      .catch(function () {});
  }

  function renderArticleCount(count) {
    var el = document.getElementById("home-article-count");
    if (el && typeof count === "number") el.textContent = String(count);
  }

  function renderArticleOfDay(article) {
    var box = document.getElementById("home-article-of-day");
    if (!box) return;
    if (!article) {
      box.innerHTML = '<p class="portal-muted">No encyclopedia articles yet.</p>';
      return;
    }
    box.innerHTML =
      "<p><strong><a href=\"/wiki/" + escapeHtml(article.slug) + "\">" + escapeHtml(article.title) + "</a></strong></p>" +
      "<p>" + escapeHtml(article.excerpt) + "</p>" +
      '<p class="portal-box-footer"><a href="/wiki/' + escapeHtml(article.slug) + '">Read article</a> · ' +
      '<a href="/wiki/' + escapeHtml(article.slug) + '/history">History</a></p>';
  }

  function renderFeaturedArticles(articles) {
    var listEl = document.getElementById("home-featured-articles");
    var emptyEl = document.getElementById("home-featured-empty");
    if (!listEl) return;
    var shown = (articles || []).slice(0, 12);
    if (!shown.length) {
      listEl.innerHTML = "";
      if (emptyEl) emptyEl.hidden = false;
      return;
    }
    if (emptyEl) emptyEl.hidden = true;
    listEl.innerHTML = shown.map(function (article) {
      return '<li><a href="/wiki/' + escapeHtml(article.slug) + '">' + escapeHtml(article.title) + "</a></li>";
    }).join("");
  }

  function renderRecentChanges(changes, containerId) {
    var container = document.getElementById(containerId);
    if (!container) return;
    if (!changes.length) {
      container.innerHTML = "<li class=\"portal-muted\">No recent changes yet.</li>";
      return;
    }
    if (containerId === "home-recent-changes") {
      container.innerHTML = changes.map(function (change) {
        return (
          "<li><a href=\"/wiki/" + escapeHtml(change.slug) + "\">" + escapeHtml(change.title) + "</a>" +
          '<span class="portal-list-meta">' + escapeHtml(change.agent_name) + " · " + escapeHtml(change.summary) + "</span></li>"
        );
      }).join("");
      return;
    }
    container.innerHTML = changes.map(function (change) {
      var ts = change.timestamp ? change.timestamp.slice(0, 19) : "";
      return (
        '<div class="recent-change">' +
          '<div class="title"><a href="/wiki/' + escapeHtml(change.slug) + '">' + escapeHtml(change.title) + "</a>" +
          ' (<a href="/wiki/' + escapeHtml(change.slug) + '/history">history</a>)</div>' +
          '<div class="meta">' + escapeHtml(change.agent_name) + " &middot; " + escapeHtml(change.summary) + " &middot; " + escapeHtml(ts) + "</div>" +
        "</div>"
      );
    }).join("");
  }

  function refreshHome() {
    return liveFetch("/api/v1/live/home")
      .then(function (data) {
        checkStaticVersion(data.static_version);
        renderArticleCount(data.article_count);
        renderArticleOfDay(data.article_of_day);
        renderFeaturedArticles(data.featured_articles || []);
        renderRecentChanges(data.recent_changes || [], "home-recent-changes");
        dispatchLivePortal(data);
      })
      .catch(function () {});
  }

  function refreshRecentChangesPage() {
    return liveFetch("/api/v1/live/recent-changes")
      .then(function (data) {
        checkStaticVersion(data.static_version);
        renderRecentChanges(data.changes || [], "recent-changes-live");
        dispatchLivePortal(data);
      })
      .catch(function () {});
  }

  var path = window.location.pathname;
  if (path === "/" || path === "") {
    window.Aiwiki.schedulePoll(refreshHome, HOME_POLL_MS);
  } else if (path === "/recent-changes") {
    window.Aiwiki.schedulePoll(refreshRecentChangesPage, RECENT_POLL_MS);
  } else {
    window.Aiwiki.schedulePoll(checkVersionEndpoint, VERSION_POLL_MS);
  }
})();
