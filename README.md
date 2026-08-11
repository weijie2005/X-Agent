# X-Agent - 生产级智能对话系统

## 📋 项目简介

X-Agent 是一个企业级智能对话系统，采用前后端分离架构，集成了先进的 AI Agent 技术与知识库管理能力。系统具备强大的对话理解、工具调用、记忆管理和知识检索能力，适用于企业知识问答、智能客服、文档分析等多种场景。

### 核心功能

- **智能对话引擎**：基于 LangGraph 的 ReAct 执行引擎，支持多轮对话和复杂推理
- **记忆系统**：三层记忆架构（短期记忆、长期记忆、工作记忆），支持上下文保持和语义检索
- **工具生态**：内置计算器、联网搜索、文档解析、Python 代码执行等多种工具
- **RAG 知识库**：支持文档上传、解析、向量化存储和智能检索，具备 CRAG 纠错能力
- **安全管控**：完善的安全拦截、审计日志、容错自愈机制
- **用户管理**：支持用户注册、登录、权限管理
- **会话管理**：多会话支持，历史记录持久化
- **文件管理**：支持 PDF、Word、Excel 等多种格式文件上传与解析
- **可视化展示**：集成 ECharts 图表、Mermaid 流程图、代码高亮等富文本渲染
- **PDF 导出**：支持对话内容导出为 PDF 文档

---

## 🏗️ 技术架构

### 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        前端层 (Vue 3)                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  对话界面     │  │  知识库管理   │  │  用户管理     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                            │ HTTP/SSE
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     后端层 (FastAPI)                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  API 路由     │  │  业务服务     │  │  Harness管控  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Agent 引擎   │    │  RAG 知识库   │    │  工具生态    │
└──────────────┘    └──────────────┘    └──────────────┘
        │                   │                   │
        ├─ Prompt引擎       ├─ 文档处理        ├─ 计算器
        ├─ 记忆系统         ├─ 向量化          ├─ 联网搜索
        └─ 执行器           └─ 混合检索        ├─ 文档解析
                                               └─ Python执行
```

### 技术栈

#### 前端技术栈

- **框架**: Vue 3.4 + Vue Router 4.6
- **构建工具**: Vite 5.0
- **HTTP 客户端**: Axios
- **图表库**: ECharts 5.5
- **Markdown 渲染**: Marked + DOMPurify
- **流程图**: Mermaid 10.9
- **代码高亮**: Highlight.js 11.9

#### 后端技术栈

- **语言**: Python 3.12
- **Web 框架**: FastAPI + Uvicorn
- **AI 框架**: LangChain + LangGraph + LangSmith
- **数据库**: PostgreSQL 16
- **缓存**: Redis 7
- **向量数据库**: Qdrant v1.12
- **对象存储**: MinIO
- **LLM**: 支持 OpenAI、DeepSeek、通义千问等多种模型

#### 基础设施

- **容器化**: Docker + Docker Compose
- **日志收集**: Loki
- **代码沙箱**: E2B Code Interpreter

---

## 🚀 前端部署指南

### 环境要求

- Node.js >= 16.0.0
- npm >= 8.0.0 或 yarn >= 1.22.0

### 安装步骤

#### 1. 进入前端目录

```bash
cd frontend
```

#### 2. 安装依赖

使用 npm:
```bash
npm install
```

或使用 yarn:
```bash
yarn install
```

#### 3. 配置环境变量

创建 `.env` 文件（如需要）：
```bash
VITE_API_BASE_URL=http://localhost:8080
```

### 运行方式

#### 开发环境

```bash
npm run dev
```

访问地址: http://localhost:3000

#### 生产构建

```bash
npm run build
```

构建产物位于 `dist/` 目录

#### 预览生产构建

```bash
npm run preview
```

### 前端目录结构

```
frontend/
├── src/
│   ├── components/      # 可复用组件
│   │   ├── ChatMessage.vue    # 对话消息组件
│   │   ├── Header.vue         # 头部导航
│   │   └── Sidebar.vue        # 侧边栏
│   ├── views/           # 页面视图
│   │   ├── ChatView.vue       # 对话页面
│   │   ├── KnowledgeBase.vue  # 知识库管理
│   │   ├── LoginView.vue      # 登录页面
│   │   ├── SessionsView.vue   # 会话管理
│   │   ├── SettingsView.vue   # 设置页面
│   │   └── UserManagement.vue # 用户管理
│   ├── router/          # 路由配置
│   ├── styles/          # 样式文件
│   ├── App.vue          # 根组件
│   └── main.js          # 入口文件
├── index.html           # HTML 模板
├── package.json         # 依赖配置
└── vite.config.js       # Vite 配置
```

---

## 🔧 后端部署指南

### 基础服务 Docker 部署

后端依赖多个基础服务，推荐使用 Docker Compose 进行部署。

#### 1. 配置环境变量

在项目根目录创建 `.env` 文件：

```bash
# PostgreSQL 配置
PG_USER=agentuser
PG_PASSWORD=your_password_here
PG_DB=agent_db

# MinIO 配置
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=your_password_here

# LLM API 配置（以 DeepSeek 为例）
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-v4-flash

# DashScope Embedding API（可选）
DASHSCOPE_API_KEY=your_dashscope_key_here
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/api/v1
DASHSCOPE_MODEL=qwen3.7-text-embedding

# Tavily API（联网搜索）
TAVILY_API_KEY=your_tavily_key_here

