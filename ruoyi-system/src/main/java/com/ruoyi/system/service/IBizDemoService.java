package com.ruoyi.system.service;

import com.ruoyi.system.domain.BizDemo;

import java.util.List;

public interface IBizDemoService {
    List<BizDemo> selectList(BizDemo query);

    BizDemo selectById(Long id);

    int insert(BizDemo row);

    int update(BizDemo row);

    int deleteById(Long id);
}
