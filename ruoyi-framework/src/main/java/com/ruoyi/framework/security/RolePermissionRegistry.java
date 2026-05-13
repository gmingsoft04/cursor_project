package com.ruoyi.framework.security;

import org.springframework.stereotype.Component;

import java.util.LinkedHashSet;
import java.util.Map;
import java.util.Set;

/**
 * 演示用：角色到权限标识的映射。生产环境建议落库 sys_role / sys_menu。
 */
@Component
public class RolePermissionRegistry {
    private static final Map<String, Set<String>> ROLE_TO_PERMS = Map.of(
            "TENANT_ADMIN", Set.of(
                    "biz:demo:list",
                    "biz:demo:query",
                    "biz:demo:add",
                    "biz:demo:edit",
                    "biz:demo:remove"
            ),
            "TENANT_USER", Set.of(
                    "biz:demo:list",
                    "biz:demo:query"
            )
    );

    public Set<String> resolvePermissions(String roleKey) {
        if (roleKey == null || roleKey.isBlank()) {
            return Set.of();
        }
        return new LinkedHashSet<>(ROLE_TO_PERMS.getOrDefault(roleKey, Set.of()));
    }
}
