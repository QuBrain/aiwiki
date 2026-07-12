/**
 * Wikipedia-style in-app confirmation dialog.
 * Returns a Promise that resolves to true (confirm) or false (cancel).
 */
window.wikiConfirm = function (options) {
  var opts = options || {};
  var title = opts.title || "Confirm action";
  var message = opts.message || "Are you sure?";
  var confirmLabel = opts.confirmLabel || "OK";
  var cancelLabel = opts.cancelLabel || "Cancel";
  var variant = opts.variant || "notice";

  return new Promise(function (resolve) {
    var overlay = document.getElementById("wiki-confirm-overlay");
    var titleEl = document.getElementById("wiki-confirm-title");
    var messageEl = document.getElementById("wiki-confirm-message");
    var confirmBtn = document.getElementById("wiki-confirm-ok");
    var cancelBtn = document.getElementById("wiki-confirm-cancel");
    var dialog = overlay.querySelector(".wiki-dialog");

    titleEl.textContent = title;
    messageEl.textContent = message;
    confirmBtn.textContent = confirmLabel;
    cancelBtn.textContent = cancelLabel;
    dialog.className = "wiki-dialog wiki-dialog-" + variant;

    function cleanup(result) {
      overlay.hidden = true;
      document.body.classList.remove("wiki-dialog-open");
      confirmBtn.removeEventListener("click", onConfirm);
      cancelBtn.removeEventListener("click", onCancel);
      overlay.removeEventListener("click", onOverlay);
      document.removeEventListener("keydown", onKeydown);
      resolve(result);
    }

    function onConfirm() { cleanup(true); }
    function onCancel() { cleanup(false); }
    function onOverlay(e) {
      if (e.target === overlay) cleanup(false);
    }
    function onKeydown(e) {
      if (e.key === "Escape") cleanup(false);
    }

    confirmBtn.addEventListener("click", onConfirm);
    cancelBtn.addEventListener("click", onCancel);
    overlay.addEventListener("click", onOverlay);
    document.addEventListener("keydown", onKeydown);

    overlay.hidden = false;
    document.body.classList.add("wiki-dialog-open");
    cancelBtn.focus();
  });
};

/**
 * Wikipedia-style in-app prompt dialog.
 * Returns a Promise that resolves to the input value, or null if cancelled.
 */
window.wikiPrompt = function (options) {
  var opts = options || {};
  var title = opts.title || "Edit";
  var message = opts.message || "";
  var value = opts.value || "";
  var confirmLabel = opts.confirmLabel || "OK";
  var cancelLabel = opts.cancelLabel || "Cancel";
  var variant = opts.variant || "notice";

  return new Promise(function (resolve) {
    var overlay = document.getElementById("wiki-prompt-overlay");
    var titleEl = document.getElementById("wiki-prompt-title");
    var messageEl = document.getElementById("wiki-prompt-message");
    var inputEl = document.getElementById("wiki-prompt-input");
    var confirmBtn = document.getElementById("wiki-prompt-ok");
    var cancelBtn = document.getElementById("wiki-prompt-cancel");
    var dialog = overlay.querySelector(".wiki-dialog");

    titleEl.textContent = title;
    messageEl.textContent = message;
    messageEl.hidden = !message;
    inputEl.value = value;
    confirmBtn.textContent = confirmLabel;
    cancelBtn.textContent = cancelLabel;
    dialog.className = "wiki-dialog wiki-dialog-" + variant;

    function cleanup(result) {
      overlay.hidden = true;
      document.body.classList.remove("wiki-dialog-open");
      confirmBtn.removeEventListener("click", onConfirm);
      cancelBtn.removeEventListener("click", onCancel);
      overlay.removeEventListener("click", onOverlay);
      document.removeEventListener("keydown", onKeydown);
      resolve(result);
    }

    function onConfirm() { cleanup(inputEl.value); }
    function onCancel() { cleanup(null); }
    function onOverlay(e) {
      if (e.target === overlay) cleanup(null);
    }
    function onKeydown(e) {
      if (e.key === "Escape") cleanup(null);
    }

    confirmBtn.addEventListener("click", onConfirm);
    cancelBtn.addEventListener("click", onCancel);
    overlay.addEventListener("click", onOverlay);
    document.addEventListener("keydown", onKeydown);

    overlay.hidden = false;
    document.body.classList.add("wiki-dialog-open");
    inputEl.focus();
    inputEl.select();
  });
};
