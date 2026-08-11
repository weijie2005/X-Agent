# 🚀 Agent 项目启动指南

## 📋 环境要求

- Python 3.14+
- Node.js 20.20.2+
- PostgreSQL
- Redis
- Qdrant

---

## 🔧 配置文件

项目使用 `.env` 文件管理配置，配置文件位于：
- **全局配置**: `/home/s8066/agent-project/.env`
- **前端配置**: `/home/s8066/agent-project/frontend/.env`

---

## 🚀 启动服务

### 1. 启动后端服务

```bash
# 进入后端目录
cd /home/s8066/agent-project/backend

# 激活虚拟环境
source venv/bin/activate

# 启动服务（自动从.env读取配置）
python run_backend.py
```

**启动信息**:
```
================================================================================
🚀 启动 Agent Backend v1.0.0
================================================================================
📡 监听地址: http://0.0.0.0:8080
📚 API 文档: http://localhost:8080/docs
🔍 健康检查: http://localhost:8080/health
================================================================================
```

### 2. 启动前端服务

```bash
# 进入前端目录
cd /home/s8066/agent-project/frontend

# 启动服务（自动从.env读取配置）
./run_frontend.sh
```

**启动信息**:
```
📋 加载配置文件: .env
📡 前端地址: http://0.0.0.0:3000
🔗 后端代理: http://localhost:8080
================================================================
🚀 启动前端服务...
```

---

## 📝 配置说明

### 后端配置项

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| BACKEND_HOST | 0.0.0.0 | 后端监听地址 |
| BACKEND_PORT | 8080 | 后端监听端口 |

### 前端配置项

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| FRONTEND_HOST | 0.0.0.0 | 前端监听地址 |
| FRONTEND_PORT | 3000 | 前端监听端口 |
| BACKEND_HOST | localhost | 后端地址（用于代理） |
| BACKEND_PORT | 8080 | 后端端口（用于代理） |

---

## 🧪 测试

### 验证配置

```bash
cd /home/s8066/agent-project/backend
source venv/bin/activate
python verify_config.py
```

### 运行API测试

```bash
cd /home/s8066/agent-project/backend
source venv/bin/activate
python test/test_fastapi.py
```

---

## 📚 API 文档

启动后端服务后，访问以下地址查看API文档：

- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc

---

## 🔗 访问地址

- **前端**: http://localhost:3000
- **后端**: http://localhost:8080
- **API文档**: http://localhost:8080/docs

---

## ⚙️ 修改配置

### 修改端口

编辑 `.env` 文件：

```env
# 后端服务配置
BACKEND_HOST=0.0.0.0
BACKEND_PORT=9000  # 修改为需要的端口

# 前端服务配置
FRONTEND_HOST=0.0.0.0
FRONTEND_PORT=4000  # 修改为需要的端口
```

同时更新 `frontend/.env` 文件：

```env
BACKEND_PORT=9000  # 与后端端口保持一致
FRONTEND_PORT=4000
```

---

## 🛠️ 故障排查

### 端口被占用

```bash
# 查看端口占用
lsof -i :8080

# 结束占用进程
kill -9 <PID>
```

### 配置未生效

1. 确认 `.env` 文件存在
2. 重启服务
3. 运行 `python verify_config.py` 验证

---

## 📦 项目结构

```
agent-project/
├── .env                        # 全局配置文件
├── CONFIG_MIGRATION_SUMMARY.md # 配置迁移总结
├── STARTUP_GUIDE.md            # 启动指南（本文件）
├── backend/
│   ├── app/
│   │   └── config.py           # 配置类
│   ├── run_backend.py          # 后端启动脚本
│   ├── verify_config.py        # 配置验证脚本
│   └── test/
│       └── test_fastapi.py     # API测试
└── frontend/
    ├── .env                    # 前端配置文件
    ├── vite.config.js          # Vite配置
    └── run_frontend.sh         # 前端启动脚本
```

---

## 🎯 快速启动（一键启动）

### 启动所有服务

```bash
# 启动后端
cd /home/s8066/agent-project/backend
source venv/bin/activate
python run_backend.py &

# 启动前端
cd /home/s8066/agent-project/frontend
./run_frontend.sh &
```

---

**最后更新**: 2026-08-07  
**版本**: 1.0.0