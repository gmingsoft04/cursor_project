package com.ruoyi.framework.web.filter;

import com.ruoyi.common.utils.SecurityUtils;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.MDC;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

/**
 * 在 Security 认证完成之后，将用户与租户写入 MDC，便于日志关联（由外层 {@link RequestLifecycleFilter} 统一 clear）。
 */
@Component
@Order(Ordered.LOWEST_PRECEDENCE)
public class PrincipalMdcFilter extends OncePerRequestFilter {

    public static final String MDC_USER_ID = "userId";
    public static final String MDC_TENANT_ID = "tenantId";
    public static final String MDC_USERNAME = "username";

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
            throws ServletException, IOException {
        var loginUser = SecurityUtils.getLoginUser();
        if (loginUser != null) {
            if (loginUser.getUserId() != null) {
                MDC.put(MDC_USER_ID, String.valueOf(loginUser.getUserId()));
            }
            if (loginUser.getTenantId() != null) {
                MDC.put(MDC_TENANT_ID, String.valueOf(loginUser.getTenantId()));
            }
            if (loginUser.getUsername() != null) {
                MDC.put(MDC_USERNAME, loginUser.getUsername());
            }
        }
        filterChain.doFilter(request, response);
    }
}
