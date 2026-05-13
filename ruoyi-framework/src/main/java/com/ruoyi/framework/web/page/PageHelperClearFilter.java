package com.ruoyi.framework.web.page;

import com.github.pagehelper.PageHelper;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

/**
 * 请求结束后清理 PageHelper 的 ThreadLocal，避免线程复用导致的分页串页。
 */
@Component
@Order(Ordered.HIGHEST_PRECEDENCE)
public class PageHelperClearFilter extends OncePerRequestFilter {

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
            throws ServletException, IOException {
        try {
            filterChain.doFilter(request, response);
        } finally {
            PageHelper.clearPage();
        }
    }
}
