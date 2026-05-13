package com.ruoyi.system.domain;

import com.ruoyi.common.core.domain.BaseEntity;

import java.io.Serial;

/**
 * 租户内用户（平台级账号可将 tenantId 置空，按需扩展）。
 */
public class SysUser extends BaseEntity {
    @Serial
    private static final long serialVersionUID = 1L;

    private Long id;
    private Long tenantId;
    private String username;
    private String password;
    private String nickName;
    private String status;
    /** 角色标识，用于生成权限集合，如 TENANT_ADMIN */
    private String roleKey;

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public Long getTenantId() {
        return tenantId;
    }

    public void setTenantId(Long tenantId) {
        this.tenantId = tenantId;
    }

    public String getUsername() {
        return username;
    }

    public void setUsername(String username) {
        this.username = username;
    }

    public String getPassword() {
        return password;
    }

    public void setPassword(String password) {
        this.password = password;
    }

    public String getNickName() {
        return nickName;
    }

    public void setNickName(String nickName) {
        this.nickName = nickName;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String getRoleKey() {
        return roleKey;
    }

    public void setRoleKey(String roleKey) {
        this.roleKey = roleKey;
    }
}
