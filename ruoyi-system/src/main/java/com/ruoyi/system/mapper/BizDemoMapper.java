package com.ruoyi.system.mapper;

import com.ruoyi.system.domain.BizDemo;
import org.apache.ibatis.annotations.Param;

import java.util.List;

public interface BizDemoMapper {
    List<BizDemo> selectList(BizDemo query);

    BizDemo selectById(@Param("id") Long id, @Param("tenantId") Long tenantId);

    int insert(BizDemo row);

    int updateById(BizDemo row);

    int deleteById(@Param("id") Long id, @Param("tenantId") Long tenantId);
}
