package com.ruoyi.framework.web.exception;

import com.ruoyi.common.constant.HttpStatus;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.exception.ServiceException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.validation.BindException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;

/**
 * 全局异常处理（若依风格 AjaxResult）。
 */
@RestControllerAdvice
public class GlobalExceptionHandler {
    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    @ExceptionHandler(ServiceException.class)
    public AjaxResult handleServiceException(ServiceException e) {
        Integer code = e.getCode();
        return code != null ? AjaxResult.error(code, e.getMessage()) : AjaxResult.error(e.getMessage());
    }

    @ExceptionHandler({MethodArgumentNotValidException.class, BindException.class})
    public AjaxResult handleValidation(Exception e) {
        String msg = "参数校验失败";
        if (e instanceof MethodArgumentNotValidException m) {
            var fe = m.getBindingResult().getFieldError();
            if (fe != null) {
                msg = fe.getDefaultMessage() != null ? fe.getDefaultMessage() : msg;
            }
        } else if (e instanceof BindException b) {
            var fe = b.getBindingResult().getFieldError();
            if (fe != null) {
                msg = fe.getDefaultMessage() != null ? fe.getDefaultMessage() : msg;
            }
        }
        return AjaxResult.error(HttpStatus.BAD_REQUEST, msg);
    }

    @ExceptionHandler(MethodArgumentTypeMismatchException.class)
    public AjaxResult handleTypeMismatch(MethodArgumentTypeMismatchException e) {
        return AjaxResult.error(HttpStatus.BAD_REQUEST, "路径或请求参数类型错误");
    }

    @ExceptionHandler(Exception.class)
    public AjaxResult handleException(Exception e) {
        log.error(e.getMessage(), e);
        return AjaxResult.error("系统繁忙，请稍后再试");
    }
}
