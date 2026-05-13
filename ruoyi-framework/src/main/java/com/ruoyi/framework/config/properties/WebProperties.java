package com.ruoyi.framework.config.properties;

import org.springframework.boot.context.properties.ConfigurationProperties;

import java.util.ArrayList;
import java.util.List;

/**
 * Web 层可配置项（CORS 等）。
 */
@ConfigurationProperties(prefix = "ruoyi.web")
public class WebProperties {

    /**
     * 允许携带凭证的跨域来源列表。为空时使用通配且 {@code allowCredentials=false}（适合仅通过 Authorization 头传 JWT 的 API）。
     */
    private List<String> corsAllowedOrigins = new ArrayList<>();

    public List<String> getCorsAllowedOrigins() {
        return corsAllowedOrigins;
    }

    public void setCorsAllowedOrigins(List<String> corsAllowedOrigins) {
        this.corsAllowedOrigins = corsAllowedOrigins != null ? corsAllowedOrigins : new ArrayList<>();
    }

    /**
     * 同一客户端 IP 每分钟允许调用登录接口的最大次数（进程内限流）。≤0 表示关闭。
     */
    private int loginMaxRequestsPerMinute = 60;

    public int getLoginMaxRequestsPerMinute() {
        return loginMaxRequestsPerMinute;
    }

    public void setLoginMaxRequestsPerMinute(int loginMaxRequestsPerMinute) {
        this.loginMaxRequestsPerMinute = loginMaxRequestsPerMinute;
    }
}
