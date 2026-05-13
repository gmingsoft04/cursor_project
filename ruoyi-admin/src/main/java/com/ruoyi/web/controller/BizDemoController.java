package com.ruoyi.web.controller;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.page.TableDataInfo;
import com.ruoyi.framework.web.core.BaseController;
import com.ruoyi.system.domain.BizDemo;
import com.ruoyi.system.service.IBizDemoService;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

/**
 * 多租户演示业务：所有数据按 JWT 中的 tenantId 隔离。
 */
@RestController
@RequestMapping("/biz/demo")
public class BizDemoController extends BaseController {

    private final IBizDemoService bizDemoService;

    public BizDemoController(IBizDemoService bizDemoService) {
        this.bizDemoService = bizDemoService;
    }

    @PreAuthorize("hasAuthority('biz:demo:list')")
    @GetMapping("/list")
    public TableDataInfo list(BizDemo query) {
        startPage();
        List<BizDemo> list = bizDemoService.selectList(query);
        return getDataTable(list);
    }

    @PreAuthorize("hasAuthority('biz:demo:query')")
    @GetMapping("/{id}")
    public AjaxResult get(@PathVariable Long id) {
        return AjaxResult.success(bizDemoService.selectById(id));
    }

    @PreAuthorize("hasAuthority('biz:demo:add')")
    @PostMapping
    public AjaxResult add(@RequestBody BizDemo row) {
        return toAjax(bizDemoService.insert(row));
    }

    @PreAuthorize("hasAuthority('biz:demo:edit')")
    @PutMapping
    public AjaxResult edit(@RequestBody BizDemo row) {
        return toAjax(bizDemoService.update(row));
    }

    @PreAuthorize("hasAuthority('biz:demo:remove')")
    @DeleteMapping("/{id}")
    public AjaxResult remove(@PathVariable Long id) {
        return toAjax(bizDemoService.deleteById(id));
    }
}
