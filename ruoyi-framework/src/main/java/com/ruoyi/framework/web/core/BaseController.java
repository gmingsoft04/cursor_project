package com.ruoyi.framework.web.core;

import com.github.pagehelper.PageHelper;
import com.github.pagehelper.PageInfo;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.page.TableDataInfo;
import com.ruoyi.framework.web.utils.ServletUtils;
import org.apache.commons.lang3.StringUtils;

import java.util.List;

/**
 * Web 层通用能力（分页与表格封装，对齐若依 BaseController 用法）。
 */
public class BaseController {

    protected void startPage() {
        String pageNumStr = ServletUtils.getParameter("pageNum");
        String pageSizeStr = ServletUtils.getParameter("pageSize");
        if (StringUtils.isNotEmpty(pageNumStr) && StringUtils.isNotEmpty(pageSizeStr)) {
            int pageNum = Integer.parseInt(pageNumStr);
            int pageSize = Integer.parseInt(pageSizeStr);
            PageHelper.startPage(pageNum, pageSize);
        }
    }

    protected TableDataInfo getDataTable(List<?> list) {
        PageInfo<?> pageInfo = new PageInfo<>(list);
        return new TableDataInfo(list, pageInfo.getTotal());
    }

    protected AjaxResult success() {
        return AjaxResult.success();
    }

    protected AjaxResult success(Object data) {
        return AjaxResult.success(data);
    }

    protected AjaxResult toAjax(int rows) {
        return rows > 0 ? AjaxResult.success() : AjaxResult.error("操作失败");
    }
}
