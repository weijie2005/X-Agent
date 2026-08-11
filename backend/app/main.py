"""
FastAPI 应用入口模块

本模块是整个后端服务的核心入口，负责：
- FastAPI 应用初始化
- 中间件配置（CORS、请求时间、限流等）
- 全局异常处理
- 路由注册
- 应用生命周期管理
- 健康检查接口

架构说明：
- 采用前后端分离架构
- 支持 SSE 流式响应
- 支持文件上传和对象存储
- 集成多种数据存储（PostgreSQL、Redis、Qdrant、MinIO）

使用方式：
    # 开发环境运行
    python -m app.main
    
    # 生产环境运行（推荐）
    uvicorn app.main:app --host 0.0.0.0 --port 8080 --workers 4

API 文档：
    - Swagger UI: http://localhost:8080/docs
    - ReDoc: http://localhost:8080/redoc
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
import logging
import time

from app.config import get_settings
from app.models.database import engine, Base
from app.routers import sessions, files, pdf, agent, auth, knowledge_base
from app.models.schemas import HealthResponse, ErrorResponse
from app.utils.logger import get_logger

# ==================== 配置和日志初始化 ====================

settings = get_settings()
"""
加载应用配置

配置加载顺序：
1. 系统环境变量
2. .env 文件
3. 默认值
"""

logger = get_logger(__name__)
"""获取当前模块的日志记录器"""


# ==================== 应用生命周期管理 ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理器
    
    负责应用启动和关闭时的资源初始化与清理工作。
    
    启动时执行：
    1. 创建数据库表（如果不存在）
    2. 初始化数据库连接池
    3. 初始化 Agent 执行器（含 PostgreSQL checkpoint）
    4. 其他启动任务
    
    关闭时执行：
    1. 关闭数据库连接
    2. 清理 Agent 执行器资源
    3. 清理缓存
    4. 其他清理任务
    
    Args:
        app: FastAPI 应用实例
    
    Yields:
        None
    
    异常处理：
    - 数据库表创建失败会记录错误日志，但不会阻止应用启动
    - 这样设计是为了支持数据库迁移工具（如 Alembic）管理表结构
    
    使用示例：
        >>> # 在 FastAPI 应用中注册
        >>> app = FastAPI(lifespan=lifespan)
    """
    logger.info("Starting up FastAPI application...")
    
    try:
        # 创建所有数据库表
        # 注意：生产环境建议使用 Alembic 进行数据库迁移管理
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
    
    # 初始化 Agent 执行器（含 PostgreSQL checkpoint）
    try:
        from app.services.agent_service import init_agent_executor
        await init_agent_executor()
        logger.info("Agent executor initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing agent executor: {e}", exc_info=True)
        logger.warning("Agent executor initialization failed, checkpoint may not work properly")
    
    # 初始化 Harness 工程管控系统
    try:
        from app.services.agent_service import get_harness_instance
        harness = get_harness_instance()
        if harness:
            logger.info(f"Harness system initialized successfully (ENABLE_HARNESS={settings.ENABLE_HARNESS})")
            logger.info(f"  - Security Interceptor: {harness.security_interceptor is not None}")
            logger.info(f"  - Audit System: {harness.audit_system is not None}")
            logger.info(f"  - Fault Tolerance: {harness.fault_tolerance_system is not None}")
        else:
            logger.info("Harness system is disabled")
    except Exception as e:
        logger.error(f"Error initializing Harness system: {e}", exc_info=True)
        logger.warning("Harness system initialization failed, security features may not work properly")
    
    yield  # 应用运行期间
    
    # 清理资源
    logger.info("Shutting down FastAPI application...")
    
    try:
        from app.services.agent_service import close_agent_executor
        await close_agent_executor()
        logger.info("Agent executor cleaned up successfully")
    except Exception as e:
        logger.error(f"Error cleaning up agent executor: {e}")


# ==================== FastAPI 应用初始化 ====================

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Agent Backend API - FastAPI Service Layer",
    lifespan=lifespan
)
"""
FastAPI 应用实例

配置说明：
- title: 应用名称，显示在 API 文档中
- version: 应用版本号
- description: 应用描述
- lifespan: 生命周期管理器

特性：
- 自动生成 OpenAPI 文档（/docs、/redoc）
- 支持异步请求处理
- 内置数据验证和序列化
- 支持 WebSocket 和 SSE
"""


