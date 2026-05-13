package com.ruoyi.common.exception;

/**
 * 业务异常，由全局异常处理器转换为 AjaxResult。
 */
public class ServiceException extends RuntimeException {
    private static final long serialVersionUID = 1L;
    private final Integer code;

    public ServiceException(String message) {
        super(message);
        this.code = null;
    }

    public ServiceException(int code, String message) {
        super(message);
        this.code = code;
    }

    public Integer getCode() {
        return code;
    }
}
