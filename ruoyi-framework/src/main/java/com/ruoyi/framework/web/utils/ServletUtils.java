package com.ruoyi.framework.web.utils;

import org.springframework.web.context.request.RequestAttributes;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

import jakarta.servlet.http.HttpServletRequest;

/**
 * Servlet 请求工具（轻量版）。
 */
public final class ServletUtils {
    private ServletUtils() {
    }

    public static HttpServletRequest getRequest() {
        RequestAttributes attrs = RequestContextHolder.getRequestAttributes();
        if (!(attrs instanceof ServletRequestAttributes servletRequestAttributes)) {
            return null;
        }
        return servletRequestAttributes.getRequest();
    }

    public static String getParameter(String name) {
        HttpServletRequest request = getRequest();
        return request != null ? request.getParameter(name) : null;
    }
}
