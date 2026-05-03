/* 模块 3：客户追踪 CRM
   - 数据持久化：localStorage('charger_leads_crm')
   - 增删改查 + 状态过滤 + 搜索 + CSV 导出 / 导入
*/

(function () {
  const KEY = "charger_leads_crm";

  const els = {
    body: document.getElementById("crm-body"),
    stats: document.getElementById("crm-stats"),
    add: document.getElementById("crm-add"),
    importBtn: document.getElementById("crm-import"),
    importFile: document.getElementById("crm-import-file"),
    exportBtn: document.getElementById("crm-export"),
    clearBtn: document.getElementById("crm-clear"),
    search: document.getElementById("crm-search"),
    filter: document.getElementById("crm-filter-status"),
    modal: document.getElementById("modal"),
    title: document.getElementById("modal-title"),
    save: document.getElementById("m-save"),
    cancel: document.getElementById("m-cancel"),
    f: {
      company: document.getElementById("m-company"),
      contact: document.getElementById("m-contact"),
      email: document.getElementById("m-email"),
      country: document.getElementById("m-country"),
      type: document.getElementById("m-type"),
      status: document.getElementById("m-status"),
      next: document.getElementById("m-next"),
      source: document.getElementById("m-source"),
      notes: document.getElementById("m-notes"),
    },
  };

  const STATUS_LABEL = {
    new: "新增",
    contacted: "已发开发信",
    replied: "已回复",
    negotiating: "谈判中",
    won: "成交",
    lost: "流失",
  };

  let leads = load();
  let editingId = null;

  function load() {
    try {
      return JSON.parse(localStorage.getItem(KEY) || "[]");
    } catch (_) {
      return [];
    }
  }
  function save() {
    localStorage.setItem(KEY, JSON.stringify(leads));
  }
  function uid() {
    return Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
  }

  function render() {
    const q = (els.search.value || "").trim().toLowerCase();
    const fs = els.filter.value;
    let view = leads.slice();
    if (q) {
      view = view.filter(
        (l) =>
          (l.company || "").toLowerCase().includes(q) ||
          (l.email || "").toLowerCase().includes(q) ||
          (l.country || "").toLowerCase().includes(q) ||
          (l.contact || "").toLowerCase().includes(q)
      );
    }
    if (fs) view = view.filter((l) => l.status === fs);

    renderStats();

    els.body.innerHTML = "";
    if (view.length === 0) {
      els.body.innerHTML = `<tr><td colspan="10" class="empty-row">暂无数据，点击"+ 添加客户"或"导入 CSV"开始</td></tr>`;
      return;
    }

    view.forEach((l) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><strong>${_escapeHtml(l.company || "")}</strong></td>
        <td>${_escapeHtml(l.contact || "")}</td>
        <td>${_escapeHtml(l.email || "")}</td>
        <td>${_escapeHtml(l.country || "")}</td>
        <td>${_escapeHtml(l.type || "")}</td>
        <td><span class="status-pill status-${l.status || "new"}">${STATUS_LABEL[l.status] || "新增"}</span></td>
        <td>${_escapeHtml(l.next || "")}</td>
        <td>${_escapeHtml(l.source || "")}</td>
        <td>${_escapeHtml(l.notes || "").slice(0, 60)}</td>
        <td class="actions">
          <button class="btn ghost" data-act="edit" data-id="${l.id}">✏️</button>
          <button class="btn danger ghost" data-act="del" data-id="${l.id}">🗑</button>
        </td>
      `;
      els.body.appendChild(tr);
    });
  }

  function renderStats() {
    const total = leads.length;
    const counts = { new: 0, contacted: 0, replied: 0, negotiating: 0, won: 0, lost: 0 };
    leads.forEach((l) => {
      counts[l.status] = (counts[l.status] || 0) + 1;
    });
    els.stats.innerHTML = `
      <div class="crm-stat"><div class="label">总计</div><div class="value">${total}</div></div>
      <div class="crm-stat"><div class="label">新增</div><div class="value">${counts.new || 0}</div></div>
      <div class="crm-stat"><div class="label">已开发</div><div class="value">${counts.contacted || 0}</div></div>
      <div class="crm-stat"><div class="label">已回复</div><div class="value">${counts.replied || 0}</div></div>
      <div class="crm-stat"><div class="label">谈判中</div><div class="value">${counts.negotiating || 0}</div></div>
      <div class="crm-stat"><div class="label">成交</div><div class="value" style="color:var(--green)">${counts.won || 0}</div></div>
    `;
  }

  function openModal(lead) {
    editingId = lead ? lead.id : null;
    els.title.textContent = lead ? "编辑客户" : "添加客户";
    const v = lead || { type: "进口商 / 批发分销商", status: "new" };
    els.f.company.value = v.company || "";
    els.f.contact.value = v.contact || "";
    els.f.email.value = v.email || "";
    els.f.country.value = v.country || "";
    els.f.type.value = v.type || "进口商 / 批发分销商";
    els.f.status.value = v.status || "new";
    els.f.next.value = v.next || "";
    els.f.source.value = v.source || "";
    els.f.notes.value = v.notes || "";
    els.modal.classList.remove("hidden");
    els.f.company.focus();
  }
  function closeModal() {
    els.modal.classList.add("hidden");
    editingId = null;
  }

  function saveModal() {
    const data = {
      company: els.f.company.value.trim(),
      contact: els.f.contact.value.trim(),
      email: els.f.email.value.trim(),
      country: els.f.country.value.trim(),
      type: els.f.type.value,
      status: els.f.status.value,
      next: els.f.next.value,
      source: els.f.source.value.trim(),
      notes: els.f.notes.value.trim(),
    };
    if (!data.company || !data.email) {
      toast("公司和邮箱为必填");
      return;
    }
    if (editingId) {
      leads = leads.map((l) => (l.id === editingId ? { ...l, ...data } : l));
    } else {
      leads.push({ id: uid(), createdAt: new Date().toISOString(), ...data });
    }
    save();
    render();
    closeModal();
    toast(editingId ? "已更新" : "已添加");
  }

  function delLead(id) {
    if (!confirm("确定删除这条记录？")) return;
    leads = leads.filter((l) => l.id !== id);
    save();
    render();
    toast("已删除");
  }

  function exportCsv() {
    if (leads.length === 0) return toast("没有数据可导出");
    const headers = ["company", "contact", "email", "country", "type", "status", "next", "source", "notes", "createdAt"];
    const rows = [headers.join(",")];
    leads.forEach((l) => {
      rows.push(headers.map((h) => csvCell(l[h] || "")).join(","));
    });
    const blob = new Blob(["\uFEFF" + rows.join("\n")], { type: "text/csv;charset=utf-8" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `charger-leads-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(a.href);
    toast(`已导出 ${leads.length} 条`);
  }

  function csvCell(v) {
    const s = String(v).replace(/"/g, '""');
    return /[",\n]/.test(s) ? `"${s}"` : s;
  }

  function importCsv(file) {
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const text = String(reader.result).replace(/^\uFEFF/, "");
        const rows = parseCsv(text);
        if (rows.length < 2) return toast("CSV 至少需要表头 + 一行数据");
        const headers = rows[0].map((h) => h.trim().toLowerCase());
        let added = 0;
        for (let i = 1; i < rows.length; i++) {
          const cells = rows[i];
          if (cells.every((c) => !c)) continue;
          const obj = {};
          headers.forEach((h, idx) => (obj[h] = (cells[idx] || "").trim()));
          if (!obj.email && !obj.company) continue;
          leads.push({
            id: uid(),
            createdAt: new Date().toISOString(),
            company: obj.company || obj["公司"] || "",
            contact: obj.contact || obj["联系人"] || "",
            email: obj.email || obj["邮箱"] || "",
            country: obj.country || obj["国家"] || obj.country_hint || "",
            type: obj.type || obj["类型"] || "进口商 / 批发分销商",
            status: obj.status || "new",
            next: obj.next || "",
            source: obj.source || obj["来源"] || obj.source_url || "",
            notes: obj.notes || obj["备注"] || obj.snippet || "",
          });
          added++;
        }
        save();
        render();
        toast(`已导入 ${added} 条`);
      } catch (e) {
        toast("CSV 解析失败：" + e.message);
      }
    };
    reader.readAsText(file, "utf-8");
  }

  /* 简易 CSV 解析（支持引号转义） */
  function parseCsv(text) {
    const rows = [];
    let row = [];
    let cur = "";
    let inQ = false;
    for (let i = 0; i < text.length; i++) {
      const c = text[i];
      if (inQ) {
        if (c === '"' && text[i + 1] === '"') {
          cur += '"';
          i++;
        } else if (c === '"') {
          inQ = false;
        } else {
          cur += c;
        }
      } else {
        if (c === '"') inQ = true;
        else if (c === ",") {
          row.push(cur);
          cur = "";
        } else if (c === "\n") {
          row.push(cur);
          rows.push(row);
          row = [];
          cur = "";
        } else if (c === "\r") {
          /* skip */
        } else {
          cur += c;
        }
      }
    }
    if (cur || row.length) {
      row.push(cur);
      rows.push(row);
    }
    return rows;
  }

  els.add.addEventListener("click", () => openModal(null));
  els.cancel.addEventListener("click", closeModal);
  els.save.addEventListener("click", saveModal);
  els.modal.addEventListener("click", (e) => {
    if (e.target === els.modal) closeModal();
  });
  els.body.addEventListener("click", (e) => {
    const btn = e.target.closest("button[data-act]");
    if (!btn) return;
    const id = btn.dataset.id;
    const lead = leads.find((l) => l.id === id);
    if (btn.dataset.act === "edit" && lead) openModal(lead);
    if (btn.dataset.act === "del") delLead(id);
  });
  els.search.addEventListener("input", render);
  els.filter.addEventListener("change", render);
  els.exportBtn.addEventListener("click", exportCsv);
  els.importBtn.addEventListener("click", () => els.importFile.click());
  els.importFile.addEventListener("change", (e) => {
    const f = e.target.files && e.target.files[0];
    if (f) importCsv(f);
    e.target.value = "";
  });
  els.clearBtn.addEventListener("click", () => {
    if (leads.length === 0) return;
    if (!confirm("确定清空全部 " + leads.length + " 条客户记录？此操作不可撤销。")) return;
    leads = [];
    save();
    render();
    toast("已清空");
  });

  /* 暴露给其它模块（例如 AI 模块插入示例数据） */
  window._addLead = function (data) {
    leads.push({ id: uid(), createdAt: new Date().toISOString(), status: "new", ...data });
    save();
    render();
  };

  render();
})();
