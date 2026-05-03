/* 设置：Hunter / Apollo API key + Apollo 代理 URL
   - 仅保存在 localStorage，不外发
   - 提供全局 window.SETTINGS 给其它模块读取
*/

(function () {
  const KEY = "charger_leads_settings";

  const defaults = {
    hunterKey: "",
    apolloKey: "",
    apolloProxy: "http://127.0.0.1:8787",
  };

  function load() {
    try {
      return Object.assign({}, defaults, JSON.parse(localStorage.getItem(KEY) || "{}"));
    } catch (_) {
      return Object.assign({}, defaults);
    }
  }

  function save(data) {
    localStorage.setItem(KEY, JSON.stringify(data));
    window.SETTINGS = data;
    document.dispatchEvent(new CustomEvent("settings:changed", { detail: data }));
  }

  window.SETTINGS = load();

  const modal = document.getElementById("settings-modal");
  const open = document.getElementById("open-settings");
  const cancel = document.getElementById("s-cancel");
  const clear = document.getElementById("s-clear");
  const saveBtn = document.getElementById("s-save");
  const f = {
    hunter: document.getElementById("s-hunter-key"),
    apollo: document.getElementById("s-apollo-key"),
    proxy: document.getElementById("s-apollo-proxy"),
  };

  function fill() {
    f.hunter.value = SETTINGS.hunterKey || "";
    f.apollo.value = SETTINGS.apolloKey || "";
    f.proxy.value = SETTINGS.apolloProxy || defaults.apolloProxy;
  }

  open.addEventListener("click", () => {
    fill();
    modal.classList.remove("hidden");
  });
  cancel.addEventListener("click", () => modal.classList.add("hidden"));
  modal.addEventListener("click", (e) => {
    if (e.target === modal) modal.classList.add("hidden");
  });
  saveBtn.addEventListener("click", () => {
    save({
      hunterKey: f.hunter.value.trim(),
      apolloKey: f.apollo.value.trim(),
      apolloProxy: (f.proxy.value || defaults.apolloProxy).trim().replace(/\/$/, ""),
    });
    modal.classList.add("hidden");
    toast("已保存");
  });
  clear.addEventListener("click", () => {
    if (!confirm("清空所有 API key？")) return;
    save(Object.assign({}, defaults));
    fill();
    toast("已清空");
  });
})();
