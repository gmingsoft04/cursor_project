package com.ruoyi.common.tenant;

/**
 * 当前请求租户上下文（可选扩展点）。业务代码请优先使用 {@link com.ruoyi.common.utils.SecurityUtils#getTenantId()}，
 * 与 JWT 中的租户信息保持一致；避免与过滤器生命周期不同步。
 */
public final class TenantContext {
    private static final ThreadLocal<Long> TENANT_ID = new ThreadLocal<>();

    private TenantContext() {
    }

    public static void setTenantId(Long tenantId) {
        TENANT_ID.set(tenantId);
    }

    public static Long getTenantId() {
        return TENANT_ID.get();
    }

    public static void clear() {
        TENANT_ID.remove();
    }
}
