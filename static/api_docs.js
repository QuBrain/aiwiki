(function () {
  document.querySelectorAll(".code-panel-copy").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var panel = btn.closest(".code-panel");
      if (!panel) return;
      var codeEl = panel.querySelector(".code-panel-body, .codehilite pre");
      if (!codeEl) return;
      var text = codeEl.textContent || "";
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(function () {
          btn.textContent = "Copied";
          setTimeout(function () { btn.textContent = "Copy"; }, 1500);
        });
      }
    });
  });

  var navLinks = document.querySelectorAll(".api-docs-nav a");
  if (!navLinks.length) return;

  var sections = [];
  navLinks.forEach(function (link) {
    var id = (link.getAttribute("href") || "").replace("#", "");
    if (!id) return;
    var section = document.getElementById(id);
    if (section) sections.push({ link: link, section: section });
  });

  function updateActive() {
    var scrollY = window.scrollY + 120;
    var current = sections[0];
    sections.forEach(function (item) {
      if (item.section.offsetTop <= scrollY) current = item;
    });
    navLinks.forEach(function (link) { link.classList.remove("active"); });
    if (current) current.link.classList.add("active");
  }

  window.addEventListener("scroll", updateActive, { passive: true });
  updateActive();
})();
