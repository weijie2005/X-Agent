# 测试目录

本目录包含所有测试脚本，用于测试 Agent 系统的各个模块。

## 目录结构

```
test/
├── README.md                              # 本文件
├── test_agent.py                          # Agent 核心功能测试
├── test_agent_api.py                      # Agent 对话接口测试（HTTP API）
├── test_deepseek.py                       # DeepSeek API 连接测试
├── test_executor_direct.py                # 直接测试 Agent 执行器
├── test_fastapi.py                        # FastAPI 接口测试
├── test_tools.py                          # 工具功能测试
├── test_rag.py                            # RAG 知识库系统测试
├── test_dashscope_embedding.py            # DashScope Embedding API 测试
├── test_dashscope_qdrant_detailed.py      # DashScope + Qdrant 详细测试
├── test_qdrant_api.py                     # Qdrant API 测试
└── delete_qdrant_collections.py           # 删除 Qdrant 集合（清理工具）
```

## 测试说明

### 1. Agent 核心功能测试

**文件**: `test_agent.py`

**功能**: 测试 Agent 执行器、记忆系统、Prompt 引擎等核心功能。

**运行**:
```bash
cd /home/s8066/agent-project/backend/test
python test_agent.py
```

### 2. Agent 对话接口测试

**文件**: `test_agent_api.py`

**功能**: 测试 Agent 对话功能，使用 DeepSeek API。

**运行**:
```bash
cd /home/s8066/agent-project/backend/test
python test_agent_api.py
```

**注意**: 需要先启动 FastAPI 服务：
```bash
cd /home/s8066/agent-project/backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

### 3. DeepSeek API 连接测试

**文件**: `test_deepseek.py`

**功能**: 测试 DeepSeek API 连接是否正常。

**运行**:
```bash
cd /home/s8066/agent-project/backend/test
python test_deepseek.py
```

### 4. Agent 执行器直接测试

**文件**: `test_executor_direct.py`

**功能**: 绕过 FastAPI，直接测试 Agent 执行器是否正常工作。

**运行**:
```bash
cd /home/s8066/agent-project/backend/test
python test_executor_direct.py
```

### 5. FastAPI 接口测试

**文件**: `test_fastapi.py`

**功能**: 测试第2阶段完成的所有 FastAPI 接口。

**运行**:
```bash
cd /home/s8066/agent-project/backend/test
python test_fastapi.py
```

**注意**: 需要先启动 FastAPI 服务：
```bash
cd /home/s8066/agent-project/backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 6. 工具功能测试

**文件**: `test_tools.py`

**功能**: 测试所有工具的基本功能（计算器、文档解析、Python 执行器、记忆搜索、联网搜索）。

**运行**:
```bash
cd /home/s8066/agent-project/backend/test
python test_tools.py
```

### 7. RAG 知识库系统测试

**文件**: `test_rag.py`

**功能**: 测试文档处理、向量化、检索等 RAG 功能。

**运行**:
```bash
cd /home/s8066/agent-project/backend/test
python test_rag.py
```

**依赖**:
- DashScope API（用于 Embedding）
- Qdrant 服务

### 8. DashScope Embedding API 测试

**文件**: `test_dashscope_embedding.py`

**功能**: 测试 DashScope Embedding API 是否正常工作。

**运行**:
```bash
cd /home/s8066/agent-project/backend/test
python test_dashscope_embedding.py
```

### 9. DashScope + Qdrant 详细测试

**文件**: `test_dashscope_qdrant_detailed.py`

**功能**: 详细测试 DashScope Embedding 和 Qdrant 向量库的集成。

**运行**:
```bash
cd /home/s8066/agent-project/backend/test
python test_dashscope_qdrant_detailed.py
```

### 10. Qdrant API 测试

**文件**: `test_qdrant_api.py`

**功能**: 测试 Qdrant API 是否正常工作。

**运行**:
```bash
cd /home/s8066/agent-project/backend/test
python test_qdrant_api.py
```

### 11. 删除 Qdrant 集合

**文件**: `delete_qdrant_collections.py`

**功能**: 清理旧的 Qdrant 集合，用于重新创建。

**运行**:
```bash
cd /home/s8066/agent-project/backend/test
python delete_qdrant_collections.py
```

## 环境配置

### 必需的环境变量

在项目根目录的 `.env` 文件中配置以下环境变量：

```bash
# LLM API（DeepSeek）
LLM_API_KEY=sk-your-deepseek-api-key-here
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL_NAME=deepseek-chat

# DashScope API（用于 Embedding）
DASHSCOPE_API_KEY=sk-your-dashscope-api-key-here
DASHSCOPE_BASE_URL=https://llm-md4indy3r8hlmm10.cn-beijing.maas.aliyuncs.com/compatible-mode/v1
DASHSCOPE_MODEL=qwen3.7-text-embedding

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Tavily API（联网搜索）
TAVILY_API_KEY=tvly-your-tavily-api-key-here

# E2B API（Python 代码沙箱）
E2B_API_KEY=e2b-your-e2b-api-key-here
```

### 启动依赖服务

```bash
# 启动 Redis
docker run -d --name agent-redis -p 6379:6379 redis:alpine

# 启动 Qdrant
docker run -d --name agent-qdrant -p 6333:6333 -p 6334:6334 qdrant/qdrant:v1.12.0

# 启动 MinIO（可选）
docker run -d --name agent-minio -p 9000:9000 -p 9001:9001 minio/minio server /data --console-address ":9001"
```

## 注意事项

1. **路径问题**: 所有测试脚本都使用相对路径，不依赖绝对路径。可以从任意目录运行。

2. **环境变量**: 测试脚本会自动加载项目根目录的 `.env` 文件。

3. **服务依赖**: 部分测试需要先启动依赖服务（Redis、Qdrant、MinIO 等）。

4. **API Key**: 确保 `.env` 文件中配置了正确的 API Key。

5. **Python 环境**: 建议使用虚拟环境：
   ```bash
   cd /home/s8066/agent-project
   source venv/bin/activate
   ```

## 测试结果

所有测试脚本都应该输出类似以下格式的结果：

```
============================================================
测试结果汇总
============================================================
测试1: ✓ 通过
测试2: ✓ 通过
...
============================================================
🎉 所有测试通过！
============================================================
```

如果测试失败，请检查：
1. 环境变量是否正确配置
2. 依赖服务是否启动
3. API Key 是否有效
4. 网络连接是否正常