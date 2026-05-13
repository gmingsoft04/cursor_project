package com.ruoyi.common.constant;

/**
 * 返回状态码（与若依 AjaxResult 习惯对齐的常用值）。
 */
public final class HttpStatus {
    public static final int SUCCESS = 200;
    public static final int CREATED = 201;
    public static final int WARN = 601;
    public static final int ERROR = 500;
    public static final int UNAUTHORIZED = 401;
    public static final int FORBIDDEN = 403;
    public static final int NOT_FOUND = 404;
    public static final int BAD_REQUEST = 400;
    public static final int TOO_MANY_REQUESTS = 429;

    private HttpStatus() {
    }
}
