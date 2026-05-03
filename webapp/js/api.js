/* API Tab：在 Hunter / Apollo 间切换 + 表单渲染 + 结果表格 + 一键加入 CRM */

(function () {
  const tabs = document.querySelectorAll(".api-tab");
  const panes = {
    hunter: document.getElementById("api-pane-hunter"),
    apollo: document.getElementById("api-pane-apollo"),
  };
  tabs.forEach((t) =>
    t.addEventListener("click", () => {
      tabs.forEach((x) => x.classList.toggle("active", x === t));
      Object.entries(panes).forEach(([k, p]) => p.classList.toggle("hidden", k !== t.dataset.api));
    })
  );

  /* ============ 顶部 API key 状态 chip ============ */
  const status = document.getElementById("api-status");
  function renderStatus() {
    const s = window.SETTINGS || {};
    status.innerHTML = `
      <span class="chip ${s.hunterKey ? "ok" : "miss"}">
        <span class="dot"></span>Hunter ${s.hunterKey ? "已配置" : "未配置"}
      </span>
      <span class="chip ${s.apolloKey ? "ok" : "miss"}">
        <span class="dot"></span>Apollo ${s.apolloKey ? "已配置" : "未配置"}
      </span>
    `;
  }
  document.addEventListener("settings:changed", renderStatus);
  renderStatus();

  /* ============ Hunter 模式切换 ============ */
  const hForms = {
    "domain-search": document.getElementById("hunter-form-domain"),
    "email-finder": document.getElementById("hunter-form-finder"),
    "email-verifier": document.getElementById("hunter-form-verify"),
    account: null,
  };
  document.querySelectorAll('input[name="hunter-mode"]').forEach((r) => {
    r.addEventListener("change", () => {
      Object.entries(hForms).forEach(([mode, el]) => {
        if (el) el.classList.toggle("hidden", mode !== r.value);
      });
    });
  });
  function hunterMode() {
    return document.querySelector('input[name="hunter-mode"]:checked').value;
  }

  /* ============ Hunter 查询 ============ */
  const hThead = document.getElementById("hunter-thead");
  const hTbody = document.getElementById("hunter-tbody");
  const hMeter = document.getElementById("hunter-meter");
  const hAddAll = document.getElementById("hunter-add-all");
  let hunterRows = []; // [{ company, email, contact, country, source, ... }]

  document.getElementById("hunter-run").addEventListener("click", runHunter);
  hAddAll.addEventListener("click", () => addAllToCrm(hunterRows, "Hunter"));

  async function runHunter() {
    const mode = hunterMode();
    const btn = document.getElementById("hunter-run");
    btn.disabled = true;
    btn.textContent = "查询中…";
    hThead.innerHTML = "";
    hTbody.innerHTML = `<tr><td colspan="6" class="empty-row">查询中…</td></tr>`;
    hMeter.textContent = "";
    hAddAll.disabled = true;
    hunterRows = [];

    try {
      if (mode === "domain-search") {
        const r = await HunterAPI.domainSearch({
          domain: document.getElementById("h-domain").value.trim(),
          type: document.getElementById("h-type").value,
          department: document.getElementById("h-department").value,
          limit: parseInt(document.getElementById("h-limit").value || "25", 10),
        });
        renderDomainSearch(r);
      } else if (mode === "email-finder") {
        const r = await HunterAPI.emailFinder({
          domain: document.getElementById("hf-domain").value.trim(),
          firstName: document.getElementById("hf-first").value.trim(),
          lastName: document.getElementById("hf-last").value.trim(),
        });
        renderEmailFinder(r);
      } else if (mode === "email-verifier") {
        const r = await HunterAPI.emailVerifier({
          email: document.getElementById("hv-email").value.trim(),
        });
        renderVerifier(r);
      } else if (mode === "account") {
        const r = await HunterAPI.account();
        renderAccount(r);
      }
    } catch (e) {
      hTbody.innerHTML = `<tr><td colspan="6" class="empty-row" style="color:var(--red)">${_escapeHtml(e.message)}</td></tr>`;
    } finally {
      btn.disabled = false;
      btn.textContent = "查询";
      hAddAll.disabled = hunterRows.length === 0;
    }
  }

  function renderDomainSearch(r) {
    const data = (r && r.data) || {};
    const emails = data.emails || [];
    const meta = r.meta || {};
    hMeter.textContent = `共 ${emails.length} 条 · 配额 ${meta.results || 0}/${(r.meta && r.meta.results) || 0}`;
    hThead.innerHTML = `<tr>
      <th>公司</th><th>邮箱</th><th>姓名 / 头衔</th><th>类型</th><th>置信度</th><th>来源</th><th></th>
    </tr>`;
    if (emails.length === 0) {
      hTbody.innerHTML = `<tr><td colspan="7" class="empty-row">无结果</td></tr>`;
      return;
    }
    hTbody.innerHTML = "";
    emails.forEach((e) => {
      const company = data.organization || data.domain || "";
      const contact = [e.first_name, e.last_name].filter(Boolean).join(" ");
      const title = e.position || e.department || "";
      const src = (e.sources && e.sources[0] && e.sources[0].uri) || "";
      hunterRows.push({
        company,
        contact,
        email: e.value,
        country: data.country || "",
        type: "进口商 / 批发分销商",
        source: "Hunter: " + (src || data.domain || ""),
        notes: title,
      });
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><strong>${_escapeHtml(company)}</strong></td>
        <td>${_escapeHtml(e.value)}</td>
        <td>${_escapeHtml(contact)}<br/><small style="color:var(--muted)">${_escapeHtml(title)}</small></td>
        <td>${_escapeHtml(e.type || "")}</td>
        <td>${e.confidence != null ? e.confidence : ""}</td>
        <td><small>${src ? `<a href="${_escapeHtml(src)}" target="_blank" rel="noopener noreferrer">来源</a>` : ""}</small></td>
        <td><button class="btn ghost" data-add-row='${hunterRows.length - 1}'>+</button></td>
      `;
      hTbody.appendChild(tr);
    });
    bindAddRow(hTbody, hunterRows, "Hunter");
  }

  function renderEmailFinder(r) {
    const d = (r && r.data) || {};
    hThead.innerHTML = `<tr><th>邮箱</th><th>得分</th><th>姓名</th><th>头衔</th><th>公司</th><th></th></tr>`;
    if (!d.email) {
      hTbody.innerHTML = `<tr><td colspan="6" class="empty-row">未找到邮箱</td></tr>`;
      return;
    }
    const company = d.company || d.domain || "";
    const contact = [d.first_name, d.last_name].filter(Boolean).join(" ");
    hunterRows.push({
      company,
      contact,
      email: d.email,
      country: d.country || "",
      type: "进口商 / 批发分销商",
      source: "Hunter Email Finder",
      notes: d.position || "",
    });
    hTbody.innerHTML = `<tr>
      <td>${_escapeHtml(d.email)}</td>
      <td>${d.score != null ? d.score : ""}</td>
      <td>${_escapeHtml(contact)}</td>
      <td>${_escapeHtml(d.position || "")}</td>
      <td>${_escapeHtml(company)}</td>
      <td><button class="btn ghost" data-add-row="0">+</button></td>
    </tr>`;
    bindAddRow(hTbody, hunterRows, "Hunter");
  }

  function renderVerifier(r) {
    const d = (r && r.data) || {};
    hThead.innerHTML = `<tr><th>邮箱</th><th>结果</th><th>得分</th><th>SMTP</th><th>MX</th><th>是否可送达</th></tr>`;
    hTbody.innerHTML = `<tr>
      <td>${_escapeHtml(d.email || "")}</td>
      <td><strong>${_escapeHtml(d.result || d.status || "")}</strong></td>
      <td>${d.score != null ? d.score : ""}</td>
      <td>${d.smtp_check ? "✅" : "❌"}</td>
      <td>${d.mx_records ? "✅" : "❌"}</td>
      <td>${d.deliverable ? "✅" : (d.result === "deliverable" ? "✅" : "❌")}</td>
    </tr>`;
    hAddAll.disabled = true;
  }

  function renderAccount(r) {
    const d = (r && r.data) || {};
    const calls = d.calls || {};
    const requests = d.requests || {};
    const searches = (requests.searches) || calls;
    const verif = (requests.verifications) || {};
    hThead.innerHTML = `<tr><th>项目</th><th>已用</th><th>额度</th><th>重置时间</th><th>计划</th><th>邮箱</th></tr>`;
    hTbody.innerHTML = `<tr>
      <td>Searches</td>
      <td>${searches.used != null ? searches.used : (calls.used || "")}</td>
      <td>${searches.available != null ? searches.available : (calls.available || "")}</td>
      <td>${_escapeHtml(d.reset_date || "")}</td>
      <td>${_escapeHtml((d.plan_name || "") + (d.plan_level ? " (" + d.plan_level + ")" : ""))}</td>
      <td>${_escapeHtml(d.email || "")}</td>
    </tr>
    <tr>
      <td>Verifications</td>
      <td>${verif.used != null ? verif.used : ""}</td>
      <td>${verif.available != null ? verif.available : ""}</td>
      <td colspan="3"></td>
    </tr>`;
    hAddAll.disabled = true;
  }

  /* ============ Apollo 查询 ============ */
  const apThead = document.getElementById("apollo-thead");
  const apTbody = document.getElementById("apollo-tbody");
  const apMeter = document.getElementById("apollo-meter");
  const apAddAll = document.getElementById("apollo-add-all");
  let apolloRows = [];

  document.getElementById("apollo-run").addEventListener("click", runApollo);
  apAddAll.addEventListener("click", () => addAllToCrm(apolloRows, "Apollo"));

  async function runApollo() {
    const btn = document.getElementById("apollo-run");
    btn.disabled = true;
    btn.textContent = "查询中…";
    apThead.innerHTML = "";
    apTbody.innerHTML = `<tr><td colspan="7" class="empty-row">查询中…</td></tr>`;
    apMeter.textContent = "";
    apAddAll.disabled = true;
    apolloRows = [];

    try {
      const r = await ApolloAPI.peopleSearch({
        keywords: document.getElementById("ap-keywords").value.trim(),
        titles: document.getElementById("ap-titles").value.trim(),
        locations: document.getElementById("ap-locations").value.trim(),
        industry: document.getElementById("ap-industry").value.trim(),
        size: document.getElementById("ap-size").value,
        perPage: parseInt(document.getElementById("ap-perpage").value || "25", 10),
        page: parseInt(document.getElementById("ap-page").value || "1", 10),
        reveal: document.getElementById("ap-reveal").value,
      });
      renderApollo(r);
    } catch (e) {
      apTbody.innerHTML = `<tr><td colspan="7" class="empty-row" style="color:var(--red)">${_escapeHtml(e.message)}</td></tr>`;
    } finally {
      btn.disabled = false;
      btn.textContent = "查询";
      apAddAll.disabled = apolloRows.length === 0;
    }
  }

  function renderApollo(r) {
    const people = (r && (r.people || r.contacts)) || [];
    const pag = r.pagination || {};
    apMeter.textContent = `第 ${pag.page || 1} 页 · 本页 ${people.length} 条 · 总共 ${pag.total_entries || people.length}`;
    apThead.innerHTML = `<tr>
      <th>姓名</th><th>头衔</th><th>公司</th><th>邮箱</th><th>国家</th><th>LinkedIn</th><th></th>
    </tr>`;
    if (people.length === 0) {
      apTbody.innerHTML = `<tr><td colspan="7" class="empty-row">无结果（试试更宽松的关键词，或检查代理是否启动）</td></tr>`;
      return;
    }
    apTbody.innerHTML = "";
    people.forEach((p) => {
      const name = [p.first_name, p.last_name].filter(Boolean).join(" ") || p.name || "";
      const org = (p.organization && p.organization.name) || p.organization_name || "";
      const country = (p.country) || (p.organization && p.organization.country) || "";
      const email =
        p.email && p.email !== "email_not_unlocked@domain.com"
          ? p.email
          : ""; // 未解锁
      const linkedin = p.linkedin_url || "";
      apolloRows.push({
        company: org,
        contact: name,
        email,
        country,
        type: "进口商 / 批发分销商",
        source: "Apollo",
        notes: (p.title || "") + (linkedin ? " · " + linkedin : ""),
      });
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><strong>${_escapeHtml(name)}</strong></td>
        <td>${_escapeHtml(p.title || "")}</td>
        <td>${_escapeHtml(org)}</td>
        <td>${email ? _escapeHtml(email) : '<small style="color:var(--muted)">未解锁</small>'}</td>
        <td>${_escapeHtml(country)}</td>
        <td>${linkedin ? `<a href="${_escapeHtml(linkedin)}" target="_blank" rel="noopener">↗</a>` : ""}</td>
        <td><button class="btn ghost" data-add-row="${apolloRows.length - 1}" ${email ? "" : "disabled"}>+</button></td>
      `;
      apTbody.appendChild(tr);
    });
    bindAddRow(apTbody, apolloRows, "Apollo");
  }

  /* ============ 共用：加入 CRM ============ */
  function bindAddRow(tbody, rows, source) {
    tbody.querySelectorAll("button[data-add-row]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const idx = parseInt(btn.dataset.addRow, 10);
        const r = rows[idx];
        if (!r || !r.email) return toast("没有可用邮箱");
        window._addLead(r);
        btn.textContent = "✓";
        btn.disabled = true;
        toast(`已加入：${r.email}`);
      });
    });
  }

  function addAllToCrm(rows, source) {
    const valid = rows.filter((r) => r.email);
    if (valid.length === 0) return toast("没有可加入的邮箱");
    valid.forEach((r) => window._addLead(r));
    toast(`已加入 ${valid.length} 条到客户追踪`);
  }
})();
