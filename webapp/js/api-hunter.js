/* Hunter.io API 封装（浏览器直连，CORS 友好）
   文档：https://hunter.io/api-documentation/v2
*/

window.HunterAPI = (function () {
  const BASE = "https://api.hunter.io/v2";

  function key() {
    return (window.SETTINGS && SETTINGS.hunterKey) || "";
  }
  function ensureKey() {
    if (!key()) throw new Error("未配置 Hunter API key（点右上角 ⚙️ 设置）");
  }

  async function call(path, params) {
    ensureKey();
    const url = new URL(BASE + path);
    Object.entries(params || {}).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, v);
    });
    url.searchParams.set("api_key", key());
    const res = await fetch(url.toString(), { method: "GET" });
    const json = await res.json().catch(() => ({}));
    if (!res.ok) {
      const msg =
        (json && json.errors && json.errors[0] && json.errors[0].details) ||
        `Hunter ${res.status}`;
      throw new Error(msg);
    }
    return json;
  }

  return {
    /** 域名查邮箱：返回 { data: { domain, organization, emails: [...] }, meta } */
    domainSearch(opts) {
      return call("/domain-search", {
        domain: opts.domain,
        type: opts.type || "",
        department: opts.department || "",
        limit: opts.limit || 25,
      });
    },

    /** 姓名找邮箱：返回 { data: { email, score, ... }, meta } */
    emailFinder(opts) {
      return call("/email-finder", {
        domain: opts.domain,
        first_name: opts.firstName,
        last_name: opts.lastName,
      });
    },

    /** 邮箱送达性验证：返回 { data: { result, score, ... }, meta } */
    emailVerifier(opts) {
      return call("/email-verifier", { email: opts.email });
    },

    /** 账号配额：返回 { data: { calls: { used, available }, ... } } */
    account() {
      return call("/account", {});
    },
  };
})();
