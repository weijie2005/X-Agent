# 日志系统配置说明

## 📋 概述

Agent Backend 使用完整的日志系统，记录所有重要数据和操作，包括：
- HTTP 请求日志
- Agent 对话日志
- 数据库操作日志
- 错误日志
- 调试日志

---

## 📁 日志文件位置

所有日志文件位于 `backend/logs/` 目录：

```
backend/logs/
├── app.log          # 所有日志（INFO及以上）
├── error.log        # 错误日志（ERROR及以上）
├── request.log      # HTTP请求日志
├── agent.log        # Agent对话日志
├── database.log     # 数据库操作日志
└── debug.log        # 调试日志（仅DEBUG模式）
```

---

## 📊 日志格式

### 标准日志格式

```
[时间] [级别] [模块名] [进程ID] [线程ID] - 消息
```

**示例**:
```
[2026-08-07 16:30:45,123] [INFO] [app.main] [12345] [MainThread] - Application started
```

### 请求日志格式

```
[时间] [级别] [模块名] [方法] [路径] [状态码] [处理时间] [客户端IP] - 消息
```

**示例**:
```
[2026-08-07 16:30:45,123] [INFO] [request] [POST] [/api/v1/agent/chat] [200] [0.123s] [127.0.0.1] - Request completed
```

---

## 🔧 日志配置

### 日志级别

| 级别 | 说明 | 使用场景 |
|------|------|----------|
| DEBUG | 调试信息 | 开发环境，详细调试 |
| INFO | 常规信息 | 生产环境，正常运行 |
| WARNING | 警告信息 | 潜在问题 |
| ERROR | 错误信息 | 错误处理 |
| CRITICAL | 严重错误 | 系统崩溃 |

### 日志轮转策略

- **按大小轮转**: 单个文件最大 10MB
- **保留数量**: 最近 30 个日志文件
- **编码格式**: UTF-8
- **轮转方式**: 自动轮转，无需手动清理

---

## 📝 日志内容

### 1. 应用日志 (app.log)

记录所有应用级别的日志，包括：
- 应用启动和关闭
- 配置加载
- 中间件执行
- 路由处理
- 异常信息

**示例**:
```
[2026-08-07 16:30:45,123] [INFO] [app.main] [12345] [MainThread] - Starting up FastAPI application...
[2026-08-07 16:30:45,234] [INFO] [app.main] [12345] [MainThread] - Database tables created successfully
[2026-08-07 16:30:45,345] [INFO] [app.main] [12345] [MainThread] - Application startup complete.
```

### 2. 请求日志 (request.log)

记录所有 HTTP 请求，包括：
- 请求方法和路径
- 客户端 IP 地址
- 请求参数
- 响应状态码
- 处理时间

**示例**:
```
[2026-08-07 16:30:45,123] [INFO] [request] [POST] [/api/v1/agent/chat] [127.0.0.1] - Request started
[2026-08-07 16:30:45,456] [INFO] [request] [POST] [/api/v1/agent/chat] [200] [0.333s] [127.0.0.1] - Request completed
```

### 3. Agent 日志 (agent.log)

记录 Agent 对话的所有细节，包括：
- 会话 ID
- 用户输入（前100个字符）
- 响应内容长度
- 处理时间
- 错误信息

**示例**:
```
[2026-08-07 16:30:45,123] [INFO] [agent] [MainThread] - Chat request started
  session_id: ca5d2ed2-b11a-4768-9cad-98d03ff4bdf3
  user_input: 你好，请介绍一下你自己
  
[2026-08-07 16:30:45,456] [INFO] [agent] [MainThread] - Chat request completed
  session_id: ca5d2ed2-b11a-4768-9cad-98d03ff4bdf3
  success: true
  output_length: 1234
  process_time: 0.333s
```

### 4. 错误日志 (error.log)

记录所有错误和异常，包括：
- 错误类型
- 错误消息
- 完整堆栈信息
- 上下文信息

**示例**:
```
[2026-08-07 16:30:45,123] [ERROR] [app.main] [12345] [MainThread] - Database connection failed
Traceback (most recent call last):
  File "app/main.py", line 123, in lifespan
    Base.metadata.create_all(bind=engine)
  ...
psycopg.OperationalError: connection failed
```

