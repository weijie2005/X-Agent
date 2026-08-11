"""
全局配置管理模块

本模块负责管理整个 FastAPI 应用的配置参数，包括：
- 数据库连接配置（PostgreSQL）
- 缓存服务配置（Redis）
- 向量数据库配置（Qdrant）
- 对象存储配置（MinIO）
- 大语言模型配置（LLM）
- 安全认证配置（JWT）
- 业务参数配置（文件上传、限流等）

配置优先级：
1. 环境变量（最高优先级）
2. .env 文件
3. 默认值（最低优先级）

使用方式：
    from app.config import get_settings
    settings = get_settings()
"""
from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache
from pydantic import model_validator

from app.utils.path_utils import get_env_file_path


class Settings(BaseSettings):
    """
    应用配置类
    
    所有配置项都通过 pydantic-settings 进行类型检查和验证，
    支持从环境变量和 .env 文件自动加载配置。
    """
    
    # ==================== 应用基础配置 ====================
    APP_NAME: str = "Agent Backend"
    """应用名称，用于日志和健康检查"""
    
    APP_VERSION: str = "1.0.0"
    """应用版本号，用于 API 文档和健康检查"""
    
    DEBUG: bool = True
    """
    调试模式开关
    
    - True: 开启调试模式，输出详细日志、SQL 语句等
    - False: 生产模式，减少日志输出
    
    注意：生产环境务必设置为 False
    """
    
    # ==================== PostgreSQL 数据库配置 ====================
    PG_USER: str
    """PostgreSQL 数据库用户名（必填，从 .env 加载）"""
    
    PG_PASSWORD: str
    """PostgreSQL 数据库密码（必填，从 .env 加载）"""
    
    PG_DB: str
    """PostgreSQL 数据库名称（必填，从 .env 加载）"""
    
    PG_HOST: str = "localhost"
    """
    PostgreSQL 数据库主机地址
    
    - 本地开发：localhost
    - Docker 容器：postgres（容器名）
    - 远程服务器：具体 IP 或域名
    """
    
    PG_PORT: int = 5432
    """PostgreSQL 数据库端口，默认 5432"""
    
    # ==================== Redis 缓存配置 ====================
    REDIS_HOST: str = "localhost"
    """
    Redis 服务主机地址
    
    - 本地开发：localhost
    - Docker 容器：redis（容器名）
    """
    
    REDIS_PORT: int = 6379
    """Redis 服务端口，默认 6379"""
    
    REDIS_DB: int = 0
    """Redis 数据库编号，默认使用 0 号数据库"""
    
    # ==================== Qdrant 向量数据库配置 ====================
    QDRANT_HOST: str = "localhost"
    """
    Qdrant 向量数据库主机地址
    
    - 本地开发：localhost
    - Docker 容器：qdrant（容器名）
    """
    
    QDRANT_PORT: int = 6333
    """Qdrant 服务端口，默认 6333（REST API 端口）"""
    
    # ==================== MinIO 对象存储配置 ====================
    MINIO_ROOT_USER: str
    """MinIO 管理员用户名（必填，从 .env 加载）"""
    
    MINIO_ROOT_PASSWORD: str
    """MinIO 管理员密码（必填，从 .env 加载）"""
    
    MINIO_HOST: str = "localhost:9000"
    """
    MinIO 服务地址
    
    - 本地开发：localhost:9000
    - Docker 容器：minio:9000
    """
    
    MINIO_SECURE: bool = False
    """
    是否使用 HTTPS 连接 MinIO
    
    - True: 使用 HTTPS（生产环境推荐）
    - False: 使用 HTTP（开发环境）
    """
    
    # ==================== 大语言模型配置 ====================
    LLM_API_KEY: str
    """LLM API 密钥（必填，从 .env 加载）"""
    
    LLM_BASE_URL: str
    """LLM API 基础地址（必填，从 .env 加载），如：https://api.openai.com/v1"""
    
    LLM_MODEL_NAME: str = "gpt-4"
    """
    默认使用的模型名称
    
    常见选项：
    - gpt-4: GPT-4 模型（推荐）
    - gpt-3.5-turbo: GPT-3.5 模型（更快更便宜）
    - claude-3-opus: Claude 3 模型
    - deepseek-v4-flash: DeepSeek 模型
    
    注意：也可以使用 LLM_MODEL 环境变量（别名）
    """
    
    LLM_MODEL: Optional[str] = None
    """
    模型名称别名（可选）
    
    如果设置了 LLM_MODEL，将覆盖 LLM_MODEL_NAME
    """
    
    LLM_TEMPERATURE: float = 0.7
    """
    模型温度参数（0.0-2.0）
    
    - 0.0: 最确定性，输出最稳定
    - 0.7: 平衡值，适合大多数场景
    - 1.0-2.0: 更随机，适合创意生成
    
    建议：生产环境使用 0.0-0.3，创意场景使用 0.7-1.0
    """
    
    LLM_MAX_TOKENS: int = 2000
    """
    单次请求最大 Token 数
    
    - 值越大，响应越长，但成本越高
    - 建议：对话场景 1000-2000，文档处理 4000+
    """
    
    LLM_TIMEOUT: int = 60
    """LLM API 请求超时时间（秒），默认 60 秒"""
    
    # ==================== Playwright PDF 服务配置 ====================
    PLAYWRIGHT_SERVICE_URL: str = "http://playwright-service:8050"
    """
    Playwright PDF 渲染服务地址
    
    用于将 HTML 转换为 PDF，支持图表、表格等复杂内容导出
    - Docker 容器：http://playwright-service:8050
    - 本地开发：http://localhost:8050
    """
    
    # ==================== CORS 跨域配置 ====================
    CORS_ORIGINS: list = ["http://localhost", "http://localhost:80"]
    """
    允许跨域请求的源地址列表
    
    示例：
    - ["http://localhost:3000"]  # React 开发服务器
    - ["http://localhost:80"]     # Vue 开发服务器
    - ["https://yourdomain.com"]  # 生产域名
    
    注意：生产环境应配置具体的域名，不要使用 ["*"]
    """
    
    # ==================== API 限流配置 ====================
    API_RATE_LIMIT: int = 100
    """
    API 请求限流阈值
    
    在 API_RATE_LIMIT_PERIOD 秒内，单个 IP 最多请求次数
    """
    
    API_RATE_LIMIT_PERIOD: int = 60
    """限流时间窗口（秒），默认 60 秒"""
    
    # ==================== 文件上传配置 ====================
    FILE_MAX_SIZE: int = 50 * 1024 * 1024
    """
    文件上传最大大小（字节）
    
    默认：50MB = 50 * 1024 * 1024
    可根据业务需求调整，如：100MB = 100 * 1024 * 1024
    """
    
    FILE_ALLOWED_EXTENSIONS: list = [".pdf", ".docx", ".doc", ".xlsx", ".xls", ".txt", ".md"]
    """
    允许上传的文件扩展名列表
    
    当前支持：
    - .pdf: PDF 文档
    - .docx/.doc: Word 文档
    - .xlsx/.xls: Excel 表格
    - .txt: 纯文本文件
    - .md: Markdown 文档
    
    可根据需要添加其他格式，如：.pptx, .csv, .json 等
    """
    
    # ==================== JWT 认证配置 ====================
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    """
    JWT 签名密钥
    
    ⚠️ 安全警告：
    - 生产环境必须修改为随机生成的强密钥
    - 建议使用：openssl rand -hex 32 生成
    - 不要在代码库中提交真实密钥
    """
    
    JWT_ALGORITHM: str = "HS256"
    """JWT 加密算法，默认 HS256（对称加密）"""
    
    JWT_EXPIRATION_HOURS: int = 24
    """JWT Token 有效期（小时），默认 24 小时"""
    
    # ==================== Tavily 联网搜索配置 ====================
    TAVILY_API_KEY: str = ""
    """
    Tavily API Key
    
    用于联网搜索功能。获取方式：
    1. 访问 https://tavily.com
    2. 注册账号并创建 API Key
    3. 将 API Key 配置到 .env 文件中
    
    如果不配置，联网搜索功能将不可用。
    """
    
    # ==================== E2B 代码沙箱配置 ====================
    E2B_API_KEY: str = ""
    """
    E2B API Key
    
    用于 Python 代码沙箱执行。获取方式：
    1. 访问 https://e2b.dev
    2. 注册账号并创建 API Key
    3. 将 API Key 配置到 .env 文件中
    
    如果不配置，代码执行功能将不可用。
    """
    
    ALLOW_LOCAL_EXECUTION: bool = False
    """
    是否允许本地代码执行
    
    ⚠️ 安全警告：
    - 生产环境必须设置为 False
    - 仅用于开发测试环境
    - 本地执行存在安全风险，可能被恶意代码利用
    
    默认：False（禁止本地执行）
    """
    
    # ==================== 服务启动配置 ====================
    BACKEND_HOST: str = "0.0.0.0"
    """
    后端服务监听地址
    
    - 0.0.0.0: 监听所有网络接口（推荐）
    - 127.0.0.1: 仅监听本地回环地址
    - 具体IP: 监听指定网络接口
    """
    
    BACKEND_PORT: int = 8080
    """
    后端服务监听端口
    
    默认：8080
    常用端口：8000, 8080, 3000
    """
    
    FRONTEND_HOST: str = "0.0.0.0"
    """
    前端服务监听地址
    
    - 0.0.0.0: 监听所有网络接口
    - 127.0.0.1: 仅监听本地回环地址
    """
    
    FRONTEND_PORT: int = 3000
    """
    前端服务监听端口
    
    默认：3000
    常用端口：3000, 8080, 8000
    """
    
    # ==================== DashScope Embedding 配置 ====================
    DASHSCOPE_API_KEY: str = ""
    """
    DashScope API Key（阿里云向量模型）
    
    用于文本 Embedding 向量化。获取方式：
    1. 访问 https://dashscope.aliyun.com
    2. 开通 DashScope 服务
    3. 创建 API Key
    4. 将 API Key 配置到 .env 文件中
    
    支持的模型：
    - qwen3.7-text-embedding
    - text-embedding-v1
    - text-embedding-v2
    
    如果不配置，将尝试使用 OpenAI API。
    """
    
    DASHSCOPE_BASE_URL: str = ""
    """
    DashScope API Base URL
    
    DashScope API 的基础 URL，兼容 OpenAI 格式。
    
    示例：
    - https://dashscope.aliyuncs.com/compatible-mode/v1
    - https://llm-md4indy3r8hlmm10.cn-beijing.maas.aliyuncs.com/compatible-mode/v1
    
    如果不配置，将使用默认 URL。
    """
    
    DASHSCOPE_MODEL: str = "qwen3.7-text-embedding"
    """
    DashScope Embedding 模型名称
    
    默认：qwen3.7-text-embedding
    
    可选模型：
    - qwen3.7-text-embedding（推荐）
    - text-embedding-v1
    - text-embedding-v2
    """
    
    @model_validator(mode='after')
    def set_llm_model_name(self):
        """
        模型验证器：处理 LLM_MODEL 和 LLM_MODEL_NAME 的关系
        
        如果设置了 LLM_MODEL，则覆盖 LLM_MODEL_NAME
        """
        if self.LLM_MODEL:
            self.LLM_MODEL_NAME = self.LLM_MODEL
        return self
    
    # ==================== Pydantic Settings 配置 ====================
    class Config:
        """Pydantic Settings 配置类"""
        
        env_file = get_env_file_path()
        """
        .env 文件路径
        
        使用动态路径获取，确保项目可迁移。
        
        配置加载顺序：
        1. 系统环境变量（最高优先级）
        2. .env 文件
        3. 类中定义的默认值（最低优先级）
        """
        
        case_sensitive = False
        """
        配置项是否区分大小写
        
        - False: 不区分大小写（推荐）
        - True: 严格区分大小写
        """


@lru_cache()
def get_settings() -> Settings:
    """
    获取配置实例（单例模式）
    
    使用 lru_cache 装饰器确保配置只加载一次，提高性能。
    
    Returns:
        Settings: 配置实例
    
    使用示例：
        >>> from app.config import get_settings
        >>> settings = get_settings()
        >>> print(settings.APP_NAME)
        'Agent Backend'
        >>> print(settings.PG_HOST)
        'localhost'
    
    注意：
        - 首次调用时会加载 .env 文件
        - 后续调用返回缓存的实例
        - 如需重新加载配置，需重启应用
    """
    return Settings()