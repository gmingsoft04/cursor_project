package com.ruoyi.common.core.domain.model.request;

import jakarta.validation.constraints.NotBlank;

/**
 * 登录请求体：租户编码 + 用户名 + 密码。
 */
public class LoginBody {
    @NotBlank(message = "租户编码不能为空")
    private String tenantCode;
    @NotBlank(message = "用户名不能为空")
    private String username;
    @NotBlank(message = "密码不能为空")
    private String password;

    public String getTenantCode() {
        return tenantCode;
    }

    public void setTenantCode(String tenantCode) {
        this.tenantCode = tenantCode;
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
}
