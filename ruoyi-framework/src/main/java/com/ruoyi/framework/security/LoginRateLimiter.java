package com.ruoyi.framework.security;

import com.github.benmanes.caffeine.cache.Cache;
import com.github.benmanes.caffeine.cache.Caffeine;
import com.ruoyi.common.constant.HttpStatus;
import com.ruoyi.common.exception.ServiceException;
import com.ruoyi.framework.config.properties.WebProperties;
import org.springframework.stereotype.Component;

import java.time.Duration;
import java.util.ArrayDeque;
import java.util.Deque;

/**
 * 登录接口按客户端 IP 的滑动窗口限流；底层使用 Caffeine 限制最大跟踪 IP 数并在无访问后淘汰，避免内存无限增长。
 * 使用 {@link Cache#asMap()} 的原子 {@code compute} 更新窗口，避免淘汰与手动同步的竞态。
 */
@Component
public class LoginRateLimiter {

    private static final long WINDOW_MS = 60_000L;

    private final WebProperties webProperties;
    private final Cache<String, Deque<Long>> buckets;

    public LoginRateLimiter(WebProperties webProperties) {
        this.webProperties = webProperties;
        this.buckets = Caffeine.newBuilder()
                .maximumSize(Math.max(1L, webProperties.getLoginRateLimiterMaxEntries()))
                .expireAfterAccess(Duration.ofMinutes(Math.max(1, webProperties.getLoginRateLimiterExpireAfterAccessMinutes())))
                .build();
    }

    /**
     * 记录一次登录尝试；超过阈值抛出 429。
     */
    public void checkAndRecord(String clientIp) {
        int max = webProperties.getLoginMaxRequestsPerMinute();
        if (max <= 0) {
            return;
        }
        String key = "login:" + (clientIp == null || clientIp.isBlank() ? "unknown" : clientIp);
        long now = System.currentTimeMillis();
        buckets.asMap().compute(key, (k, existing) -> {
            Deque<Long> dq = existing == null ? new ArrayDeque<>() : existing;
            while (!dq.isEmpty() && dq.peekFirst() < now - WINDOW_MS) {
                dq.pollFirst();
            }
            if (dq.size() >= max) {
                throw new ServiceException(HttpStatus.TOO_MANY_REQUESTS, "登录请求过于频繁，请稍后再试");
            }
            dq.addLast(now);
            return dq;
        });
    }
}
