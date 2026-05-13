# RuoYi-Vue 后端模块与包结构参考

## 官方仓库说明

- 源码：<https://gitee.com/y_project/RuoYi-Vue>
- 前后端分离：本 Skill 侧重 **Java 后端**；前端可为 Vue2（`ruoyi-ui`）或官方推荐的 Vue3 等独立仓库。

## `ruoyi-admin`

- 包含 `*Application.java` 启动类与 `application.yml` 等入口配置。
- 常放置 **对外业务 Controller**（或聚合各业务模块的依赖）。
- `resources` 下可有 `banner.txt`、`i18n`、静态资源等。

## `ruoyi-common`

典型子包（以官方为准，不同分支可能微调）：

- `annotation`：自定义注解（如 Excel、日志、数据权限等）。
- `config`：通用配置类。
- `constant`：常量。
- `core`：核心文本、控制器基类等。
- `enums`：业务枚举。
- `exception`：全局异常与业务异常。
- `json`：序列化相关。
- `utils`：字符串、日期、文件、安全等工具。
- `xss`：XSS 过滤相关。

**原则**：无具体业务表逻辑；被其它模块依赖。

## `ruoyi-framework`

- **Security**：认证过滤器、UserDetails、权限元数据、JWT 签发与校验。
- **Web**：跨域、重复提交、全局异常处理器绑定等。
- **Aspect**：数据权限切面、日志切面等。
- **Redis / DataSource**：缓存与数据源配置。

**原则**：框架级能力；新增业务表相关代码一般不放这里。

## `ruoyi-system`

- `domain`：`SysUser`、`SysRole`、`SysMenu` 等与 `sys_*` 表对应实体。
- `mapper` + `resources/mapper/system/*.xml`：系统管理 SQL。
- `service`：系统管理业务实现。

业务子模块（若依 Pro 或自建）常复制此结构为 `ruoyi-xxx`。

## `ruoyi-quartz`

- `domain`：任务与日志实体。
- `task`：示例 `RyTask` 等，业务定时方法建议集中在明确命名的 Bean 中，便于在「定时任务」菜单里配置调用目标字符串。

## `ruoyi-generator`

- Velocity 模板与生成配置；改模板会影响生成代码风格，需谨慎并与团队规范统一。

## 资源文件约定

- MyBatis XML：`模块/src/main/resources/mapper/**/*.xml`，`namespace` 指向 Mapper 接口全限定名。
- Mapper 接口：`@Mapper` 或在启动类同包路径扫描。

## 业务扩展的常见做法

1. **新建 Maven 模块** `ruoyi-<业务名>`，依赖 `ruoyi-common`，按需依赖 `ruoyi-system`。
2. 在 `ruoyi-admin` 的 `pom.xml` 中引入新业务模块。
3. 启动类所在包或 `@MapperScan` 需覆盖新业务 Mapper 包（按项目现有方式配置）。
