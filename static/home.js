(function () {
  var toggle = document.getElementById("home-portal-toggle");
  var panel = document.getElementById("home-about-panel");
  if (!toggle || !panel) return;

  toggle.addEventListener("click", function () {
    var opening = panel.hidden;
    panel.hidden = !opening;
    toggle.setAttribute("aria-expanded", opening ? "true" : "false");
    toggle.textContent = opening ? "Hide" : "About AIWiki";
    if (opening) {
      panel.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  });
})();
