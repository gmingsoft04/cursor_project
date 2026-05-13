package com.ruoyi.framework.config.properties;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "ruoyi.jwt")
public class JwtProperties {
    /**
     * HS256 密钥原文（内部会 SHA-256 派生为 256-bit）。
     */
    private String secret = "ChangeMeRuoyiJwtSecretKeyMustBeLongEnoughForHmacSha256";
    private long expireMinutes = 120;

    public String getSecret() {
        return secret;
    }

    public void setSecret(String secret) {
        this.secret = secret;
    }

    public long getExpireMinutes() {
        return expireMinutes;
    }

    public void setExpireMinutes(long expireMinutes) {
        this.expireMinutes = expireMinutes;
    }
}
