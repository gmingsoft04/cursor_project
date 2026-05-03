/* 模块 5：AI 客户生成（基于 data.js 中的知识库做规则化推理）
   - 输入：国家 × 客户类型 × 规模
   - 输出：买家画像 / 平台组合 / 关键词 / 4 周行动计划
   - 不依赖外部 API，完全离线
*/

(function () {
  const out = document.getElementById("ai-output");
  const btn = document.getElementById("ai-generate");

  function getInput() {
    return {
      country: document.getElementById("ai-country").value,
      type: document.getElementById("ai-type").value,
      scale: document.getElementById("ai-scale").value,
    };
  }

  function pickKeywords(country, type) {
    const all = [];
    KEYWORD_CATEGORIES.forEach((c) => c.items.forEach((kw) => all.push({ kw, cat: c.id })));
    const countryShort = country.match(/\(([A-Z]+)\)/)?.[1] || "";
    const countryName = country.replace(/\s*\(.*?\)/, "").toLowerCase();
    return all
      .filter((it) => {
        const k = it.kw.toLowerCase();
        const countryMatch =
          k.includes(countryName) ||
          (countryShort && k.toLowerCase().includes(countryShort.toLowerCase()));
        const typeMatch =
          (type === "distributor" && /(distrib|importer|wholesale|grossist|grossiste|großh)/i.test(k)) ||
          (type === "retailer" && /(retail|chain|store|merchand|category)/i.test(k)) ||
          (type === "ecommerce" && /(amazon|ebay|fba|shop|tiktok|walmart marketplace)/i.test(k)) ||
          (type === "oem" && /(oem|odm|private label|product manager|sourcing|brand)/i.test(k)) ||
          (type === "telecom" && /(telecom|operator|verizon|vodafone)/i.test(k));
        return countryMatch || typeMatch;
      })
      .slice(0, 8)
      .map((it) => it.kw);
  }

  function pickPlatforms(type, scale) {
    const list = [];
    if (scale === "small") {
      list.push("Apollo.io 免费档", "Alibaba RFQ Market", "Hunter.io（域名查邮箱）", "LinkedIn 基础搜索");
    } else if (scale === "medium") {
      list.push("Apollo.io 付费档", "ImportGenius（重点）", "Hunter.io", "LinkedIn Sales Navigator", "Europages / Kompass");
    } else {
      list.push("ImportGenius + Panjiva", "Apollo.io 团队版", "LinkedIn Sales Navigator", "线下展会（CES / IFA / Mobile World Congress）");
    }
    if (type === "ecommerce") list.push("Helium 10 / Jungle Scout 反查 Amazon BSR 卖家");
    if (type === "oem") list.push("LinkedIn Sales Navigator 找 PM/Sourcing Director");
    if (type === "telecom") list.push("通过现有 ODM 工厂引荐成为 Tier 2");
    return Array.from(new Set(list));
  }

  function buildPlan(scale, type, country) {
    const typeInfo = AI_KB.types[type];
    const cn = country;
    return [
      {
        title: "第 1 周：搭建武器库",
        body:
          "完成英文公司画册（PDF）、Top 5 SKU spec sheet、" +
          "样品视频（30s 内拆箱 + 测试）、价格梯度表。" +
          "在 Apollo / ImportGenius / Hunter 注册并完成账号验证。",
      },
      {
        title: "第 2 周：批量找客户",
        body:
          "用 ImportGenius 拉" + cn + "近 6 个月 USB charger / phone charger 进口数据，" +
          "导出 100+ Consignee 公司名；用 Hunter 批量补全邮箱。" +
          "同时 Apollo 按 " + (typeInfo?.label || "目标客户") + " 头衔筛选另外 50–80 联系人。",
      },
      {
        title: "第 3 周：首轮触达",
        body:
          "用本工具的「开发信模板」分批发送（每天 ≤ 30 封，避免被标垃圾），" +
          "三种风格 A/B 测试。所有收件人同步导入「客户追踪」模块跟踪状态。" +
          "对开信无回复的 3 天后发跟进邮件。",
      },
      {
        title: "第 4 周：转化与样品",
        body:
          "对回复的客户：48h 内出 PI（含价格梯度 + MOQ + Lead time），" +
          "免费寄样（DHL/FedEx 4–7 天）。同时用 LinkedIn 加对接人，" +
          "加企业微信 / WhatsApp 进入私域跟进。月底盘点：触达数 / 回复率 / 寄样数 / PI 数。",
      },
    ];
  }

  function render() {
    const { country, type, scale } = getInput();
    const c = AI_KB.countries[country];
    const t = AI_KB.types[type];
    const s = AI_KB.scales[scale];
    if (!c || !t || !s) return;

    const kws = pickKeywords(country, type);
    const platforms = pickPlatforms(type, scale);
    const plan = buildPlan(scale, type, country);

    const html = [];

    html.push(`<div class="ai-card">
      <h3>🎯 ${escapeHtml(country)} · ${escapeHtml(t.label)} · ${escapeHtml(s.label)}</h3>
      <p><strong>买家画像：</strong>${escapeHtml(c.buyerProfile)}</p>
      <p><strong>开发要点：</strong></p>
      <ul>${t.strategy.map((x) => `<li>${escapeHtml(x)}</li>`).join("")}</ul>
      <p><strong>样品/MOQ 策略：</strong>${escapeHtml(t.sample)}</p>
      <p><strong>必备认证：</strong>${c.certs.map(escapeHtml).join(" · ")}</p>
      <p><strong>主流付款方式：</strong>${c.payment.map(escapeHtml).join(" · ")}</p>
      <p><strong>该国当前热销品类：</strong>${c.hot.map(escapeHtml).join(" · ")}</p>
    </div>`);

    html.push(`<div class="ai-card">
      <h3>🌐 推荐平台组合</h3>
      <ul>${platforms.map((p) => `<li>${escapeHtml(p)}</li>`).join("")}</ul>
    </div>`);

    if (kws.length) {
      html.push(`<div class="ai-card">
        <h3>🔍 推荐搜索关键词（点击复制）</h3>
        <div class="kw-grid">
          ${kws.map((k) => `<div class="kw-item" data-kw="${escapeHtml(k)}"><span>${escapeHtml(k)}</span><span class="kw-cat">推荐</span></div>`).join("")}
        </div>
      </div>`);
    }

    html.push(`<div class="ai-card">
      <h3>📅 4 周行动计划</h3>
      ${plan.map((w) => `<div class="ai-week"><h4>${escapeHtml(w.title)}</h4><p>${escapeHtml(w.body)}</p></div>`).join("")}
    </div>`);

    out.innerHTML = html.join("");

    out.querySelectorAll(".kw-item[data-kw]").forEach((el) => {
      el.addEventListener("click", () => {
        const kw = el.dataset.kw;
        _copyToClipboard(kw).then(() => toast("已复制：" + kw));
      });
    });
  }

  function escapeHtml(s) { return _escapeHtml(String(s)); }

  btn.addEventListener("click", render);
})();
