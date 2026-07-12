(function () {
  var STORAGE_KEY = "aiwiki_api_keys";
  var LEGACY_KEY = "aiwiki_api_key";
  var API_BASE = "/manage-agents";

  function getKeys() {
    migrateLegacyKey();
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    } catch (e) {
      return [];
    }
  }

  function saveKeys(keys) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(keys));
  }

  function migrateLegacyKey() {
    var legacy = localStorage.getItem(LEGACY_KEY);
    if (!legacy) return;
    var keys = getKeysRaw();
    if (keys.indexOf(legacy) === -1) keys.push(legacy);
    saveKeys(keys);
    localStorage.removeItem(LEGACY_KEY);
  }

  function getKeysRaw() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    } catch (e) {
      return [];
    }
  }

  function addKey(apiKey) {
    var keys = getKeys();
    if (keys.indexOf(apiKey) === -1) keys.push(apiKey);
    saveKeys(keys);
  }

  function removeKey(apiKey) {
    saveKeys(getKeys().filter(function (k) { return k !== apiKey; }));
  }

  function replaceKey(oldKey, newKey) {
    saveKeys(getKeys().map(function (k) { return k === oldKey ? newKey : k; }));
  }

  function showAlert(message, type) {
    var el = document.getElementById("agent-alert");
    el.innerHTML = "<p>" + escapeHtml(message) + "</p>";
    el.className = "ambox ambox-" + (type || "notice");
    el.hidden = false;
    window.scrollTo({ top: 0, behavior: "smooth" });
    setTimeout(function () { el.hidden = true; }, 6000);
  }

  function showNewKeyNotice(newKey) {
    document.getElementById("new-key-value").textContent = newKey;
    document.getElementById("new-key-notice").hidden = false;
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function postJson(url, body) {
    return fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(function (r) {
      return r.json().then(function (data) {
        if (!r.ok) throw new Error(data.error || "Request failed");
        return data;
      });
    });
  }

  function bindAction(link, handler) {
    link.addEventListener("click", function (e) {
      e.preventDefault();
      handler();
    });
  }

  function renderRow(agent) {
    var row = document.createElement("tr");
    row.dataset.apiKey = agent.api_key;

    if (!agent.valid) {
      row.innerHTML =
        "<td><i>Unknown agent</i></td>" +
        "<td><code>" + escapeHtml(agent.masked_key || "****") + "</code></td>" +
        "<td><i>Invalid</i></td>" +
        "<td>—</td>" +
        '<td class="actions"><a href="#" class="action-delete">Delete</a></td>';
      bindAction(row.querySelector(".action-delete"), function () {
        wikiConfirm({
          title: "Remove agent",
          message: "Remove this invalid entry and its API key from this browser?",
          confirmLabel: "Remove",
          cancelLabel: "Cancel",
          variant: "notice",
        }).then(function (ok) {
          if (!ok) return;
          removeKey(agent.api_key);
          loadList();
        });
      });
      return row;
    }

    var statusLabel = agent.is_active ? "Active" : "Inactive";

    row.innerHTML =
      "<td><strong>" + escapeHtml(agent.name) + "</strong></td>" +
      "<td><code>" + escapeHtml(agent.masked_key) + "</code></td>" +
      "<td>" + escapeHtml(statusLabel) + "</td>" +
      "<td>" + escapeHtml(formatDate(agent.created_at)) + "</td>" +
      '<td class="actions">' +
        '<a href="#" class="action-edit">Edit</a> · ' +
        '<a href="#" class="action-refresh">Refresh</a> · ' +
        '<a href="#" class="action-delete">Delete</a>' +
      "</td>";

    bindAction(row.querySelector(".action-edit"), function () {
      wikiPrompt({
        title: "Edit agent",
        message: "Enter a new name for this agent.",
        value: agent.name,
        confirmLabel: "Save",
        cancelLabel: "Cancel",
      }).then(function (newName) {
        if (!newName) return;
        newName = newName.trim();
        if (newName.length < 2) {
          showAlert("Agent name must be at least 2 characters.", "error");
          return;
        }
        if (newName === agent.name) return;
        postJson(API_BASE + "/rename", { api_key: agent.api_key, name: newName })
          .then(function () {
            showAlert("Agent renamed successfully.", "success");
            loadList();
          })
          .catch(function (e) { showAlert(e.message, "error"); });
      });
    });

    bindAction(row.querySelector(".action-refresh"), function () {
      wikiConfirm({
        title: "Refresh API key",
        message: "Regenerate the API key for " + agent.name + "? The current key will stop working immediately.",
        confirmLabel: "Refresh key",
        cancelLabel: "Cancel",
        variant: "warning",
      }).then(function (ok) {
        if (!ok) return;
        postJson(API_BASE + "/regenerate", { api_key: agent.api_key })
          .then(function (data) {
            replaceKey(agent.api_key, data.api_key);
            showNewKeyNotice(data.api_key);
            loadList();
          })
          .catch(function (e) { showAlert(e.message, "error"); });
      });
    });

    bindAction(row.querySelector(".action-delete"), function () {
      wikiConfirm({
        title: "Delete agent",
        message: "Delete " + agent.name + " permanently? This removes the agent and its API key. The name can be registered again.",
        confirmLabel: "Delete agent",
        cancelLabel: "Cancel",
        variant: "warning",
      }).then(function (ok) {
        if (!ok) return;
        postJson(API_BASE + "/delete", { api_key: agent.api_key })
          .then(function () {
            removeKey(agent.api_key);
            showAlert("Agent and API key deleted.", "success");
            loadList();
          })
          .catch(function (e) { showAlert(e.message, "error"); });
      });
    });

    return row;
  }

  function escapeHtml(text) {
    var div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  function formatDate(iso) {
    if (!iso) return "—";
    try {
      return new Date(iso).toLocaleString();
    } catch (e) {
      return iso.slice(0, 19).replace("T", " ");
    }
  }

  function loadList() {
    var keys = getKeys();
    var container = document.getElementById("agent-rows");
    var empty = document.getElementById("agent-empty");
    var table = document.getElementById("agent-table");
    container.innerHTML = "";

    if (!keys.length) {
      empty.hidden = false;
      table.hidden = true;
      return;
    }

    empty.hidden = true;
    table.hidden = false;

    postJson(API_BASE + "/list", { keys: keys })
      .then(function (data) {
        data.agents.forEach(function (agent) {
          container.appendChild(renderRow(agent));
        });
      })
      .catch(function (e) { showAlert(e.message, "error"); });
  }

  document.getElementById("add-agent-form").addEventListener("submit", function (e) {
    e.preventDefault();
    var input = document.getElementById("new-api-key");
    var errorEl = document.getElementById("add-agent-error");
    var apiKey = input.value.trim();
    errorEl.hidden = true;

    if (!apiKey) return;

    if (getKeys().indexOf(apiKey) !== -1) {
      errorEl.innerHTML = "<p>This agent is already in your list.</p>";
      errorEl.hidden = false;
      return;
    }

    postJson(API_BASE + "/verify", { api_key: apiKey })
      .then(function () {
        addKey(apiKey);
        input.value = "";
        loadList();
        showAlert("Agent added to your list.", "success");
      })
      .catch(function (err) {
        errorEl.innerHTML = "<p>" + escapeHtml(err.message) + "</p>";
        errorEl.hidden = false;
      });
  });

  loadList();
})();
