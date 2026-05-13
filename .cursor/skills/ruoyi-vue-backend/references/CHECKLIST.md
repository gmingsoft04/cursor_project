# 新功能 / 新菜单开发检查清单

## 数据库与实体

- [ ] 表名、字段命名与项目现有风格一致；必备字段（如 `create_by`、`create_time` 等）与 `BaseEntity` 对齐。
- [ ] 索引与唯一约束满足查询与权限场景。

## 代码层

- [ ] `domain`、`mapper`、`service`、`controller`、`mapper.xml` 四层齐全（或生成后已删减冗余）。
- [ ] 分页接口已调用 `startPage()`，列表返回 `getDataTable`。
- [ ] 所有对外变更类接口有 `@PreAuthorize`，字符串已在菜单中配置。
- [ ] 需要数据权限的查询已加 `@DataScope` 且 XML 中表别名匹配。

## 菜单与权限

- [ ] 菜单类型、路由、组件路径（若依 Vue）与后端模块一致。
- [ ] 按钮级权限标识与 Controller 一致。

## 日志与审计

- [ ] 写操作带 `@Log`，`businessType` 正确。

## 配置与部署

- [ ] 新增配置项写入 `application.yml` 或 profile 文件，并文档化默认值。
- [ ] 未将敏感信息硬编码进仓库。

## 验证

- [ ] 单元测试或至少手工验证：列表、详情、增删改、权限拒绝场景。
- [ ] Swagger / 接口文档（若启用）描述可读。
