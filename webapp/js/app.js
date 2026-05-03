/* 主入口：Tab 切换 + 全局 toast */

(function () {
  const tabs = document.querySelectorAll(".tab");
  const panels = {
    keywords: document.getElementById("panel-keywords"),
    platforms: document.getElementById("panel-platforms"),
    api: document.getElementById("panel-api"),
    crm: document.getElementById("panel-crm"),
    templates: document.getElementById("panel-templates"),
    ai: document.getElementById("panel-ai"),
  };

  function activate(name) {
    tabs.forEach((t) => t.classList.toggle("active", t.dataset.tab === name));
    Object.entries(panels).forEach(([k, p]) => p.classList.toggle("hidden", k !== name));
    history.replaceState(null, "", "#" + name);
  }

  tabs.forEach((t) => t.addEventListener("click", () => activate(t.dataset.tab)));
  document.addEventListener("click", (e) => {
    const j = e.target.closest("[data-jump]");
    if (j) {
      e.preventDefault();
      activate(j.dataset.jump);
    }
  });

  const initial = (location.hash || "#keywords").slice(1);
  if (panels[initial]) activate(initial);

  /* 全局 toast */
  const toastEl = document.getElementById("toast");
  let toastTimer = null;
  window.toast = function (msg) {
    toastEl.textContent = msg;
    toastEl.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toastEl.classList.remove("show"), 1800);
  };
})();
