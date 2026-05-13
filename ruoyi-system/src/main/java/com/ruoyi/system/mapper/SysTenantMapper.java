package com.ruoyi.system.mapper;

import com.ruoyi.system.domain.SysTenant;
import org.apache.ibatis.annotations.Param;

public interface SysTenantMapper {
    SysTenant selectByTenantCode(@Param("tenantCode") String tenantCode);
}
