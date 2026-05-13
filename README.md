# universal-saas

基于 **若依式 Maven 多模块**（`ruoyi-common` / `ruoyi-framework` / `ruoyi-system` / `ruoyi-admin`）的通用 **SaaS 多租户** 后端骨架：Spring Boot 3、Spring Security、JWT、MyBatis、PageHelper；默认 **H2 内存库** 一键启动，可选 **MySQL** 配置。

仓库内同时包含 Cursor Agent Skill：`.cursor/skills/ruoyi-vue-backend/`（与 [RuoYi-Vue](https://gitee.com/y_project/RuoYi-Vue) 后端约定对齐）。

## 能力概览

- **租户模型**：`sys_tenant`（套餐 `plan_code`、席位 `seat_limit`、到期 `expire_time`）+ `sys_user`（租户内账号，`tenant_id` 外键）。
- **登录**：`POST /auth/login`，请求体为 `tenantCode` + `username` + `password`，返回 `accessToken`（JWT 内含 `tenantId` 与权限标识）。
- **数据隔离**：演示业务表 `biz_demo` 全量 SQL 带 `tenant_id`；`IBizDemoService` 从当前登录用户解析租户，禁止跨租户读写。
- **权限**：`RolePermissionRegistry` 演示「角色 → 权限字符串」映射；接口使用 `@PreAuthorize("hasAuthority('...')")`（生产可改为落库 RBAC）。
- **可观测**：`requestId` / `tenantId` / `userId` 写入 **SLF4J MDC**，控制台日志带关联字段；`AuditLogAspect` 对 Controller 统计耗时，**超过 1s 打 WARN**（不记录方法参数，避免密码进日志）。
- **登录限流**：按 **客户端 IP** 滑动窗口限制 `/auth/login`（超限 **429**）；实现为 **Caffeine**（`maximumSize` + `expireAfterAccess`），避免无限堆积 IP 状态。多实例仍建议网关或 Redis。

## 快速开始

```bash
mvn -pl ruoyi-admin -am spring-boot:run
```

默认账号（租户编码 `demo` / 用户 `admin` / 密码 `admin123`）。

### 主要接口

- `POST /auth/login`：获取 JWT。
- `GET /biz/demo/list`：分页列表（需 `Authorization: Bearer <token>`）；**未传 `pageNum`/`pageSize` 时默认第 1 页、每页 10 条**（单页最大 100），非法分页参数返回 **HTTP 400**。
- `GET /biz/demo/{id}`、`POST /biz/demo`、`PUT /biz/demo`、`DELETE /biz/demo/{id}`：演示 CRUD；`{id}` 仅数字；详情/删除在记录不存在时返回 **HTTP 404** 与业务文案。

### 安全与跨域

- **H2 Console**：仅在 **`spring.profiles.active` 含 `dev`** 时放行 `/h2-console/**`；生产勿启用 `dev`。
- **CORS**：`ruoyi.web.cors-allowed-origins` 为空时，通配来源且 **`Access-Control-Allow-Credentials=false`**（适合仅用 `Authorization` 头传 JWT）。生产可配置为具体前端域名并开启凭证。
- **Clickjacking**：非 `dev` 使用 `X-Frame-Options: SAMEORIGIN` 并开启 **`X-Content-Type-Options: nosniff`**；`dev` 下为兼容 H2 控制台放宽 frame 限制。

### MySQL

1. 创建库并执行 `sql/mysql/schema.sql`。
2. 自行插入租户与用户（密码需 BCrypt）。
3. 启动：`mvn -pl ruoyi-admin -am spring-boot:run -Dspring-boot.run.profiles=mysql`（或 `java -jar ... --spring.profiles.active=mysql`），并编辑 `ruoyi-admin/src/main/resources/application-mysql.yml` 中的数据源。

### 配置项

- `ruoyi.jwt.secret`：JWT 密钥原文（内部 SHA-256 派生为 HMAC 密钥，**生产务必修改**）。
- `ruoyi.jwt.expire-minutes`：令牌有效期（分钟）。
- `ruoyi.web.cors-allowed-origins`：跨域来源白名单；为空则通配且不携带凭证（见上文）。
- `ruoyi.web.login-max-requests-per-minute`：每 IP 每分钟登录接口上限；`≤0` 关闭限流。
- `ruoyi.web.login-rate-limiter-max-entries`：登录限流 Caffeine 最大条目数（不同 IP）。
- `ruoyi.web.login-rate-limiter-expire-after-access-minutes`：某 IP 无登录尝试多久后淘汰其限流状态。

## 模块说明

| 模块 | 说明 |
| --- | --- |
| `ruoyi-common` | `AjaxResult`、`TableDataInfo`、实体基类、`TenantContext`（可选扩展）、`LoginUser`、`SecurityUtils` 等 |
| `ruoyi-framework` | Security、JWT、`RequestLifecycleFilter`（MDC + PageHelper 清理）、`PrincipalMdcFilter`、`TablePageSupport`、`AuditLogAspect`、登录限流、全局异常、`BaseController`、登录服务 |
| `ruoyi-system` | 租户/用户/演示业务 Mapper + XML + Service |
| `ruoyi-admin` | 启动类、对外 Controller、配置文件与初始化 SQL |

## 扩展建议

- 将 `RolePermissionRegistry` 替换为 `sys_role` / `sys_menu` 与若依一致的权限模型。
- 增加「平台管理员」与租户生命周期（开通、冻结、计费）服务。
- 新业务表继承 `BaseTenantEntity`，所有 Mapper XML 强制 `tenant_id` 条件；必要时引入 SQL 审计或中间件级租户路由。
