package com.ruoyi.system.domain;

import com.ruoyi.common.core.domain.BaseTenantEntity;

import java.io.Serial;
import java.math.BigDecimal;

/**
 * 多租户演示业务表：所有 SQL 必须带 tenant_id 条件。
 */
public class BizDemo extends BaseTenantEntity {
    @Serial
    private static final long serialVersionUID = 1L;

    private Long id;
    private String name;
    private BigDecimal amount;

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public BigDecimal getAmount() {
        return amount;
    }

    public void setAmount(BigDecimal amount) {
        this.amount = amount;
    }
}
