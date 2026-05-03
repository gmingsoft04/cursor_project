/* 模块 1：搜索关键词渲染 + 过滤 + 点击复制；Google Dork 直跳 */

(function () {
  const grid = document.getElementById("keyword-grid");
  const searchInput = document.getElementById("kw-search");
  const tabsBox = document.getElementById("kw-tabs");
  const dorkBox = document.getElementById("dork-list");

  let activeCat = "all";

  function flatItems() {
    const list = [];
    KEYWORD_CATEGORIES.forEach((cat) => {
      cat.items.forEach((kw) =>
        list.push({ kw, catId: cat.id, catName: cat.name })
      );
    });
    return list;
  }

  function renderTabs() {
    tabsBox.innerHTML = "";
    const all = document.createElement("button");
    all.textContent = `全部 (${flatItems().length})`;
    all.dataset.cat = "all";
    tabsBox.appendChild(all);
    KEYWORD_CATEGORIES.forEach((cat) => {
      const b = document.createElement("button");
      b.textContent = `${cat.name} (${cat.items.length})`;
      b.dataset.cat = cat.id;
      tabsBox.appendChild(b);
    });
    tabsBox.addEventListener("click", (e) => {
      if (e.target.tagName !== "BUTTON") return;
      activeCat = e.target.dataset.cat;
      [...tabsBox.children].forEach((c) => c.classList.toggle("active", c === e.target));
      render();
    });
    [...tabsBox.children][0].classList.add("active");
  }

  function render() {
    const q = (searchInput.value || "").trim().toLowerCase();
    let items = flatItems();
    if (activeCat !== "all") items = items.filter((i) => i.catId === activeCat);
    if (q) items = items.filter((i) => i.kw.toLowerCase().includes(q) || i.catName.toLowerCase().includes(q));

    grid.innerHTML = "";
    if (items.length === 0) {
      grid.innerHTML = '<div class="empty-row" style="grid-column: 1 / -1;">没有匹配的关键词</div>';
      return;
    }
    items.forEach((it) => {
      const el = document.createElement("div");
      el.className = "kw-item";
      el.innerHTML = `<span>${escapeHtml(it.kw)}</span><span class="kw-cat">${escapeHtml(it.catName)}</span>`;
      el.title = "点击复制";
      el.addEventListener("click", () => {
        copyToClipboard(it.kw).then(() => toast(`已复制：${it.kw}`));
      });
      grid.appendChild(el);
    });
  }

  function renderDorks() {
    dorkBox.innerHTML = "";
    DORKS.forEach((d) => {
      const a = document.createElement("a");
      a.href = "https://www.google.com/search?q=" + encodeURIComponent(d.query);
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      a.textContent = `🔎 ${d.label}  →  ${d.query}`;
      dorkBox.appendChild(a);
    });
  }

  function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text);
    }
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand("copy"); } catch (_) {}
    ta.remove();
    return Promise.resolve();
  }

  function escapeHtml(s) {
    return s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }

  searchInput.addEventListener("input", render);

  renderTabs();
  render();
  renderDorks();

  window._copyToClipboard = copyToClipboard;
  window._escapeHtml = escapeHtml;
})();
