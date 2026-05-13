package com.ruoyi.system.mapper;

import com.ruoyi.system.domain.SysUser;
import org.apache.ibatis.annotations.Param;

public interface SysUserMapper {
    SysUser selectByTenantIdAndUsername(@Param("tenantId") Long tenantId, @Param("username") String username);
}
