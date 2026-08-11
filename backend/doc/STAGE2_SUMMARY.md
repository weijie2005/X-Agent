# Agent Backend - FastAPI 服务层

## 📋 项目概述

Agent Backend 是整个 Agent 系统的后端服务层，采用 FastAPI 框架构建，提供 RESTful API 接口，支持前后端分离架构。本服务作为系统的核心枢纽，负责会话管理、文件处理、Agent 编排、数据存储等核心功能。

### 核心职责

- **会话管理**：创建、查询、更新、删除会话，管理对话历史
- **文件处理**：文件上传、存储、下载、元数据管理
- **Agent 编排**：LangGraph 状态机编排，LangChain 组件集成
- **数据存储**：PostgreSQL 关系型数据、Redis 缓存、Qdrant 向量库、MinIO 对象存储
- **流式响应**：SSE（Server-Sent Events）实时流式输出
- **PDF 导出**：基于 Playwright 的 HTML 转 PDF 服务（预留）

---

## 🏗️ 技术栈

### 核心框架

| 技术 | 版本 | 用途 |
|------|------|------|
| **FastAPI** | 最新 | Web 框架，提供高性能异步 API |
| **Pydantic** | 最新 | 数据验证和序列化 |
| **SQLAlchemy** | 2.0+ | ORM 框架，数据库操作 |
| **Uvicorn** | 最新 | ASGI 服务器，支持异步处理 |

### 数据存储

| 技术 | 用途 | 端口 |
|------|------|------|
| **PostgreSQL** | 关系型数据库，存储会话、消息、文件元数据 | 5432 |
| **Redis** | 缓存服务，存储临时数据、会话状态 | 6379 |
| **Qdrant** | 向量数据库，存储文档向量、支持 RAG 检索 | 6333 |
| **MinIO** | 对象存储，存储上传的文件 | 9000 |

### AI/ML 组件

| 技术 | 用途 |
|------|------|
| **LangChain** | LLM 应用开发框架，提供工具、记忆、RAG 等组件 |
| **LangGraph** | Agent 编排框架，支持状态机、分支、循环 |
| **LangSmith** | 全链路追踪和调试平台 |

### 其他组件

| 技术 | 用途 |
|------|------|
| **psycopg** | PostgreSQL 异步驱动 |
| **python-multipart** | 文件上传处理 |
| **httpx** | 异步 HTTP 客户端 |

---

## 📁 项目结构

```
backend/
├── app/
│   ├── __init__.py              # 包初始化
│   ├── config.py                # 全局配置管理
│   ├── main.py                  # FastAPI 应用入口
│   │
│   ├── models/                  # 数据模型层
│   │   ├── __init__.py
│   │   ├── database.py          # 数据库连接管理
│   │   ├── tables.py            # 数据库表定义（ORM）
│   │   └── schemas.py           # Pydantic 数据模型
│   │
│   ├── routers/                 # 路由层（API 接口）
│   │   ├── __init__.py
│   │   ├── sessions.py          # 会话管理接口
│   │   ├── files.py             # 文件上传接口
│   │   └── pdf.py               # PDF 导出接口（预留）
│   │
│   ├── services/                # 服务层（业务逻辑）
│   │   ├── __init__.py
│   │   ├── session_service.py   # 会话服务
│   │   └── file_service.py      # 文件服务
│   │
│   └── utils/                   # 工具层
│       ├── __init__.py
│       ├── minio_client.py      # MinIO 客户端封装
│       └── sse.py               # SSE 流式响应工具
│
├── requirements.txt             # Python 依赖
├── Dockerfile                   # Docker 构建文件
└── README.md                    # 本文档
```

### 分层架构说明

```
┌─────────────────────────────────────────┐
│           前端应用 (Chatbot-UI)          │
└────────────────┬────────────────────────┘
                 │ HTTP/SSE
┌────────────────▼────────────────────────┐
│          路由层 (Routers)                │
│  - 接收请求、参数验证、响应格式化         │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│          服务层 (Services)               │
│  - 业务逻辑处理、事务管理                 │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│          模型层 (Models)                 │
│  - 数据库操作、数据验证                   │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│       数据存储层 (Storage)               │
│  PostgreSQL | Redis | Qdrant | MinIO    │
└─────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 环境要求

- Python 3.12+
- PostgreSQL 15+
- Redis 7+
- MinIO (最新版)
- Qdrant (最新版)

### 安装依赖

```bash
# 进入项目目录
cd backend

