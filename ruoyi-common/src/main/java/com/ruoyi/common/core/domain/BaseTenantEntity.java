package com.ruoyi.common.core.domain;

import java.io.Serial;

/**
 * 带租户隔离字段的实体基类：业务表建议继承此类并保证 Mapper 中 WHERE 含 tenant_id。
 */
public class BaseTenantEntity extends BaseEntity {
    @Serial
    private static final long serialVersionUID = 1L;

    private Long tenantId;

    public Long getTenantId() {
        return tenantId;
    }

    public void setTenantId(Long tenantId) {
        this.tenantId = tenantId;
    }
}
