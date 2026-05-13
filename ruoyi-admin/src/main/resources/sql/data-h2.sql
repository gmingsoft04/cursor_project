INSERT INTO sys_tenant (tenant_code, tenant_name, status, plan_code, seat_limit)
VALUES ('demo', '演示租户', '0', 'FREE', 99);

INSERT INTO sys_user (tenant_id, username, password, nick_name, status, role_key)
VALUES (
    1,
    'admin',
    '$2b$10$EQGEBw7iaiIDqGXrKty0d.m79oQnpGqOVcMH3/fM0AWM7sFB.pQCW',
    '管理员',
    '0',
    'TENANT_ADMIN'
);

INSERT INTO biz_demo (tenant_id, name, amount)
VALUES (1, '示例订单', 199.00);
