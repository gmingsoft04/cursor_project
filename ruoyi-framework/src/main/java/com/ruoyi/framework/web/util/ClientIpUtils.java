package com.ruoyi.framework.web.util;

import jakarta.servlet.http.HttpServletRequest;
import org.apache.commons.lang3.StringUtils;

/**
 * 解析客户端 IP（优先 X-Forwarded-For 第一段，需网关可信时配合使用）。
 */
public final class ClientIpUtils {

    private ClientIpUtils() {
    }

    public static String resolve(HttpServletRequest request) {
        if (request == null) {
            return "";
        }
        String xff = request.getHeader("X-Forwarded-For");
        if (StringUtils.isNotBlank(xff)) {
            int comma = xff.indexOf(',');
            String first = comma > 0 ? xff.substring(0, comma).trim() : xff.trim();
            if (StringUtils.isNotBlank(first)) {
                return first;
            }
        }
        String realIp = request.getHeader("X-Real-IP");
        if (StringUtils.isNotBlank(realIp)) {
            return realIp.trim();
        }
        return StringUtils.defaultString(request.getRemoteAddr(), "");
    }
}