# 激活虚拟环境
source ~/agent-project/venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 配置环境变量

在项目根目录创建 `.env` 文件：

```env
# PostgreSQL 配置
PG_USER=your_username
PG_PASSWORD=your_password
PG_DB=agent_db
PG_HOST=localhost
PG_PORT=5432

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Qdrant 配置
QDRANT_HOST=localhost
QDRANT_PORT=6333

# MinIO 配置
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
MINIO_HOST=localhost:9000

# LLM 配置
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL_NAME=gpt-4
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000

# 应用配置
DEBUG=True
```

### 启动服务

#### 开发环境

```bash
# 方式 1: 直接运行
python -m app.main

# 方式 2: 使用 uvicorn（推荐）
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 生产环境

```bash
# 使用 gunicorn + uvicorn worker
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 访问 API 文档

服务启动后，访问以下地址：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/health

---

## 📡 API 接口文档

### 基础接口

#### 1. 根路径

```http
GET /
```

**响应示例**：
```json
{
  "message": "Welcome to Agent Backend",
  "version": "1.0.0",
  "docs": "/docs",
  "redoc": "/redoc"
}
```

#### 2. 健康检查

```http
GET /health
```

**响应示例**：
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "minio": "healthy",
    "qdrant": "healthy"
  }
}
```

---

### 会话管理接口

#### 1. 创建会话

```http
POST /sessions
Content-Type: application/json

{
  "title": "新对话",
  "user_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**响应示例**：
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "新对话",
  "created_at": "2026-08-06T10:00:00",
  "updated_at": "2026-08-06T10:00:00",
  "is_active": true
}
```

#### 2. 获取会话列表

```http
GET /sessions?user_id={user_id}&skip=0&limit=20
```

**查询参数**：
- `user_id` (可选): 用户 ID
- `skip` (可选): 跳过数量，默认 0
- `limit` (可选): 限制数量，默认 20

**响应示例**：
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "新对话",
    "created_at": "2026-08-06T10:00:00",
    "updated_at": "2026-08-06T10:00:00",
    "is_active": true
  }
]
```

#### 3. 获取会话详情

```http
GET /sessions/{session_id}
```

**响应示例**：
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "新对话",
  "created_at": "2026-08-06T10:00:00",
  "updated_at": "2026-08-06T10:00:00",
  "is_active": true
}
```

#### 4. 更新会话

```http
PATCH /sessions/{session_id}
Content-Type: application/json

{
  "title": "更新后的标题",
  "is_active": true
}
```

**响应示例**：
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "更新后的标题",
  "created_at": "2026-08-06T10:00:00",
  "updated_at": "2026-08-06T10:05:00",
  "is_active": true
}
```

#### 5. 删除会话

```http
DELETE /sessions/{session_id}
```

**响应**: 204 No Content

#### 6. 添加消息到会话

```http
POST /sessions/{session_id}/messages
Content-Type: application/json

{
  "role": "user",
  "content": "你好，请帮我分析一下这个问题",
  "tokens_used": 15
}
```

**响应示例**：
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "session_id": "550e8400-e29b-41d4-a716-446655440001",
  "role": "user",
  "content": "你好，请帮我分析一下这个问题",
  "created_at": "2026-08-06T10:10:00",
  "tokens_used": 15
}
```

#### 7. 获取会话历史消息

```http
GET /sessions/{session_id}/messages?skip=0&limit=100
```

**响应示例**：
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "session_id": "550e8400-e29b-41d4-a716-446655440001",
    "role": "user",
    "content": "你好，请帮我分析一下这个问题",
    "created_at": "2026-08-06T10:10:00",
    "tokens_used": 15
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440003",
    "session_id": "550e8400-e29b-41d4-a716-446655440001",
    "role": "assistant",
    "content": "你好！我很乐意帮助你分析问题...",
    "created_at": "2026-08-06T10:10:05",
    "tokens_used": 150
  }
]
```

---

### 文件管理接口

#### 1. 上传文件

```http
POST /files/upload/{session_id}
Content-Type: multipart/form-data

file: [二进制文件]
```

**请求限制**：
- 文件大小：最大 50MB
- 支持格式：.pdf, .docx, .doc, .xlsx, .xls, .txt, .md

