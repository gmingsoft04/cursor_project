package com.ruoyi.common.core.domain;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.ruoyi.common.constant.HttpStatus;

import java.util.HashMap;
import java.util.Map;

/**
 * 统一响应体（若依风格）。
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
public class AjaxResult extends HashMap<String, Object> {
    private static final long serialVersionUID = 1L;

    public static AjaxResult success() {
        return success("操作成功");
    }

    public static AjaxResult success(Object data) {
        return success("操作成功", data);
    }

    public static AjaxResult success(String msg, Object data) {
        AjaxResult r = new AjaxResult();
        r.put("code", HttpStatus.SUCCESS);
        r.put("msg", msg);
        r.put("data", data);
        return r;
    }

    public static AjaxResult warn(String msg) {
        AjaxResult r = new AjaxResult();
        r.put("code", HttpStatus.WARN);
        r.put("msg", msg);
        return r;
    }

    public static AjaxResult error(String msg) {
        return error(HttpStatus.ERROR, msg);
    }

    public static AjaxResult error(int code, String msg) {
        AjaxResult r = new AjaxResult();
        r.put("code", code);
        r.put("msg", msg);
        return r;
    }

    public AjaxResult put(String key, Object value) {
        super.put(key, value);
        return this;
    }

    @SuppressWarnings("unchecked")
    public static AjaxResult fromMap(Map<String, Object> map) {
        AjaxResult r = new AjaxResult();
        r.putAll(map);
        return r;
    }
}
