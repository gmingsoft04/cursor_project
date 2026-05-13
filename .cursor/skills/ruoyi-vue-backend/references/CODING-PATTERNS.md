# RuoYi-Vue 后端编码范式参考

以下模式与官方示例一致；具体类名以仓库为准。

## Controller

```java
@RestController
@RequestMapping("/system/demo")
public class DemoController extends BaseController {

    @Autowired
    private IDemoService demoService;

    @PreAuthorize("@ss.hasPermi('system:demo:list')")
    @GetMapping("/list")
    public TableDataInfo list(Demo demo) {
        startPage();
        List<Demo> list = demoService.selectDemoList(demo);
        return getDataTable(list);
    }

    @PreAuthorize("@ss.hasPermi('system:demo:query')")
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") Long id) {
        return success(demoService.selectDemoById(id));
    }

    @PreAuthorize("@ss.hasPermi('system:demo:add')")
    @Log(title = "示例", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@Validated @RequestBody Demo demo) {
        return toAjax(demoService.insertDemo(demo));
    }
}
```

要点：

- 继承 `BaseController` 以使用 `startPage()`、`getDataTable()`、`success()`、`toAjax()` 等。
- 增删改使用 `@Log` 记录操作类型。
- 入参校验：`@Validated` + Bean 上的 JSR-303 注解。

## Service

```java
@Service
public class DemoServiceImpl implements IDemoService {
    @Autowired
    private DemoMapper demoMapper;

    @Override
    @DataScope(deptAlias = "d", userAlias = "u")
    public List<Demo> selectDemoList(Demo demo) {
        return demoMapper.selectDemoList(demo);
    }
}
```

要点：

- 接口 `IDemoService` 与实现 `DemoServiceImpl` 分离。
- 需要数据权限时加 `@DataScope`，别名与 Mapper XML 中表别名一致。

## Mapper 接口与 XML

- 接口方法名与 XML `id` 一致。
- 动态 SQL 使用 `<if>`、`<where>`，避免字符串拼接导致 SQL 注入。
- 批量插入/更新优先使用 MyBatis 动态 SQL 或 `foreach`。

## 返回体

| 场景 | 类型 |
| --- | --- |
| 非分页列表 / 详情 / 布尔结果 | `AjaxResult` |
| 分页表格 | `TableDataInfo`（配合 `startPage`） |

## 权限字符串

- 格式习惯：`模块:功能:操作`，如 `system:user:edit`。
- 需与菜单管理中「权限标识」一致，前端按钮 `v-hasPermi` 同源。

## 异常

- 业务可抛出 `ServiceException`（或项目统一业务异常），由全局异常处理器转为 `AjaxResult`。
- 不要在 Controller 吞掉异常并返回 null；保持与框架一致的错误码与消息。

## 工具类

- 优先使用 `ruoyi-common` 中已有 `StringUtils`、`DateUtils`、`SecurityUtils` 等，避免重复造轮子。