**响应示例**：
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440004",
  "session_id": "550e8400-e29b-41d4-a716-446655440001",
  "filename": "document.pdf",
  "file_size": 1048576,
  "content_type": "application/pdf",
  "uploaded_at": "2026-08-06T10:15:00"
}
```

#### 2. 获取文件元数据

```http
GET /files/{file_id}
```

**响应示例**：
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440004",
  "session_id": "550e8400-e29b-41d4-a716-446655440001",
  "filename": "document.pdf",
  "file_size": 1048576,
  "content_type": "application/pdf",
  "uploaded_at": "2026-08-06T10:15:00"
}
```

#### 3. 获取会话的所有文件

```http
GET /files/session/{session_id}
```

**响应示例**：
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440004",
    "session_id": "550e8400-e29b-41d4-a716-446655440001",
    "filename": "document.pdf",
    "file_size": 1048576,
    "content_type": "application/pdf",
    "uploaded_at": "2026-08-06T10:15:00"
  }
]
```

#### 4. 获取文件下载链接

```http
GET /files/{file_id}/url?expires=3600
```

**查询参数**：
- `expires`: URL 有效期（秒），默认 3600

**响应示例**：
```json
{
  "url": "http://localhost:9000/agent-files/xxx-document.pdf?X-Amz-...",
  "expires_in": 3600
}
```

#### 5. 删除文件

```http
DELETE /files/{file_id}
```

**响应**: 204 No Content

---

### PDF 导出接口（预留）

#### 1. 导出会话为 PDF

```http
POST /pdf/export/{session_id}?include_charts=true
```

**状态**: 501 Not Implemented（待后续开发）

#### 2. 查询导出任务状态

```http
GET /pdf/status/{task_id}
```

**状态**: 501 Not Implemented（待后续开发）

#### 3. 下载 PDF 文件

```http
GET /pdf/download/{task_id}
```

**状态**: 501 Not Implemented（待后续开发）

---

## 🔧 内部工作流程

### 1. 请求处理流程

```
客户端请求
    ↓
FastAPI 路由层（参数验证）
    ↓
中间件处理（CORS、时间记录）
    ↓
服务层（业务逻辑）
    ↓
模型层（数据操作）
    ↓
数据存储层（PostgreSQL/Redis/MinIO/Qdrant）
    ↓
响应返回
```

### 2. 会话创建流程

```
POST /sessions
    ↓
1. 参数验证（Pydantic）
    ↓
2. 创建 Session 对象
    ↓
3. 保存到 PostgreSQL
    ↓
4. 返回会话信息
```

### 3. 文件上传流程

```
POST /files/upload/{session_id}
    ↓
1. 验证文件大小和类型
    ↓
2. 生成唯一对象名（UUID）
    ↓
3. 上传到 MinIO
    ↓
4. 保存元数据到 PostgreSQL
    ↓
5. 返回文件信息
```

### 4. SSE 流式响应流程

```
客户端建立 SSE 连接
    ↓
服务端返回流式响应头
    ↓
循环生成数据块
    ↓
格式化为 SSE 消息
    ↓
实时推送给客户端
    ↓
发送完成标记 [DONE]
```

---

## 🗄️ 数据库设计

### 表结构

#### sessions 表（会话）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| user_id | UUID | 用户 ID（可选） |
| title | VARCHAR(255) | 会话标题 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |
| is_active | BOOLEAN | 是否激活 |

#### messages 表（消息）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| session_id | UUID | 外键，关联 sessions |
| role | ENUM | 角色：user/assistant/system |
| content | TEXT | 消息内容 |
| created_at | TIMESTAMP | 创建时间 |
| tokens_used | INTEGER | 使用的 Token 数 |

#### files 表（文件）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| session_id | UUID | 外键，关联 sessions |
| filename | VARCHAR(255) | 原始文件名 |
| object_name | VARCHAR(512) | MinIO 对象名 |
| bucket_name | VARCHAR(255) | MinIO 存储桶名 |
| file_size | INTEGER | 文件大小（字节） |
| content_type | VARCHAR(100) | 文件类型 |
| uploaded_at | TIMESTAMP | 上传时间 |

---

## 🔐 安全配置

### CORS 配置

```python
# 开发环境
CORS_ORIGINS = ["http://localhost", "http://localhost:80"]

