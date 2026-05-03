#!/usr/bin/env node
/* Apollo.io API 本地代理 — 零依赖（仅 Node 原生 http/https）
 *
 * 用途：浏览器无法直连 Apollo（CORS 限制），由这个进程帮忙转发。
 * API key 由前端在请求 header 里带过来：x-apollo-key
 * 请求体格式：{ path: "/v1/...", method: "POST"|"GET", body: {...} }
 *
 * 启动：
 *   node proxy/server.js              # 默认端口 8787
 *   PORT=9000 node proxy/server.js    # 自定义端口
 *
 * 安全：
 *   - 仅监听 127.0.0.1，不对外暴露
 *   - 不写日志中包含 API key 的内容
 *   - 仅允许 path 以 /v1/ 开头的 Apollo 接口
 */

"use strict";

const http = require("http");
const https = require("https");
const { URL } = require("url");

const PORT = parseInt(process.env.PORT || "8787", 10);
const HOST = process.env.HOST || "127.0.0.1";
const APOLLO_HOST = "api.apollo.io";

function send(res, status, obj, extraHeaders) {
  const body = Buffer.from(JSON.stringify(obj));
  res.writeHead(status, Object.assign({
    "Content-Type": "application/json; charset=utf-8",
    "Content-Length": body.length,
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, x-apollo-key",
    "Access-Control-Max-Age": "600",
  }, extraHeaders || {}));
  res.end(body);
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    let total = 0;
    req.on("data", (chunk) => {
      total += chunk.length;
      if (total > 1024 * 1024) {
        reject(new Error("body too large"));
        req.destroy();
        return;
      }
      chunks.push(chunk);
    });
    req.on("end", () => {
      const raw = Buffer.concat(chunks).toString("utf8") || "{}";
      try {
        resolve(JSON.parse(raw));
      } catch (e) {
        reject(new Error("invalid JSON body"));
      }
    });
    req.on("error", reject);
  });
}

function forward(apolloKey, payload) {
  return new Promise((resolve, reject) => {
    const path = String(payload.path || "");
    if (!/^\/v1\//.test(path)) {
      return reject(Object.assign(new Error("path 必须以 /v1/ 开头"), { status: 400 }));
    }
    const method = (payload.method || "POST").toUpperCase();
    const body = payload.body || {};
    const data = method === "GET" ? "" : JSON.stringify(body);

    const opts = {
      host: APOLLO_HOST,
      method,
      path,
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        "User-Agent": "charger-leads-proxy/0.1",
        "X-Api-Key": apolloKey,
      },
    };
    if (data) opts.headers["Content-Length"] = Buffer.byteLength(data);

    const req = https.request(opts, (resp) => {
      const chunks = [];
      resp.on("data", (c) => chunks.push(c));
      resp.on("end", () => {
        const raw = Buffer.concat(chunks).toString("utf8") || "{}";
        let json;
        try {
          json = JSON.parse(raw);
        } catch (_) {
          json = { raw };
        }
        resolve({ status: resp.statusCode || 502, body: json });
      });
    });
    req.on("error", (e) => reject(e));
    if (data) req.write(data);
    req.end();
  });
}

const server = http.createServer(async (req, res) => {
  if (req.method === "OPTIONS") {
    return send(res, 204, {});
  }
  if (req.method === "GET" && req.url === "/") {
    return send(res, 200, {
      name: "charger-leads apollo proxy",
      ok: true,
      hint: "POST /apollo with header x-apollo-key and JSON body { path, method, body }",
    });
  }
  if (req.method === "POST" && req.url === "/apollo") {
    const key = req.headers["x-apollo-key"];
    if (!key || typeof key !== "string") {
      return send(res, 401, { error: "missing x-apollo-key header" });
    }
    let payload;
    try {
      payload = await readBody(req);
    } catch (e) {
      return send(res, 400, { error: e.message });
    }
    try {
      const r = await forward(key, payload);
      return send(res, r.status, r.body);
    } catch (e) {
      const code = e.status || 502;
      return send(res, code, { error: e.message || "proxy error" });
    }
  }
  send(res, 404, { error: "not found" });
});

server.listen(PORT, HOST, () => {
  console.log(`[charger-leads-proxy] listening on http://${HOST}:${PORT}`);
  console.log(`  POST http://${HOST}:${PORT}/apollo  (header: x-apollo-key)`);
  console.log("  press Ctrl+C to stop");
});
