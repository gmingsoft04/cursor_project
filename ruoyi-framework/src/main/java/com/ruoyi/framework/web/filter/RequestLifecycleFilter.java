package com.ruoyi.framework.web.filter;

import com.github.pagehelper.PageHelper;
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
import java.util.UUID;

/**
 * 请求入口：写入 requestId 到 MDC；出口：清理 PageHelper 与 MDC，避免线程复用污染。
 */
@Component
@Order(Ordered.HIGHEST_PRECEDENCE)
public class RequestLifecycleFilter extends OncePerRequestFilter {

    public static final String MDC_REQUEST_ID = "requestId";

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
            throws ServletException, IOException {
        MDC.put(MDC_REQUEST_ID, UUID.randomUUID().toString().replace("-", ""));
        try {
            filterChain.doFilter(request, response);
        } finally {
            PageHelper.clearPage();
            MDC.clear();
        }
    }
}