# 生产环境（建议配置具体域名）
CORS_ORIGINS = ["https://yourdomain.com"]
```

### JWT 认证

```python
# 生成密钥（生产环境必须修改）
openssl rand -hex 32

# 配置
JWT_SECRET_KEY = "your-secret-key"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24
```

### 文件上传安全

- 文件大小限制：50MB
- 文件类型白名单：.pdf, .docx, .doc, .xlsx, .xls, .txt, .md
- 文件名随机化：使用 UUID 避免路径遍历攻击

---

## 📊 性能优化

### 数据库优化

- 连接池配置：pool_size=10, max_overflow=20
- 查询优化：使用索引、避免 N+1 查询
- 异步操作：使用 async/await 提高并发性能

### 缓存策略

- Redis 缓存热点数据
- 会话状态缓存
- 查询结果缓存

### API 性能监控

- 请求处理时间记录（X-Process-Time 响应头）
- 慢查询日志
- 异常监控和告警

---

## 🧪 测试

### 运行测试

```bash
# 安装测试依赖
pip install pytest pytest-asyncio httpx

# 运行测试
pytest tests/ -v
```

### 测试覆盖范围

- 单元测试：服务层、工具类
- 集成测试：API 接口
- 性能测试：并发请求、大数据量

---

## 📦 部署

### Docker 部署

```bash
# 构建镜像
docker build -t agent-backend:latest .

# 运行容器
docker run -d \
  --name agent-backend \
  -p 8000:8000 \
  --env-file .env \
  agent-backend:latest
```

### Docker Compose 部署

```yaml
services:
  fastapi-backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: agent-backend
    restart: unless-stopped
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - postgres
      - redis
      - qdrant
      - minio
```

### 生产环境建议

1. **使用进程管理器**：systemd、supervisor
2. **反向代理**：Nginx、Traefik
3. **负载均衡**：多实例部署
4. **监控告警**：Prometheus、Grafana
5. **日志收集**：ELK Stack、Loki
6. **数据库备份**：定期备份 PostgreSQL

---

## 🔍 故障排查

### 常见问题

#### 1. 数据库连接失败

**症状**：启动时报错 `could not connect to server`

**解决方案**：
```bash
# 检查数据库服务状态
docker ps | grep postgres

# 检查连接配置
echo $PG_HOST $PG_PORT

# 测试连接
psql -h localhost -U username -d agent_db
```

#### 2. MinIO 连接失败

**症状**：文件上传失败

**解决方案**：
```bash
# 检查 MinIO 服务
curl http://localhost:9000/minio/health/live

# 检查认证信息
echo $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD
```

#### 3. Redis 连接超时

**症状**：缓存操作超时

**解决方案**：
```bash
# 检查 Redis 服务
redis-cli ping

# 检查配置
echo $REDIS_HOST $REDIS_PORT
```

### 日志查看

```bash
# 查看应用日志
tail -f logs/app.log

# 查看 Docker 日志
docker logs agent-backend -f

# 查看特定时间段的日志
docker logs agent-backend --since 1h
```

---

## 📚 开发指南

### 添加新接口

1. 在 `models/schemas.py` 中定义请求/响应模型
2. 在 `services/` 中实现业务逻辑
3. 在 `routers/` 中添加路由处理函数
4. 在 `main.py` 中注册路由

### 代码规范

- 使用类型注解
- 编写文档字符串
- 遵循 PEP 8 规范
- 添加单元测试

### 提交代码

```bash
# 运行代码检查
flake8 app/
black app/ --check

# 运行测试
pytest tests/ -v

# 提交代码
git add .
git commit -m "feat: 添加新功能"
git push
```

---

## 📝 更新日志

### v1.0.0 (2026-08-06)

- ✅ 完成基础架构搭建
- ✅ 实现会话管理接口
- ✅ 实现文件上传接口
- ✅ 实现 SSE 流式响应
- ✅ 集成 PostgreSQL、Redis、MinIO、Qdrant
- ✅ 添加健康检查接口
- 🔜 PDF 导出功能（待开发）
- 🔜 Agent 编排功能（待开发）
- 🔜 用户认证功能（待开发）

---

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](../LICENSE) 文件。

---

## 📞 联系方式

- 项目维护者：weijie.shen
- 邮箱：451970365@qq.com
- 文档：http://localhost:8000/docs

---

**最后更新时间**: 2026-08-06