package com.ruoyi.framework.web.aspect;

import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

/**
 * 记录 Controller 调用耗时（不记录方法参数，避免密码等敏感信息落日志）。
 */
@Aspect
@Component
public class AuditLogAspect {

    private static final Logger log = LoggerFactory.getLogger(AuditLogAspect.class);
    private static final long SLOW_MS = 1000L;

    @Around("execution(public * com.ruoyi.web.controller..*(..))")
    public Object aroundController(ProceedingJoinPoint pjp) throws Throwable {
        long start = System.currentTimeMillis();
        try {
            return pjp.proceed();
        } finally {
            long cost = System.currentTimeMillis() - start;
            String sig = pjp.getSignature().toShortString();
            if (cost >= SLOW_MS) {
                log.warn("Slow API {} took {} ms", sig, cost);
            } else if (log.isDebugEnabled()) {
                log.debug("API {} took {} ms", sig, cost);
            }
        }
    }
}
