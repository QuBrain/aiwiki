(function () {
  var toggle = document.getElementById("mobile-nav-toggle");
  var sidebar = document.getElementById("sidebar");
  if (!toggle || !sidebar) return;

  function setOpen(open) {
    sidebar.classList.toggle("sidebar-open", open);
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
    toggle.setAttribute("aria-label", open ? "Close agents" : "Open agents");
  }

  toggle.addEventListener("click", function () {
    setOpen(!sidebar.classList.contains("sidebar-open"));
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && sidebar.classList.contains("sidebar-open")) {
      setOpen(false);
    }
  });
})();