### 5. 数据库日志 (database.log)

记录数据库操作，包括：
- SQL 查询语句
- 查询参数
- 执行时间
- 影响行数

**示例**:
```
[2026-08-07 16:30:45,123] [INFO] [database] [MainThread] - Query executed
  query: SELECT * FROM sessions WHERE id = %s
  duration: 0.023s
  rows: 1
```

---

## 🔍 日志查看工具

### 查看最新日志

```bash
# 查看最新的50行应用日志
python view_logs.py app

# 查看最新的100行错误日志
python view_logs.py error --lines 100

# 查看所有ERROR级别的日志
python view_logs.py app --level ERROR
```

### 实时监控日志

```bash
# 实时监控应用日志
python view_logs.py app --follow

# 实时监控错误日志
python view_logs.py error --follow
```

### 搜索日志

```bash
# 搜索包含"session"的日志
python view_logs.py app --search session

# 搜索包含"error"的日志
python view_logs.py app --search error
```

### 列出日志文件

```bash
# 列出所有日志文件
python view_logs.py --list
```

---

## 📊 日志统计

### 日志文件大小

| 日志文件 | 最大大小 | 保留数量 | 总大小（最大） |
|----------|----------|----------|----------------|
| app.log | 10MB | 30 | 300MB |
| error.log | 10MB | 30 | 300MB |
| request.log | 10MB | 30 | 300MB |
| agent.log | 10MB | 30 | 300MB |
| database.log | 10MB | 30 | 300MB |
| debug.log | 10MB | 30 | 300MB |
| **总计** | - | - | **1.8GB** |

---

## 🔒 日志安全

### 敏感信息处理

- ✅ 不记录 API 密钥完整内容
- ✅ 不记录用户密码
- ✅ 不记录完整的用户输入（只记录前100个字符）
- ✅ 不记录完整的响应内容（只记录长度）

### 日志访问控制

- 日志文件权限：仅应用用户可读写
- 日志目录权限：仅应用用户可访问
- 建议生产环境使用日志收集系统（如 ELK）

---

## 🛠️ 日志维护

### 日志清理

日志系统自动轮转，无需手动清理。如需手动清理：

```bash
# 删除所有日志文件
rm -rf backend/logs/*.log

# 删除旧的日志备份文件
rm -rf backend/logs/*.log.*
```

### 日志备份

建议定期备份日志文件：

```bash
# 备份日志目录
tar -czf logs_backup_$(date +%Y%m%d).tar.gz backend/logs/
```

---

## 📈 日志分析

### 使用 grep 分析

```bash
# 统计错误数量
grep -c "\[ERROR\]" backend/logs/app.log

# 查找特定会话的所有日志
grep "session_id: ca5d2ed2-b11a-4768-9cad-98d03ff4bdf3" backend/logs/agent.log

# 查找慢请求（处理时间超过1秒）
grep "process_time: [1-9]\." backend/logs/request.log
```

### 使用 awk 分析

```bash
# 统计各状态码的数量
awk '{print $8}' backend/logs/request.log | sort | uniq -c

# 统计各IP的请求次数
awk '{print $10}' backend/logs/request.log | sort | uniq -c
```

---

## 🎯 最佳实践

### 开发环境

1. **启用 DEBUG 日志**: 设置 `DEBUG=True` 在 `.env` 文件
2. **实时监控**: 使用 `--follow` 参数实时查看日志
3. **详细日志**: 记录所有调试信息

### 生产环境

1. **禁用 DEBUG 日志**: 设置 `DEBUG=False`
2. **日志收集**: 使用 ELK 或其他日志收集系统
3. **日志分析**: 定期分析日志，识别性能瓶颈
4. **日志告警**: 配置错误日志告警

---

## 📚 相关文件

- 日志配置模块: [backend/app/utils/logger.py](file:///home/s8066/agent-project/backend/app/utils/logger.py)
- 日志查看工具: [backend/view_logs.py](file:///home/s8066/agent-project/backend/view_logs.py)
- 主应用: [backend/app/main.py](file:///home/s8066/agent-project/backend/app/main.py)
- Agent路由: [backend/app/routers/agent.py](file:///home/s8066/agent-project/backend/app/routers/agent.py)

---

**最后更新**: 2026-08-07  
**版本**: 1.0.0