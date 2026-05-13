package com.ruoyi.framework.web.service;

import com.ruoyi.common.core.domain.model.request.LoginBody;

import java.util.Map;

public interface IAuthService {
    Map<String, Object> login(LoginBody body);
}
