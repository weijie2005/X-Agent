-- 添加手机号和部门字段到 users 表
-- 执行时间: 2026-08-10

-- 添加 phone 字段
ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(20);

-- 添加 department 字段
ALTER TABLE users ADD COLUMN IF NOT EXISTS department VARCHAR(100);

-- 添加注释
COMMENT ON COLUMN users.phone IS '用户手机号';
COMMENT ON COLUMN users.department IS '用户所在部门';