package com.ruoyi.web.controller;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.domain.model.request.LoginBody;
import com.ruoyi.framework.web.service.IAuthService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/auth")
public class AuthController {

    private final IAuthService authService;

    public AuthController(IAuthService authService) {
        this.authService = authService;
    }

    @PostMapping("/login")
    public AjaxResult login(@Valid @RequestBody LoginBody body) {
        return AjaxResult.success(authService.login(body));
    }
}