# ==================== 中间件配置 ====================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
"""
CORS（跨域资源共享）中间件

作用：
- 允许前端应用从不同域名访问后端 API
- 解决浏览器同源策略限制

配置建议：
- 开发环境：允许 localhost
- 生产环境：配置具体的前端域名，不要使用 ["*"]

安全提示：
- allow_credentials=True 时，allow_origins 不能为 ["*"]
- 生产环境务必配置具体的域名
"""


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    请求处理时间中间件
    
    功能：
    - 记录每个请求的处理时间
    - 在响应头中添加 X-Process-Time
    - 记录请求详细信息到日志文件
    
    用途：
    - 性能监控
    - 慢请求排查
    - API 性能优化
    - 审计追踪
    
    Args:
        request: FastAPI 请求对象
        call_next: 下一个中间件或路由处理函数
    
    Returns:
        Response: FastAPI 响应对象
    
    响应头示例：
        X-Process-Time: 0.1234
    
    使用场景：
    - 监控 API 响应时间
    - 识别性能瓶颈
    - 优化慢查询接口
    - 安全审计
    """
    start_time = time.time()
    
    # 获取客户端IP
    client_ip = request.client.host if request.client else "unknown"
    if "x-forwarded-for" in request.headers:
        client_ip = request.headers["x-forwarded-for"].split(",")[0]
    
    # 记录请求开始
    request_logger = get_logger('request', 'request')
    request_logger.info(
        f"Request started: {request.method} {request.url.path}",
        extra={
            'method': request.method,
            'path': request.url.path,
            'client_ip': client_ip,
            'query_params': str(request.query_params) if request.query_params else None
        }
    )
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        # 记录请求完成
        request_logger.info(
            f"Request completed: {request.method} {request.url.path}",
            extra={
                'method': request.method,
                'path': request.url.path,
                'status_code': response.status_code,
                'process_time': process_time,
                'client_ip': client_ip
            }
        )
        
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        
        # 记录请求失败
        request_logger.error(
            f"Request failed: {request.method} {request.url.path} - {str(e)}",
            extra={
                'method': request.method,
                'path': request.url.path,
                'status_code': 500,
                'process_time': process_time,
                'client_ip': client_ip
            },
            exc_info=True
        )
        raise


# ==================== 异常处理器 ====================

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    HTTP 异常处理器
    
    处理所有 HTTP 异常（如 404、403、500 等）
    
    Args:
        request: FastAPI 请求对象
        exc: HTTP 异常实例
    
    Returns:
        JSONResponse: 统一格式的错误响应
    
    响应格式：
        {
            "error": "错误描述"
        }
    
    常见 HTTP 异常：
    - 400: 请求参数错误
    - 401: 未授权
    - 403: 禁止访问
    - 404: 资源不存在
    - 500: 服务器内部错误
    
    示例：
        >>> raise HTTPException(status_code=404, detail="Session not found")
        >>> # 响应: {"error": "Session not found"}
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    请求验证异常处理器
    
    处理 Pydantic 数据验证失败的异常
    
    Args:
        request: FastAPI 请求对象
        exc: 请求验证异常实例
    
    Returns:
        JSONResponse: 包含详细错误信息的响应
    
    响应格式：
        {
            "error": "Validation failed",
            "details": [
                {
                    "field": "body.title",
                    "message": "field required"
                }
            ]
        }
    
    功能：
    - 提取所有验证错误
    - 格式化错误信息
    - 返回友好的错误提示
    
    使用场景：
    - 请求参数缺失
    - 参数类型错误
    - 参数格式不符合要求
    
    示例：
        >>> # 缺少必填字段
        >>> POST /sessions {}
        >>> # 响应: {"error": "Validation failed", "details": [...]}
    """
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation failed",
            "details": errors
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    全局异常处理器
    
    捕获所有未处理的异常，防止应用崩溃
    
    Args:
        request: FastAPI 请求对象
        exc: 异常实例
    
    Returns:
        JSONResponse: 统一的错误响应
    
    响应格式：
        开发环境：
        {
            "error": "Internal server error",
            "detail": "具体错误信息"
        }
        
        生产环境：
        {
            "error": "Internal server error",
            "detail": "An unexpected error occurred"
        }
    
    功能：
    - 记录完整的异常堆栈信息
    - 防止敏感信息泄露（生产环境）
    - 提供详细调试信息（开发环境）
    
    安全考虑：
    - 生产环境不返回详细错误信息
    - 开发环境返回完整异常信息便于调试
    
    日志记录：
    - 使用 logger.error 记录异常堆栈
    - exc_info=True 记录完整堆栈信息
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred"
        }
    )


# ==================== 基础路由 ====================

