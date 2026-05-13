-- MySQL 8 初始化脚本（与 H2 结构等价，可按需调整字符集）
CREATE TABLE IF NOT EXISTS sys_tenant (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    tenant_code VARCHAR(64) NOT NULL,
    tenant_name VARCHAR(128) NOT NULL,
    status CHAR(1) DEFAULT '0' COMMENT '0正常 1停用',
    expire_time DATETIME NULL,
    plan_code VARCHAR(32) DEFAULT 'FREE',
    seat_limit INT DEFAULT 10,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_sys_tenant_code (tenant_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS sys_user (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    tenant_id BIGINT NOT NULL,
    username VARCHAR(64) NOT NULL,
    password VARCHAR(100) NOT NULL,
    nick_name VARCHAR(64),
    status CHAR(1) DEFAULT '0',
    role_key VARCHAR(64) DEFAULT 'TENANT_USER',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_sys_user_tenant_username (tenant_id, username),
    CONSTRAINT fk_sys_user_tenant FOREIGN KEY (tenant_id) REFERENCES sys_tenant (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS biz_demo (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    tenant_id BIGINT NOT NULL,
    name VARCHAR(128) NOT NULL,
    amount DECIMAL(18, 2),
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_biz_demo_tenant FOREIGN KEY (tenant_id) REFERENCES sys_tenant (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
