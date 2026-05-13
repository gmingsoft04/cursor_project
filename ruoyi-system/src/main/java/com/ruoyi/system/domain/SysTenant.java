package com.ruoyi.system.domain;

import com.ruoyi.common.core.domain.BaseEntity;

import java.io.Serial;
import java.time.LocalDateTime;

/**
 * 租户（SaaS 订阅与席位可在本实体上扩展）。
 */
public class SysTenant extends BaseEntity {
    @Serial
    private static final long serialVersionUID = 1L;

    private Long id;
    private String tenantCode;
    private String tenantName;
    private String status;
    private LocalDateTime expireTime;
    private String planCode;
    private Integer seatLimit;

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getTenantCode() {
        return tenantCode;
    }

    public void setTenantCode(String tenantCode) {
        this.tenantCode = tenantCode;
    }

    public String getTenantName() {
        return tenantName;
    }

    public void setTenantName(String tenantName) {
        this.tenantName = tenantName;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public LocalDateTime getExpireTime() {
        return expireTime;
    }

    public void setExpireTime(LocalDateTime expireTime) {
        this.expireTime = expireTime;
    }

    public String getPlanCode() {
        return planCode;
    }

    public void setPlanCode(String planCode) {
        this.planCode = planCode;
    }

    public Integer getSeatLimit() {
        return seatLimit;
    }

    public void setSeatLimit(Integer seatLimit) {
        this.seatLimit = seatLimit;
    }
}
