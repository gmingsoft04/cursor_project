package com.ruoyi.framework.security;

import com.ruoyi.common.constant.HttpStatus;
import com.ruoyi.common.exception.ServiceException;
import com.ruoyi.framework.config.properties.WebProperties;
import org.springframework.stereotype.Component;

import java.util.ArrayDeque;
import java.util.Deque;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 登录接口按客户端 IP 的滑动窗口限流（进程内内存实现，多实例需网关或 Redis 限流）。
 */
@Component
public class LoginRateLimiter {

    private static final long WINDOW_MS = 60_000L;

    private final WebProperties webProperties;
    private final ConcurrentHashMap<String, Deque<Long>> buckets = new ConcurrentHashMap<>();

    public LoginRateLimiter(WebProperties webProperties) {
        this.webProperties = webProperties;
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
        Deque<Long> dq = buckets.computeIfAbsent(key, k -> new ArrayDeque<>());
        synchronized (dq) {
            while (!dq.isEmpty() && dq.peekFirst() < now - WINDOW_MS) {
                dq.pollFirst();
            }
            if (dq.size() >= max) {
                throw new ServiceException(HttpStatus.TOO_MANY_REQUESTS, "登录请求过于频繁，请稍后再试");
            }
            dq.addLast(now);
        }
    }
}
