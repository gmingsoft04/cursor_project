/* 模块 4：开发信模板 3 种风格
   - 实时根据表单生成
   - 支持复制到剪贴板
   - 表单数据自动持久化（除接收方）
*/

(function () {
  const KEY = "charger_leads_tpl_form";

  const ids = [
    "tpl-style", "tpl-recipient-company", "tpl-recipient-name",
    "tpl-sender-company", "tpl-sender-name", "tpl-sender-title",
    "tpl-sender-email", "tpl-sender-phone", "tpl-sender-website",
    "tpl-product", "tpl-certs", "tpl-source",
  ];
  const els = {};
  ids.forEach((id) => (els[id] = document.getElementById(id)));
  const preview = document.getElementById("tpl-preview");
  const regen = document.getElementById("tpl-regen");
  const copy = document.getElementById("tpl-copy");

  function load() {
    try {
      const data = JSON.parse(localStorage.getItem(KEY) || "{}");
      Object.entries(data).forEach(([k, v]) => {
        if (els[k] && k !== "tpl-recipient-company" && k !== "tpl-recipient-name") {
          els[k].value = v;
        }
      });
    } catch (_) {}
  }
  function persist() {
    const data = {};
    ids.forEach((id) => (data[id] = els[id].value));
    localStorage.setItem(KEY, JSON.stringify(data));
  }

  function val(id) {
    return (els[id].value || "").trim();
  }

  function buildFormal(v) {
    return `Subject: ${v.senderCompany} — ${v.product}, factory direct samples available

Dear ${v.recipientName || "Purchasing Team"},

I'm ${v.senderName}${v.senderTitle ? ", " + v.senderTitle : ""} from ${v.senderCompany}, a Shenzhen-based manufacturer of ${v.product}. We supply private-label and OEM programs to importers and retailers across the US and EU, and I'm reaching out to ${v.recipientCompany || "your team"} to explore a possible fit.

A short profile of our offer:
  • Products: ${v.product}
  • Certifications: ${v.certs}
  • MOQ from 500 pcs, lead time ~25 days, FOB Shenzhen / DDP US/EU
  • Free samples for verified buyers, FBA-ready packaging available
  • In-house QC, AQL 0.65, full safety test reports on request

If this is relevant, I'd be glad to share our PDF catalog and a sample quotation for your top SKUs. If you are not the right contact, a quick forward to your purchasing team would mean a lot.

You can reply STOP and I will remove ${v.recipientCompany || "your address"} from this list immediately.

Best regards,
${v.senderName}
${v.senderTitle ? v.senderTitle + " · " : ""}${v.senderCompany}
${v.senderPhone ? "Tel/WhatsApp: " + v.senderPhone : ""}
${v.senderEmail ? "Email: " + v.senderEmail : ""}
${v.senderWebsite ? "Web: " + v.senderWebsite : ""}

---
Why you received this: I found your business contact${v.source ? " on " + v.source : ""} and reached out under legitimate B2B interest. We do not share or sell contact data. Reply "unsubscribe" to opt out from future emails.`;
  }

  function buildConcise(v) {
    return `Subject: Quick question — ${v.product} for ${v.recipientCompany || "your sourcing team"}

Hi ${v.recipientName || "there"},

${v.senderName} here from ${v.senderCompany} (Shenzhen).

We make ${v.product}. Three things buyers usually like:
  1. Certs ready: ${v.certs}
  2. MOQ 500, ~25 days, FOB or DDP
  3. Free samples for verified buyers

Would a 5-line quote and 2 sample units help you compare?

Just reply "yes" or "not now". Either is fine.

— ${v.senderName}
${v.senderEmail ? v.senderEmail : ""}${v.senderPhone ? " · " + v.senderPhone : ""}${v.senderWebsite ? " · " + v.senderWebsite : ""}

(Reply "unsubscribe" to stop. Found your address${v.source ? " on " + v.source : ""}.)`;
  }

  function buildProduct(v) {
    return `Subject: New 65W GaN III for 2026 — datasheet & MOQ inside (${v.senderCompany})

Hello ${v.recipientName || "team"},

I'm ${v.senderName} from ${v.senderCompany}. I'm writing because ${v.recipientCompany || "your team"} looks like a great fit for our 2026 GaN charging line.

Highlights:
  • GaN III, PD 3.1 / PPS, 1C / 2C1A / 3C1A versions, 20W–140W
  • USB-C / Lightning cables, MFi optional, braided & silicone
  • Certs: ${v.certs}
  • Custom PCBA / mold / packaging — full OEM in 45 days
  • MOQ 500 pcs, lead time ~25 days, FOB Shenzhen or DDP

What I can send today:
  ① Full PDF catalog with FOB price ladder
  ② 1-page spec sheet of our top 5 SKUs (BSR-tested)
  ③ 2 free samples by FedEx (you cover shipping ~$30)

Just reply with your top SKU type (e.g. 65W 2C1A GaN) and I'll send a quotation within 24h.

Best,
${v.senderName}
${v.senderTitle ? v.senderTitle + " · " : ""}${v.senderCompany}
${v.senderEmail ? v.senderEmail : ""}${v.senderPhone ? " · " + v.senderPhone : ""}
${v.senderWebsite ? v.senderWebsite : ""}

---
You're receiving this because your public business email${v.source ? " (" + v.source + ")" : ""} indicated interest in mobile accessories sourcing. Reply "unsubscribe" and I will remove you immediately and permanently.`;
  }

  function buildAll() {
    const v = {
      style: val("tpl-style"),
      recipientCompany: val("tpl-recipient-company"),
      recipientName: val("tpl-recipient-name"),
      senderCompany: val("tpl-sender-company") || "[Your Company]",
      senderName: val("tpl-sender-name") || "[Your Name]",
      senderTitle: val("tpl-sender-title"),
      senderEmail: val("tpl-sender-email"),
      senderPhone: val("tpl-sender-phone"),
      senderWebsite: val("tpl-sender-website"),
      product: val("tpl-product") || "GaN fast chargers and USB-C cables",
      certs: val("tpl-certs") || "FCC, CE, UKCA, RoHS, REACH",
      source: val("tpl-source"),
    };
    if (v.style === "concise") return buildConcise(v);
    if (v.style === "product") return buildProduct(v);
    return buildFormal(v);
  }

  function render() {
    preview.textContent = buildAll();
    persist();
  }

  ids.forEach((id) => els[id].addEventListener("input", render));
  regen.addEventListener("click", render);
  copy.addEventListener("click", () => {
    _copyToClipboard(preview.textContent).then(() => toast("已复制到剪贴板"));
  });

  load();
  render();
})();
