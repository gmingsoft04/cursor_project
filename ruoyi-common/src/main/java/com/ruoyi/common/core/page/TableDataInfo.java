package com.ruoyi.common.core.page;

import com.ruoyi.common.constant.HttpStatus;

import java.io.Serial;
import java.io.Serializable;
import java.util.List;

/**
 * 分页表格数据（若依 TableDataInfo 简化版）。
 */
public class TableDataInfo implements Serializable {
    @Serial
    private static final long serialVersionUID = 1L;
    private long total;
    private List<?> rows;
    private int code;
    private String msg;

    public TableDataInfo() {
    }

    public TableDataInfo(List<?> rows, long total) {
        this.rows = rows;
        this.total = total;
        this.code = HttpStatus.SUCCESS;
        this.msg = "查询成功";
    }

    public long getTotal() {
        return total;
    }

    public void setTotal(long total) {
        this.total = total;
    }

    public List<?> getRows() {
        return rows;
    }

    public void setRows(List<?> rows) {
        this.rows = rows;
    }

    public int getCode() {
        return code;
    }

    public void setCode(int code) {
        this.code = code;
    }

    public String getMsg() {
        return msg;
    }

    public void setMsg(String msg) {
        this.msg = msg;
    }
}
