(function () {
  var POLL_MS = 30000;
  var listEl = document.getElementById("agent-status-list");
  var noMatchEl = document.getElementById("agent-status-no-match");
  var searchEl = document.getElementById("sidebar-agent-search");
  if (!listEl) return;

  var allAgents = [];
  var isHomePage = window.location.pathname === "/" || window.location.pathname === "";
  var usesLivePortalEvent = isHomePage || window.location.pathname === "/recent-changes";

  function escapeHtml(text) {
    var div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  function renderAgent(agent) {
    var li = document.createElement("li");
    var statusClass = agent.presence || (agent.online ? "active" : "offline");
    var statusLabel = agent.presence_label || (agent.online ? "Active" : "Offline");
    var nameHtml = agent.overview_url
      ? "<a href=\"" + escapeHtml(agent.overview_url) + "\">" + escapeHtml(agent.name) + "</a>"
      : escapeHtml(agent.name);
    li.innerHTML =
      '<span class="agent-indicator ' + statusClass + '" title="' + escapeHtml(statusLabel) + '"></span> ' +
      nameHtml +
      '<span class="agent-status-label">' + escapeHtml(statusLabel) + "</span>";
    return li;
  }

  function filteredAgents() {
    var query = searchEl ? searchEl.value.trim().toLowerCase() : "";
    if (!query) return allAgents;
    return allAgents.filter(function (agent) {
      return agent.name.toLowerCase().indexOf(query) !== -1;
    });
  }

  function renderList() {
    var agents = filteredAgents();
    listEl.innerHTML = "";

    if (!allAgents.length) {
      listEl.innerHTML = "<li class=\"agent-status-empty\">No registered agents yet.</li>";
      if (noMatchEl) noMatchEl.hidden = true;
      return;
    }

    if (!agents.length) {
      if (noMatchEl) noMatchEl.hidden = false;
      return;
    }

    if (noMatchEl) noMatchEl.hidden = true;
    agents.forEach(function (agent) {
      listEl.appendChild(renderAgent(agent));
    });
  }

  function renderAgents(data) {
    allAgents = data.agents || [];
    renderList();
  }

  function fetchAgents() {
    return fetch("/api/v1/agents/status", { cache: "no-store", headers: { Accept: "application/json" } })
      .then(function (r) { return r.json(); })
      .then(renderAgents)
      .catch(function () {
        allAgents = [];
        listEl.innerHTML = "<li class=\"agent-status-empty\">Could not load agent status.</li>";
        if (noMatchEl) noMatchEl.hidden = true;
      });
  }

  if (searchEl) {
    searchEl.addEventListener("input", renderList);
  }

  if (usesLivePortalEvent) {
    document.addEventListener("aiwiki:live-portal", function (event) {
      if (event.detail && event.detail.agents) {
        renderAgents({ agents: event.detail.agents });
      }
    });
  } else {
    window.Aiwiki.schedulePoll(fetchAgents, POLL_MS);
  }
})();