# E2B API（Python 代码沙箱）
E2B_API_KEY=your_e2b_key_here
```

#### 2. 启动基础服务

```bash
docker-compose up -d
```

这将启动以下服务：
- **PostgreSQL**: 数据库服务 (端口 5432)
- **Redis**: 缓存服务 (端口 6379)
- **Qdrant**: 向量数据库 (端口 6333)
- **MinIO**: 对象存储 (端口 9000, 控制台 9001)
- **Loki**: 日志收集 (端口 3100)

#### 3. 验证服务状态

```bash
docker-compose ps
```

#### 4. 查看服务日志

```bash
docker-compose logs -f [service_name]
```

#### 5. 停止服务

```bash
docker-compose down
```

#### 6. 清理数据（谨慎操作）

```bash
docker-compose down -v
```

### 后端代码部署

#### 环境要求

- Python >= 3.12
- pip >= 23.0

#### 安装步骤

##### 1. 进入后端目录

```bash
cd backend
```

##### 2. 创建虚拟环境

```bash
python -m venv venv
```

##### 3. 激活虚拟环境

Linux/macOS:
```bash
source venv/bin/activate
```

Windows:
```bash
venv\Scripts\activate
```

##### 4. 安装依赖

```bash
pip install -r requirements.txt
```

主要依赖包括：
- FastAPI + Uvicorn（Web 框架）
- LangChain + LangGraph（AI 框架）
- SQLAlchemy + Psycopg（数据库）
- Qdrant Client（向量数据库）
- Minio（对象存储）
- PyPDF2 + python-docx + openpyxl（文档解析）

##### 5. 初始化数据库

数据库表会在首次启动时自动创建，也可以手动运行迁移脚本：

```bash
python migrations/migrate_db.py
```

### 运行方式

#### 开发环境

使用启动脚本：
```bash
python run_backend.py
```

或直接使用 Uvicorn：
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

#### 生产环境

推荐使用多进程模式：
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080 --workers 4
```

#### Docker 部署

构建镜像：
```bash
docker build -t x-agent-backend .
```

运行容器：
```bash
docker run -d \
  --name x-agent-backend \
  --env-file ../.env \
  -p 8080:8000 \
  x-agent-backend
```

### 访问地址

- **API 服务**: http://localhost:8080
- **API 文档 (Swagger)**: http://localhost:8080/docs
- **API 文档 (ReDoc)**: http://localhost:8080/redoc
- **健康检查**: http://localhost:8080/health

### 后端目录结构

```
backend/
├── app/
│   ├── agent/              # Agent 核心模块
│   │   ├── core/           # 执行引擎
│   │   ├── memory/         # 记忆系统
│   │   ├── tools/          # 工具生态
│   │   ├── rag/            # RAG 知识库
│   │   ├── harness/        # Harness 管控
│   │   ├── prompts/        # Prompt 引擎
│   │   └── checkpoints/    # 检查点管理
│   ├── models/             # 数据模型
│   │   ├── database.py     # 数据库连接
│   │   ├── schemas.py      # Pydantic 模型
│   │   └── tables.py       # 数据表定义
│   ├── routers/            # API 路由
│   │   ├── agent.py        # Agent 对话接口
│   │   ├── auth.py         # 用户认证
│   │   ├── files.py        # 文件管理
│   │   ├── knowledge_base.py # 知识库管理
│   │   ├── pdf.py          # PDF 导出
│   │   └── sessions.py     # 会话管理
│   ├── services/           # 业务服务
│   ├── utils/              # 工具函数
│   ├── config.py           # 配置管理
│   └── main.py             # 应用入口
├── test/                   # 测试脚本
├── migrations/             # 数据库迁移
├── logs/                   # 日志文件
├── doc/                    # 项目文档
├── requirements.txt        # Python 依赖
├── Dockerfile              # Docker 构建文件
└── run_backend.py          # 启动脚本
```

---

## 📚 API 接口说明

### 主要接口

#### 对话接口

```http
POST /api/v1/agent/chat
Content-Type: application/json

{
  "session_id": "uuid",
  "message": "你好",
  "user_id": "user123"
}
```

#### 会话管理

```http
GET /api/v1/sessions          # 获取会话列表
POST /api/v1/sessions         # 创建新会话
DELETE /api/v1/sessions/{id}  # 删除会话
```

#### 文件上传

```http
POST /api/v1/files/upload
Content-Type: multipart/form-data

file: [文件]
```

#### 知识库管理

```http
POST /api/v1/knowledge-base/documents    # 上传文档
GET /api/v1/knowledge-base/documents     # 文档列表
DELETE /api/v1/knowledge-base/documents/{id}  # 删除文档
```

#### 用户认证

```http
POST /api/v1/auth/register    # 用户注册
POST /api/v1/auth/login       # 用户登录
GET /api/v1/auth/me           # 获取当前用户信息
```

---

## 🔐 安全说明

- 生产环境请修改 `.env` 中的默认密码
- 建议启用 HTTPS
- 配置防火墙规则，限制数据库端口外网访问
- 定期更新依赖包，修复安全漏洞
- 启用 ALLOW_LOCAL_EXECUTION=false（默认），禁止本地代码执行

---

## 📝 开发指南

### 代码规范

- 后端遵循 PEP 8 编码规范
- 前端遵循 Vue 3 Composition API 最佳实践
- 使用类型注解提高代码可维护性

### 日志查看

```bash
# 查看应用日志
tail -f backend/logs/app.log

# 查看 Agent 日志
tail -f backend/logs/agent.log

# 查看错误日志
tail -f backend/logs/error.log
```

### 测试

```bash
# 运行测试脚本
cd backend/test
python test_agent.py
python test_rag.py
```

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

---

## 📄 许可证

本项目仅供学习和研究使用。

---

## 📧 联系方式

如有问题或建议，请提交 Issue。