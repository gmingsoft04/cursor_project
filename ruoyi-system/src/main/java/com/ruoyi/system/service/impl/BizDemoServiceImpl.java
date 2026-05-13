package com.ruoyi.system.service.impl;

import com.ruoyi.common.constant.HttpStatus;
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
        validateForWrite(row);
        Long tenantId = requireTenantId();
        row.setTenantId(tenantId);
        int rows = bizDemoMapper.insert(row);
        if (rows == 0) {
            throw new ServiceException(HttpStatus.ERROR, "写入失败，请重试");
        }
        return rows;
    }

    @Override
    public int update(BizDemo row) {
        if (row == null || row.getId() == null) {
            throw new ServiceException(HttpStatus.BAD_REQUEST, "id 不能为空");
        }
        validateForWrite(row);
        Long tenantId = requireTenantId();
        row.setTenantId(tenantId);
        BizDemo existing = bizDemoMapper.selectById(row.getId(), tenantId);
        if (existing == null) {
            throw new ServiceException(HttpStatus.NOT_FOUND, "记录不存在或无权访问");
        }
        int rows = bizDemoMapper.updateById(row);
        if (rows == 0) {
            throw new ServiceException(HttpStatus.NOT_FOUND, "记录不存在或数据未变更");
        }
        return rows;
    }

    @Override
    public int deleteById(Long id) {
        int rows = bizDemoMapper.deleteById(id, requireTenantId());
        if (rows == 0) {
            throw new ServiceException(HttpStatus.NOT_FOUND, "记录不存在或已删除");
        }
        return rows;
    }

    private void validateForWrite(BizDemo row) {
        if (row == null) {
            throw new ServiceException(HttpStatus.BAD_REQUEST, "请求体不能为空");
        }
        if (row.getName() == null || row.getName().isBlank()) {
            throw new ServiceException(HttpStatus.BAD_REQUEST, "名称不能为空");
        }
        if (row.getName().length() > 200) {
            throw new ServiceException(HttpStatus.BAD_REQUEST, "名称长度不能超过 200");
        }
        if (row.getAmount() != null && row.getAmount().signum() < 0) {
            throw new ServiceException(HttpStatus.BAD_REQUEST, "金额不能为负数");
        }
    }
}
