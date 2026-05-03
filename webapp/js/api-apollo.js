/* Apollo.io API 封装（走本地代理，规避 CORS）
   文档：https://docs.apollo.io/reference/people-search

   代理协议（极简）：
     POST {proxyBase}/apollo
     headers: x-apollo-key: <APOLLO_KEY>
     body:    { path: "/v1/mixed_people/search", method: "POST", body: {...} }
*/

window.ApolloAPI = (function () {
  function key() {
    return (window.SETTINGS && SETTINGS.apolloKey) || "";
  }
  function proxy() {
    return (window.SETTINGS && SETTINGS.apolloProxy) || "http://127.0.0.1:8787";
  }
  function ensure() {
    if (!key()) throw new Error("未配置 Apollo API key（点右上角 ⚙️ 设置）");
    if (!proxy()) throw new Error("未配置 Apollo 代理地址");
  }

  async function call(path, body, method) {
    ensure();
    const url = proxy().replace(/\/$/, "") + "/apollo";
    let res;
    try {
      res = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-apollo-key": key(),
        },
        body: JSON.stringify({ path, method: method || "POST", body: body || {} }),
      });
    } catch (e) {
      throw new Error(
        "无法连接代理 " + url + "。请先在 proxy/ 目录运行 `node proxy/server.js`"
      );
    }
    const json = await res.json().catch(() => ({}));
    if (!res.ok) {
      const msg =
        (json && (json.error || json.message || json.detail)) || `Apollo ${res.status}`;
      throw new Error(msg);
    }
    return json;
  }

  function csv(text) {
    if (!text) return undefined;
    return text
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
  }

  return {
    /** Mixed People Search：联系人搜索 */
    peopleSearch(opts) {
      const body = {
        q_keywords: opts.keywords || undefined,
        person_titles: csv(opts.titles),
        person_locations: csv(opts.locations),
        organization_industry_tag_ids: undefined,
        q_organization_keyword_tags: csv(opts.industry),
        page: opts.page || 1,
        per_page: opts.perPage || 25,
        reveal_personal_emails: opts.reveal === true || opts.reveal === "true",
      };
      if (opts.size) {
        const [a, b] = String(opts.size).split(",").map((n) => parseInt(n, 10));
        if (!isNaN(a) && !isNaN(b)) {
          body.organization_num_employees_ranges = [`${a},${b}`];
        }
      }
      return call("/v1/mixed_people/search", body, "POST");
    },
  };
})();
