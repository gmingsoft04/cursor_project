package com.ruoyi.common.utils;

import com.ruoyi.common.core.domain.model.LoginUser;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;

/**
 * 安全工具（仅依赖 spring-security-core，可在 system 模块使用）。
 */
public final class SecurityUtils {
    private SecurityUtils() {
    }

    public static LoginUser getLoginUser() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        if (authentication == null || !authentication.isAuthenticated()) {
            return null;
        }
        Object principal = authentication.getPrincipal();
        if (principal instanceof LoginUser loginUser) {
            return loginUser;
        }
        return null;
    }

    public static Long getTenantId() {
        LoginUser u = getLoginUser();
        return u != null ? u.getTenantId() : null;
    }

    public static Long getUserId() {
        LoginUser u = getLoginUser();
        return u != null ? u.getUserId() : null;
    }
}
