# Apollo.io 本地代理

零依赖（只用 Node 原生模块）的最小 HTTP 代理，把浏览器请求转发到 `https://api.apollo.io`。
之所以需要它，是因为 Apollo API **不支持浏览器跨域调用**（CORS）。

## 启动

要求：Node.js ≥ 18（LTS 即可）

```bash
node proxy/server.js
# 默认监听 http://127.0.0.1:8787
# 自定义端口：PORT=9000 node proxy/server.js
```

控制台会打印：

```
[charger-leads-proxy] listening on http://127.0.0.1:8787
  POST http://127.0.0.1:8787/apollo  (header: x-apollo-key)
```

## 协议

```
POST /apollo
headers:
  Content-Type: application/json
  x-apollo-key: <YOUR_APOLLO_API_KEY>
body:
  {
    "path":   "/v1/mixed_people/search",
    "method": "POST",
    "body":   { ...Apollo 原生请求体... }
  }
```

返回 Apollo 的原始 JSON 响应，状态码透传。

## 安全说明

- 默认只监听 `127.0.0.1`，不对外暴露
- API key 不写入任何日志
- 仅允许 `path` 以 `/v1/` 开头的 Apollo 接口
- 单次请求体 ≤ 1 MB

## 健康检查

```bash
curl http://127.0.0.1:8787/
# {"name":"charger-leads apollo proxy","ok":true,...}
```