@app.get("/", tags=["root"])
async def root():
    """
    根路径接口
    
    提供应用基本信息和 API 文档链接
    
    Returns:
        dict: 应用信息
    
    响应示例：
        {
            "message": "Welcome to Agent Backend",
            "version": "1.0.0",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    
    用途：
    - 验证服务是否正常运行
    - 提供 API 文档入口
    - 健康检查（基础）
    """
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """
    健康检查接口
    
    检查所有依赖服务的健康状态
    
    Returns:
        HealthResponse: 健康状态响应
    
    响应示例：
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
    
    检查项：
    1. PostgreSQL 数据库连接
    2. Redis 缓存服务连接
    3. MinIO 对象存储连接
    4. Qdrant 向量数据库连接
    
    状态说明：
    - healthy: 服务正常
    - unhealthy: 服务异常
    - unknown: 检查失败
    
    整体状态：
    - healthy: 所有服务正常
    - degraded: 部分服务异常
    
    用途：
    - 容器编排健康检查
    - 负载均衡器健康检查
    - 监控系统集成
    
    性能考虑：
    - 每次检查都会创建新的连接
    - 设置了超时时间（2秒）
    - 不影响主业务性能
    """
    from app.utils.minio_client import minio_client
    from sqlalchemy import text
    from app.models.database import SessionLocal
    
    services_status = {
        "database": "unknown",
        "redis": "unknown",
        "minio": "unknown",
        "qdrant": "unknown"
    }
    
    # 检查 PostgreSQL 数据库
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        services_status["database"] = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        services_status["database"] = "unhealthy"
    
    # 检查 Redis 缓存
    try:
        import redis
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            socket_connect_timeout=2
        )
        redis_client.ping()
        services_status["redis"] = "healthy"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        services_status["redis"] = "unhealthy"
    
    # 检查 MinIO 对象存储
    try:
        minio_client.client.list_buckets()
        services_status["minio"] = "healthy"
    except Exception as e:
        logger.error(f"MinIO health check failed: {e}")
        services_status["minio"] = "unhealthy"
    
    # 检查 Qdrant 向量数据库
    try:
        from qdrant_client import QdrantClient
        qdrant_client = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT
        )
        qdrant_client.get_collections()
        services_status["qdrant"] = "healthy"
    except Exception as e:
        logger.error(f"Qdrant health check failed: {e}")
        services_status["qdrant"] = "unhealthy"
    
    return HealthResponse(
        status="healthy" if all(s == "healthy" for s in services_status.values()) else "degraded",
        version=settings.APP_VERSION,
        services=services_status
    )


# ==================== 路由注册 ====================

app.include_router(sessions.router, prefix="/api/v1")
"""
注册会话管理路由

路由前缀：/api/v1/sessions
功能：
- 创建会话
- 获取会话列表
- 获取会话详情
- 更新会话
- 删除会话
- 添加消息
- 获取历史消息
"""

app.include_router(files.router, prefix="/api/v1")
"""
注册文件管理路由

路由前缀：/api/v1/files
功能：
- 文件上传
- 文件下载
- 获取文件元数据
- 删除文件
"""

app.include_router(pdf.router, prefix="/api/v1")
"""
注册 PDF 导出路由

路由前缀：/api/v1/pdf
功能：
- 导出会话为 PDF（预留接口）
- 查询导出任务状态（预留接口）
- 下载 PDF 文件（预留接口）
"""

app.include_router(agent.router, prefix="/api/v1")
"""
注册 Agent 对话路由

路由前缀：/api/v1/agent
功能：
- 执行对话（同步）
- 执行对话（流式 SSE）
"""

app.include_router(auth.router, prefix="/api/v1")
"""
注册用户认证路由

路由前缀：/api/v1/auth
功能：
- 用户注册
- 用户登录
- 用户登出
- 获取当前用户信息
"""

app.include_router(knowledge_base.router, prefix="/api/v1")
"""
注册知识库管理路由

路由前缀：/api/v1/knowledge-bases
功能：
- 创建知识库
- 获取知识库列表
- 获取知识库详情
- 更新知识库
- 删除知识库
- 上传文档
- 获取文档列表
- 删除文档
- 检索知识库
"""


# ==================== 主程序入口 ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
"""
主程序入口

直接运行本模块时启动开发服务器

运行方式：
    python -m app.main
    
参数说明：
- host: 监听地址，"0.0.0.0" 表示所有网络接口
- port: 监听端口，默认 8000
- reload: 是否启用热重载，开发环境为 True

生产环境建议：
    使用 gunicorn + uvicorn worker：
    gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker

注意：
- 此方式仅用于开发环境
- 生产环境应使用进程管理器（如 systemd、supervisor）
- 建议使用 Nginx 反向代理
"""