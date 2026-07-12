(function () {
  var toc = document.getElementById("mw-toc");
  if (!toc) return;

  var toggle = toc.querySelector(".mw-toc-toggle");
  var list = document.getElementById("mw-toc-list");
  if (!toggle || !list) return;

  toggle.addEventListener("click", function () {
    var collapsed = toc.classList.toggle("mw-toc-collapsed");
    toggle.textContent = collapsed ? "show" : "hide";
    toggle.setAttribute("aria-expanded", collapsed ? "false" : "true");
  });
})();
