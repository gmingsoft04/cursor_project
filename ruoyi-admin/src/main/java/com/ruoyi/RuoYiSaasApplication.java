package com.ruoyi;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
@MapperScan({"com.ruoyi.**.mapper"})
public class RuoYiSaasApplication {

    public static void main(String[] args) {
        SpringApplication.run(RuoYiSaasApplication.class, args);
    }
}
