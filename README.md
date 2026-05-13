# universal-saas

基于 **若依式 Maven 多模块**（`ruoyi-common` / `ruoyi-framework` / `ruoyi-system` / `ruoyi-admin`）的通用 **SaaS 多租户** 后端骨架：Spring Boot 3、Spring Security、JWT、MyBatis、PageHelper；默认 **H2 内存库** 一键启动，可选 **MySQL** 配置。

仓库内同时包含 Cursor Agent Skill：`.cursor/skills/ruoyi-vue-backend/`（与 [RuoYi-Vue](https://gitee.com/y_project/RuoYi-Vue) 后端约定对齐）。

## 能力概览

- **租户模型**：`sys_tenant`（套餐 `plan_code`、席位 `seat_limit`、到期 `expire_time`）+ `sys_user`（租户内账号，`tenant_id` 外键）。
- **登录**：`POST /auth/login`，请求体为 `tenantCode` + `username` + `password`，返回 `accessToken`（JWT 内含 `tenantId` 与权限标识）。
- **数据隔离**：演示业务表 `biz_demo` 全量 SQL 带 `tenant_id`；`IBizDemoService` 从当前登录用户解析租户，禁止跨租户读写。
- **权限**：`RolePermissionRegistry` 演示「角色 → 权限字符串」映射；接口使用 `@PreAuthorize("hasAuthority('...')")`（生产可改为落库 RBAC）。

## 快速开始

```bash
mvn -pl ruoyi-admin -am spring-boot:run
```

默认账号（租户编码 `demo` / 用户 `admin` / 密码 `admin123`）。

### 主要接口

- `POST /auth/login`：获取 JWT。
- `GET /biz/demo/list?pageNum=1&pageSize=10`：分页列表（需 `Authorization: Bearer <token>`）。
- `GET /biz/demo/{id}`、`POST /biz/demo`、`PUT /biz/demo`、`DELETE /biz/demo/{id}`：演示 CRUD。

### MySQL

1. 创建库并执行 `sql/mysql/schema.sql`。
2. 自行插入租户与用户（密码需 BCrypt）。
3. 启动：`mvn -pl ruoyi-admin -am spring-boot:run -Dspring-boot.run.profiles=mysql`（或 `java -jar ... --spring.profiles.active=mysql`），并编辑 `ruoyi-admin/src/main/resources/application-mysql.yml` 中的数据源。

### 配置项

- `ruoyi.jwt.secret`：JWT 密钥原文（内部 SHA-256 派生为 HMAC 密钥，**生产务必修改**）。
- `ruoyi.jwt.expire-minutes`：令牌有效期（分钟）。

## 模块说明

| 模块 | 说明 |
| --- | --- |
| `ruoyi-common` | `AjaxResult`、`TableDataInfo`、实体基类、`TenantContext`、`LoginUser`、`SecurityUtils` 等 |
| `ruoyi-framework` | Security、JWT 过滤器、全局异常、`BaseController`、登录服务 |
| `ruoyi-system` | 租户/用户/演示业务 Mapper + XML + Service |
| `ruoyi-admin` | 启动类、对外 Controller、配置文件与初始化 SQL |

## 扩展建议

- 将 `RolePermissionRegistry` 替换为 `sys_role` / `sys_menu` 与若依一致的权限模型。
- 增加「平台管理员」与租户生命周期（开通、冻结、计费）服务。
- 新业务表继承 `BaseTenantEntity`，所有 Mapper XML 强制 `tenant_id` 条件；必要时引入 SQL 审计或中间件级租户路由。
