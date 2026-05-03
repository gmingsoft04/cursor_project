/* 模块 2：目标平台卡片 */

(function () {
  const grid = document.getElementById("platform-grid");

  PLATFORMS.forEach((p) => {
    const card = document.createElement("div");
    card.className = "platform-card" + (p.featured ? " featured" : "");
    let html = "";
    if (p.badge) html += `<span class="badge">${_escapeHtml(p.badge)}</span>`;
    html += `<span class="ptype">${_escapeHtml(p.type)}</span>`;
    html += `<h3>${_escapeHtml(p.name)}</h3>`;
    html += `<p>${_escapeHtml(p.desc)}</p>`;
    if (p.tips && p.tips.length) {
      html += '<div class="meta"><strong>使用要点：</strong><ul style="margin:6px 0;padding-left:18px;">';
      p.tips.forEach((t) => (html += `<li>${_escapeHtml(t)}</li>`));
      html += "</ul></div>";
    }
    html += `<a class="btn primary" href="${p.url}" target="_blank" rel="noopener noreferrer">前往 ${_escapeHtml(p.name)} ↗</a>`;
    card.innerHTML = html;
    grid.appendChild(card);
  });
})();
