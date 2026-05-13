package com.ruoyi.framework.security;

import com.ruoyi.common.core.domain.model.LoginUser;
import com.ruoyi.framework.config.properties.JwtProperties;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Arrays;
import java.util.Date;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

@Component
public class JwtTokenService {
    private static final String CLAIM_USER_ID = "uid";
    private static final String CLAIM_TENANT_ID = "tid";
    private static final String CLAIM_TENANT_CODE = "tcode";
    private static final String CLAIM_PERMS = "perms";
    private static final String CLAIM_ROLE = "role";

    private final JwtProperties jwtProperties;

    public JwtTokenService(JwtProperties jwtProperties) {
        this.jwtProperties = jwtProperties;
    }

    public String createToken(LoginUser loginUser) {
        long now = System.currentTimeMillis();
        long exp = now + jwtProperties.getExpireMinutes() * 60_000L;
        String perms = String.join(",", loginUser.getPermissions());
        return Jwts.builder()
                .subject(loginUser.getUsername())
                .issuedAt(new Date(now))
                .expiration(new Date(exp))
                .claim(CLAIM_USER_ID, loginUser.getUserId())
                .claim(CLAIM_TENANT_ID, loginUser.getTenantId())
                .claim(CLAIM_TENANT_CODE, loginUser.getTenantCode())
                .claim(CLAIM_PERMS, perms)
                .claim(CLAIM_ROLE, loginUser.getRoleKey() != null ? loginUser.getRoleKey() : "")
                .signWith(signingKey())
                .compact();
    }

    public LoginUser parseLoginUser(String token) {
        Claims claims = Jwts.parser()
                .verifyWith(signingKey())
                .build()
                .parseSignedClaims(token)
                .getPayload();

        LoginUser user = new LoginUser();
        user.setUsername(claims.getSubject());
        user.setUserId(claims.get(CLAIM_USER_ID, Long.class));
        user.setTenantId(claims.get(CLAIM_TENANT_ID, Long.class));
        user.setTenantCode(claims.get(CLAIM_TENANT_CODE, String.class));
        String permsStr = claims.get(CLAIM_PERMS, String.class);
        Set<String> perms = new LinkedHashSet<>();
        if (permsStr != null && !permsStr.isBlank()) {
            perms.addAll(Arrays.asList(permsStr.split(",")));
        }
        user.setPermissions(perms);
        String roleKey = claims.get(CLAIM_ROLE, String.class);
        user.setRoleKey(roleKey);
        List<SimpleGrantedAuthority> authorities = perms.stream()
                .map(SimpleGrantedAuthority::new)
                .collect(Collectors.toList());
        if (roleKey != null && !roleKey.isBlank()) {
            authorities.add(new SimpleGrantedAuthority("ROLE_" + roleKey));
        }
        user.setAuthorities(authorities);
        return user;
    }

    private SecretKey signingKey() {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] keyBytes = digest.digest(jwtProperties.getSecret().getBytes(StandardCharsets.UTF_8));
            return Keys.hmacShaKeyFor(keyBytes);
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException("SHA-256 not available", e);
        }
    }
}
