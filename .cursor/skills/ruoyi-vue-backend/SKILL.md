---
name: ruoyi-vue-backend
description: 若依 RuoYi-Vue 前后端分离版后端（Spring Boot、Spring Security、JWT、Redis、MyBatis）的开发规范与工作流程。在用户维护/扩展若依后端、权限、代码生成、定时任务或排查接口与安全相关问题时使用。
paths:
  - "**/ruoyi-*/**"
---

# 若依 RuoYi-Vue 标准后端 Skill

本 Skill 对齐官方仓库：[RuoYi-Vue（Gitee）](https://gitee.com/y_project/RuoYi-Vue)。文档站：[http://doc.ruoyi.vip](http://doc.ruoyi.vip)。

## 何时使用

- 新增业务模块、菜单权限、接口与数据库表。
- 修改登录鉴权、JWT、Redis 会话、数据权限、操作日志。
- 使用或扩展代码生成器、定时任务（Quartz）、多数据源。
- 排查 `AjaxResult`、`TableDataInfo`、分页、全局异常与 XSS 相关行为。

## 技术栈与分支约定

| 维度 | 说明 |
| --- | --- |
| 默认分支 | `master` 对应 Spring Boot 4.x（JDK 17+） |
| 其它后端分支 | `springboot3`（Boot 3）、`springboot2`（Boot 2 / JDK 8+） |
| 安全 | Spring Security + JWT，多终端可扩展 |
| ORM | MyBatis（XML + Mapper 接口） |
| 缓存 | Redis（会话、字典、参数等按需） |

实现前确认当前仓库所用 **Boot 版本与 JDK**，依赖与包名（`jakarta.*` vs `javax.*`）随分支变化。

## Maven 多模块职责（典型）

| 模块 | 职责 |
| --- | --- |
| `ruoyi-admin` | Spring Boot 启动入口、打包可执行、部分对外 Controller |
| `ruoyi-common` | 通用工具、常量、枚举、异常、注解、JSON/XSS 等横切能力 |
| `ruoyi-framework` | Security 配置、Web 配置、AOP、Redis、数据源、拦截器 |
| `ruoyi-system` | 系统管理域（用户、角色、菜单、部门、字典、参数等） |
| `ruoyi-quartz` | 定时任务与调度日志 |
| `ruoyi-generator` | 代码生成（Java、Vue、SQL、XML 等） |

更细的包结构与扩展点见：`references/MODULES.md`。

## 分层与命名（必须遵守）

1. **Controller**：接收请求、参数校验、调用 Service；不写复杂业务与 SQL。
2. **Service**：业务与事务边界；接口 `IXxxService` + 实现 `XxxServiceImpl` 为若依惯例。
3. **Mapper**：数据访问；接口与 `resources/mapper/**/*.xml` 一一对应。
4. **Domain / Entity**：与表或视图映射；业务实体可放 `domain`，注意与代码生成器输出风格一致。

## 接口与返回体约定

- 单对象 / 操作结果：统一 `AjaxResult`（含 `success`、`warn`、`error` 等工厂方法）。
- 分页列表：`TableDataInfo` + `startPage()`（PageHelper）在 Service 查询前开启分页。
- 权限：方法级 `@PreAuthorize`，权限字符串与菜单「权限标识」一致，例如 `@ss.hasPermi('system:user:list')`。
- 操作日志：`@Log(title = "...", businessType = BusinessType.XXX)` 与 AOP 配合写入 `sys_oper_log`。

## 新增菜单与权限的推荐顺序

1. 建表（或执行 SQL 脚本），与现有表命名风格一致（如 `sys_`、`业务前缀_`）。
2. 用代码生成器生成 `domain` / `mapper` / `service` / `controller` / `mapper.xml` / 菜单 SQL（按需调整包名与权限前缀）。
3. 在「菜单管理」中配置路由与 **权限标识**，与 `@PreAuthorize` 字符串对齐。
4. 若需数据权限：在 Service 层配合 `@DataScope` 与角色数据范围配置。

完整检查清单：`references/CHECKLIST.md`。

## 配置与安全注意

- 生产环境关闭 Swagger、关闭调试接口、修改默认口令与 JWT 密钥。
- `application-druid.yml` 等中的数据库与 Redis 连接勿提交真实密钥；使用环境变量或外部配置。
- 文件上传、任意路径、SQL 拼接为高风险点；沿用框架已有工具与白名单策略。

## 按需深入阅读

- 模块与包约定：`references/MODULES.md`
- Controller / Service / Mapper / 安全 / 分页代码范式：`references/CODING-PATTERNS.md`

## 对 Agent 的执行要求

- 修改前先定位模块（`ruoyi-admin` / `ruoyi-system` / 业务子模块），避免把业务逻辑写进 `ruoyi-framework` 核心配置类中除非确属横切需求。
- 保持与现有类相同的注解风格、日志、异常处理与返回类型。
- 涉及权限与菜单时，同时检查 **前端路由 meta.permissions** 与后端 `@PreAuthorize` 是否一致（若仓库含前端）。
- 数据库变更提供可回滚的 SQL，并与代码生成或手写 Mapper 同步。
