package com.ruoyi.system.service.impl;

import com.ruoyi.common.exception.ServiceException;
import com.ruoyi.common.utils.SecurityUtils;
import com.ruoyi.system.domain.BizDemo;
import com.ruoyi.system.mapper.BizDemoMapper;
import com.ruoyi.system.service.IBizDemoService;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class BizDemoServiceImpl implements IBizDemoService {
    private final BizDemoMapper bizDemoMapper;

    public BizDemoServiceImpl(BizDemoMapper bizDemoMapper) {
        this.bizDemoMapper = bizDemoMapper;
    }

    private Long requireTenantId() {
        Long tenantId = SecurityUtils.getTenantId();
        if (tenantId == null) {
            throw new ServiceException("当前登录未绑定租户，无法访问租户业务数据");
        }
        return tenantId;
    }

    @Override
    public List<BizDemo> selectList(BizDemo query) {
        Long tenantId = requireTenantId();
        if (query == null) {
            query = new BizDemo();
        }
        query.setTenantId(tenantId);
        return bizDemoMapper.selectList(query);
    }

    @Override
    public BizDemo selectById(Long id) {
        return bizDemoMapper.selectById(id, requireTenantId());
    }

    @Override
    public int insert(BizDemo row) {
        Long tenantId = requireTenantId();
        row.setTenantId(tenantId);
        return bizDemoMapper.insert(row);
    }

    @Override
    public int update(BizDemo row) {
        Long tenantId = requireTenantId();
        row.setTenantId(tenantId);
        BizDemo existing = bizDemoMapper.selectById(row.getId(), tenantId);
        if (existing == null) {
            throw new ServiceException("记录不存在或无权访问");
        }
        return bizDemoMapper.updateById(row);
    }

    @Override
    public int deleteById(Long id) {
        return bizDemoMapper.deleteById(id, requireTenantId());
    }
}
