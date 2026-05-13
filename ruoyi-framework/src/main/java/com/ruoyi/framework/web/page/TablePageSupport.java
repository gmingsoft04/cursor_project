package com.ruoyi.framework.web.page;

import com.github.pagehelper.PageHelper;
import com.ruoyi.common.constant.HttpStatus;
import com.ruoyi.common.exception.ServiceException;
import com.ruoyi.framework.web.utils.ServletUtils;
import org.apache.commons.lang3.StringUtils;

/**
 * PageHelper 分页启动：非法参数抛出业务异常；缺省时使用默认页码与页大小并限制最大值。
 */
public final class TablePageSupport {

    public static final int DEFAULT_PAGE_NUM = 1;
    public static final int DEFAULT_PAGE_SIZE = 10;
    public static final int MAX_PAGE_SIZE = 100;

    private TablePageSupport() {
    }

    /**
     * 从请求参数解析分页；均未传时使用默认第 1 页、每页 10 条，避免无意全表扫描。
     */
    public static void startPage() {
        String pageNumStr = ServletUtils.getParameter("pageNum");
        String pageSizeStr = ServletUtils.getParameter("pageSize");
        boolean blankNum = StringUtils.isBlank(pageNumStr);
        boolean blankSize = StringUtils.isBlank(pageSizeStr);
        if (blankNum && blankSize) {
            PageHelper.startPage(DEFAULT_PAGE_NUM, DEFAULT_PAGE_SIZE);
            return;
        }
        int pageNum = blankNum ? DEFAULT_PAGE_NUM : parsePositiveInt(pageNumStr, "pageNum");
        int pageSize = blankSize ? DEFAULT_PAGE_SIZE : parsePositiveInt(pageSizeStr, "pageSize");
        if (pageNum < 1) {
            pageNum = DEFAULT_PAGE_NUM;
        }
        if (pageSize < 1) {
            pageSize = DEFAULT_PAGE_SIZE;
        }
        if (pageSize > MAX_PAGE_SIZE) {
            pageSize = MAX_PAGE_SIZE;
        }
        PageHelper.startPage(pageNum, pageSize);
    }

    private static int parsePositiveInt(String raw, String paramName) {
        try {
            return Integer.parseInt(raw.trim());
        } catch (NumberFormatException e) {
            throw new ServiceException(HttpStatus.BAD_REQUEST, paramName + " 必须为有效整数");
        }
    }
}
