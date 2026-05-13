package com.ruoyi.framework.web.service.impl;

import com.ruoyi.common.exception.ServiceException;
import com.ruoyi.common.core.domain.model.LoginUser;
import com.ruoyi.common.core.domain.model.request.LoginBody;
import com.ruoyi.framework.config.properties.JwtProperties;
import com.ruoyi.framework.security.JwtTokenService;
import com.ruoyi.framework.security.RolePermissionRegistry;
import com.ruoyi.framework.web.service.IAuthService;
import com.ruoyi.system.domain.SysTenant;
import com.ruoyi.system.domain.SysUser;
import com.ruoyi.system.mapper.SysTenantMapper;
import com.ruoyi.system.mapper.SysUserMapper;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

@Service
public class AuthServiceImpl implements IAuthService {
    private final SysTenantMapper tenantMapper;
    private final SysUserMapper userMapper;
    private final PasswordEncoder passwordEncoder;
    private final JwtTokenService jwtTokenService;
    private final JwtProperties jwtProperties;
    private final RolePermissionRegistry rolePermissionRegistry;

    public AuthServiceImpl(SysTenantMapper tenantMapper,
                           SysUserMapper userMapper,
                           PasswordEncoder passwordEncoder,
                           JwtTokenService jwtTokenService,
                           JwtProperties jwtProperties,
                           RolePermissionRegistry rolePermissionRegistry) {
        this.tenantMapper = tenantMapper;
        this.userMapper = userMapper;
        this.passwordEncoder = passwordEncoder;
        this.jwtTokenService = jwtTokenService;
        this.jwtProperties = jwtProperties;
        this.rolePermissionRegistry = rolePermissionRegistry;
    }

    @Override
    public Map<String, Object> login(LoginBody body) {
        SysTenant tenant = tenantMapper.selectByTenantCode(body.getTenantCode());
        if (tenant == null) {
            throw new ServiceException("租户不存在");
        }
        if (!"0".equals(tenant.getStatus())) {
            throw new ServiceException("租户已停用");
        }
        if (tenant.getExpireTime() != null && tenant.getExpireTime().isBefore(LocalDateTime.now())) {
            throw new ServiceException("租户已过期，请联系平台续费");
        }

        SysUser user = userMapper.selectByTenantIdAndUsername(tenant.getId(), body.getUsername());
        if (user == null) {
            throw new ServiceException("用户不存在");
        }
        if (!"0".equals(user.getStatus())) {
            throw new ServiceException("用户已停用");
        }
        if (!passwordEncoder.matches(body.getPassword(), user.getPassword())) {
            throw new ServiceException("用户名或密码错误");
        }

        LoginUser loginUser = buildLoginUser(user, tenant);
        String token = jwtTokenService.createToken(loginUser);
        Map<String, Object> data = new HashMap<>();
        data.put("accessToken", token);
        data.put("expireMinutes", jwtProperties.getExpireMinutes());
        data.put("tenantCode", tenant.getTenantCode());
        data.put("username", user.getUsername());
        return data;
    }

    private LoginUser buildLoginUser(SysUser user, SysTenant tenant) {
        LoginUser lu = new LoginUser();
        lu.setUserId(user.getId());
        lu.setTenantId(tenant.getId());
        lu.setTenantCode(tenant.getTenantCode());
        lu.setUsername(user.getUsername());
        lu.setPassword(null);
        lu.setRoleKey(user.getRoleKey());
        Set<String> perms = rolePermissionRegistry.resolvePermissions(user.getRoleKey());
        lu.setPermissions(perms);
        List<SimpleGrantedAuthority> authorities = new ArrayList<>();
        for (String p : perms) {
            authorities.add(new SimpleGrantedAuthority(p));
        }
        if (user.getRoleKey() != null && !user.getRoleKey().isBlank()) {
            authorities.add(new SimpleGrantedAuthority("ROLE_" + user.getRoleKey()));
        }
        lu.setAuthorities(authorities);
        return lu;
    }
}
